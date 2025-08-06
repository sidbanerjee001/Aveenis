import os
import time
import logging
from typing import List, Dict, Optional, Union, Callable
from datetime import datetime, timedelta
import pytz
from dataclasses import dataclass, asdict

from browser_manager import BrowserManager
from html_parsing import StockTwitsHTMLParser, PostMetrics, PostData


@dataclass
class ScrapingConfig:
    hours_back: int = 24
    max_scroll_time: int = 48
    scroll_increment: int = 20000
    scroll_delay: float = 2
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
    earliest_post_date: Optional[datetime] = None
    latest_post_date: Optional[datetime] = None


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
        self.browser_manager = browser_manager or BrowserManager(headless = False, logger=self.logger)
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
            reached_target_date = self._scroll_to_load_posts(target_datetime)
            
            # Get final HTML and parse
            final_html = self.browser_manager.get_page_source()
            
            if return_posts:
                data = self.html_parser.parse_posts_to_list(final_html, ticker, target_datetime)
                # Extract both earliest and latest post dates from the data
                earliest_post_date, latest_post_date = self._extract_post_date_range(data, return_posts)
            else:
                data = self.html_parser.parse_posts_to_metrics(final_html, ticker, target_datetime, reached_target_date)
                # For metrics, get both earliest and latest post dates directly from HTML
                earliest_post_date, latest_post_date = self._get_post_date_range_from_html(final_html, ticker, target_datetime)
            
            processing_time = time.time() - start_time
            self.scraped_tickers.add(ticker)
            
            return ScrapingResult(
                ticker=ticker,
                success=True,
                data=data,
                processing_time=processing_time,
                earliest_post_date=earliest_post_date,
                latest_post_date=latest_post_date
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
                      progress_callback: Optional[Callable] = None,
                      output_file: Optional[str] = None) -> List[ScrapingResult]:

        results = []
        total_tickers = len(tickers)
        
        self.logger.info(f"Starting scraping for {total_tickers} tickers")
        
        # Load existing results if output file exists
        existing_results = {}
        if output_file and os.path.exists(output_file):
            try:
                import joblib
                with open(output_file, 'rb') as f:
                    existing_results = joblib.load(f)
                self.logger.info(f"Loaded {len(existing_results)} existing results from {output_file}")
            except Exception as e:
                self.logger.warning(f"Could not load existing results: {e}")
        
        for i, ticker in enumerate(tickers):
            # Skip if already completed
            if ticker.lower() in existing_results:
                self.logger.info(f"Skipping {ticker} - already completed ({i+1}/{total_tickers})")
                # Create a dummy successful result for progress tracking
                results.append(ScrapingResult(
                    ticker=ticker,
                    success=True,
                    data=None,  # We don't need to load the data
                    processing_time=0.0
                ))
                if progress_callback:
                    progress_callback(i + 1, total_tickers, results[-1])
                continue
            
            self.logger.info(f"Scraping {ticker} ({i+1}/{total_tickers})")
            
            success, result = self.retry_strategy.execute_with_retry(
                self.scrape_ticker, ticker, return_posts
            )
            
            if success:
                results.append(result)
                
                # Save immediately after successful scraping
                if output_file and result.success and result.data:
                    try:
                        self._save_single_result_to_file(result, output_file, existing_results)
                        self.logger.info(f"Saved {ticker} to {output_file}")
                    except Exception as e:
                        self.logger.error(f"Failed to save {ticker}: {e}")
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
    
    def _extract_post_date_range(self, data: Optional[Union[PostMetrics, List[PostData]]], return_posts: bool) -> tuple[Optional[datetime], Optional[datetime]]:
        """Extract both earliest (oldest) and latest (newest) post dates from the scraped data."""
        if not data:
            return None, None
            
        try:
            if return_posts and isinstance(data, list):
                # When return_posts=True, data is List[PostData]
                if not data:
                    return None, None
                # Find both earliest and latest post dates from all posts
                post_dates = [post.datetime_object for post in data]
                earliest_date = min(post_dates)
                latest_date = max(post_dates)
                return earliest_date, latest_date
            else:
                # When return_posts=False, data is PostMetrics
                # We don't have individual post dates in PostMetrics, so we'll need to
                # get this information from the HTML parsing process
                return None, None
        except Exception as e:
            self.logger.warning(f"Error extracting post date range: {e}")
            return None, None
    
    def _get_post_date_range_from_html(self, html: str, ticker: str, target_datetime: datetime) -> tuple[Optional[datetime], Optional[datetime]]:
        """Extract both earliest (oldest) and latest (newest) post dates directly from HTML."""
        try:
            # Parse posts to get the date range
            posts = self.html_parser.parse_posts_to_list(html, ticker, target_datetime)
            if posts:
                # Return both earliest and latest dates among all posts
                post_dates = [post.datetime_object for post in posts]
                earliest_date = min(post_dates)
                latest_date = max(post_dates)
                return earliest_date, latest_date
            return None, None
        except Exception as e:
            self.logger.warning(f"Error extracting post date range from HTML: {e}")
            return None, None
    
    def _scroll_to_load_posts(self, target_datetime: datetime) -> bool:
        """
        Scroll to load posts until target date is reached or no more posts load.
        Returns True if target date was reached, False otherwise.
        """
        scroll_times = [2, 4, 8, 16, self.config.max_scroll_time]
        prev_posts_count = 0
        reached_target_date = False
        
        for scroll_duration in scroll_times:
            start_time = time.time()
            print(scroll_duration)
            while (time.time() - start_time) < scroll_duration:
                self.browser_manager.scroll_page(
                    pixels=self.config.scroll_increment,
                    delay=self.config.scroll_delay
                )
            
            html = self.browser_manager.get_page_source()
            if html:
                if not self.html_parser.check_earliest_post_date(html, target_datetime):
                    self.logger.info("Reached target date, stopping scroll")
                    reached_target_date = True
                    break
                
                current_posts = html.count(self.html_parser.post_container_class)
                if current_posts == prev_posts_count:
                    self.logger.info("No new posts loaded, stopping scroll")
                    break
                
                prev_posts_count = current_posts
                self.logger.info(f"Loaded {current_posts} posts, continuing scroll...")
                # self.logger.info(f"Loaded posts, continuing scroll...")
        
        return reached_target_date
    
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
                            "total_likes": result.data.total_likes,
                            "reached_target_date": result.data.reached_target_date
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
    
    def _save_single_result_to_file(self, result: ScrapingResult, filepath: str, existing_results: dict = None) -> bool:
        """Save a single scraping result to a joblib file incrementally"""
        try:
            import joblib
            
            # Load existing results if not provided
            if existing_results is None:
                if os.path.exists(filepath):
                    with open(filepath, 'rb') as f:
                        existing_results = joblib.load(f)
                else:
                    existing_results = {}
            
            # Convert single result to serializable format
            if result.success and result.data:
                if isinstance(result.data, PostMetrics):
                    existing_results[result.ticker.lower()] = {
                        "hours": result.data.hours,
                        "likes": result.data.likes,
                        "total_mentions": result.data.total_mentions,
                        "total_likes": result.data.total_likes,
                        "reached_target_date": result.data.reached_target_date,
                        "earliest_post_date": result.earliest_post_date.isoformat() if result.earliest_post_date else None,
                        "latest_post_date": result.latest_post_date.isoformat() if result.latest_post_date else None
                    }
                elif isinstance(result.data, list):
                    # Convert list of PostData to metrics
                    total_mentions = len(result.data)
                    total_likes = sum(post.likes for post in result.data)
                    existing_results[result.ticker.lower()] = {
                        "total_mentions": total_mentions,
                        "total_likes": total_likes,
                        "earliest_post_date": result.earliest_post_date.isoformat() if result.earliest_post_date else None,
                        "latest_post_date": result.latest_post_date.isoformat() if result.latest_post_date else None
                    }
                
                # Save back to file
                with open(filepath, 'wb') as f:
                    joblib.dump(existing_results, f)
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to save single result for {result.ticker}: {e}")
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
            tickers = ["TSLA"]
            results = scraper.scrape_tickers(
                tickers, 
                return_posts=False,
                progress_callback=progress_callback
            )
            
            # Print results
            print("\nResults:")
            for result in results:
                if result.success:
                    date_info = ""
                    if result.earliest_post_date:
                        date_info += f", Earliest post: {result.earliest_post_date}"
                    if result.latest_post_date:
                        date_info += f", Latest post: {result.latest_post_date}"
                    if not date_info:
                        date_info = ", No post dates available"
                    print(f"{result.ticker}: {result.data.total_mentions} mentions, {result.data.total_likes} likes{date_info}")
                else:
                    print(f"{result.ticker}: Failed - {result.error_message}")
            
            # Save results
            scraper.save_results_to_file(results, "scraping_results.joblib")
            
            print(results)
            # Print stats
            stats = scraper.get_scraping_stats()
            print(f"\nStats: {stats}")
        else:
            print("Failed to initialize scraper")
