import time
import os
from dotenv import load_dotenv
import pytz
import random
import logging
from datetime import datetime, timedelta

import config
# import dataprocessing

# parallelization
from concurrent.futures import ThreadPoolExecutor, as_completed

import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
import pickle

load_dotenv()

def create_driver(arguments, DRIVER_PATH) -> uc.Chrome:
    """
    Create undetected chrome driver with the specified arguments.
    """
    options = Options()
    options.binary_location = "./chrome/chrome-linux64/chrome"
    
    if len(arguments) > 0:
        for i in arguments:
            argument = i.split("=")
            if (len(argument) == 1):
                options.add_argument(f"--{argument}")
            else:
                options.add_argument(f"--{argument[0]}={argument[1]}")

    driver = uc.Chrome(
        browser_executable_path=DRIVER_PATH,
        options=options,
        version_main=132,  # Update this to match the current browser version
    )
    
    return driver

def is_within_timeframe(target_datetime, datetime_object):
    return target_datetime - datetime_object < timedelta(0)

def get_earliest_blog(blogs):
    # print(blogs[-1].get_attribute("innerHTML"))
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
    likes = twit.findAll('span', attrs = {'class' : 'StreamMessageLabelCount_labelCount__dWyPL mr-1 text-dark-grey-2 dark|text-stream-text'})[2]
    likes = likes.text if likes.text else '0'

    return message, date_info, likes

def analyze_posts(html, ticker, target_datetime):
    """
    Parses stocktwits page HTML and returns a list of dictionaries containing the post information (each list entry --> separate post).
    """
    posts = []
    soup = BeautifulSoup(html, 'html.parser')
    
    sentiment_messages = soup.find_all('div', attrs = {'class' : 'GaugeScore_gaugeNumber__R1hoe'})
    
    twits = soup.find_all('div', attrs = {'class' : 'StreamMessage_container__omTCg'})
    if (len(twits) == 0):
        return []
    
    for twit in twits:
        message, date, likes = extract_post_data(twit)
        datetime_object = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
        datetime_object = pytz.UTC.localize(datetime_object)
        
        # check if post falls within desired time range
        if (not target_datetime - datetime_object < timedelta(0)):
            continue

        # update post info
        post_info = {
            'Popularity' : random.randint(0, 100),
            'In Text Popularity' : random.randint(0, 100),
            'Ticker' : ticker,
            'Date' : date,
            'Message' : message,
            'Likes' : likes
        }
        posts.append(post_info)
    
    return posts

def analyze_stocktwits_page(stock, driver, target_datetime):
    """
    Analyzes the StockTwits page for a given stock and returns a list of dictionaries containing the post information.
    """
    # load page
    wait = WebDriverWait(driver, 10)
    search_input = wait.until(EC.element_to_be_clickable((By.NAME, "desktopSearch")))
    search_input.click()
    search_input.send_keys(stock)
    search_input.click()
    time.sleep(0.5)
    search_input.send_keys(Keys.ENTER)
        
    # Wait until the main content is loaded
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "infinite-scroll-component__outerdiv")))
    
    driver.set_page_load_timeout(10)
    # store height of page and page length
    feed = driver.find_element(By.CLASS_NAME, "infinite-scroll-component__outerdiv")
    blog_posts = feed.find_elements(By.CLASS_NAME, "StreamMessage_container__omTCg")
    
    if (len(blog_posts) == 0):
        print("No posts to analyze")
        return [] # no posts to analyze
    
    earliest_blogHTML = get_earliest_blog(blog_posts)
    
    # loop through until final post is beyond desired date range
    # possible better approach: just scroll a fuck ton pixels and then convert to bs4 no matter what
    while(blog_within_date_stocktwits(earliest_blogHTML, target_datetime)):
        driver.execute_script("window.scrollBy(0,20000);")
        blog_posts = driver.find_elements(By.CLASS_NAME, "StreamMessage_container__omTCg")
        earliest_blogHTML = get_earliest_blog(blog_posts)
    
    html_source = driver.page_source
    analyzedPosts = analyze_posts(html_source, stock, target_datetime)

    return analyzedPosts

