from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json
import requests
from bs4 import BeautifulSoup

class IntelligentWebScraper:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.driver = None
        self.wait = None
        
    def start_browser(self, headless=False):
        """Start browser with intelligent configurations"""
        try:
            from selenium.webdriver.chrome.options import Options
            
            options = Options()
            if headless:
                options.add_argument('--headless')
            
            # Anti-detection options
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.wait = WebDriverWait(self.driver, 10)
            return True
            
        except Exception as e:
            print(f"Failed to start browser: {e}")
            return False
    
    def smart_navigate(self, url, wait_for_element=None, max_retries=3):
        """Navigate with intelligent waiting and retry logic"""
        for attempt in range(max_retries):
            try:
                print(f"Navigating to {url} (attempt {attempt + 1})")
                
                self.driver.get(url)
                
                # Wait for page load
                self.wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                
                # Wait for specific element if provided
                if wait_for_element:
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_element)))
                
                # Handle common popups/overlays
                self.handle_common_popups()
                
                return True
                
            except TimeoutException:
                print(f"Navigation timeout on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                else:
                    return False
            except Exception as e:
                print(f"Navigation error: {e}")
                return False
        
        return False
    
    def handle_common_popups(self):
        """Handle common website popups and overlays"""
        popup_selectors = [
            # Cookie banners
            "[id*='cookie'] button",
            "[class*='cookie'] button", 
            "button[aria-label*='Accept']",
            "button[aria-label*='Close']",
            
            # Newsletter popups
            "[class*='modal'] [class*='close']",
            "[class*='popup'] [class*='close']",
            ".modal-close",
            
            # Age verification
            "button[id*='age']",
            "button[class*='age']"
        ]
        
        for selector in popup_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        element.click()
                        time.sleep(0.5)
                        print(f"Closed popup using selector: {selector}")
                        break
            except:
                continue
    
    def extract_structured_data(self, url, data_config):
        """Extract structured data based on configuration"""
        try:
            if not self.smart_navigate(url):
                return {"success": False, "error": "Failed to navigate to URL"}
            
            extracted_data = {}
            
            for field_name, field_config in data_config.items():
                try:
                    selector = field_config.get("selector")
                    attribute = field_config.get("attribute", "text")
                    multiple = field_config.get("multiple", False)
                    
                    if multiple:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        values = []
                        for element in elements:
                            if attribute == "text":
                                values.append(element.text.strip())
                            else:
                                values.append(element.get_attribute(attribute))
                        extracted_data[field_name] = values
                    else:
                        element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                        if attribute == "text":
                            extracted_data[field_name] = element.text.strip()
                        else:
                            extracted_data[field_name] = element.get_attribute(attribute)
                            

                except TimeoutException:
                    print(f"Could not find element for field: {field_name}")
                    extracted_data[field_name] = None
                except Exception as e:
                    print(f"Error extracting {field_name}: {e}")
                    extracted_data[field_name] = None
            
            return {
                "success": True,
                "data": extracted_data,
                "url": url
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def ai_powered_extraction(self, url, description):
        """Use AI to help extract data based on natural language description"""
        try:
            if not self.api_key:
                return {"success": False, "error": "No API key provided for AI extraction"}
            
            # Navigate to the page
            if not self.smart_navigate(url):
                return {"success": False, "error": "Failed to navigate to URL"}
            
            # Get page source
            page_source = self.driver.page_source
            
            # Use AI to analyze the page and suggest extraction strategy
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
            Analyze this HTML page and help extract data based on this description: "{description}"
            
            Page HTML (first 5000 chars):
            {page_source[:5000]}
            
            Return a JSON configuration for data extraction with this format:
            {{
                "field_name": {{
                    "selector": "CSS_SELECTOR",
                    "attribute": "text_or_attribute_name",
                    "multiple": false
                }}
            }}
            
            Focus on finding the most relevant selectors for: {description}
            """
            
            response = model.generate_content(prompt)
            
            try:
                # Parse AI response
                config_text = response.text.strip()
                config_text = config_text.replace('```json', '').replace('```', '')
                
                start_idx = config_text.find('{')
                end_idx = config_text.rfind('}') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    config_json = config_text[start_idx:end_idx]
                    data_config = json.loads(config_json)
                    
                    # Use the AI-generated config to extract data
                    return self.extract_structured_data(url, data_config)
                
            except json.JSONDecodeError as e:
                print(f"Could not parse AI response: {e}")
                return {"success": False, "error": "AI response parsing failed"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def scrape_with_pagination(self, url, data_config, max_pages=5):
        """Scrape data from multiple pages"""
        all_data = []
        current_page = 1
        
        try:
            while current_page <= max_pages:
                print(f"Scraping page {current_page}")
                
                if current_page == 1:
                    if not self.smart_navigate(url):
                        break
                
                # Extract data from current page
                result = self.extract_structured_data(self.driver.current_url, data_config)
                if result["success"]:
                    all_data.extend(result["data"] if isinstance(result["data"], list) else [result["data"]])
                
                # Try to find and click next page button
                next_selectors = [
                    "a[aria-label*='Next']",
                    "a[class*='next']",
                    "button[class*='next']",
                    ".pagination .next",
                    ".pager .next"
                ]
                
                next_clicked = False
                for selector in next_selectors:
                    try:
                        next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if next_button.is_enabled() and next_button.is_displayed():
                            next_button.click()
                            time.sleep(2)
                            next_clicked = True
                            break
                    except:
                        continue
                
                if not next_clicked:
                    print("No more pages found")
                    break
                
                current_page += 1
            
            return {
                "success": True,
                "data": all_data,
                "pages_scraped": current_page - 1
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()

# Add to ActionExecutor
class ActionExecutor:
    def __init__(self, logger=print, api_key=None):
        # ...existing code...
        self.web_scraper = IntelligentWebScraper(api_key)
    
    def scrape_website(self, url, data_description):
        """Scrape website using AI-powered extraction"""
        if not self.web_scraper.start_browser():
            return {"success": False, "error": "Failed to start browser"}
        
        try:
            result = self.web_scraper.ai_powered_extraction(url, data_description)
            return result
        finally:
            self.web_scraper.close()