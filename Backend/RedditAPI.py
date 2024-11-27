import praw
import logging
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv  

# Define fthe logger and reddit at the modeule level so functions don't give errors when run alone
logger = None
reddit = None

# Setup Functions
def setup_logger():
    """Set up the logger"""
    global logger
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

def load_env_vars():
    """Load environment variables from .env file"""
    load_dotenv()

    required_vars = ['reddit_client_id', 'reddit_client_secret', 'reddit_user_agent']

    env_vars = {var : os.environ.get(var) for var in required_vars}

    for var, value in env_vars.items():
        if not value:
            raise ValueError(f"Missing {value}. Check your .env file")
    
    return env_vars

def setup_reddit(env_vars):
    """
    Set up the Reddit instance
    Args:
        env_vars (dict): Dictionary of environment variables given by load_env_vars()
    """
    global reddit
    reddit = praw.Reddit(
        client_id = env_vars['reddit_client_id'],
        client_secret = env_vars['reddit_client_secret'],
        user_agent = env_vars['reddit_user_agent']
    )
    return reddit


# Function to fetch data from a subreddit
def get_data(subreddit_name, reddit):
    """
    Fetch data from a subreddit
    Args:  
        subreddit_name (str): Name of the subreddit to fetch data from
        reddit (praw.Reddit): Reddit instance given by setup_reddit()
    """
    logger.info(f"Fetching data for subreddit: {subreddit_name}")
    
    # Load tickers from file
    current_dir = os.path.dirname(__file__)
    ticker_filepath = os.path.join(current_dir, 'tickers.txt')
    with open(ticker_filepath, 'r') as file:
        tickers = file.read().splitlines()

    # Create a dictionary to store the data
    dict_to_return = {ticker : [0, 0] for ticker in tickers}

    # Fetch data from the subreddit
    try:
        subreddit = reddit.subreddit(subreddit_name)
        # options for types of subreddits are hot, new, random, rising, top
        posts = subreddit.new(limit=20)

        for post in posts:
            post_text = post.selftext

            # Fetch comments
            post.comments.replace_more(limit=None)
            comments_text = " ".join(comment.body for comment in post.comments.list())
            post_and_comments_text = post_text + " " + comments_text

            # Count ticker mentions in the post and comments and add post upvotes to mentioned tickers
            for ticker in tickers:
                raw_mentions = post_and_comments_text.count(ticker)
                dict_to_return[ticker][0] += raw_mentions
                if (raw_mentions > 0):
                    dict_to_return[ticker][1] += post.ups
                
        return dict_to_return

    except Exception as e:
        logger.error(f"Error fetching or storing data: {e}")
        return None


# Driver Function
def run(subreddit_names: list):
    """
    Runs all the necessary setup functions and fetches data from all subreddits in passed subreddit_names list
    Args:
        subreddit_name (str): Name of the subreddit to fetch data from
    Returns:
        data (dict): A dictionary with tickers as keys and a list of mentions and upvotes as values
    """
    # Run setup fumctions
    setup_logger()
    setup_reddit(load_env_vars())

    # Create a dictionary to store the data
    data = {}

    # Get the damn data
    for subreddit_name in subreddit_names:
        subreddit_data = get_data(subreddit_name, reddit)
        if subreddit_data:
            for ticker, values in subreddit_data.items():
                if ticker not in data:
                    data[ticker] = values
                else:
                    data[ticker][0] += values[0]
                    data[ticker][1] += values[1]


    # Ensure data was fetched properly
    if data:
        logger.info(f"Data fetched successfully: {data}")
    else:
        logger.error("Error fetching data")

    # data is a dictionary with tickers as keys and a list of mentions and upvotes as values
    return data



def main():
    # print("Aveenis!")
    subreddit_names = ['wallstreetbets', 'stocks', 'investing']
    print(run(subreddit_names))

if __name__ == "__main__":
    main()



