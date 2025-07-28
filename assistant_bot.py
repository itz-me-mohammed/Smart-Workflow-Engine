# assistant_bot.py

import json
import google.generativeai as genai
import pyautogui
import subprocess
import time
import os
import cv2
import numpy as np
from selenium_controller import SeleniumController
from memory_system import MemorySystem

# Import the new feature classes - add these imports
try:
    from workflow_recorder import WorkflowRecorder
except ImportError:
    # Create a dummy class if the module doesn't exist
    class WorkflowRecorder:
        def __init__(self):
            pass
        def start_recording(self, name):
            return False
        def stop_recording(self):
            return None
        def replay_workflow(self, file, speed):
            return False
        def list_workflows(self):
            return []

try:
    from screen_analyzer import ScreenAnalyzer
except ImportError:
    class ScreenAnalyzer:
        def __init__(self, api_key=None):
            pass
        def analyze_screen_with_ai(self, prompt):
            return {"success": False, "error": "ScreenAnalyzer not available"}
        def extract_text_from_screen(self, region=None):
            return {"success": False, "error": "ScreenAnalyzer not available"}

try:
    from error_recovery import SmartErrorRecovery
except ImportError:
    class SmartErrorRecovery:
        def __init__(self, api_key=None, logger=print):
            pass
        def handle_failed_step(self, step, error, context=None):
            return False

try:
    from visual_detector import VisualElementDetector
except ImportError:
    class VisualElementDetector:
        def __init__(self):
            pass
        def find_buttons_advanced(self):
            return {"success": False, "error": "VisualElementDetector not available"}
        def find_element_by_color(self, color_range):
            return {"success": False, "error": "VisualElementDetector not available"}

try:
    from web_scraper import IntelligentWebScraper
except ImportError:
    class IntelligentWebScraper:
        def __init__(self, api_key=None):
            pass
        def start_browser(self):
            return False
        def ai_powered_extraction(self, url, description):
            return {"success": False, "error": "IntelligentWebScraper not available"}
        def close(self):
            pass

try:
    from chat_interface import AIChatInterface
except ImportError:
    class AIChatInterface:
        def __init__(self, api_key=None):
            pass
        def chat(self, message):
            return {"success": False, "error": "AIChatInterface not available"}

# Note: API key will be configured dynamically when needed

