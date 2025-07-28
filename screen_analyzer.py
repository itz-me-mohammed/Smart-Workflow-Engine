import pyautogui
import cv2
import numpy as np
from PIL import Image, ImageGrab
import google.generativeai as genai
import base64
import io
import json

class ScreenAnalyzer:
    def __init__(self, api_key=None):
        self.api_key = api_key
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def analyze_screen_with_ai(self, prompt="Analyze this screen and suggest next actions"):
        """Use AI to analyze current screen content"""
        try:
            # Take screenshot
            screenshot = pyautogui.screenshot()
            
            # Convert to base64 for AI analysis
            buffer = io.BytesIO()
            screenshot.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            # Send to Gemini for analysis
            analysis_prompt = f"""
            {prompt}
            
            Analyze this screenshot and provide:
            1. What applications/windows are visible
            2. Current state of the interface
            3. Suggested next actions
            4. Any clickable elements you can identify
            5. Potential automation opportunities
            
            Return your analysis in JSON format:
            {{
                "applications_detected": [],
                "interface_state": "",
                "suggested_actions": [],
                "clickable_elements": [],
                "automation_opportunities": []
            }}
            """
            
            response = self.model.generate_content([
                analysis_prompt,
                {"mime_type": "image/png", "data": img_base64}
            ])
            
            # Parse response
            try:
                analysis = json.loads(response.text)
                return analysis
            except:
                return {"error": "Could not parse AI response", "raw_response": response.text}
                
        except Exception as e:
            return {"error": f"Screen analysis failed: {str(e)}"}
    
    def extract_text_from_screen(self, region=None):
        """Extract text from screen using OCR"""
        try:
            import pytesseract
            
            if region:
                # Extract from specific region
                screenshot = ImageGrab.grab(bbox=region)
            else:
                # Extract from entire screen
                screenshot = ImageGrab.grab()
            
            # Convert to format suitable for OCR
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # Enhance image for better OCR
            gray = cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2GRAY)
            
            # Apply denoising and sharpening
            denoised = cv2.medianBlur(gray, 3)
            
            # Extract text
            text = pytesseract.image_to_string(denoised, config='--psm 6')
            
            return {
                "success": True,
                "text": text,
                "region": region or "full_screen"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def detect_ui_elements(self, element_types=['buttons', 'text_fields', 'links']):
        """Detect UI elements on screen"""
        try:
            screenshot = pyautogui.screenshot()
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            detected_elements = []
            
            if 'buttons' in element_types:
                buttons = self._detect_buttons(screenshot_cv)
                detected_elements.extend(buttons)
            
            if 'text_fields' in element_types:
                text_fields = self._detect_text_fields(screenshot_cv)
                detected_elements.extend(text_fields)
            
            return {
                "success": True,
                "elements": detected_elements,
                "count": len(detected_elements)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _detect_buttons(self, image):
        """Detect button-like elements"""
        buttons = []
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect rectangles (potential buttons)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            # Filter by area and aspect ratio
            area = cv2.contourArea(contour)
            if 500 < area < 10000:  # Reasonable button size
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h
                
                if 0.5 < aspect_ratio < 5:  # Reasonable button proportions
                    buttons.append({
                        "type": "button",
                        "x": x + w//2,
                        "y": y + h//2,
                        "width": w,
                        "height": h,
                        "confidence": 0.7
                    })
        
        return buttons
    
    def _detect_text_fields(self, image):
        """Detect text input fields"""
        text_fields = []
        
        # This is a simplified implementation
        # In production, you'd use more sophisticated methods
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect white rectangles (potential text fields)
        _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if 1000 < area < 20000:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h
                
                if aspect_ratio > 2:  # Text fields are usually wider than tall
                    text_fields.append({
                        "type": "text_field",
                        "x": x + w//2,
                        "y": y + h//2,
                        "width": w,
                        "height": h,
                        "confidence": 0.6
                    })
        
        return text_fields

    def smart_element_finder(self, description):
        """Find elements based on natural language description"""
        try:
            # Analyze screen with AI
            analysis = self.analyze_screen_with_ai(f"Find elements matching this description: {description}")
            
            # Extract text for better context
            text_data = self.extract_text_from_screen()
            
            # Detect UI elements
            ui_elements = self.detect_ui_elements()
            
            # Combine results
            result = {
                "description": description,
                "ai_analysis": analysis,
                "screen_text": text_data.get("text", ""),
                "ui_elements": ui_elements.get("elements", []),
                "suggestions": []
            }
            
            # Generate suggestions based on description
            if "button" in description.lower():
                result["suggestions"] = [elem for elem in ui_elements.get("elements", []) if elem["type"] == "button"]
            elif "text" in description.lower() or "input" in description.lower():
                result["suggestions"] = [elem for elem in ui_elements.get("elements", []) if elem["type"] == "text_field"]
            
            return result
            
        except Exception as e:
            return {"error": f"Smart element finder failed: {str(e)}"}