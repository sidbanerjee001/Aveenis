DRIVER_PATH = "./chrome/chrome-linux64/chrome"
TICKER_FILE = "tickers.txt"
HOURS = 24
driver_break = False

# Subreddit scraping settings
SUBREDDIT_NAMES = ["stocks"]  # List of subreddits to scrape
POST_TYPE = "new"  # Type of posts to fetch: "hot", "new", "random", "rising", or "top"
POST_LIMIT = 100  # Number osf posts to fetch per subreddit
JOBLIB_PATH_STOCKTWITS = "6-11real.joblib"  # Path to the joblib file for storing scraped data
JOBLIB_PATH_REDDIT = "reddit6-10.joblib"  # Path to the joblib file for storing scraped Reddit data