class ActionExecutor:
    def __init__(self, logger=print, api_key=None):
        self.logger = logger
        self.selenium_controller = SeleniumController()
        self.memory_system = MemorySystem()
        self.selenium_active = False
        self.api_key = api_key
        
        # Initialize new features with safe imports
        self.workflow_recorder = WorkflowRecorder()
        self.screen_analyzer = ScreenAnalyzer(api_key)
        self.error_recovery = SmartErrorRecovery(api_key, logger)
        self.visual_detector = VisualElementDetector()
        
        # Initialize web scraper properly
        try:
            from web_scraper import IntelligentWebScraper
            self.web_scraper = IntelligentWebScraper(api_key)
        except ImportError:
            print("⚠️ Web scraping functionality not available")
            self.web_scraper = None
        
        try:
            from chat_interface import AIChatInterface
            self.chat_interface = AIChatInterface(api_key)
        except ImportError:
            class AIChatInterface:
                def __init__(self, api_key=None):
                    pass
                def chat(self, message):
                    return {"success": False, "error": "AIChatInterface not available"}
            self.chat_interface = AIChatInterface()

    def execute_step(self, step):
        """Enhanced execute_step with smart error recovery"""
        action = step.get('action')
        self.logger(f"Executing: {action}")
        
        # Save to memory
        self.memory_system.save_step(step)
        
        max_retries = 2 if action in ['click_element', 'type_text'] else 1
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    self.logger(f"Retry attempt {attempt}/{max_retries-1}")
                    time.sleep(2)
                
                # Execute the action
                success = self._execute_action(step)
                
                if success:
                    time.sleep(0.5)
                    return True
                
            except Exception as e:
                error_message = str(e)
                self.logger(f"Step failed (attempt {attempt + 1}): {error_message}")
                
                # Try smart error recovery on final attempt
                if attempt == max_retries - 1:
                    self.logger("Attempting smart error recovery...")
                    recovery_success = self.error_recovery.handle_failed_step(
                        step, error_message, context={"attempt": attempt}
                    )
                    
                    if recovery_success:
                        self.logger("✅ Smart error recovery successful!")
                        return True
                    else:
                        self.logger("❌ Smart error recovery failed")
        
        return False
    
    def _execute_action(self, step):
        """Execute individual actions"""
        action = step.get('action')
        
        # Existing actions
        if action in ["navigate_url", "search_google", "click_first_result"]:
            return self._execute_web_action(step)
        elif action in ["open_application", "type_text", "press_key", "click_desktop_coordinates", "take_screenshot", "wait_seconds"]:
            return self._execute_desktop_action(step)
        
        # New workflow actions
        elif action == "start_workflow_recording":
            return self.workflow_recorder.start_recording(step.get('name', 'untitled'))
        elif action == "stop_workflow_recording":
            filename = self.workflow_recorder.stop_recording()
            self.logger(f"Workflow saved: {filename}")
            return filename is not None
        elif action == "replay_workflow":
            return self.workflow_recorder.replay_workflow(step.get('file'), step.get('speed', 1.0))
        
        # Screen analysis actions
        elif action == "analyze_screen":
            result = self.screen_analyzer.analyze_screen_with_ai(step.get('prompt', 'Analyze this screen'))
            self.logger(f"Screen analysis: {json.dumps(result, indent=2)}")
            return result.get('success', True)
        elif action == "extract_text_from_screen":
            result = self.screen_analyzer.extract_text_from_screen(step.get('region'))
            self.logger(f"Extracted text: {result.get('text', 'No text found')}")
            return result.get('success', True)
        
        # Visual detection actions
        elif action == "find_visual_element":
            result = self.visual_detector.find_buttons_advanced()
            self.logger(f"Found {result.get('count', 0)} visual elements")
            return result.get('success', True)
        
        # Web scraping actions
        elif action == "scrape_website":
            if not self.web_scraper.start_browser():
                return False
            try:
                result = self.web_scraper.ai_powered_extraction(
                    step.get('url'), 
                    step.get('description', 'Extract all relevant data')
                )
                self.logger(f"Scraping result: {json.dumps(result, indent=2)}")
                return result.get('success', False)
            finally:
                self.web_scraper.close()
        
        # Chat actions
        elif action == "chat_with_ai":
            result = self.chat_interface.chat(step.get('message', ''))
            self.logger(f"AI Response: {result.get('response', 'No response')}")
            return result.get('success', True)
        
        else:
            self.logger(f"Unknown action: {action}")
            return False
    
    def open_application(self, app_name):
        """Improved application opening with better reliability"""
        self.logger(f"Opening {app_name}...")
        
        # Normalize app name
        app_name_lower = app_name.lower()
        
        try:
            if os.name == 'nt':  # Windows
                # Special handling for Cisco Packet Tracer
                if 'cisco' in app_name_lower or 'packet tracer' in app_name_lower:
                    # Use the exact path from your system
                    cisco_path = r"C:\Program Files\Cisco Packet Tracer 8.2.2\bin\PacketTracer.exe"
                    
                    if os.path.exists(cisco_path):
                        subprocess.Popen([cisco_path])
                        self.logger(f"Started Cisco Packet Tracer from: {cisco_path}")
                        time.sleep(8)  # Extra time for Packet Tracer to load
                        return
                    else:
                        self.logger(f"Cisco Packet Tracer not found at: {cisco_path}")
                        # Try fallback
                        subprocess.Popen(['start', 'cisco packet tracer'], shell=True)
                        time.sleep(8)
                        return
                
                # Common application mappings
                app_commands = {
                    'notepad': 'notepad.exe',
                    'calculator': 'calc.exe',
                    'chrome': 'chrome.exe',
                    'firefox': 'firefox.exe',
                    'cmd': 'cmd.exe',
                    'powershell': 'powershell.exe',
                    'explorer': 'explorer.exe',
                    'paint': 'mspaint.exe',
                    'wordpad': 'wordpad.exe'
                }
                
                # Get command for the app
                command = app_commands.get(app_name_lower, app_name)
                
                # Try to start the application
                try:
                    subprocess.Popen([command])
                    self.logger(f"Started {app_name} successfully")
                    time.sleep(2)  # Wait for app to start
                except FileNotFoundError:
                    # Fallback: try via Start menu
                    subprocess.Popen(['start', app_name], shell=True)
                    self.logger(f"Started {app_name} via Start menu")
                    time.sleep(3)
                    
            else:  # Non-Windows systems
                subprocess.Popen([app_name])
                time.sleep(2)
                
        except Exception as e:
            self.logger(f"Failed to open {app_name}: {str(e)}")
            raise

    def type_text(self, text):
        self.logger(f"Typing text: {text}")
        pyautogui.typewrite(text)
        time.sleep(1)

    def press_key(self, key):
        self.logger(f"Pressing key: {key}")
        pyautogui.press(key)
        time.sleep(1)

    def take_screenshot(self, filename=None):
        self.logger(f"Taking screenshot: {filename}")
        screenshot = pyautogui.screenshot()
        
        if not filename:
            filename = "screenshot.png"
        
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            filename += '.png'
            
        screenshot.save(filename)
        self.logger(f"Screenshot saved as: {filename}")
        time.sleep(1)

    def click_element(self, target):
        """Enhanced click_element that works with both web and desktop elements"""
        self.logger(f"Clicking on: {target}")
        
        if self.selenium_active and isinstance(target, str):
            try:
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support import expected_conditions as EC
                from selenium.webdriver.support.ui import WebDriverWait
                
                # Determine selector type
                by_method = By.CSS_SELECTOR
                if str(target).startswith("//"):
                    by_method = By.XPATH
                    
                # Wait for element to be present and clickable
                element = WebDriverWait(self.selenium_controller.driver, 10).until(
                    EC.element_to_be_clickable((by_method, target))
                )
                
                # Scroll element into view
                self.selenium_controller.execute_javascript(
                    "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", 
                    element
                )
                time.sleep(0.5)  # Allow time for scrolling
                
                element.click()
                self.logger(f"Clicked web element: {target}")
                return True
                
            except Exception as e:
                self.logger(f"Selenium click failed: {e}")
                # Don't fall back to default position for web elements
                return False
        
        # Handle desktop UI elements
        else:
            try:
                # Find element position based on target specification
                position = self.find_ui_element(target)
                
                if position:
                    x, y = position
                    self.logger(f"Clicking at position ({x}, {y})")
                    pyautogui.click(x=x, y=y)
                    time.sleep(0.5)  # Wait after click
                    return True
                else:
                    # If target is a dict with x,y coordinates
                    if isinstance(target, dict) and 'x' in target and 'y' in target:
                        self.logger(f"Clicking at specified position ({target['x']}, {target['y']})")
                        pyautogui.click(x=target['x'], y=target['y'])
                        time.sleep(0.5)
                        return True
                    else:
                        self.logger(f"Could not determine click position for: {target}")
                        # Use default position only as last resort
                        self.logger("Using default click position (500, 200) as fallback")
                        pyautogui.click(x=500, y=200)
                        time.sleep(0.5)
                        return False
                        
            except Exception as e:
                self.logger(f"Click operation failed: {e}")
                return False

    def close_all(self):
        if self.selenium_active:
            self.selenium_controller.close_browser()

    def wait_seconds(self, seconds=3):
        self.logger(f"Waiting for {seconds} seconds...")
        time.sleep(seconds)
        self.logger("Wait complete")

    def check_element_exists(self, target, fallback_action=None, fallback_params=None):
        """Check if element exists, execute fallback if it doesn't"""
        self.logger(f"Checking if element exists: {target}")
        
        if self.selenium_active:
            try:
                # Try to find element with timeout
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support import expected_conditions as EC
                from selenium.webdriver.support.ui import WebDriverWait
                
                # Default to CSS selector
                by_method = By.CSS_SELECTOR
                if target.startswith("//"):
                    by_method = By.XPATH
                
                element_exists = WebDriverWait(self.selenium_controller.driver, 5).until(
                    EC.presence_of_element_located((by_method, target))
                )
                
                self.logger(f"Element found: {target}")
                return True
                
            except Exception as e:
                self.logger(f"Element not found: {target}")
                
                # Execute fallback action if provided
                if fallback_action and hasattr(self, fallback_action):
                    self.logger(f"Executing fallback action: {fallback_action}")
                    method = getattr(self, fallback_action)
                    if fallback_params:
                        method(**fallback_params)
                    else:
                        method()
                
                return False
        else:
            self.logger("Selenium not active, cannot check for elements")
            return False

    def extract_text(self, target=None, x1=None, y1=None, x2=None, y2=None):
        """Extract text from a page element or screen region"""
        self.logger(f"Extracting text from {'element' if target else 'screen region'}")
        
        text = ""
        if self.selenium_active and target:
            try:
                # Try to find element
                from selenium.webdriver.common.by import By
                
                by_method = By.CSS_SELECTOR
                if target.startswith("//"):
                    by_method = By.XPATH
                    
                element = self.selenium_controller.driver.find_element(by_method, target)
                text = element.text
                self.logger(f"Extracted text: {text[:100]}{'...' if len(text) > 100 else ''}")
                
            except Exception as e:
                self.logger(f"Failed to extract text from element: {e}")
        else:
            # Extract from screen region using OCR
            try:
                from PIL import ImageGrab
                import pytesseract
                
                # Take screenshot of region or full screen
                if all([x1, y1, x2, y2]):
                    screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
                    self.logger(f"Taking screenshot of region: ({x1}, {y1}, {x2}, {y2})")
                else:
                    screenshot = ImageGrab.grab()
                    self.logger("Taking full screenshot for text extraction")
                
                # Extract text using OCR
                try:
                    text = pytesseract.image_to_string(screenshot)
                    self.logger(f"Extracted text: {text[:100]}{'...' if len(text) > 100 else ''}")
                except Exception as e:
                    self.logger(f"OCR failed: {e}")
            except ImportError:
                self.logger("Required packages missing. Install PIL and pytesseract.")
        
        return text

    def conditional_step(self, condition, value, if_action, else_action=None):
        """Execute different actions based on a condition"""
        self.logger(f"Evaluating condition: {condition} == {value}")
        
        # Get the condition value - could be from extracted text, element state, etc.
        condition_met = False
        
        if condition == "text_contains" and hasattr(self, "_last_extracted_text"):
            condition_met = value in getattr(self, "_last_extracted_text", "")
        elif condition == "element_exists":
            condition_met = self.check_element_exists(value)
        
        # Execute the appropriate action
        if condition_met:
            self.logger(f"Condition met: Executing {if_action.get('action')}")
            self.execute_step(if_action)
        elif else_action:
            self.logger(f"Condition not met: Executing {else_action.get('action')}")
            self.execute_step(else_action)
        else:
            self.logger("Condition not met and no alternative action specified")

    def find_ui_element(self, element_spec):
        """Find UI elements in desktop applications using image recognition"""
        self.logger(f"Looking for UI element: {element_spec}")
        
        # If element_spec is a simple coordinate pair, return it directly
        if isinstance(element_spec, dict) and 'x' in element_spec and 'y' in element_spec:
            return (element_spec['x'], element_spec['y'])
        
        try:
            # Import vision-related libraries
            from PIL import ImageGrab
            import cv2
            import numpy as np
            import os
            
            # Take screenshot
            screenshot = ImageGrab.grab()
            screenshot_np = np.array(screenshot)
            screenshot_cv = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
            
            # If the element is defined by an image reference
            if isinstance(element_spec, dict) and 'image' in element_spec:
                image_path = element_spec['image']
                if not os.path.exists(image_path):
                    # Check in a default images directory
                    base_dir = os.path.dirname(os.path.abspath(__file__))
                    image_path = os.path.join(base_dir, 'ui_images', element_spec['image'])
                
                if not os.path.exists(image_path):
                    self.logger(f"Image not found: {element_spec['image']}")
                    return None
                
                # Load the template image
                template = cv2.imread(image_path)
                if template is None:
                    self.logger(f"Failed to load image: {image_path}")
                    return None
                
                # Perform template matching
                result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                # If the match confidence is high enough
                if max_val > 0.7:  # Threshold can be adjusted
                    h, w = template.shape[:2]
                    center_x = max_loc[0] + w // 2
                    center_y = max_loc[1] + h // 2
                    self.logger(f"Found UI element at ({center_x}, {center_y}) with confidence {max_val:.2f}")
                    return (center_x, center_y)
                else:
                    self.logger(f"No good match found for {image_path}. Best match confidence: {max_val:.2f}")
                    return None
            
            # If the element is defined by text
            elif isinstance(element_spec, dict) and 'alt_text' in element_spec:
                # Use OCR to find text on screen
                import pytesseract
                
                text = pytesseract.image_to_string(screenshot)
                lines = text.split('\n')
                
                # Search for the specified text
                target_text = element_spec['alt_text']
                for i, line in enumerate(lines):
                    if target_text.lower() in line.lower():
                        # Use the actual captured coordinates for Cisco Packet Tracer elements
                        if 'End Devices' in target_text:
                            return (50, 220)  # Left sidebar End Devices
                        elif 'Generic PC' in target_text:
                            return (80, 260)  # Device in expanded list
                        elif 'Connections' in target_text:
                            return (50, 380)  # Left sidebar Connections (below expanded devices)
                        elif 'Cross-Over' in target_text or 'Copper Cross-Over' in target_text:
                            return (80, 420)  # Cable in expanded connections list
                        else:
                            # Default positions for workspace
                            return (500, 350)  # Center of workspace as fallback
            
            # Fallback to specified coordinates
            if isinstance(element_spec, dict) and 'type' in element_spec and element_spec['type'] == 'canvas_area':
                self.logger(f"Using canvas coordinates: ({element_spec['x']}, {element_spec['y']})")
                return (element_spec['x'], element_spec['y'])
            
            # Special handling for PC ports in network simulators
            if isinstance(element_spec, dict) and 'type' in element_spec and element_spec['type'] == 'pc_port':
                pc_num = element_spec.get('pc_number', 1)
                # Approximate coordinates based on PC number
                # These would need to be calibrated for your screen
                x_base = 100 + (pc_num - 1) * 200  # PCs might be spaced 200px apart
                y_base = 300                       # Adjusted vertical position
                self.logger(f"Using calculated port position for PC{pc_num}: ({x_base}, {y_base})")
                return (x_base, y_base)
            
            self.logger(f"Could not locate UI element: {element_spec}")
            return None
            
        except ImportError as e:
            self.logger(f"Required packages not available: {e}")
            self.logger("Install opencv-python, numpy, and pytesseract for better UI automation")
            return None
        except Exception as e:
            self.logger(f"Error finding UI element: {e}")
            return None

    def click_element_desktop(self, target):
        """Click elements on desktop applications using pyautogui"""
        import pyautogui
        
        self.logger(f"Desktop clicking: {target}")
        
        try:
            # If target is a dictionary with coordinates
            if isinstance(target, dict):
                if 'x' in target and 'y' in target:
                    pyautogui.click(target['x'], target['y'])
                    self.logger(f"Clicked at coordinates ({target['x']}, {target['y']})")
                    return True
                elif 'text' in target:
                    # Try to find text on screen
                    try:
                        location = pyautogui.locateOnScreen(target['text'])
                        if location:
                            pyautogui.click(pyautogui.center(location))
                            self.logger(f"Clicked on text: {target['text']}")
                            return True
                    except:
                        pass
            
            # If target is coordinates as string "x,y"
            elif ',' in str(target):
                x, y = map(int, str(target).split(','))
                pyautogui.click(x, y)
                self.logger(f"Clicked at coordinates ({x}, {y})")
                return True
            
            # Try to find image on screen
            else:
                try:
                    location = pyautogui.locateOnScreen(str(target))
                    if location:
                        pyautogui.click(pyautogui.center(location))
                        self.logger(f"Clicked on image: {target}")
                        return True
                except:
                    self.logger(f"Could not find image: {target}")
                    return False
                    
        except Exception as e:
            self.logger(f"Desktop click failed: {str(e)}")
            return False
        
        return False

    def focus_application(self, app_name):
        """Ensure the application window is focused without changing its size"""
        import pyautogui
        
        self.logger(f"Focusing on {app_name} window...")
        
        try:
            import win32gui
            import win32con
            
            # Find window by title
            def enum_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    window_title = win32gui.GetWindowText(hwnd)
                    if app_name.lower() in window_title.lower():
                        windows.append((hwnd, window_title))
                return True
            
            windows = []
            win32gui.EnumWindows(enum_windows_callback, windows)
            
            if windows:
                hwnd, title = windows[0]
                self.logger(f"Found window: {title}")
                
                # Check if window is minimized
                window_state = win32gui.GetWindowPlacement(hwnd)[1]
                
                # Only restore if minimized, don't change size if already visible
                if window_state == win32con.SW_SHOWMINIMIZED:
                    self.logger("Window is minimized, restoring...")
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    time.sleep(2)  # Wait for restore animation
                
                # Just bring to foreground without changing size
                try:
                    win32gui.SetForegroundWindow(hwnd)
                    time.sleep(0.5)
                except:
                    # Alternative method if SetForegroundWindow fails
                    self.logger("Using alternative focus method...")
                    win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                    win32gui.BringWindowToTop(hwnd)
                    time.sleep(0.5)
                
                # Get window position and size for debugging
                rect = win32gui.GetWindowRect(hwnd)
                self.logger(f"Window position after focus: {rect}")
                
                # Click on the window to ensure it has focus
                center_x = (rect[0] + rect[2]) // 2
                center_y = (rect[1] + rect[3]) // 2
                pyautogui.click(center_x, center_y)
                time.sleep(0.5)
                
                return True
            else:
                self.logger(f"No window found for {app_name}")
                return False
                
        except ImportError:
            self.logger("win32gui not available, using alternative method")
            # Fallback: simple click method
            pyautogui.click(960, 540)  # Click center of screen
            time.sleep(1)
            return True
        except Exception as e:
            self.logger(f"Error focusing window: {e}")
            # Fallback: simple click method
            pyautogui.click(960, 540)
            time.sleep(1)
            return True

    def click_desktop_coordinates(self, x, y):
        """Enhanced click without aggressive window focusing"""
        import pyautogui
        
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                self.logger(f"Attempting click {attempt + 1}/{max_attempts} at ({x}, {y})")
                
                # Only focus on first attempt or if previous attempts failed
                if attempt == 0:
                    # Gentle focus - just bring to front without resizing
                    self.gentle_focus_application("Cisco Packet Tracer")
                
                # Move mouse to position first (helps with focus)
                pyautogui.moveTo(x, y, duration=0.3)
                time.sleep(0.2)
                
                # Take screenshot before click for validation
                before_screenshot = pyautogui.screenshot()
                
                # Perform the click
                pyautogui.click(x, y)
                time.sleep(0.5)
                
                # Take screenshot after click
                after_screenshot = pyautogui.screenshot()
                
                # Validate the click worked
                import numpy as np
                before_array = np.array(before_screenshot)
                after_array = np.array(after_screenshot)
                
                # Calculate difference
                diff = np.sum(np.abs(before_array - after_array))
                change_percentage = diff / (before_array.size * 255) * 100
                
                self.logger(f"Click at ({x}, {y}) caused {change_percentage:.2f}% screen change")
                
                if change_percentage > 0.1:
                    self.logger(f"✅ Click at ({x}, {y}) successful - UI changed")
                    return True
                else:
                    self.logger(f"⚠️ Click at ({x}, {y}) - no UI change detected")
                    if attempt < max_attempts - 1:
                        self.logger("Retrying click...")
                        time.sleep(1)
                    
            except Exception as e:
                self.logger(f"Click attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_attempts - 1:
                    time.sleep(1)
        
        self.logger(f"❌ All click attempts failed for ({x}, {y})")
        return False

    def gentle_focus_application(self, app_name):
        """Gentle focus that doesn't change window size"""
        import pyautogui
        
        try:
            import win32gui
            import win32con
            
            # Find window by title
            def enum_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    window_title = win32gui.GetWindowText(hwnd)
                    if app_name.lower() in window_title.lower():
                        windows.append((hwnd, window_title))
                return True
            
            windows = []
            win32gui.EnumWindows(enum_windows_callback, windows)
            
            if windows:
                hwnd, title = windows[0]
                
                # Just set foreground without changing window state
                try:
                    win32gui.SetForegroundWindow(hwnd)
                    self.logger(f"Gently focused: {title}")
                    time.sleep(0.3)
                    return True
                except:
                    # If that fails, try bringing to top
                    win32gui.BringWindowToTop(hwnd)
                    time.sleep(0.3)
                    return True
            
            return False
            
        except ImportError:
            # Fallback: just click on the taskbar area
            pyautogui.click(960, 1060)  # Click on taskbar
            time.sleep(0.5)
            return True
        except Exception as e:
            self.logger(f"Gentle focus failed: {e}")
            return False

    def scrape_website_data(self, url, description):
        """Scrape website using AI-powered extraction"""
        try:
            print("🌐 Starting browser...")
            if not self.web_scraper.start_browser():
                return {"success": False, "error": "Failed to start browser"}
                
            try:
                # Use AI-powered extraction with retry
                max_retries = 2
                for attempt in range(max_retries):
                    try:
                        print(f"🔄 Extraction attempt {attempt + 1}/{max_retries}")
                        result = self.web_scraper.ai_powered_extraction(url, description)
                        
                        if result.get("success"):
                            return result
                        
                        if attempt < max_retries - 1:
                            print("Retrying extraction...")
                            time.sleep(2)
                            
                    except Exception as e:
                        print(f"Extraction attempt {attempt + 1} failed: {str(e)}")
                        if attempt < max_retries - 1:
                            time.sleep(2)
                            continue
                        raise
                        
                return {
                    "success": False, 
                    "error": "All extraction attempts failed"
                }
                
            finally:
                # Always close browser
                print("Closing browser...")
                self.web_scraper.close()
                
        except Exception as e:
            print(f"❌ Scraping error: {str(e)}")
            return {
                "success": False,
                "error": f"Scraping failed: {str(e)}"
            }
        
    def analyze_screen_with_ai(self, prompt):
        """Analyze current screen with AI"""
        return self.screen_analyzer.analyze_screen_with_ai(prompt)

    def find_visual_element(self, element_description):
        """Find elements visually based on description"""
        description_lower = element_description.lower()
        
        if "button" in description_lower:
            return self.visual_detector.find_buttons_advanced()
        elif "blue" in description_lower:
            color_range = {"lower": [100, 50, 50], "upper": [130, 255, 255]}
            return self.visual_detector.find_element_by_color(color_range)
        elif "red" in description_lower:
            color_range = {"lower": [0, 50, 50], "upper": [20, 255, 255]}
            return self.visual_detector.find_element_by_color(color_range)
        else:
            return {"success": False, "error": "Unknown element description"}

    def _execute_web_action(self, step):
        """Execute web-based actions"""
        action = step.get('action')
        
        try:
            if not self.selenium_active:
                self.selenium_controller.start_browser()
                self.selenium_active = True
            
            if action == "navigate_url":
                self.selenium_controller.navigate_to(step.get('url'))
                return True
            elif action == "search_google":
                self.selenium_controller.search_google(step.get('query'))
                return True
            elif action == "click_first_result":
                self.selenium_controller.click_first_result()
                return True
            
            return False
        except Exception as e:
            self.logger(f"Web action failed: {e}")
            return False

    def _execute_desktop_action(self, step):
        """Execute desktop-based actions"""
        action = step.get('action')
        
        try:
            if action == "open_application":
                self.open_application(step.get('application'))
                return True
            elif action == "type_text":
                self.type_text(step.get('text'))
                return True
            elif action == "press_key":
                self.press_key(step.get('key'))
                return True
            elif action == "click_desktop_coordinates":
                return self.click_desktop_coordinates(step.get('x'), step.get('y'))
            elif action == "take_screenshot":
                self.take_screenshot(step.get('filename'))
                return True
            elif action == "wait_seconds":
                self.wait_seconds(step.get('seconds', 3))
                return True
            elif action == "gentle_focus_application":
                return self.gentle_focus_application(step.get('application'))
            
            return False
        except Exception as e:
            self.logger(f"Desktop action failed: {e}")
            return False

    def start_workflow_recording(self, name):
        """Start recording a workflow"""
        return self.workflow_recorder.start_recording(name)

    def stop_workflow_recording(self):
        """Stop recording and save workflow"""
        return self.workflow_recorder.stop_recording()

    def list_workflows(self):
        """List all saved workflows"""
        return self.workflow_recorder.list_workflows()

    def replay_workflow(self, workflow_file, speed=1.0):
        """Replay a saved workflow"""
        return self.workflow_recorder.replay_workflow(workflow_file, speed)

    def chat_with_assistant(self, message):
        """Chat with the AI assistant"""
        return self.chat_interface.chat(message)

    def get_task_analysis(self, task_description):
        """Get AI analysis of an automation task"""
        return self.chat_interface.analyze_automation_task(task_description)

    def get_improvement_suggestions(self, execution_log):
        """Get AI suggestions for improvement"""
        return self.chat_interface.suggest_improvements(execution_log)

    def update_api_key(self, api_key):
        """Update the API key for all components"""
        self.api_key = api_key
        
        # Update API key in all components that need it
        if hasattr(self.screen_analyzer, 'api_key'):
            self.screen_analyzer.api_key = api_key
        if hasattr(self.chat_interface, 'api_key'):
            self.chat_interface.api_key = api_key
        if hasattr(self.web_scraper, 'api_key'):
            self.web_scraper.api_key = api_key
        if hasattr(self.error_recovery, 'api_key'):
            self.error_recovery.api_key = api_key
        
        # Reconfigure Gemini for components that use it directly
        if api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
            except:
                pass

def get_steps_from_gemini(user_prompt, api_key):
    """Generate execution steps using Gemini AI with provided API key"""
    if not api_key:
        print("Error: No API key provided")
        return create_fallback_plan(user_prompt)
    
    # Configure Gemini with the provided API key
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-pro')
    except Exception as e:
        print(f"Error configuring Gemini API: {e}")
        return create_fallback_plan(user_prompt)
    
    # Enhanced prompt with CORRECTED Cisco Packet Tracer coordinates
    system_prompt = """You are a computer automation assistant. Convert the user's request into a JSON list of steps.

AVAILABLE ACTIONS:
- open_application: Opens apps (use: "cisco packet tracer", "notepad", "calculator", "chrome")
- navigate_url: Go to websites (Chrome only)
- type_text: Type text into focused element
- press_key: Press keys ("Enter", "Tab", "Escape")
- click_element: Click web elements (CSS selectors for web, coordinates for desktop)
- click_desktop_coordinates: Click at specific desktop coordinates (x, y)
- drag_and_drop: Drag from coordinates (from_x, from_y) to (to_x, to_y)
- wait_seconds: Wait for specified seconds
- take_screenshot: Capture screen

CISCO PACKET TRACER RULES (CORRECTED COORDINATES):
- Use "cisco packet tracer" as application name
- After opening, wait 10 seconds for loading
- End Devices button: (50, 220) - in left sidebar
- Generic PC icon: (80, 260) - in expanded device list under End Devices
- Connections button: (50, 380) - in left sidebar (below expanded devices)
- Copper Cross-Over cable: (80, 420) - in expanded connections list
- Canvas area for placing devices: (400, 300) to (800, 500) - main white workspace
- Always take screenshot after major actions

IMPORTANT: Return ONLY valid JSON with a "steps" array.

Example for Cisco Packet Tracer connecting PCs:
{"steps": [
  {"action": "open_application", "application": "cisco packet tracer"},
  {"action": "wait_seconds", "seconds": 10},
  {"action": "click_desktop_coordinates", "x": 50, "y": 220},
  {"action": "wait_seconds", "seconds": 2},
  {"action": "click_desktop_coordinates", "x": 80, "y": 260},
  {"action": "wait_seconds", "seconds": 1},
  {"action": "click_desktop_coordinates", "x": 450, "y": 350},
  {"action": "wait_seconds", "seconds": 2},
  {"action": "click_desktop_coordinates", "x": 80, "y": 260},
  {"action": "click_desktop_coordinates", "x": 650, "y": 350},
  {"action": "wait_seconds", "seconds": 2},
  {"action": "click_desktop_coordinates", "x": 50, "y": 380},
  {"action": "wait_seconds", "seconds": 2},
  {"action": "click_desktop_coordinates", "x": 80, "y": 420},
  {"action": "click_desktop_coordinates", "x": 450, "y": 350},
  {"action": "press_key", "key": "Enter"},
  {"action": "click_desktop_coordinates", "x": 650, "y": 350},
  {"action": "press_key", "key": "Enter"},
  {"action": "take_screenshot", "filename": "pcs_connected.png"}
]}

User request: {user_prompt}

JSON response:"""

    try:
        response = model.generate_content(
            system_prompt.format(user_prompt=user_prompt),
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=1200,
                candidate_count=1
            )
        )
        
        if not response or not response.text:
            print("No response from Gemini API")
            return create_fallback_plan(user_prompt)
        
        content = response.text.strip()
        print(f"Raw Gemini response: {content}")
        
        # Clean up the response more thoroughly
        content = content.replace('```json', '').replace('```', '')
        content = content.replace('`', '')
        
        # Find the JSON object boundaries
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        
        if start_idx == -1 or end_idx == 0:
            print("No JSON object found in response")
            return create_fallback_plan(user_prompt)
        
        json_str = content[start_idx:end_idx]
        print(f"Extracted JSON: {json_str}")
        
        # Parse JSON
        try:
            plan = json.loads(json_str)
            steps = plan.get("steps", [])
            
            if not steps:
                print("No steps found in response")
                return create_fallback_plan(user_prompt)
            
            print(f"Successfully parsed {len(steps)} steps")
            return steps
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed: {e}")
            print(f"Problematic JSON: {json_str}")
            return create_fallback_plan(user_prompt)
        
    except Exception as e:
        print(f"Error generating steps: {e}")
        return create_fallback_plan(user_prompt)

