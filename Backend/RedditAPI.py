import praw
import logging
# from supabase import create_client, Client
# from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, timedelta, timezone
import os
# from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
# load_dotenv()


# Access environment variables
reddit_client_id = os.environ.get('reddit_client_id')
reddit_client_secret = os.environ.get('reddit_client_secret')
reddit_user_agent = os.environ.get('reddit_user_agent')
sb_url = os.environ.get('sb_url')
sb_key = os.environ.get('sb_key')

# Print out environment variables to check if they are loaded correctly
print(f"Reddit Client ID: {reddit_client_id}")
print(f"Supabase URL: {sb_url}")


# Check if required environment variables are loaded
if not reddit_client_id or not reddit_client_secret or not reddit_user_agent:
    raise ValueError("Missing one or more Reddit API credentials")

if not sb_url or not sb_key:
    raise ValueError("Missing Supabase URL or Key")

# Reddit API setup
reddit = praw.Reddit(
    client_id=reddit_client_id,
    client_secret=reddit_client_secret,
    user_agent=reddit_user_agent
)


# ===================================================================== Useful Shit ================================

# Supabase client setup
# supabase: Client = create_client(sb_url, sb_key)

# def convert_to_iso8601(timestamp):
#     dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
#     return dt.isoformat()


# Load tickers from file
current_dir = os.path.dirname(__file__)
ticker_filepath = os.path.join(current_dir, 'tickers.txt')

with open(ticker_filepath, 'r') as file:
    tickers = file.read().splitlines()


# Function to store post data
def get_data(subreddit_name):
    logger.info(f"Fetching data for subreddit: {subreddit_name}")
    
    list_to_return = {ticker : [0, 0] for ticker in tickers}


    try:
        subreddit = reddit.subreddit(subreddit_name)
        posts = subreddit.new(limit=10)

        for post in posts:
            post_text = post.selftext

            # Fetch comments
            post.comments.replace_more(limit=None)
            comments_text = " ".join(comment.body for comment in post.comments.list())
            post_and_comments_text = post_text + " " + comments_text

            for ticker in tickers:
                raw_mentions = post_and_comments_text.count(ticker)
                list_to_return[ticker][0] += raw_mentions
                list_to_return[ticker][1] += post.ups
                
        return list_to_return

    except Exception as e:
        logger.error(f"Error fetching or storing data: {e}")





# Main
def main():
    subreddit_name = 'chatgpt_promptDesign' 
    get_data(subreddit_name)

if __name__ == "__main__":
    main()



