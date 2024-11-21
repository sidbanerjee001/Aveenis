import time
import os
import pytz
import random
import logging
from datetime import datetime, timedelta

import config
# import dataprocessing

import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

def create_driver(arguments, DRIVER_PATH) -> uc.Chrome:
    """
    Create undetected chrome driver with the specified arguments.
    """
    options = Options()

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
        version_main=130,
    )
    
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
    likes = twit.findAll('span', attrs = {'class' : 'StreamMessageLabelCount_labelCount__dWyPL mr-1 text-dark-grey-2 dark|text-stream-text'})[2]
    likes = likes.text if likes.text else '0'

    return message, date_info, likes

def analyze_posts(html, ticker, target_datetime):
    """
    Parses stocktwits page HTML and returns a list of dictionaries containing the post information (each list entry --> separate post).
    """
    posts = []
    soup = BeautifulSoup(html, 'html.parser')
    twits = soup.find_all('div', attrs = {'class' : 'StreamMessage_container__omTCg'})
    if (len(twits) == 0):
        return []
    
    for twit in twits:
        message, date, likes = extract_post_data(twit)
        
        datetime_object = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
        datetime_object = pytz.UTC.localize(datetime_object)
        
        # check if post falls within desired time range
        if (not target_datetime - datetime_object < timedelta(0)):
            break
        
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
    web = f'https://stocktwits.com/symbol/{stock}'
    driver.get(web)
    driver.set_page_load_timeout(10)
    
    # store height of page and page length
    height = driver.execute_script("return document.body.scrollHeight")
    feed = driver.find_element(By.CLASS_NAME, "infinite-scroll-component__outerdiv")
    blog_posts = feed.find_elements(By.CLASS_NAME, "StreamMessage_container__omTCg")
    
    if (len(blog_posts) == 0):
        return [] # no posts to analyze
    
    earliest_blogHTML = get_earliest_blog(blog_posts)
    
    # loop through until final post is beyond desired date range
    # possible better approach: just scroll a fuck ton pixels and then convert to bs4 no matter what
    while(blog_within_date_stocktwits(earliest_blogHTML, target_datetime)):
        driver.execute_script("window.scrollBy(0,2000);")
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        # for login screen (will prevent scrolling)
        if (new_height == height):
                    break
        else:
            height = new_height

        blog_posts = driver.find_elements(By.CLASS_NAME, "StreamMessage_container__omTCg")
        earliest_blogHTML = get_earliest_blog(blog_posts)
    
    html_source = driver.page_source
    analyzedPosts = analyze_posts(html_source, stock, target_datetime)

    return analyzedPosts

def posts_to_metrics(posts):
    """ 
    From raw data --> list [raw mentions, likes]
    """
    metrics = [0] * 2
    
    metrics[0] = len(posts)
    metrics[1] = sum(int(post['Likes']) for post in posts)
    
    return metrics

def perform_stocktwits_scrape():
    """
    Scrapes StockTwits posts for the given tickers within the specified hours.
    """
    # Once database figured out, adjust how time is set
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

    # Get Desired Tickers through TXT file
    with open(config.TICKER_FILE, 'r') as file:
        tickers = file.read().splitlines()

    #--- Research if using chrome drive manager is better ---#
    driver = create_driver(["user-agent=Chrome/77", "headless", "no-sandbox", "disable-dev-shm-usage"], config.DRIVER_PATH)

    # Begin Full Data Collection
    twits_logger.log(logging.INFO, f"StockTwits Full Data Collection Started for {config.TICKER_FILE}")
    scraping_results = {}
    for line in tickers:
        retries = 0
        posts = []
        
        while (retries < 3):
            try:
                if (retries > 0):       
                    driver = create_driver(["user-agent=Chrome/77", "headless", "no-sandbox", "disable-dev-shm-usage"], config.DRIVER_PATH)
                posts = analyze_stocktwits_page(line, driver, TARGET_DATETIME)
                twits_logger.info(f"Posts for {line} have been scraped")
                break
            except TimeoutException as e:     
                driver.close()
                driver.quit()
                time.sleep(2)
                twits_logger.error(f"Timeout Error for {line}")
                
                retries += 1
            except Exception as e:
                driver.close()
                driver.quit()
                twits_logger.error(f"Error fetching page for {line}: {e}")
                
                retries += 1
        
        scraping_results[line] = posts_to_metrics(posts)
       
    driver.close()
    driver.quit()
    twits_logger.log(logging.INFO, "StockTwits Full Data Collection Complete")
    
    return scraping_results