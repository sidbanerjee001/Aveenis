# # This first section just uses the pure Reddit API with no wrapper

# CLIENT_ID = '57wfqIvZxAc3yDoCqkIt4g'
# SECRET = 'v9atZRxE6pKwXiUDQOIw74hCa9TG9g'

# import requests
# auth = requests.auth.HTTPBasicAuth(CLIENT_ID, SECRET)

# with open('password.txt', 'r') as f:
#     pw = f.read()

# data = { 
#        'grant_type' : 'password', 
#        'username' : 'Entire-Award4624',
#        'password' : pw
#        }
# headers = {'User-Agent' : 'MyAPI/0.0.1'}

# res = requests.post('https://www.reddit.com/api/v1/access_token', 
#                     auth=auth, data=data, headers=headers)
# TOKEN = res.json()['access_token']
# headers['Authorization'] = f'bearer {TOKEN}'

# print(headers)

# requests.get('https://oauth.reddit.com/api/v1/me', headers = headers).json()

# oauth = 'https://oauth.reddit.com'

# res = requests.get(f'{oauth}/r/chatgpt_promptDesign/new', headers=headers, params={'limit' : '100'})
# res.json()['data']['children']


# import pandas as pd
# dicts_list = [{'subreddit' : post['data']['subreddit'],
#                 'title' : post['data']['title'],
#                 'selftext' : post['data']['selftext'],
#                 'ups' : post['data']['ups'],
#                 'downs' : post['data']['downs'],
#                 'upvote_ratio' : post['data']['upvote_ratio'],
#                 'score' : post['data']['score'],
#                 'num_comments' : post['data']['num_comments'],
#                 'id' : post['data']['id'],
#                 'subreddit_subscribers' : post['data']['subreddit_subscribers']} for post in res.json()['data']['children']]
# df = pd.DataFrame(dicts_list)
# df






#================== supabase implementation =================================

import praw
import logging
from supabase import create_client, Client
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, timedelta, timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up Reddit
reddit = praw.Reddit(
    client_id='57wfqIvZxAc3yDoCqkIt4g',
    client_secret='v9atZRxE6pKwXiUDQOIw74hCa9TG9g',
    user_agent='MyAPI/0.0.1'
)

# Set up Supabase
supabase_url = 'https://kihdsmeyunyjldhtgsfc.supabase.co'
supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtpaGRzbWV5dW55amxkaHRnc2ZjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjE3NzgzOTIsImV4cCI6MjAzNzM1NDM5Mn0.ytac9Ze1Idy2Aw0rJGuDDDsSUCDUISHNkrFtlWDDCk4'
supabase: Client = create_client(supabase_url, supabase_key)

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

            # Insert or update post data in Supabase
            response = supabase.table('posts').upsert(post_data).execute()
            logger.info(f"Supabase response for post: {response}")

            # Fetch and store comments
            post.comments.replace_more(limit=None)
            for comment in post.comments.list():
                comment_data = {
                    'id': comment.id,
                    'post_id': post.id,
                    'body': comment.body,
                    'author': comment.author.name if comment.author else None,
                    'created_utc': convert_to_iso8601(comment.created_utc)
                }
    
                # Insert or update comment data in Supabase
                response = supabase.table('comments').upsert(comment_data).execute()
                logger.info(f"Supabase response for comment: {response}")

    except Exception as e:
        logger.error(f"Error fetching or storing data: {e}")

def main():
    subreddit_name = 'chatgpt_promptDesign' 
    get_data(subreddit_name)

if __name__ == "__main__":
    main()





# This timer doesn't work unless the program is running, so we need to find a different way
# # Scheduled updates every 12 hours
# scheduler = BlockingScheduler()

# @scheduler.scheduled_job('interval', hours=12)
# def update_data():
#     get_data('YOUR_SUBREDDIT_NAME')

# # Scheduled data deletion daily
# def delete_old_data():
#     threshold_date = datetime.utcnow() - timedelta(days=4)
#     supabase.table('posts').delete().lte('timestamp', threshold_date.timestamp()).execute()
#     supabase.table('comments').delete().lte('created_utc', threshold_date.timestamp()).execute()

# scheduler.add_job(delete_old_data, 'interval', days=1)

# # Run the scheduler
# if __name__ == "__main__":
#     get_data('YOUR_SUBREDDIT_NAME')  # Initial fetch
#     scheduler.start()
