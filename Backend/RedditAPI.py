import praw
import logging
from supabase import create_client, Client
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv




logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Load environment variables from .env file
load_dotenv()


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

# Supabase client setup
supabase: Client = create_client(sb_url, sb_key)

def convert_to_iso8601(timestamp):
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return dt.isoformat()

# Function to store post data
def get_data(subreddit_name):
    logger.info(f"Fetching data for subreddit: {subreddit_name}")
    try:
        subreddit = reddit.subreddit(subreddit_name)
        posts = subreddit.new(limit=10)

        for post in posts:
            post_data = {
                'id': post.id,
                'title': post.title,
                'selftext': post.selftext,
                'upvotes': post.ups,
                'downvotes': post.downs,
                'comment_count': post.num_comments,
                'timestamp': convert_to_iso8601(post.created_utc)
            }

            print(post_data)


# process the data that was scraped and then put it into the supabase








    #         # Insert or update post data in Supabase
    #         response = supabase.table('posts').upsert(post_data).execute()
    #         logger.info(f"Supabase response for post: {response}")

    #         # Fetch and store comments
    #         post.comments.replace_more(limit=None)
    #         for comment in post.comments.list():
    #             comment_data = {
    #                 'id': comment.id,
    #                 'post_id': post.id,
    #                 'body': comment.body,
    #                 'author': comment.author.name if comment.author else None,
    #                 'created_utc': convert_to_iso8601(comment.created_utc)
    #             }
    
    #             # Insert or update comment data in Supabase
    #             response = supabase.table('comments').upsert(comment_data).execute()
    #             logger.info(f"Supabase response for comment: {response}")

    except Exception as e:
        logger.error(f"Error fetching or storing data: {e}")

def main():
    subreddit_name = 'chatgpt_promptDesign' 
    get_data(subreddit_name)

if __name__ == "__main__":
    main()