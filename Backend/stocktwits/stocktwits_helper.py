import time
import os
from dotenv import load_dotenv
import pytz
import random
import logging
from datetime import datetime, timedelta
import signal
import sys
import multiprocessing

import config


from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
import joblib   

import json
import os
import tempfile
from functools import reduce
from selenium.webdriver import Edge
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
import subprocess

# import undetected_chromedriver as webdriver


# class ChromeWithPrefs(webdriver.Chrome):
#     def __init__(self, *args, options=None, **kwargs):
#         if options:
#             self._handle_prefs(options)

#         super().__init__(*args, options=options, **kwargs)

#         # remove the user_data_dir when quitting
#         self.keep_user_data_dir = False

#     @staticmethod
#     def _handle_prefs(options):
#         if prefs := options.experimental_options.get("prefs"):
#             # turn a (dotted key, value) into a proper nested dict
#             def undot_key(key, value):
#                 if "." in key:
#                     key, rest = key.split(".", 1)
#                     value = undot_key(rest, value)
#                 return {key: value}

#             # undot prefs dict keys
#             undot_prefs = reduce(
#                 lambda d1, d2: {**d1, **d2},  # merge dicts
#                 (undot_key(key, value) for key, value in prefs.items()),
#             )

#             # create an user_data_dir and add its path to the options
#             user_data_dir = os.path.normpath(tempfile.mkdtemp())
#             options.add_argument(f"--user-data-dir={user_data_dir}")

#             # create the preferences json file in its default directory
#             default_dir = os.path.join(user_data_dir, "Default")
#             os.mkdir(default_dir)

#             prefs_file = os.path.join(default_dir, "Preferences")
#             with open(prefs_file, encoding="latin1", mode="w") as f:
#                 json.dump(undot_prefs, f)

#             # pylint: disable=protected-access
#             # remove the experimental_options to avoid an error
#             del options._experimental_options["prefs"]

