import os
import time
import logging
from typing import List, Dict, Optional, Union, Callable
from datetime import datetime, timedelta
import pytz
from dataclasses import dataclass, asdict

from stocktwits.browser_manager import BrowserManager
from stocktwits.html_parsing import StockTwitsHTMLParser, PostMetrics, PostData


@dataclass
class ScrapingConfig:
    hours_back: int = 24
    max_scroll_time: int = 32
    scroll_increment: int = 20000
    scroll_delay: float = 0.5
    max_retries: int = 3
    timeout: int = 20
    save_intermediate: bool = True


@dataclass
class ScrapingResult:
    ticker: str
    success: bool
    data: Optional[Union[PostMetrics, List[PostData]]]
    error_message: Optional[str] = None
    processing_time: float = 0.0


class RetryStrategy:  
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
    
    def execute_with_retry(self, 
                          func: Callable, 
                          *args, 
                          **kwargs) -> tuple[bool, any]:
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                result = func(*args, **kwargs)
                return True, result
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    time.sleep(self.base_delay)

        return False, last_error


class StockTwitsScraper:
    def __init__(self, 
                 config: Optional[ScrapingConfig] = None,
                 browser_manager: Optional[BrowserManager] = None,
                 html_parser: Optional[StockTwitsHTMLParser] = None,
                 logger: Optional[logging.Logger] = None):
        
        self.config = config or ScrapingConfig()
        self.logger = logger or logging.getLogger(__name__)
        self.browser_manager = browser_manager or BrowserManager(logger=self.logger)
        self.html_parser = html_parser or StockTwitsHTMLParser(logger=self.logger)
        self.retry_strategy = RetryStrategy(max_retries=self.config.max_retries)
        
        # State tracking
        self.is_logged_in = False
        self.scraped_tickers: set = set()
        self.failed_tickers: set = set()
        
    def initialize(self, username: str, password: str) -> bool:
        try:
            self.browser_manager.start()
            
            if self.browser_manager.login_stocktwits(username, password):
                self.is_logged_in = True
                self.logger.info("StockTwits scraper initialized successfully")
                return True
            else:
                self.logger.error("Failed to login to StockTwits")
                return False
                
        except Exception as e:
            self.logger.error(f"Error initializing scraper: {e}")
            return False
    
    def scrape_ticker(self, ticker: str, return_posts: bool = False) -> ScrapingResult:
        start_time = time.time()
        
        if not self.is_logged_in:
            return ScrapingResult(
                ticker=ticker,
                success=False,
                data=None,
                error_message="Scraper not initialized"
            )
        
        try:
            # Calculate target datetime
            target_datetime = datetime.now(pytz.UTC) - timedelta(hours=self.config.hours_back)
            
            # Load the ticker page
            url = f"https://stocktwits.com/symbol/{ticker}"
            if not self.browser_manager.get_page(url):
                return ScrapingResult(
                    ticker=ticker,
                    success=False,
                    data=None,
                    error_message="Failed to load page"
                )
            
            # Validate page content
            html = self.browser_manager.get_page_source()
            if not html:
                return ScrapingResult(
                    ticker=ticker,
                    success=False,
                    data=None,
                    error_message="Failed to get page source"
                )
            
            validation = self.html_parser.validate_page_content(html)
            if not validation["is_valid"]:
                return ScrapingResult(
                    ticker=ticker,
                    success=False,
                    data=None,
                    error_message=validation["error_message"]
                )
            
            # Scroll to load more posts
            self._scroll_to_load_posts(target_datetime)
            
            # Get final HTML and parse
            final_html = self.browser_manager.get_page_source()
            
            if return_posts:
                data = self.html_parser.parse_posts_to_list(final_html, ticker, target_datetime)
            else:
                data = self.html_parser.parse_posts_to_metrics(final_html, ticker, target_datetime)
            
            processing_time = time.time() - start_time
            self.scraped_tickers.add(ticker)
            
            return ScrapingResult(
                ticker=ticker,
                success=True,
                data=data,
                processing_time=processing_time
            )
            
        except Exception as e:
            self.logger.error(f"Error scraping ticker {ticker}: {e}")
            self.failed_tickers.add(ticker)
            
            return ScrapingResult(
                ticker=ticker,
                success=False,
                data=None,
                error_message=str(e),
                processing_time=time.time() - start_time
            )
    
    def scrape_tickers(self, 
                      tickers: List[str], 
                      return_posts: bool = False,
                      progress_callback: Optional[Callable] = None) -> List[ScrapingResult]:

        results = []
        total_tickers = len(tickers)
        
        self.logger.info(f"Starting scraping for {total_tickers} tickers")
        
        for i, ticker in enumerate(tickers):
            self.logger.info(f"Scraping {ticker} ({i+1}/{total_tickers})")
            
            success, result = self.retry_strategy.execute_with_retry(
                self.scrape_ticker, ticker, return_posts
            )
            
            if success:
                results.append(result)
            else:
                # Create failed result
                results.append(ScrapingResult(
                    ticker=ticker,
                    success=False,
                    data=None,
                    error_message=f"Failed after {self.config.max_retries} retries"
                ))
            
            # Progress callback
            if progress_callback:
                progress_callback(i + 1, total_tickers, results[-1])
            
            # Brief delay between tickers
            time.sleep(1)
        
        self.logger.info(f"Scraping completed. Success: {sum(1 for r in results if r.success)}/{total_tickers}")
        return results
    
    def _scroll_to_load_posts(self, target_datetime: datetime) -> None:
        start_time = time.time()
        prev_posts_count = 0
        
        scroll_times = [0, 4, 8, 16, self.config.max_scroll_time]
        
        for scroll_duration in scroll_times:
            while (time.time() - start_time) < scroll_duration:
                self.browser_manager.scroll_page(
                    pixels=self.config.scroll_increment,
                    delay=self.config.scroll_delay
                )
            
            html = self.browser_manager.get_page_source()
            if html:
                if not self.html_parser.check_earliest_post_date(html, target_datetime):
                    self.logger.info("Reached target date, stopping scroll")
                    break
                
                current_posts = html.count(self.html_parser.post_container_class)
                if current_posts == prev_posts_count:
                    self.logger.info("No new posts loaded, stopping scroll")
                    break
                
                prev_posts_count = current_posts
                self.logger.info(f"Loaded {current_posts} posts, continuing scroll...")
    
    def get_scraping_stats(self) -> Dict[str, any]:
        return {
            "scraped_tickers": len(self.scraped_tickers),
            "failed_tickers": len(self.failed_tickers),
            "success_rate": len(self.scraped_tickers) / (len(self.scraped_tickers) + len(self.failed_tickers)) if (self.scraped_tickers or self.failed_tickers) else 0,
            "browser_health": self.browser_manager.get_health_status(),
            "is_logged_in": self.is_logged_in
        }
    
    def save_results_to_file(self, results: List[ScrapingResult], filepath: str) -> bool:
        try:
            import joblib
            
            # Convert results to serializable format
            serializable_data = {}
            for result in results:
                if result.success and result.data:
                    if isinstance(result.data, PostMetrics):
                        # Convert PostMetrics to dict format expected by existing code
                        serializable_data[result.ticker.lower()] = {
                            "hours": result.data.hours,
                            "likes": result.data.likes,
                            "total_mentions": result.data.total_mentions,
                            "total_likes": result.data.total_likes
                        }
                    elif isinstance(result.data, list):
                        # Convert list of PostData to metrics
                        total_mentions = len(result.data)
                        total_likes = sum(post.likes for post in result.data)
                        serializable_data[result.ticker.lower()] = {
                            "total_mentions": total_mentions,
                            "total_likes": total_likes
                        }
            
            with open(filepath, 'wb') as f:
                joblib.dump(serializable_data, f)
            
            self.logger.info(f"Results saved to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving results: {e}")
            return False
    
    def cleanup(self) -> None:
        try:
            self.browser_manager.stop()
            self.is_logged_in = False
            self.logger.info("Scraper cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


# Example usage
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Configuration
    config = ScrapingConfig(
        hours_back=24,
        max_scroll_time=16,
        max_retries=2
    )
    
    # Progress callback
    def progress_callback(current: int, total: int, result: ScrapingResult):
        status = "✓" if result.success else "✗"
        print(f"{status} {current}/{total}: {result.ticker} - {result.processing_time:.2f}s")
    
    # Example usage with context manager
    with StockTwitsScraper(config=config, logger=logger) as scraper:
        # Initialize
        username = os.getenv("STOCK_USER")
        password = os.getenv("STOCK_PASS")
        
        if scraper.initialize(username, password):
            # Scrape some tickers
            tickers = ["NKE"]
            results = scraper.scrape_tickers(
                tickers, 
                return_posts=False,
                progress_callback=progress_callback
            )
            
            # Print results
            print("\nResults:")
            for result in results:
                if result.success:
                    print(f"{result.ticker}: {result.data.total_mentions} mentions, {result.data.total_likes} likes")
                else:
                    print(f"{result.ticker}: Failed - {result.error_message}")
            
            # Save results
            scraper.save_results_to_file(results, "scraping_results.joblib")
            
            # Print stats
            stats = scraper.get_scraping_stats()
            print(f"\nStats: {stats}")
        else:
            print("Failed to initialize scraper")