def posts_to_metrics(posts):
    """ 
    From raw data --> list [raw mentions, likes]
    """
    return [len(posts), sum(int(post['Likes']) for post in posts)]

def stocktwits_login(driver):
    driver.get("https://stocktwits.com/signin?next=/login")
    wait = WebDriverWait(driver, 10)
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='log-in-username']"))).send_keys(os.getenv("STOCK_USER"))
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='log-in-password']"))).send_keys(os.getenv("STOCK_PASS"))
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='log-in-submit']"))).click()
    return

def perform_stocktwits_scrape_init(file_name, target_datetime, logger):
    """
    Scrapes StockTwits posts for the given tickers within the specified hours.
    Stores intermediate values into a pickle object for robustness.
    """
    # Load or initialize scraping results
    pickle_file = f"{file_name}_results.pkl"
    try:
        with open(pickle_file, 'rb') as f:
            scraping_results = pickle.load(f)
    except (FileNotFoundError, EOFError):
        scraping_results = {}

    # Get Desired Tickers through TXT file
    with open(file_name, 'r') as file:
        tickers = file.read().splitlines()

    # Filter out already scraped tickers
    tickers_to_scrape = [ticker for ticker in tickers if ticker not in scraping_results]

    if not tickers_to_scrape:
        logger.info("All tickers have already been scraped.")
        return 1

    # Create driver and login
    driver = create_driver(["user-agent=Chrome/77", "headless", "no-sandbox", "disable-dev-shm-usage"], config.DRIVER_PATH)
    stocktwits_login(driver)
    
    # Begin Full Data Collection
    logger.log(logging.INFO, f"StockTwits Full Data Collection Started for {file_name}")
    
    for line in tickers_to_scrape:
        retries = 0
        posts = []
        
        while retries < 3:
            try:
                posts = analyze_stocktwits_page(line, driver, target_datetime)
                logger.info(f"Posts for {line} have been scraped")
                break
            except TimeoutException as e:     
                time.sleep(2)
                logger.error(f"Timeout Error for {line}")
                retries += 1
            except Exception as e:
                logger.error(f"Error fetching page for {line}: {e}")
                retries += 1
        
        scraping_results[line] = posts_to_metrics(posts)
        
        # Save intermediate results to pickle
        with open(pickle_file, 'wb') as f:
            pickle.dump(scraping_results, f)
       
    driver.close()
    driver.quit()
    logger.log(logging.INFO, "StockTwits Full Data Collection Complete")
    
    return

def perform_stocktwits_scrape():
    TARGET_DATETIME = datetime.now(pytz.UTC) - timedelta(hours=config.HOURS)
    
    # Set up Logger
    twits_logger = logging.getLogger('twits_logger')
    twits_logger.setLevel(logging.INFO)
    twits_handler = logging.FileHandler('scrapingStocktwits.log')
    twits_handler.setLevel(logging.INFO)
    functions_formatter = logging.Formatter(
        "{asctime} - {name} - {levelname} - {message}", style="{", datefmt="%Y-%m-%d %H:%M"
    )
    twits_handler.setFormatter(functions_formatter)
    twits_logger.addHandler(twits_handler)
    
    # Reset pkl object
    if os.path.exists(config.TICKER_FILE + "_results.pkl"):
        os.remove(config.TICKER_FILE + "_results.pkl")
        
    # files = ["tickers1.txt", "tickers2.txt", "tickers3.txt"]
    start_time = time.time()
    
    while True:
        try:
            result = perform_stocktwits_scrape_init(config.TICKER_FILE, TARGET_DATETIME, twits_logger)
            if result == 1:
                break
        except Exception as e:
            twits_logger.error(f"Error occurred: {e}. Retrying...")
            time.sleep(2)  # Wait for 5 seconds before retrying
    
    # Parallelization ?!!?!???!??! (I have no clue how/if this will work with selenium)
    # with ThreadPoolExecutor(max_workers=3) as executor:
    #     futures = [executor.submit(perform_stocktwits_scrape, file, TARGET_DATETIME, twits_logger) for file in files]
    #     for future in as_completed(futures):
    #         future.result()
    
    twits_logger.info(f"Scraping completed in {time.time() - start_time:.2f} seconds.")