def kill_browser_processes():

    try:
        subprocess.call(['pkill', '-f', 'msedgedriver'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.call(['pkill', '-f', 'msedge'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.call(['pkill', '-f', 'chromedriver'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)  # Give a moment for cleanup
    except Exception as e:
        print(f"Error killing browser processes: {e}")


def create_driver(arguments, DRIVER_PATH):

    ### CHROME
    # prefs = {
    #     "profile.default_content_setting_values.images": 2,
    #     # "profile.managed_default_content_settings.fonts": 2,
    #     # "profile.default_content_setting_values.popups": 2,
    #     "profile.default_content_setting_values.autoplay": 2,
    #     # "profile.default_content_setting_values.geolocation": 2,
    #     # "profile.default_content_setting_values.media_stream": 2,
    # }
    # options = webdriver.ChromeOptions()
    # options.add_experimental_option("prefs", prefs)
    # options.binary_location = "/home/jovie/PROJECTS/Aveenis/Aveenis/Backend/chrome/chrome-linux64/chrome"
    # options.page_load_strategy = 'eager'
    # options.add_argument("--headless")
    # options.add_argument("--no-sandbox")
    # options.add_argument("--disable-dev-shm-usage")
    # options.add_argument("--disable-gpu")
    # driver = webdriver.Chrome(options=options)
    kill_browser_processes()
    print("CHROME PROCESSES KILLED")
    
    # Edge
    options = Options()

    prefs = {
        "profile.managed_default_content_settings.images": 2 
    }
    options.add_experimental_option("prefs", prefs)
    options.use_chromium = True
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-setuid-sandbox")
    options.page_load_strategy = 'eager' 
    options.binary_location = "/usr/bin/microsoft-edge"
    
    service = Service("/usr/local/bin/msedgedriver")
    driver = Edge(service=service, options=options)
    driver.command_executor.set_timeout(10)

    # if len(arguments) > 0:
    #     for i in arguments:
    #         argument = i.split("=")
    #         if (len(argument) == 1):
    #             options.add_argument(f"--{argument}")
    #         else:
    #             options.add_argument(f"--{argument[0]}={argument[1]}")

    return driver

def is_within_timeframe(target_datetime, datetime_object):
    return target_datetime - datetime_object < timedelta(0)

def get_earliest_blog(blogs):
    return blogs[-1].get_attribute("innerHTML")

def blog_within_date_stocktwits(text, target_datetime):
    """
    Checks if the earliest blog post is within the desired date range, based on target_datetime.
    """
    soup = BeautifulSoup(text, 'html.parser')
    date_of_post = datetime.strptime(soup.find('time')['datetime'], "%Y-%m-%dT%H:%M:%SZ")
    date_of_post = pytz.UTC.localize(date_of_post)
    
    return is_within_timeframe(target_datetime, date_of_post)

def extract_post_data(twit):
    """
    Extracts the message, datetime, likes from a single posts HTML.
    """
    
    message = twit.find('div', attrs = {'class' : 'RichTextMessage_body__4qUeP whitespace-pre-wrap'}).text
    date_info = twit.find('time')['datetime']
    like_spans = twit.find_all('span', attrs = {'class' : 'StreamMessageLabelCount_labelCount__dWyPL mr-1 text-dark-grey-2 dark|text-stream-text'})
    if len(like_spans) > 2:
        likes = like_spans[2].text if like_spans[2].text else '0'
    else:
        likes = '0'

    return message, date_info, likes

# def analyze_posts(html, ticker, target_datetime):
#     """
#     Parses stocktwits page HTML and returns a list of dictionaries containing the post information (each list entry --> separate post).
#     """
#     posts = []
#     soup = BeautifulSoup(html, 'html.parser')
    
#     # sentiment_messages = soup.find_all('div', attrs = {'class' : 'GaugeScore_gaugeNumber__R1hoe'})
    
#     twits = soup.find_all('div', attrs = {'class' : 'StreamMessage_container__omTCg'})
#     if (len(twits) == 0):
#         return []
    
#     for twit in twits:
#         message, date, likes = extract_post_data(twit)
#         datetime_object = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
#         datetime_object = pytz.UTC.localize(datetime_object)
        
#         # check if post falls within desired time range
#         if (not target_datetime - datetime_object < timedelta(0)):
#             continue

#         # update post info
#         post_info = {
#             'Popularity' : random.randint(0, 100),
#             'In Text Popularity' : random.randint(0, 100),
#             'Ticker' : ticker,
#             'Date' : date,
#             'Message' : message,
#             'Likes' : likes
#         }
#         posts.append(post_info)
    
#     return posts

def analyze_posts(html, ticker, target_datetime):
    """
    Parses stocktwits page HTML and returns a list of dictionaries containing the post information (each list entry --> separate post).
    """
    posts = []
    soup = BeautifulSoup(html, 'html.parser')
    
    # sentiment_messages = soup.find_all('div', attrs = {'class' : 'GaugeScore_gaugeNumber__R1hoe'})
    
    twits = soup.find_all('div', attrs = {'class' : 'StreamMessage_container__omTCg'})
    if (len(twits) == 0):
        return [[0] * 24, [0] * 24, 0, 0]
    
    hours = [0] * 24
    likes = [0] * 24
    for twit in twits:      
        message, date, likes_op = extract_post_data(twit)
        datetime_object = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
        datetime_object = pytz.UTC.localize(datetime_object)
        
        # check if post falls within desired time range
        if (not target_datetime - datetime_object < timedelta(0)):
            continue

        hour = datetime_object.hour
        hours[hour] += 1
        # update post info
        likes[hour] += int(likes_op)

    total_mentions = sum(hours)
    total_likes = sum(likes)
    posts = {
        "hours": hours,
        "likes": likes,
        "total_mentions": total_mentions,
        "total_likes": total_likes
    }
    print(posts)
    return posts

def analyze_stocktwits_page(stock, driver, target_datetime, logger, stop_event, restart_event):
    """
    Analyzes the StockTwits page for a given stock and returns a list of dictionaries containing the post information.
    """
    # load page
    link = f"https://stocktwits.com/symbol/{stock}"
    print(f"Loading page: {link}")
    
    attempts = 0
    # Retry loading the page up to 3 times
    # driver.command_executor.set_timeout(10)  # Set a timeout for page load
    while attempts < 3:
        try:
            driver.get(link)
            break
        except Exception as e:
            print(f"Error loading page: {e}")
            logger.error(f"Error loading page: {e}")
            ### UNRESPONSIVE HERE
            restart_event.set()
            time.sleep(50)
            print("SET FALSE")
            return -1

    print("Page loaded")
    
    # Check if the page is a 404
    if "Page Not Found - 404 - Symbol Page" in driver.title:
        print(f"404 Page Not Found for stock: {stock}")
        logger.info(f"404 Page Not Found for stock: {stock}")
        return ""
    
    if driver.current_url.casefold() != link.casefold():
        print(f"URL mismatch: {driver.current_url.casefold()} != {link.casefold()}")
        driver.get(link)
    
    # Wait until the main content is loaded
    print("loading page...")
    # wait.until(EC.presence_of_element_located((By.CLASS_NAME, "infinite-scroll-component__outerdiv")))
    print("page loaded")

    # store height of page and page length
    try:
        # feed = WebDriverWait(driver, 20).until(
        #     EC.presence_of_element_located((By.CLASS_NAME, "infinite-scroll-component__outerdiv"))
        # )
        feed = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "SymbolStream_container__SRJQv"))
        )
        print("feed found")
        blog_posts = feed.find_elements(By.CLASS_NAME, "StreamMessage_container__omTCg")
    except Exception as e:
        print(f"Error finding feed: {e}")
        logger.error(f"Error finding feed: {e}")
        return -1
    print("elements found")
    
    if (len(blog_posts) == 0):
        print("No posts to analyze")
        return [] # no posts to analyze
    
    earliest_blogHTML = get_earliest_blog(blog_posts)
    
    
    # NEW LOOPING: checks initial load. If earliest post is within date range, scrolls down for 4 seconds.
    # Otherwise, scrolls down for 8 seconds, checks again, continues, maximum scrolling is 32 seconds, afterwards will make estimate.
    
    start = time.time()
    prev_blog_posts_length = 0
    
    # initial load, then increments
    for scroll_time in [0, 4, 8, 16, 32]:
        while (time.time() - start < scroll_time):
            driver.execute_script("window.scrollBy(0,20000);")
            time.sleep(0.5)
             
        blog_posts = driver.find_elements(By.CLASS_NAME, "StreamMessage_container__omTCg")
        earliest_blogHTML = get_earliest_blog(blog_posts)

        if not blog_within_date_stocktwits(earliest_blogHTML, target_datetime):
            break
        
        if len(blog_posts) == prev_blog_posts_length:
            break
        prev_blog_posts_length = len(blog_posts)
        logger.info("Scrolling down to load more posts...")

    # loop through until final post is beyond desired date range
    # possible better approach: just scroll a fuck ton pixels and then convert to bs4 no matter what
    # while(blog_within_date_stocktwits(earliest_blogHTML, target_datetime)):
    #     driver.execute_script("window.scrollBy(0,20000);")
    #     blog_posts = driver.find_elements(By.CLASS_NAME, "StreamMessage_container__omTCg")
    #     earliest_blogHTML = get_earliest_blog(blog_posts)
    
    html_source = driver.page_source
    
    # HERE
    try:
        analyzedPosts = analyze_posts(html_source, stock, target_datetime)
    except Exception as e:
        print(f"Error analyzing posts: {e}")
        logger.error(f"Error analyzing posts: {e}")
        return -1

    print("analysis done")
    return analyzedPosts
    # return analyzedPosts


def posts_to_metrics(posts):
    """ 
    From raw data --> list [raw mentions, likes]
    """

    return [len(posts), sum(int(post['Likes']) for post in posts)]

def stocktwits_login(driver):
    while True:
        try:
            driver.get("https://stocktwits.com/signin")
            time.sleep(2)
            if driver.current_url.rstrip('/') == "https://stocktwits.com":
                return 1
            
            wait = WebDriverWait(driver, 10)
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='log-in-username']"))).send_keys(os.getenv("STOCK_USER"))
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='log-in-password']"))).send_keys(os.getenv("STOCK_PASS"))
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='log-in-submit']"))).click()
            time.sleep(1)
            return 1
        except TimeoutException as e:
            print(f"Login timed out: {e}")
    return

