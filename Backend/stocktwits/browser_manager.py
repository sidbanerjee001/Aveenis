"""
Browser Manager Class for handling WebDriver lifecycle and operations.
Separates browser management from scraping logic for better maintainability.
"""

import os
import time
import subprocess
import logging
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from selenium import webdriver
from selenium.webdriver import Edge
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException


class BrowserManager:
    """
    Manages WebDriver lifecycle, configuration, and cleanup.
    Provides a clean interface for browser operations.
    """
    
    def __init__(self, 
                 headless: bool = True,
                 timeout: int = 10,
                 page_load_strategy: str = 'eager',
                 logger: Optional[logging.Logger] = None):
        self.headless = headless
        self.timeout = timeout
        self.page_load_strategy = page_load_strategy
        self.logger = logger or logging.getLogger(__name__)
        self.driver: Optional[Edge] = None
        self._is_logged_in = False
        
    def create_driver(self) -> Edge:
        self.kill_browser_processes()
        self.logger.info("Creating new browser driver")
        
        options = Options()
        
        prefs = {
            "profile.managed_default_content_settings.images": 2  # Block images
        }
        # options.add_experimental_option("prefs", prefs)
        
        # Browser options
        options.use_chromium = True
        if self.headless:
            options.add_argument("--headless")
        # options.add_argument("--disable-gpu")
        # options.add_argument("--no-sandbox")
        # options.add_argument("--disable-dev-shm-usage")
        # options.add_argument("--disable-setuid-sandbox")
        # options.add_argument("--disable-extensions")
        # options.add_argument("--disable-plugins")
        options.page_load_strategy = self.page_load_strategy
        options.binary_location = "/usr/bin/microsoft-edge"
        
        service = Service("/usr/local/bin/msedgedriver")
        driver = Edge(service=service, options=options)
        driver.set_page_load_timeout(self.timeout)
        driver.implicitly_wait(10)
        
        return driver
    
    def start(self) -> None:
        if self.driver is None:
            self.driver = self.create_driver()
            self.logger.info("Browser driver started successfully")
    
    def stop(self) -> None:
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("Browser driver stopped")
            except Exception as e:
                self.logger.error(f"Error stopping driver: {e}")
            finally:
                self.driver = None
                self._is_logged_in = False
        
        self.kill_browser_processes()
    
    def restart(self) -> None:
        self.logger.info("Restarting browser driver")
        self.stop()
        time.sleep(2)
        self.start()
    
    @contextmanager
    def browser_session(self):
        try:
            self.start()
            yield self.driver
        finally:
            self.stop()
    
    def get_page(self, url: str, max_retries: int = 3) -> bool:
        if not self.driver:
            self.start()
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Loading page: {url} (attempt {attempt + 1})")
                self.driver.get(url)
                
                # Wait for page to load
                WebDriverWait(self.driver, self.timeout).until(
                    lambda d: d.execute_script('return document.readyState') == 'complete'
                )
                
                if url != "https://stocktwits.com/signin":
                    try:

                        element = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="latestTabs-label-Latest"]')
                        
                        # Scroll into view
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                        # time.sleep(0.5)
                        element.click()
                        
                        self.logger.info("Switched to latest posts")
                    except Exception as e:
                        self.logger.error(f"Error switching to latest posts, no latest tab found, scrolling normally.")

                return True
                
            except TimeoutException:
                self.logger.warning(f"Page load timeout for {url} (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
            except WebDriverException as e:
                self.logger.error(f"WebDriver error loading {url}: {e}")
                if attempt < max_retries - 1:
                    self.restart()
                    continue
            except Exception as e:
                self.logger.error(f"Unexpected error loading {url}: {e}")
                break
        
        return False
    
    def wait_for_element(self, 
                        by: By, 
                        value: str, 
                        timeout: Optional[int] = None) -> Optional[Any]:

        if not self.driver:
            return None
            
        try:
            wait_timeout = timeout or self.timeout
            element = WebDriverWait(self.driver, wait_timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            self.logger.warning(f"Element not found: {by}='{value}'")
            return None
    
    def scroll_page(self, pixels: int = 20000, delay: float = 0.5) -> None:
        if self.driver:
            self.driver.execute_script(f"window.scrollBy(0,{pixels});")
            time.sleep(delay)
    
    def get_page_source(self) -> Optional[str]:
        if self.driver:
            return self.driver.page_source
        return None
    
    def is_page_valid(self, expected_url: Optional[str] = None) -> bool:
        if not self.driver:
            return False
        
        try:
            # Check for 404 or error pages
            if "404" in self.driver.title or "Error" in self.driver.title:
                return False
            
            # Check URL match if provided
            if expected_url and self.driver.current_url.lower() != expected_url.lower():
                self.logger.warning(f"URL mismatch: expected {expected_url}, got {self.driver.current_url}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking page validity: {e}")
            return False
    
    def kill_browser_processes(self) -> None:
        """Kill any existing browser processes"""
        try:
            processes = ['msedgedriver', 'msedge', 'chromedriver', 'chrome']
            for process in processes:
                subprocess.call(['pkill', '-f', process], 
                              stdout=subprocess.DEVNULL, 
                              stderr=subprocess.DEVNULL)
            time.sleep(1)
            self.logger.debug("Browser processes killed")
        except Exception as e:
            self.logger.error(f"Error killing browser processes: {e}")
    
    def login_stocktwits(self, username: str, password: str) -> bool:
        if self._is_logged_in:
            return True
        
        try:
            if not self.get_page("https://stocktwits.com/signin"):
                return False
                        
            # Check if already logged in
            if self.driver.current_url.rstrip('/') == "https://stocktwits.com":
                self._is_logged_in = True
                return True
            
            # Fill login form
            username_field = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='log-in-username']")
            password_field = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='log-in-password']")
            submit_button = self.wait_for_element(By.CSS_SELECTOR, "[data-testid='log-in-submit']")
            
            if not all([username_field, password_field, submit_button]):
                self.logger.error("Login form elements not found")
                return False
            
            username_field.send_keys(username)
            password_field.send_keys(password)

            # Click submit button
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='log-in-submit']"))).click()            
            
            time.sleep(3)
            
            # Verify login success
            if "stocktwits.com" in self.driver.current_url and "signin" not in self.driver.current_url:
                self._is_logged_in = True
                self.logger.info("StockTwits login successful")
                return True
            
        except Exception as e:
            self.logger.error(f"Login failed: {e}")
        
        return False
    
    def is_logged_in(self) -> bool:
        return self._is_logged_in
    
    def get_health_status(self) -> Dict[str, Any]:
        return {
            "driver_active": self.driver is not None,
            "logged_in": self._is_logged_in,
            "current_url": self.driver.current_url if self.driver else None,
            "page_title": self.driver.title if self.driver else None,
        }


# Example usage
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Create browser manager
    browser = BrowserManager(headless=False, logger=logger)
    
    try:
        # Example usage with context manager
        with browser.browser_session():
            # Login
            username = os.getenv("STOCK_USER")
            password = os.getenv("STOCK_PASS")
            
            if browser.login_stocktwits(username, password):
                print("Login successful!")
                
                # Navigate to a stock page
                if browser.get_page("https://stocktwits.com/symbol/AAPL"):
                    print("Page loaded successfully!")
                    
                    # Get page source for parsing
                    html = browser.get_page_source()
                    print(f"HTML length: {len(html) if html else 0}")
                    
                    # Check health
                    health = browser.get_health_status()
                    print(f"Health: {health}")
                else:
                    print("Failed to load page")
            else:
                print("Login failed")
                
    except Exception as e:
        logger.error(f"Error in example: {e}")