def create_fallback_plan(user_prompt):
    """Create a simple fallback plan when Gemini fails"""
    prompt_lower = user_prompt.lower()
    
    # Enhanced Cisco Packet Tracer fallback with corrected coordinates
    if "cisco" in prompt_lower and "packet tracer" in prompt_lower:
        if "connect" in prompt_lower and ("pc" in prompt_lower or "computer" in prompt_lower):
            return [
                {"action": "open_application", "application": "cisco packet tracer"},
                {"action": "wait_seconds", "seconds": 12},
                {"action": "take_screenshot", "filename": "1_packet_tracer_opened.png"},
                
                # Gentle focus only once at the beginning
                {"action": "gentle_focus_application", "application": "cisco packet tracer"},
                {"action": "wait_seconds", "seconds": 3},
                
                # Click End Devices in left sidebar
                {"action": "click_desktop_coordinates", "x": 50, "y": 220},
                {"action": "wait_seconds", "seconds": 3},
                {"action": "take_screenshot", "filename": "2_end_devices_clicked.png"},
                
                # Click Generic PC in the expanded device list (adjusted Y coordinate)
                {"action": "click_desktop_coordinates", "x": 80, "y": 260},
                {"action": "wait_seconds", "seconds": 2},
                {"action": "take_screenshot", "filename": "3_pc_selected.png"},
                
                # Place first PC in workspace
                {"action": "click_desktop_coordinates", "x": 450, "y": 350},
                {"action": "wait_seconds", "seconds": 3},
                {"action": "take_screenshot", "filename": "4_first_pc_placed.png"},
                
                # Click Generic PC again for second PC
                {"action": "click_desktop_coordinates", "x": 80, "y": 260},
                {"action": "wait_seconds", "seconds": 2},
                
                # Place second PC in workspace
                {"action": "click_desktop_coordinates", "x": 650, "y": 350},
                {"action": "wait_seconds", "seconds": 3},
                {"action": "take_screenshot", "filename": "5_second_pc_placed.png"},
                
                # Click Connections in left sidebar (adjusted for expanded list)
                {"action": "click_desktop_coordinates", "x": 50, "y": 380},
                {"action": "wait_seconds", "seconds": 3},
                {"action": "take_screenshot", "filename": "6_connections_clicked.png"},
                
                # Click Copper Cross-Over cable in expanded connections list
                {"action": "click_desktop_coordinates", "x": 80, "y": 420},
                {"action": "wait_seconds", "seconds": 2},
                {"action": "take_screenshot", "filename": "7_cable_selected.png"},
                
                # Connect first PC
                {"action": "click_desktop_coordinates", "x": 450, "y": 350},
                {"action": "wait_seconds", "seconds": 2},
                {"action": "press_key", "key": "Enter"},
                {"action": "wait_seconds", "seconds": 1},
                
                # Connect second PC
                {"action": "click_desktop_coordinates", "x": 650, "y": 350},
                {"action": "wait_seconds", "seconds": 2},
                {"action": "press_key", "key": "Enter"},
                {"action": "wait_seconds", "seconds": 1},
                
                {"action": "take_screenshot", "filename": "8_pcs_connected_final.png"}
            ]
        else:
            # Just open Packet Tracer
            return [
                {"action": "open_application", "application": "cisco packet tracer"},
                {"action": "wait_seconds", "seconds": 12},
                {"action": "gentle_focus_application", "application": "cisco packet tracer"},
                {"action": "take_screenshot", "filename": "packet_tracer_opened.png"}
            ]
    
    # Enhanced fallback for YouTube searches
    elif "youtube" in prompt_lower and ("search" in prompt_lower or "mrbeast" in prompt_lower):
        # Extract search term
        search_term = "mrbeast"  # default
        
        if "search for" in prompt_lower:
            search_start = prompt_lower.find("search for") + 10
            search_term = user_prompt[search_start:].strip()
        elif "search" in prompt_lower:
            words = user_prompt.split()
            search_idx = next((i for i, word in enumerate(words) if "search" in word.lower()), -1)
            if search_idx != -1 and search_idx + 1 < len(words):
                search_term = " ".join(words[search_idx + 1:])
        
        # Clean up search term
        search_term = search_term.replace('"', '').replace("'", '').strip()
        
        return [
            {"action": "open_application", "application": "chrome"},
            {"action": "wait_seconds", "seconds": 3},
            {"action": "navigate_url", "url": "https://www.youtube.com"},
            {"action": "wait_seconds", "seconds": 4},
            {"action": "click_element", "target": "input#search"},
            {"action": "wait_seconds", "seconds": 1},
            {"action": "type_text", "text": search_term},
            {"action": "wait_seconds", "seconds": 1},
            {"action": "press_key", "key": "Enter"}
        ]
    
    elif "chrome" in prompt_lower and "youtube" in prompt_lower:
        return [
            {"action": "open_application", "application": "chrome"},
            {"action": "wait_seconds", "seconds": 3},
            {"action": "navigate_url", "url": "https://www.youtube.com"},
            {"action": "wait_seconds", "seconds": 3}
        ]
    
    elif "notepad" in prompt_lower:
        steps = [
            {"action": "open_application", "application": "notepad"},
            {"action": "wait_seconds", "seconds": 2}
        ]
        
        # Check if there's text to type
        if "type" in prompt_lower:
            # Extract text after "type"
            text_start = prompt_lower.find("type") + 4
            text_to_type = user_prompt[text_start:].strip()
            if text_to_type:
                steps.append({"action": "type_text", "text": text_to_type})
        
        return steps
    
    elif "calculator" in prompt_lower or "calc" in prompt_lower:
        return [
            {"action": "open_application", "application": "calculator"},
            {"action": "wait_seconds", "seconds": 2}
        ]
    
    elif "screenshot" in prompt_lower:
        return [
            {"action": "take_screenshot", "filename": "screenshot.png"}
        ]
    
    else:
        # Very basic fallback
        return [
            {"action": "wait_seconds", "seconds": 1}
        ]