def perform_stocktwits_scrape_init(file_name, target_datetime, logger, driver, pickle_file, scraping_results, stop_event, restart_event):
    """
    Scrapes StockTwits posts for the given tickers within the specified hours.
    Stores intermediate values into a pickle object for robustness.
    """

    # Get Desired Tickers through TXT file
    with open(file_name, 'r') as file:
        tickers = file.read().splitlines()
    file.close()
            
    # Filter out already scraped tickers
    tickers_to_scrape = [ticker for ticker in tickers if ticker not in scraping_results]

    if not tickers_to_scrape:
        logger.info("All tickers have already been scraped.")
        return 1

    #Login
    stocktwits_login(driver)
    print("Logged in to StockTwits")
    
    # Begin Full Data Collection
    logger.log(logging.INFO, f"StockTwits Full Data Collection Started for {file_name}")
    
    for line in tickers_to_scrape:
        posts = []
        
        try:
            print(f"Scraping {line}...")
            posts = analyze_stocktwits_page(line, driver, target_datetime, logger, stop_event, restart_event)
            logger.info(f"Posts for {line} have been scraped")
        except TimeoutException as e:  
            posts = -1
        except Exception as e:
            print(e)
            posts = -1

        if posts == -1:
            print(f"Error fetching page for {line}")
            logger.error(f"Error fetching page for {line}")
            ## DRIVER BECOMES IRRESPONSIVE HERE ## 
            # stop_event.set()
            ####
            print("RESTARTING DRIVER")
            restart_event.set()
            time.sleep(50)
            return -1
        else: 
            scraping_results[line] = posts # posts_to_metrics(posts)
            print("results loaded")
            logger.info(f"Scraped {len(posts)} posts for {line}")

            # Save intermediate results to joblib
            with open(pickle_file, 'wb') as f:
                joblib.dump(scraping_results, f)
            print("results saved")
       
    driver.close()
    driver.quit()
    logger.log(logging.INFO, "StockTwits Full Data Collection Complete")
    
    return 1

