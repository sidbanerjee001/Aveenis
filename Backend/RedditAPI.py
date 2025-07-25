import praw
import logging
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv 
import time
import config
import csv

# Define fthe logger so functions don't give errors when run alone
logger = None

# Trie class for tickers
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_ticker = False

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, ticker):
        """Inserts a word into the trie"""
        node = self.root
        for char in ticker:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_ticker = True
    
    def search(self, word):
        """Returns True if the word is in the trie"""
        node = self.root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end_of_ticker
    
    def search_and_count(self, text, dict_with_ticker_rm_and_upvotes, company_to_ticker: dict):
        """Counts appearances of a ticker, and adds raw mentions to dictionary. Returns a set of tickers mentioned"""
        mentioned_tickers = set()
        for i in range(len(text)):
            node = self.root
            j = i
            while j < len(text) and text[j] in node.children:
                node = node.children[text[j]]
                j += 1
                if node.is_end_of_ticker:
                    is_start_of_word = (i == 0) or not text[i-1].isalnum()
                    is_end_of_word = (j == len(text)) or not text[j].isalnum()
                    if is_start_of_word and is_end_of_word:
                        detected_ticker = text[i:j]
                        print(f"found this ticker/company: {detected_ticker}")
                        if detected_ticker in company_to_ticker:
                            detected_ticker = company_to_ticker[detected_ticker]
                        dict_with_ticker_rm_and_upvotes[detected_ticker][0] += 1
                        mentioned_tickers.add(detected_ticker)
        return mentioned_tickers


#======================================= Setup Functions =======================================
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
    reddit = praw.Reddit(
        client_id = env_vars['reddit_client_id'],
        client_secret = env_vars['reddit_client_secret'],
        user_agent = env_vars['reddit_user_agent']
    )
    return reddit
    
def setup_company_to_ticker():
    """
    Reads company-to-ticker mappings from a CSV file.

    Returns:
        dict: A dictionary mapping company names to tickers.
    """
    try:
        current_dir = os.path.dirname(__file__)
        file_path = os.path.join(current_dir, 'company_to_ticker.csv')
        company_to_ticker = {}
        with open(file_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                company_name = row['Company Name'].strip().lower()
                ticker = row['Ticker'].strip().lower()
                company_to_ticker[company_name] = ticker
        return company_to_ticker
    
    except FileNotFoundError:
        logger.error("CSV file not found. Ensure 'company_to_ticker.csv' is in the project directory.")
        return {}
    except KeyError:
        logger.error("CSV file is missing required headers: 'Company Name' and 'Ticker'.")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error loading company-to-ticker mapping: {e}")
        return {}
   
def setup_trie(tickers, companies):
    """Set up the trie for tickers"""
    trie = Trie()
    for ticker in tickers:
        trie.insert(ticker)
    for company in companies:
        trie.insert(company)
    return trie




#======================================= Functions to fetch data from a subreddit =======================================
def get_data(subreddit_name, reddit, data_dict, trie, company_to_ticker):
    """
    Fetch data from a subreddit
    Args:  
        subreddit_name (str): Name of the subreddit to fetch data from
        reddit (praw.Reddit): Reddit instance given by setup_reddit()
        tickers (list): List of tickers
        data_dict (dict): Dictionary with tickers as keys and a list of mentions and upvotes as values
    """
    logger.info(f"Fetching data for subreddit: {subreddit_name}")

    # Fetch data from the subreddit
    try:
        subreddit = reddit.subreddit(subreddit_name)
        
        if hasattr(subreddit, config.POST_TYPE):
            posts = getattr(subreddit, config.POST_TYPE)(limit=config.POST_LIMIT)

        else:
            raise ValueError(f"Invalid post_type '{config.POST_TYPE}'. Must be 'hot', 'new', 'rising', etc.")

        for post in posts:
            post_title = post.title
            post_text = post.selftext

            # Fetch comments
            post.comments.replace_more(limit=None)
            comments_text = " ".join(comment.body for comment in post.comments.list())
            post_and_comments_text = (post_title + " " + post_text + " " + comments_text).lower()

            # Update data_dict with raw mentions and upvotes for mentioned tickers
            mentioned_tickers = trie.search_and_count(post_and_comments_text, data_dict, company_to_ticker)
            for mentioned_ticker in mentioned_tickers:
                data_dict[mentioned_ticker][1] += post.ups

    except ValueError as ve:
        logger.error(f"Configuration error: {ve}")
    except Exception as e:
        logger.error(f"Unexpected error while fetching data from {subreddit_name}: {e}")


# Driver Function
def run_reddit_scrape():
    """
    Runs all the necessary setup functions and fetches data from all subreddits in passed subreddit_names list
    Args:
        subreddit_name (str): Name of the subreddit to fetch data from
    Returns:
        data (dict): A dictionary with tickers as keys and a list of mentions and upvotes as values
    """
    # Run setup fumctions
    setup_logger()
    reddit = setup_reddit(load_env_vars())
    company_to_ticker = setup_company_to_ticker()
    tickers = list(set(company_to_ticker.values()))
    companies = list(company_to_ticker.keys())
    trie = setup_trie(tickers, companies)


    # Create a dictionary to store the data
    data_dict = {ticker : [0, 0] for ticker in tickers}

    # Get the damn data
    subreddit_names = config.SUBREDDIT_NAMES
    for subreddit_name in subreddit_names:
        get_data(subreddit_name, reddit, data_dict, trie, company_to_ticker)

    # Puts tickers with most raw mentions at end of dictionary for debugging purposes
    sorted_data_dict = dict(sorted(data_dict.items(), key=lambda item: item[1][0]))


    # Ensure data was fetched properly
    if data_dict:
        logger.info(f"Data fetched successfully")
    else:
        logger.error("Error fetching data")

    # data is a dictionary with tickers as keys and a list of mentions and upvotes as values
    return sorted_data_dict



def main():
    # This function is just for testing!! NOT THE DRIVER FUNCTION
    start = time.time()
    print(run_reddit_scrape())
    end = time.time()
    print(f"Time taken: {end-start} seconds")
    



if __name__ == "__main__":
    main()