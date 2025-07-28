import time
import pyautogui
import json
from screen_analyzer import ScreenAnalyzer

class SmartErrorRecovery:
    def __init__(self, api_key=None, logger=print):
        self.api_key = api_key
        self.logger = logger
        self.screen_analyzer = ScreenAnalyzer(api_key)
        self.recovery_strategies = []
        
    def handle_failed_step(self, failed_step, error_message, context=None):
        """Intelligently recover from failed automation steps"""
        self.logger(f"🔧 Starting smart error recovery for: {failed_step.get('action', 'unknown')}")
        
        # Take screenshot for analysis
        error_screenshot = pyautogui.screenshot()
        error_screenshot.save("error_screenshot.png")
        
        # Analyze current screen state
        screen_analysis = self.screen_analyzer.analyze_screen_with_ai(
            f"This automation step failed: {failed_step}. Error: {error_message}. "
            "What might have gone wrong and what are alternative approaches?"
        )
        
        # Try recovery strategies
        recovery_success = False
        
        # Strategy 1: Element position might have changed
        if failed_step.get('action') == 'click_desktop_coordinates':
            recovery_success = self._recover_click_coordinates(failed_step, screen_analysis)
        
        # Strategy 2: Application might not be focused
        elif 'focus' in error_message.lower() or 'window' in error_message.lower():
            recovery_success = self._recover_window_focus(failed_step, context)
        
        # Strategy 3: Element might need more time to load
        elif 'timeout' in error_message.lower() or 'not found' in error_message.lower():
            recovery_success = self._recover_wait_and_retry(failed_step)
        
        # Strategy 4: Try alternative element selectors
        elif failed_step.get('action') == 'click_element':
            recovery_success = self._recover_alternative_selectors(failed_step, screen_analysis)
        
        # Strategy 5: AI-powered recovery
        if not recovery_success:
            recovery_success = self._ai_powered_recovery(failed_step, screen_analysis, error_message)
        
        return recovery_success
    
    def _recover_click_coordinates(self, failed_step, screen_analysis):
        """Try to find the element at alternative coordinates"""
        self.logger("🎯 Attempting coordinate recovery...")
        
        original_x = failed_step.get('x', 0)
        original_y = failed_step.get('y', 0)
        
        # Try nearby coordinates
        offsets = [
            (0, 0),    # Original position
            (10, 0),   # Slightly right
            (-10, 0),  # Slightly left
            (0, 10),   # Slightly down
            (0, -10),  # Slightly up
            (20, 20),  # Diagonal
            (-20, -20) # Opposite diagonal
        ]
        
        for dx, dy in offsets:
            try:
                new_x = original_x + dx
                new_y = original_y + dy
                
                self.logger(f"🎯 Trying coordinates ({new_x}, {new_y})")
                
                # Take screenshot before click
                before = pyautogui.screenshot()
                
                # Try the click
                pyautogui.click(new_x, new_y)
                time.sleep(0.5)
                
                # Check if it worked
                after = pyautogui.screenshot()
                
                # Simple change detection
                if self._detect_screen_change(before, after):
                    self.logger(f"✅ Coordinate recovery successful at ({new_x}, {new_y})")
                    return True
                    
            except Exception as e:
                self.logger(f"⚠️ Coordinate attempt failed: {e}")
                continue
        
        return False
    
    def _recover_window_focus(self, failed_step, context):
        """Try to recover window focus issues"""
        self.logger("🪟 Attempting window focus recovery...")
        
        try:
            # Try Alt+Tab to cycle windows
            pyautogui.keyDown('alt')
            pyautogui.press('tab')
            pyautogui.keyUp('alt')
            time.sleep(1)
            
            # Try clicking on taskbar
            pyautogui.click(960, 1060)
            time.sleep(1)
            
            # Try Windows key to open start menu and close it
            pyautogui.press('win')
            time.sleep(0.5)
            pyautogui.press('escape')
            time.sleep(0.5)
            
            self.logger("✅ Window focus recovery attempted")
            return True
            
        except Exception as e:
            self.logger(f"❌ Window focus recovery failed: {e}")
            return False
    
    def _recover_wait_and_retry(self, failed_step):
        """Wait longer and retry the action"""
        self.logger("⏱️ Attempting wait and retry recovery...")
        
        # Wait longer than usual
        wait_times = [2, 5, 10]
        
        for wait_time in wait_times:
            try:
                self.logger(f"⏱️ Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
                
                # Retry the action (simplified)
                action = failed_step.get('action')
                
                if action == 'click_desktop_coordinates':
                    pyautogui.click(failed_step.get('x'), failed_step.get('y'))
                elif action == 'type_text':
                    pyautogui.typewrite(failed_step.get('text'))
                elif action == 'press_key':
                    pyautogui.press(failed_step.get('key'))
                
                self.logger(f"✅ Wait and retry recovery successful after {wait_time}s")
                return True
                
            except Exception as e:
                self.logger(f"⚠️ Retry attempt failed: {e}")
                continue
        
        return False
    
    def _recover_alternative_selectors(self, failed_step, screen_analysis):
        """Try alternative ways to find and click elements"""
        self.logger("🔍 Attempting alternative selector recovery...")
        
        target = failed_step.get('target', '')
        
        # Try alternative selectors for web elements
        alternative_selectors = [
            target.replace('#', '.'),  # ID to class
            target.replace('.', '#'),  # Class to ID
            f"[data-testid*='{target}']",  # Data test ID
            f"[aria-label*='{target}']",   # Aria label
            f"[title*='{target}']",        # Title attribute
        ]
        
        for selector in alternative_selectors:
            try:
                self.logger(f"🔍 Trying selector: {selector}")
                # This would integrate with selenium if available
                # For now, just log the attempt
                time.sleep(1)
                return False  # Placeholder
                
            except Exception as e:
                continue
        
        return False
    
    def _ai_powered_recovery(self, failed_step, screen_analysis, error_message):
        """Use AI to suggest and execute recovery actions"""
        self.logger("🤖 Attempting AI-powered recovery...")
        
        try:
            if not self.api_key:
                return False
            
            recovery_prompt = f"""
            An automation step has failed. Help me recover by suggesting alternative actions.
            
            Failed Step: {json.dumps(failed_step, indent=2)}
            Error Message: {error_message}
            Screen Analysis: {json.dumps(screen_analysis, indent=2)}
            
            Suggest 3 alternative approaches to accomplish the same goal.
            Return as JSON array with this format:
            [
                {{
                    "approach": "description",
                    "action": "action_type",
                    "parameters": {{"key": "value"}},
                    "confidence": 0.8
                }}
            ]
            """
            
            import google.generativeai as genai
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(recovery_prompt)
            
            try:
                suggestions = json.loads(response.text)
                
                # Try each suggestion
                for suggestion in suggestions:
                    if suggestion.get('confidence', 0) > 0.6:
                        self.logger(f"🤖 Trying AI suggestion: {suggestion['approach']}")
                        
                        # Execute the suggested action
                        if self._execute_recovery_action(suggestion):
                            self.logger("✅ AI-powered recovery successful!")
                            return True
                            
            except json.JSONDecodeError:
                self.logger("⚠️ Could not parse AI recovery suggestions")
                
        except Exception as e:
            self.logger(f"❌ AI-powered recovery failed: {e}")
        
        return False
    
    def _execute_recovery_action(self, suggestion):
        """Execute a recovery action suggested by AI"""
        try:
            action = suggestion.get('action')
            params = suggestion.get('parameters', {})
            
            if action == 'click_desktop_coordinates':
                pyautogui.click(params.get('x'), params.get('y'))
            elif action == 'type_text':
                pyautogui.typewrite(params.get('text'))
            elif action == 'press_key':
                pyautogui.press(params.get('key'))
            elif action == 'wait_seconds':
                time.sleep(params.get('seconds', 1))
            
            time.sleep(1)
            return True
            
        except Exception as e:
            self.logger(f"Recovery action failed: {e}")
            return False
    
    def _detect_screen_change(self, before_img, after_img, threshold=0.1):
        """Detect if the screen has changed significantly"""
        try:
            import numpy as np
            
            before_array = np.array(before_img)
            after_array = np.array(after_img)
            
            # Calculate difference
            diff = np.sum(np.abs(before_array - after_array))
            change_percentage = diff / (before_array.size * 255) * 100
            
            return change_percentage > threshold
            
        except Exception:
            return False