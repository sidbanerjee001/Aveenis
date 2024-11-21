import time
import os
import pytz
import random
import logging
import re
from datetime import datetime, timedelta

import config
# import dataprocessing

import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

def get_earliest_blog(blogs):
    return blogs[-1].get_attribute("innerHTML")

def convert_to_datetime(date_str):
    # Get the current date
    today = datetime.today()
    
    # Check if the string contains "Today" or "Yesterday"
    if "Now!" in date_str:
        return datetime.now()
    elif "Today" in date_str:
        date_part = today
        time_part = date_str.replace("Today, ", "")
    elif "Yesterday" in date_str:
        date_part = today - timedelta(days=1)
        time_part = date_str.replace("Yesterday, ", "")
    else:
        # If the string does not contain "Today" or "Yesterday", parse it directly
        return datetime.now() - timedelta(days=999)
    
    # Parse the time part
    time_part = datetime.strptime(time_part, "%I:%M %p").time()
    
    # Combine the date and time parts
    return datetime.combine(date_part, time_part)

def blog_within_date_SA(text, target_datetime):
    soup = BeautifulSoup(text, 'html.parser')
    blog_info = soup.select('span')
    
    # Get the date of the post
    for x in blog_info:
        text = x.text
        
        # Check if the text contains the date
        if "Now!" in text or "Today, " in text or "Yesterday, " in text: # Possibility of these being contained in author name
            date = convert_to_datetime(text)
            date = pytz.timezone("America/New_York").localize(date)
            return is_within_timeframe(target_datetime, date)
            
    return False

def is_within_timeframe(target_datetime, datetime_object):
    return target_datetime - datetime_object < timedelta(0)

def process_seeking_alpha_article(article, headers):
    # FINISH
    blogpost = {}
    blogSoup = BeautifulSoup(r.content, 'html.parser')
    blogpost['ticker'] = article['ticker']
    
    if blogSoup.title.string:
        blogpost['title'] = blogSoup.title.string
    else:
        blogpost['title'] = 'NO ENTRY'
    
    date = blogSoup.find('span', attrs = {'class' : 'inline text-share-text-2 z4idr'})
    if date:
        blogpost['date'] = date.get_text()
    else:
        blogpost['date'] = ""
        
    likes = blogSoup.find('span', attrs = {'data-test-id' : 'post-likes-count'})
    if likes:
        blogpost['likes'] = likes.get_text()
    else: 
        blogpost['likes'] = "0"
    
    followers = blogSoup.find('div', attrs = {'class' : 'text-small-r text-black-35 inline text-share-text-3 xs:text-small-r'})
    if followers: 
        followerString = followers.get_text()
        followerCount = re.search(r"[-+]?(?:\d*\.*\d+)", followerString).group()
    
        if followerString[len(followerCount)] == 'K':
            blogpost['followers'] = float(followerCount) * 1000
        else:
            blogpost['followers'] = float(followerCount)
    else:
        blogpost['followers'] = 0
    
    summaryBullets = blogSoup.findAll('li', attrs = {'data-test-id' : 'article-summary-item'})
    content = ""
    if summaryBullets:   
        for bullet in summaryBullets:
            content += bullet.get_text()
    blogpost['content'] = content

    return blogpost

def analyze_seeking_alpha_page(html, target_datetime):
    soup = BeautifulSoup(html, 'html.parser')
    
    # collect article links
    articles = []
    table = soup.findAll('article', attrs = {'class':'flex border-b border-b-black-10 px-0 text-bl0ack-35 last:border-b-0 dark:border-b-black-80 dark:text-black-30 py-18 lg:py-16 last:pb-0'})
    
    if len(articles) == 0:
        print("empty")
        
    for row in table:
        print(row.get_attribute("innerHTML"))
        if not blog_within_date_SA(row.get_attribute("innerHTML"), target_datetime):
            break
        
        article = {}
        # scrape link
        a_tag = row.find('a', href=True)
        if a_tag:
            linkEnd = "https://seekingalpha.com" + a_tag['href']
            article['link'] = linkEnd
        
        # scrape ticker
        tickerSymbol = row.find('a', attrs = {'data-test-id' : 'post-list-ticker'})
        if tickerSymbol:
            article['ticker'] = tickerSymbol.text.strip()
        else: 
            article['ticker'] = ""
        
        articles.append(article)
            
    for a in articles:
        print(a['link'] + a['ticker'])

    return articles

def seekingAlpha(driver, target_datetime):
    # load page
    web = "https://seekingalpha.com/latest-articles?page=1"
    print("loading web")
    driver.get(web)
    print("displaying web")
    driver.set_page_load_timeout(10)

    pages = []
    # get date of earliest blog post
    html = driver.page_source
    print(html)
    article_posts = driver.find_elements(By.TAG_NAME, "article")
    
    pages.append((article_posts, driver.page_source))
    print(article_posts)
    earliest_articleHTML = get_earliest_blog(article_posts)
      
    # go through pages until article beyond desired date range is reached
    while(blog_within_date_SA(earliest_articleHTML, target_datetime)):
        driver.implicitly_wait(2)  # Add wait to ensure the page loaded
        article_posts = driver.find_elements(By.TAG_NAME, "article")
        pages.append((article_posts, driver.page_source))
        
        if article_posts:
            earliest_articleHTML = get_earliest_blog(article_posts)
        else:
            break
        
        try:
            # close overlay (holy fuck such a stupid ass fucking GHNAAA!!!! RAAA!!!)
            close_button = driver.find_element(By.CSS_SELECTOR, '[data-test-id="mcm-strip-dismiss"]')
            close_button.click()
        except:
            pass
        
        # go to next page
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-test-id="next-button"]'))
        )
        button.click()
    
    rawscores = []
    for page in pages:
        rawscores.append(analyze_seeking_alpha_page(page[1], target_datetime))
        
    return rawscores