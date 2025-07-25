import os
import time
import logging
import multiprocessing
import threading
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

from stocktwits.stocktwits_scraper import StockTwitsScraper, ScrapingConfig
from stocktwits.browser_manager import BrowserManager


class ProcessState(Enum):
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAILED = "failed"
    RESTARTING = "restarting"


@dataclass
class MonitoringConfig:
    file_check_interval: int = 30  # seconds between file checks
    max_file_age: int = 100  # seconds before file is considered stale
    min_runtime: int = 120  # minimum runtime before restart is allowed
    max_restarts: int = 10  # maximum restarts before giving up
    restart_delay: int = 5  # seconds to wait before restart
    health_check_interval: int = 30  # seconds between health checks
    progress_timeout: int = 300  # seconds without progress before restart
    ticker_file: str = "tickers.txt"  # file containing target tickers


@dataclass
class ProcessHealth:
    state: ProcessState
    last_file_update: Optional[datetime]
    runtime: float
    restart_count: int
    last_error: Optional[str]
    progress_stalled: bool
    file_exists: bool
    tickers_completed: int = 0
    total_tickers: int = 0
    completion_rate: float = 0.0


class ProcessSupervisor:
    def __init__(self, 
                 config: Optional[MonitoringConfig] = None,
                 scraping_config: Optional[ScrapingConfig] = None,
                 logger: Optional[logging.Logger] = None):
        
        self.config = config or MonitoringConfig()
        self.scraping_config = scraping_config or ScrapingConfig()
        self.logger = logger or logging.getLogger(__name__)
        
        # Process management
        self.process: Optional[multiprocessing.Process] = None
        self.stop_event = multiprocessing.Event()
        self.restart_event = multiprocessing.Event()
        
        # State tracking
        self.state = ProcessState.IDLE
        self.start_time: Optional[datetime] = None
        self.restart_count = 0
        self.last_file_mtime: Optional[float] = None
        self.last_progress_time: Optional[datetime] = None
        self.shutdown_requested = False
        
        # Ticker completion tracking
        self.target_tickers: set = set()
        self.completed_tickers: set = set()
        
        # Monitoring thread
        self.monitor_thread: Optional[threading.Thread] = None
        self.monitor_running = False
    
    def start_monitoring(self, 
                        target_function: Callable,
                        target_args: tuple = (),
                        target_kwargs: Dict = None,
                        monitor_file: Optional[str] = None) -> bool:

        if self.monitor_running:
            self.logger.warning("Monitoring already running")
            return False
        
        try:
            self.target_function = target_function
            self.target_args = target_args or ()
            self.target_kwargs = target_kwargs or {}
            self.monitor_file = monitor_file
            
            # Load target tickers from file
            self._load_target_tickers()
            
            # Reset state
            self.shutdown_requested = False
            self.restart_count = 0
            self.completed_tickers.clear()
            self.stop_event.clear()
            self.restart_event.clear()
            
            # Start monitoring thread
            self.monitor_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self.monitor_running = True
            self.monitor_thread.start()
            
            self.logger.info("Process monitoring started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start monitoring: {e}")
            return False
    
    def stop_monitoring(self, timeout: int = 30) -> bool:
        self.logger.info("Stopping process monitoring...")
        self.shutdown_requested = True
        
        # Stop the subprocess
        if self.process and self.process.is_alive():
            self.stop_event.set()
            self.process.join(timeout=timeout)
            
            if self.process.is_alive():
                self.logger.warning("Process didn't stop gracefully, terminating...")
                self.process.terminate()
                self.process.join(timeout=5)
                
                if self.process.is_alive():
                    self.logger.error("Process didn't terminate, killing...")
                    self.process.kill()
                    self.process.join()
        
        # Stop monitoring thread
        self.monitor_running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        
        self.state = ProcessState.IDLE
        self.logger.info("Process monitoring stopped")
        return True
    
    def _monitoring_loop(self) -> None:
        while self.monitor_running and not self.shutdown_requested:
            try:
                # Start process if not running
                if not self.process or not self.process.is_alive():
                    if self.restart_count >= self.config.max_restarts:
                        self.logger.error(f"Maximum restarts ({self.config.max_restarts}) reached. Stopping monitoring.")
                        break
                    
                    self._start_process()
                
                # Check process health
                health = self._check_process_health()
                
                # Check if all tickers are completed
                if self._all_tickers_completed():
                    self.logger.info(f"All {len(self.target_tickers)} tickers completed successfully. Stopping monitoring.")
                    self.shutdown_requested = True
                    break
                
                # Decide if restart is needed
                if self._should_restart(health):
                    self.logger.info("Restart condition detected")
                    self._restart_process()
                
                # Log health status periodically
                if self.restart_count % (self.config.health_check_interval // self.config.file_check_interval) == 0:
                    self._log_health_status(health)
                
                time.sleep(self.config.file_check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.config.file_check_interval)
        
        self.logger.info("Monitoring loop ended")
    
    def _start_process(self) -> None:
        try:
            self.logger.info("Starting new process...")
            self.state = ProcessState.STARTING
            
            self.stop_event = multiprocessing.Event()
            self.restart_event = multiprocessing.Event()
            
            self.process = multiprocessing.Process(
                target=self.target_function,
                args=self.target_args + (self.stop_event, self.restart_event),
                kwargs=self.target_kwargs
            )
            self.process.start()
            
            self.start_time = datetime.now()
            self.last_progress_time = datetime.now()
            self.state = ProcessState.RUNNING
            
            self.logger.info(f"Process started")
            
        except Exception as e:
            self.logger.error(f"Failed to start process: {e}")
            self.state = ProcessState.FAILED
    
    def _restart_process(self) -> None:
        try:
            self.logger.info("Restarting process...")
            self.state = ProcessState.RESTARTING
            self.restart_count += 1
            
            # Stop current process
            if self.process and self.process.is_alive():
                self.stop_event.set()
                self.process.join(timeout=10)
                
                if self.process.is_alive():
                    self.logger.warning("Process didn't stop gracefully, terminating...")
                    self.process.terminate()
                    self.process.join(timeout=5)
            
            # Wait before restart
            time.sleep(self.config.restart_delay)
            
            # Start new process
            self._start_process()
            
        except Exception as e:
            self.logger.error(f"Failed to restart process: {e}")
            self.state = ProcessState.FAILED
    
    def _check_process_health(self) -> ProcessHealth:
        file_exists = False
        last_file_update = None
        progress_stalled = False
        
        # Update completed tickers from joblib file
        self._update_completed_tickers()
        
        # Check monitored file if specified
        if self.monitor_file and os.path.exists(self.monitor_file):
            file_exists = True
            current_mtime = os.path.getmtime(self.monitor_file)
            last_file_update = datetime.fromtimestamp(current_mtime)
            
            # Check if file has been updated
            if self.last_file_mtime is not None and current_mtime != self.last_file_mtime:
                self.last_progress_time = datetime.now()
            
            self.last_file_mtime = current_mtime
            
            # Check for stalled progress
            if self.last_progress_time:
                time_since_progress = (datetime.now() - self.last_progress_time).total_seconds()
                progress_stalled = time_since_progress > self.config.progress_timeout
        
        # Calculate runtime
        runtime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        # Calculate completion metrics
        total_tickers = len(self.target_tickers)
        completed_tickers = len(self.completed_tickers)
        completion_rate = completed_tickers / total_tickers if total_tickers > 0 else 0.0
        
        return ProcessHealth(
            state=self.state,
            last_file_update=last_file_update,
            runtime=runtime,
            restart_count=self.restart_count,
            last_error=None,
            progress_stalled=progress_stalled,
            file_exists=file_exists,
            tickers_completed=completed_tickers,
            total_tickers=total_tickers,
            completion_rate=completion_rate
        )
    
    def _should_restart(self, health: ProcessHealth) -> bool:
        # Don't restart if we haven't been running long enough
        if health.runtime < self.config.min_runtime:
            return False
        
        # Check if restart was explicitly requested
        if self.restart_event.is_set():
            self.restart_event.clear()
            print("Restart requested")
            return True
        
        # Check if process is dead
        if not self.process or not self.process.is_alive():
            print("Process dead")
            return True
        
        # Check file-based conditions
        if self.monitor_file and health.file_exists and health.last_file_update:
            file_age = (datetime.now() - health.last_file_update).total_seconds()
            
            # File too old and we've been running long enough
            print(f"File age: {file_age} seconds")
            if file_age > self.config.max_file_age and health.runtime > self.config.min_runtime:
                return True
        
        # Check for stalled progress
        if health.progress_stalled:
            print("STALLED")
            return True
        
        return False
    
    def _log_health_status(self, health: ProcessHealth) -> None:
        status_msg = f"Process Health - State: {health.state.value}, Runtime: {health.runtime:.1f}s, Restarts: {health.restart_count}"
        status_msg += f", Progress: {health.tickers_completed}/{health.total_tickers} ({health.completion_rate:.1%})"
        
        if self.monitor_file:
            if health.file_exists and health.last_file_update:
                file_age = (datetime.now() - health.last_file_update).total_seconds()
                status_msg += f", File age: {file_age:.1f}s"
            else:
                status_msg += ", File: not found"
        
        if health.progress_stalled:
            status_msg += " [STALLED]"
        
        # Show remaining tickers if not too many
        remaining = self.target_tickers - self.completed_tickers
        if len(remaining) <= 10:
            status_msg += f", Remaining: {sorted(list(remaining))}"
        
        self.logger.info(status_msg)
    
    def get_status(self) -> Dict[str, Any]:
        health = self._check_process_health()
        
        return {
            "monitoring_active": self.monitor_running,
            "process_state": self.state.value,
            "process_alive": self.process.is_alive() if self.process else False,
            "process_pid": self.process.pid if self.process else None,
            "runtime": health.runtime,
            "restart_count": self.restart_count,
            "max_restarts": self.config.max_restarts,
            "file_monitored": self.monitor_file,
            "file_exists": health.file_exists,
            "last_file_update": health.last_file_update.isoformat() if health.last_file_update else None,
            "progress_stalled": health.progress_stalled
        }
    
    def request_restart(self) -> bool:
        if self.monitor_running:
            self.restart_event.set()
            self.logger.info("Restart requested")
            return True
        return False
    
    def _load_target_tickers(self) -> None:
        """Load target tickers from the ticker file"""
        try:
            ticker_file = self.config.ticker_file
            if os.path.exists(ticker_file):
                with open(ticker_file, 'r') as f:
                    tickers = [line.strip().lower() for line in f.readlines() if line.strip()]
                self.target_tickers = set(tickers)
                self.logger.info(f"Loaded {len(self.target_tickers)} target tickers from {ticker_file}")
            else:
                self.logger.warning(f"Ticker file {ticker_file} not found")
                self.target_tickers = set()
        except Exception as e:
            self.logger.error(f"Error loading target tickers: {e}")
            self.target_tickers = set()
    
    def _update_completed_tickers(self) -> None:
        """Update the set of completed tickers from the joblib file"""
        try:
            if self.monitor_file and os.path.exists(self.monitor_file):
                import joblib
                with open(self.monitor_file, 'rb') as f:
                    results = joblib.load(f)
                
                # Extract ticker keys (they should be lowercase)
                if isinstance(results, dict):
                    completed = set(key.lower() for key in results.keys() if key is not None)
                    
                    # Check for new completions
                    new_completions = completed - self.completed_tickers
                    if new_completions:
                        self.logger.info(f"New completions detected: {sorted(list(new_completions))}")
                    
                    self.completed_tickers = completed
                else:
                    self.logger.warning("Joblib file doesn't contain expected dictionary format")
        except Exception as e:
            self.logger.debug(f"Error updating completed tickers: {e}")
    
    def _all_tickers_completed(self) -> bool:
        """Check if all target tickers have been completed"""
        if not self.target_tickers:
            return False
        
        return self.target_tickers.issubset(self.completed_tickers)
    
    def get_remaining_tickers(self) -> set:
        """Get the set of tickers that still need to be processed"""
        return self.target_tickers - self.completed_tickers


def run_supervised_scraping(username: str, 
                          password: str,
                          tickers: List[str],
                          output_file: str,
                          monitoring_config: Optional[MonitoringConfig] = None,
                          scraping_config: Optional[ScrapingConfig] = None) -> None:

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('supervisor.log'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    
    # Create supervisor
    supervisor = ProcessSupervisor(
        config=monitoring_config,
        scraping_config=scraping_config,
        logger=logger
    )
    
    def scraping_worker(stop_event, restart_event):
        """Worker function that runs the actual scraping"""
        try:
            with StockTwitsScraper(config=scraping_config, logger=logger) as scraper:
                if scraper.initialize(username, password):
                    results = scraper.scrape_tickers(tickers)
                    scraper.save_results_to_file(results, output_file)
                    logger.info("Scraping completed successfully")
                    supervisor.shutdown_requested = True
                else:
                    logger.error("Failed to initialize scraper")
                    restart_event.set()
        except Exception as e:
            logger.error(f"Scraping worker error: {e}")
            restart_event.set()
    
    try:
        if supervisor.start_monitoring(
            target_function=scraping_worker,
            monitor_file=output_file
        ):
            logger.info("Supervised scraping started.")
            
            while supervisor.monitor_running:
                time.sleep(10)
                status = supervisor.get_status()
                if status["restart_count"] >= supervisor.config.max_restarts:
                    logger.error("Maximum restarts reached. Stopping.")
                    break
        
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    finally:
        supervisor.stop_monitoring()


# Example usage
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Configuration
    monitoring_config = MonitoringConfig(
        max_file_age=120,
        min_runtime=60,
        max_restarts=5
    )
    
    scraping_config = ScrapingConfig(
        hours_back=24,
        max_retries=2
    )
    
    # Run supervised scraping
    run_supervised_scraping(
        username=os.getenv("STOCK_USER"),
        password=os.getenv("STOCK_PASS"),
        tickers=["NKE"],
        output_file="supervised_results.joblib",
        monitoring_config=monitoring_config,
        scraping_config=scraping_config
    )
