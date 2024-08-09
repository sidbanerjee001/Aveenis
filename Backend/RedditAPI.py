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
# print(f"Reddit Client ID: {reddit_client_id}")
# print(f"Supabase URL: {sb_url}")


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



# Create directory to store reddit posts and comments
output_dir = 'reddit_posts'
os.makedirs(output_dir, exist_ok=True)




# Function to store post data
def get_data(subreddit_name):
    logger.info(f"Fetching data for subreddit: {subreddit_name}")
    try:
        subreddit = reddit.subreddit(subreddit_name)
        posts = subreddit.top(limit=10)

        for post in posts:
            post.comments.replace_more(limit=None)
            valid_title = ''.join(letter if letter.isalnum() else '_' for letter in post.title)
            file_name = f"{valid_title}_{post.id}.txt"
            filepath = os.path.join(output_dir, file_name)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Post title: {post.title}\n")
                f.write(f"Post id: {post.id}\n")
                f.write(f"Post text/body: {post.selftext}\n\n")
                f.write(f"Post upvotes: {post.ups}\n")
                f.write(f"Post downvotes: {post.downs}\n")
                f.write(f"Number of comments: {post.num_comments}\n")
                f.write(f"Time post was created in UTC: {convert_to_iso8601(post.created_utc)}\n")

                comment_counter = 1
                f.write(f"\nComments for the post begin here:\n\n")
                for comment in post.comments.list():
                    f.write(f"Comment number {comment_counter}, id: {comment.id}\n")
                    f.write(f"Comment author: {comment.author if comment.author else None}\n")
                    f.write(f"Comment text/body: {comment.body}\n")
                    f.write(f"Comment upvotes: {comment.ups}\n")
                    f.write(f"Comment downvotes: {comment.downs}\n")
                    f.write(f"Time comment was created in UTC: {convert_to_iso8601(comment.created_utc)}\n\n")
                    comment_counter+=1



            # # Insert or update post data in Supabase
            # response = supabase.table('posts').upsert(post_data).execute()
            # logger.info(f"Supabase response for post: {response}")

    
            # # Insert or update comment data in Supabase
            # response = supabase.table('comments').upsert(comment_data).execute()
            # logger.info(f"Supabase response for comment: {response}")

    except Exception as e:
        pass
    #     logger.error(f"Error fetching or storing data: {e}")




def main():
    subreddit_name = 'chatgpt_promptDesign' 
    get_data(subreddit_name)

if __name__ == "__main__":
    main()