import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
import os

class SeleniumController:
    def __init__(self):
        self.driver = None

    def start_browser(self):
        print("Starting Chrome Browser with undetected-chromedriver...")
        import undetected_chromedriver as uc
        import os

        options = uc.ChromeOptions()
        options.add_argument("--start-maximized")
        user_data_dir = os.path.join(os.path.expanduser("~"), "chrome_automation_profile")
        options.add_argument(f'--user-data-dir={user_data_dir}')

        try:
            # Specify your Chrome major version here
            self.driver = uc.Chrome(options=options, version_main=137)
            print("Chrome started successfully.")
        except Exception as e:
            print(f"Failed to start Chrome: {e}")
            raise

    def navigate_to(self, url):
        print(f"Navigating to {url}")
        self.driver.get(url)
        time.sleep(3)

    def search_google(self, query):
        print(f"Searching Google for: {query}")
        self.driver.get("https://www.google.com")
        search_box = self.driver.find_element(By.NAME, "q")
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        time.sleep(3)

    def click_first_result(self):
        print("Clicking first search result...")
        results = self.driver.find_elements(By.CSS_SELECTOR, 'h3')
        if results:
            results[0].click()
        else:
            print("No search results found.")
        time.sleep(3)

    def wait_for_element(self, selector, timeout=10, by=By.CSS_SELECTOR):
        """Wait for element to be present"""
        print(f"Waiting for element: {selector}")
        try:
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            return element
        except Exception as e:
            print(f"Element not found after {timeout} seconds: {e}")
            return None

    def wait_for_page_load(self, timeout=30):
        """Wait for page to finish loading"""
        print("Waiting for page to load completely...")
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            print("Page loaded")
            return True
        except Exception as e:
            print(f"Page load timeout: {e}")
            return False

    def execute_javascript(self, script, *args):
        """Execute JavaScript in browser"""
        print(f"Executing JavaScript: {script[:50]}...")
        try:
            result = self.driver.execute_script(script, *args)
            print("JavaScript executed successfully")
            return result
        except Exception as e:
            print(f"JavaScript execution failed: {e}")
            return None

    def close_browser(self):
        if self.driver:
            self.driver.quit()
            
    def search_youtube(self, query):
        """Search YouTube with improved reliability"""
        print(f"Searching YouTube for: {query}")
        
        try:
            # Wait for page to load
            time.sleep(3)
            
            # Try multiple ways to find and click the search box
            search_selectors = [
                "input#search",
                "input[name='search_query']",
                "#search-input input",
                "ytd-searchbox input",
                "[placeholder*='Search']"
            ]
            
            search_element = None
            for selector in search_selectors:
                try:
                    search_element = self.wait_for_element(selector, timeout=5)
                    if search_element:
                        print(f"Found search box with selector: {selector}")
                        break
                except:
                    continue
            
            if not search_element:
                raise Exception("Could not find YouTube search box")
            
            # Clear any existing text and enter the search query
            search_element.clear()
            time.sleep(0.5)
            search_element.send_keys(query)
            time.sleep(1)
            search_element.send_keys(Keys.RETURN)
            
            print(f"Successfully searched for: {query}")
            time.sleep(2)  # Wait for results to load
            
        except Exception as e:
            print(f"YouTube search failed: {str(e)}")
            raise