def setup_logger():
    twits_logger = logging.getLogger('twits_logger')
    twits_logger.setLevel(logging.INFO)
    twits_handler = logging.FileHandler('scrapingStocktwits.log')
    twits_handler.setLevel(logging.INFO)
    functions_formatter = logging.Formatter(
        "{asctime} - {name} - {levelname} - {message}", style="{", datefmt="%Y-%m-%d %H:%M"
    )
    twits_handler.setFormatter(functions_formatter)
    twits_logger.addHandler(twits_handler)
    
    return twits_logger

def perform_stocktwits_scrape(stop_event, restart_event):
    driver = create_driver(["user-agent=Chrome/77", "--headless", "no-sandbox", "disable-dev-shm-usage"], config.DRIVER_PATH)
    print("Scraper started.")
    pickle_file = config.JOBLIB_PATH_STOCKTWITS

    try:
        with open(pickle_file, 'rb') as f:
            scraping_results = joblib.load(f)
    except (FileNotFoundError, EOFError):
        print("Pickle file not found. Initializing...")
        scraping_results = {}
        with open(pickle_file, 'wb') as f:
            joblib.dump(scraping_results, f)

    TARGET_DATETIME = datetime.now(pytz.UTC) - timedelta(hours=config.HOURS)
    twits_logger = setup_logger()
    start_time = time.time()

    try:
        while not stop_event.is_set():
            print("Starting scraping loop...")
            result = perform_stocktwits_scrape_init(config.TICKER_FILE, TARGET_DATETIME, twits_logger, driver, pickle_file, scraping_results, stop_event, restart_event)
            if result == -1:
                break
    except Exception as e:
        twits_logger.error(f"Error occurred: {e}. Exiting...")
    finally:
        kill_browser_processes()
        driver.quit()
        twits_logger.info(f"Scraping ended. Total time: {time.time() - start_time:.2f} seconds.")


def monitor_stocktwits_and_restart(process, stop_event, restart_event):
    last_mtime = os.path.getmtime(config.JOBLIB_PATH_STOCKTWITS) if os.path.exists(config.JOBLIB_PATH_STOCKTWITS) else None
    start = time.time()

    while not stop_event.is_set():

        if not os.path.exists(config.JOBLIB_PATH_STOCKTWITS):
            print("File not found.")
            break

        current_mtime = os.path.getmtime(config.JOBLIB_PATH_STOCKTWITS)
        if last_mtime is not None and current_mtime == last_mtime:
            age = time.time() - current_mtime
            runtime = time.time() - start
            if restart_event.is_set() or (age > 100 and runtime > 120):
                print("File unchanged for too long. Restarting process...")
                stop_event.set()  # signal scraper to stop
                restart_event.clear()
                process.join(timeout=10)
                if process.is_alive():
                    process.terminate()
                    process.join()
                return True  # trigger restart
            time.sleep(5)
        last_mtime = current_mtime
    return False


def execute_stocktwits_scrape():
    while True:
        stop_event = multiprocessing.Event()
        restart_event = multiprocessing.Event()
        process = multiprocessing.Process(target=perform_stocktwits_scrape, args=(stop_event, restart_event))
        process.start()

        should_restart = monitor_stocktwits_and_restart(process, stop_event, restart_event)

        if not should_restart:
            break  # shutdown triggered


if __name__ == "__main__":
    config.driver_break = False

    tickers = ["NKE"]
    
    for ticker in tickers:
        print(f"Analyzing StockTwits for {ticker}...")
        driver = create_driver([], config.DRIVER_PATH)
        target_datetime = datetime.now(pytz.UTC) - timedelta(hours=config.HOURS)
        stocktwits_login(driver)
        posts = analyze_stocktwits_page(ticker, driver, target_datetime, setup_logger(), multiprocessing.Event(), multiprocessing.Event())
        if posts != -1:
            print(f"Posts for {ticker}: {posts}")
        else:
            print(f"Failed to analyze StockTwits for {ticker}.")
        driver.quit()
        
        
    try:
        print("DONE")
    except KeyboardInterrupt:
        print("Shutdown requested. Exiting...")