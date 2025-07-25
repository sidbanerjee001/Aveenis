from dataclasses import dataclass
from typing import List, Dict, Optional, Union
from datetime import datetime, timedelta
import pytz
from bs4 import BeautifulSoup
import logging


@dataclass
class PostData:
    # Data class for single stocktwits post
    message: str
    date: str
    likes: int
    datetime_object: datetime
    ticker: str


@dataclass
class PostMetrics:
    # Data class for aggregated post metrics
    hours: List[int]  # 24-hour array of post counts
    likes: List[int]  # 24-hour array of like counts
    total_mentions: int
    total_likes: int
    ticker: str


class StockTwitsHTMLParser:
    """
    Handles all HTML parsing logic for StockTwits pages.
    Separated from driver management for better testability and maintainability.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.post_container_class = "StreamMessage_container__omTCg"
        self.message_class = "RichTextMessage_body__4qUeP whitespace-pre-wrap"
        self.like_count_class = "StreamMessageLabelCount_labelCount__dWyPL mr-1 text-dark-grey-2 dark|text-stream-text"
    
    def is_within_timeframe(self, target_datetime: datetime, post_datetime: datetime) -> bool:
        return target_datetime - post_datetime < timedelta(0)
    
    def extract_post_data(self, twit_element) -> Optional[PostData]:
        try:
            # Extract message
            message_element = twit_element.find('div', class_=self.message_class)
            if not message_element:
                self.logger.warning("Message element not found")
                return None
            message = message_element.get_text(strip=True)
            
            # Extract date
            time_element = twit_element.find('time')
            if not time_element or 'datetime' not in time_element.attrs:
                self.logger.warning("Time element not found")
                return None
            date_info = time_element['datetime']
            
            # Extract likes
            like_spans = twit_element.find_all('span', class_=self.like_count_class)
            likes = 0
            if len(like_spans) > 2 and like_spans[2].text:
                try:
                    likes = int(like_spans[2].text.replace(',', ''))
                except ValueError:
                    likes = 0
            
            # Parse datetime
            datetime_object = datetime.strptime(date_info, "%Y-%m-%dT%H:%M:%SZ")
            datetime_object = pytz.UTC.localize(datetime_object)
            
            return PostData(
                message=message,
                date=date_info,
                likes=likes,
                datetime_object=datetime_object,
                ticker=""  # Will be set by caller
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting post data: {e}")
            return None
    
    def check_earliest_post_date(self, html: str, target_datetime: datetime) -> bool:
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            twits = soup.find_all('div', class_=self.post_container_class)
            earliest_twit = twits[-1]

            time_element = earliest_twit.find('time')
            if not time_element or 'datetime' not in time_element.attrs:
                return False
            
            date_of_post = datetime.strptime(time_element['datetime'], "%Y-%m-%dT%H:%M:%SZ")
            date_of_post = pytz.UTC.localize(date_of_post)
            
            return self.is_within_timeframe(target_datetime, date_of_post)
            
        except Exception as e:
            self.logger.error(f"Error checking earliest post date: {e}")
            return False
    
    def parse_posts_to_metrics(self, html: str, ticker: str, target_datetime: datetime) -> PostMetrics:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all post containers
        twit_elements = soup.find_all('div', class_=self.post_container_class)
        
        if not twit_elements:
            self.logger.warning(f"No posts found for ticker {ticker}")
            return PostMetrics(
                hours=[0] * 24,
                likes=[0] * 24,
                total_mentions=0,
                total_likes=0,
                ticker=ticker
            )
        
        # Initialize hourly arrays
        hourly_posts = [0] * 24
        hourly_likes = [0] * 24
        
        processed_posts = 0
        
        for twit_element in twit_elements:
            post_data = self.extract_post_data(twit_element)
            if not post_data:
                continue
                
            # Check if post is within timeframe
            if not self.is_within_timeframe(target_datetime, post_data.datetime_object):
                continue
            
            # Add to hourly buckets
            hour = post_data.datetime_object.hour
            hourly_posts[hour] += 1
            hourly_likes[hour] += post_data.likes
            processed_posts += 1
        
        total_mentions = sum(hourly_posts)
        total_likes = sum(hourly_likes)
        
        self.logger.info(f"Processed {processed_posts} posts for {ticker}: {total_mentions} mentions, {total_likes} likes")
        
        return PostMetrics(
            hours=hourly_posts,
            likes=hourly_likes,
            total_mentions=total_mentions,
            total_likes=total_likes,
            ticker=ticker
        )
    
    def parse_posts_to_list(self, html: str, ticker: str, target_datetime: datetime) -> List[PostData]:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all post containers
        twit_elements = soup.find_all('div', class_=self.post_container_class)
        
        if not twit_elements:
            self.logger.warning(f"No posts found for ticker {ticker}")
            return []
        
        posts = []
        
        for twit_element in twit_elements:
            post_data = self.extract_post_data(twit_element)
            if not post_data:
                continue
                
            # Check if post is within timeframe
            if not self.is_within_timeframe(target_datetime, post_data.datetime_object):
                continue
            
            post_data.ticker = ticker
            posts.append(post_data)
        
        self.logger.info(f"Extracted {len(posts)} posts for {ticker}")
        return posts
    
    def validate_page_content(self, html: str) -> Dict[str, Union[bool, str]]:

        soup = BeautifulSoup(html, 'html.parser')
        
        # Check for 404 page
        is_404 = "Page Not Found - 404 - Symbol Page" in html
        
        # Check for expected elements
        has_feed = bool(soup.find(class_="SymbolStream_container__SRJQv"))
        has_posts = bool(soup.find_all('div', class_=self.post_container_class))
        
        # Check for login requirement
        needs_login = "Sign In" in html and not has_posts
        
        return {
            "is_valid": not is_404 and has_feed,
            "is_404": is_404,
            "has_feed": has_feed,
            "has_posts": has_posts,
            "needs_login": needs_login,
            "error_message": self._get_error_message(is_404, has_feed, has_posts, needs_login)
        }
    
    def _get_error_message(self, is_404: bool, has_feed: bool, has_posts: bool, needs_login: bool) -> Optional[str]:
        """Generate appropriate error message based on validation results"""
        if is_404:
            return "Page not found (404)"
        elif needs_login:
            return "Login required"
        elif not has_feed:
            return "Feed container not found"
        elif not has_posts:
            return "No posts found"
        return None


# Ex
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Create parser instance
    parser = StockTwitsHTMLParser(logger)
    
    # Example HTML
    with open("sample_html.txt", "r") as f:
        sample_html = f.read()
        
    # Test validation
    validation = parser.validate_page_content(sample_html)
    print(f"Validation: {validation}")
    
    # Should return all posts within the last 24 hours
    target_datetime = datetime.now(pytz.UTC) - timedelta(hours=24)
    metrics = parser.parse_posts_to_metrics(sample_html, "AAPL", target_datetime)
    print(f"Metrics: {metrics}")
    
    posts = parser.parse_posts_to_list(sample_html, "AAPL", target_datetime)
    print(f"Posts: {posts}")