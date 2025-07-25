import os
import pickle
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from concurrent.futures import ThreadPoolExecutor
import math
import time
from stocktwits.stocktwits_helper import analyze_stocktwits_page, create_driver, posts_to_metrics, stocktwits_login
import logging
import config
from datetime import datetime, timedelta
import pytz
import random
from multiprocessing import Process
import shutil
import tempfile
from joblib import dump
from joblib import load


# setting up logging (threadsafe?)
def setup_logger():
    logger = logging.getLogger("Scraper")
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler("/home/jovie/PROJECTS/Aveenis/Aveenis/Backend/scraper.log")
    functions_formatter = logging.Formatter(
        "{asctime} - {name} - {levelname} - {message}", style="{", datefmt="%Y-%m-%d %H:%M"
    )
    handler.setFormatter(functions_formatter)
    if not logger.handlers:
        logger.addHandler(handler)
        
    return logger

# general bullshit
TARGET_DATETIME = datetime.now(pytz.UTC) - timedelta(hours=config.HOURS)
FILE_NAME = config.TICKER_FILE
NUM_WORKERS = 4

### Scraping function for each worker (just running through same process, with less tickers per worker)
def scrape(worker_id, ticker_batch, logger):
    print("IN WORKER ", worker_id)
    
    # temp_profile = tempfile.mkdtemp(prefix=f"selenium_profile_worker{worker_id}_")
    profile = f"selenium_profile_worker{worker_id}"
    driver = create_driver(["user-agent=Chrome/77", "disable-dev-shm-usage", f"user-data-dir={profile}"], config.DRIVER_PATH)

    stocktwits_login(driver)
    scraping_results = {}
    pickle_file = f"/home/jovie/PROJECTS/Aveenis/Aveenis/Backend/worker_{worker_id}.joblib"
    
    scraping_results = load(pickle_file) if os.path.exists(pickle_file) else {}
    ticker_batch = [a for a in ticker_batch if a not in scraping_results]

    for line in ticker_batch:
        print(f"Worker {worker_id} processing ticker: {line}")
        # time.sleep(random.uniform(0.0, 3.0))
        logger.info(f"Worker {worker_id} scraping {line}")
        posts = []
        
        try:
            posts = analyze_stocktwits_page(line, driver, TARGET_DATETIME, logger)
            logger.info(f"Posts for {line} have been scraped")
        except TimeoutException as e:  
            posts = -1
        except Exception as e:
           posts = -1

        if posts == -1:
            logger.error(f"Error fetching page for {line}")
            driver.quit()
            driver = create_driver(["user-agent=Chrome/77", "headless", "no-sandbox", "disable-dev-shm-usage"], config.DRIVER_PATH)
            stocktwits_login(driver)
            continue
        else: 
            # HERE
            scraping_results[line] = posts
            # scraping_results[line] = posts_to_metrics(posts)
            # print("results loaded")
            # logger.info(f"Scraped {len(posts)} posts for {line}")
            
            # Save intermediate results to pickle
            dump(scraping_results, pickle_file)
            print("results saved")
       
    driver.close()
    driver.quit()
    logger.log(logging.INFO, f"StockTwits Full Data Collection Complete for worker {worker_id}")


if __name__ == "__main__":
    with open("/home/jovie/PROJECTS/Aveenis/Aveenis/Backend/tickers.txt", 'r') as file:
        tickers = file.read().splitlines()
    file.close()
    TICKERS_PER_WORKER = math.ceil(len(tickers) / NUM_WORKERS)

    # setting up logger
    logger = setup_logger()
    logger.info(f"Starting scraping with {NUM_WORKERS} workers for {len(tickers)} tickers.")
    start = time.time()
    batches = [tickers[i:i + TICKERS_PER_WORKER] for i in range(0, len(tickers), TICKERS_PER_WORKER)]
    print(f"Total batches: {len(batches)}")
    
    # clear pkl files
    # for file in os.listdir('.'):
    #     if file.endswith('.pkl') and file.startswith('worker_'):
    #         with open(file, 'wb') as f:
    #             pass  # Truncate the file to zero length
    #         print(f"Cleared existing pickle file: {file}")
    
    # create joblib files
    # for i in range(NUM_WORKERS):
    #     with open(f"worker_{i}.joblib", 'wb') as f:
    #         pickle.dump({}, f)  # Initialize with an empty dictionary
    #     print(f"Initialized worker {i} pickle file.")
            
    # multiprocessing setup
    processes = []
    start = time.time()
    for i, batch in enumerate(batches):
        p = Process(target=scrape, args=(i, batch, logger))
        p.start()
        processes.append(p)
        logger.info(f"Started worker {i} for batch {i + 1}/{len(batches)} with {len(batch)} tickers.")
    for p in processes:
        p.join()

    end = time.time()
    logger.info(f"Scraping completed in {end - start:.2f} seconds.")
    logger.info("All workers have completed their tasks.")