import cv2
import numpy as np
import pyautogui
from PIL import Image, ImageGrab
import json
import os

class VisualElementDetector:
    def __init__(self):
        self.confidence_threshold = 0.7
        self.template_cache = {}
    
    def find_element_by_image(self, template_path, confidence=None):
        """Find elements on screen using template matching"""
        if confidence is None:
            confidence = self.confidence_threshold
            
        try:
            # Take screenshot
            screenshot = pyautogui.screenshot()
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # Load template
            if template_path in self.template_cache:
                template = self.template_cache[template_path]
            else:
                template = cv2.imread(template_path)
                if template is None:
                    return {"success": False, "error": f"Template not found: {template_path}"}
                self.template_cache[template_path] = template
            
            # Perform template matching
            result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= confidence)
            
            matches = []
            for pt in zip(*locations[::-1]):
                h, w = template.shape[:2]
                matches.append({
                    "x": pt[0] + w//2,
                    "y": pt[1] + h//2,
                    "confidence": float(result[pt[1], pt[0]]),
                    "width": w,
                    "height": h
                })
            
            return {
                "success": True,
                "matches": matches,
                "count": len(matches)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def find_element_by_color(self, color_range, min_area=100):
        """Find elements by color"""
        try:
            screenshot = ImageGrab.grab()
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2HSV)
            
            # Create mask for the color range
            lower = np.array(color_range["lower"])
            upper = np.array(color_range["upper"])
            mask = cv2.inRange(hsv, lower, upper)
            
            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            elements = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > min_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    elements.append({
                        "x": x + w//2,
                        "y": y + h//2,
                        "width": w,
                        "height": h,
                        "area": area
                    })
            
            return {
                "success": True,
                "elements": elements,
                "count": len(elements)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def find_buttons_advanced(self):
        """Advanced button detection using multiple methods"""
        try:
            screenshot = ImageGrab.grab()
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2GRAY)
            
            buttons = []
            
            # Method 1: Edge detection for rectangular buttons
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if 500 < area < 10000:  # Reasonable button size
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    
                    if 0.3 < aspect_ratio < 5:  # Reasonable button proportions
                        buttons.append({
                            "type": "edge_detected",
                            "x": x + w//2,
                            "y": y + h//2,
                            "width": w,
                            "height": h,
                            "confidence": 0.7
                        })
            
            # Method 2: Color-based detection for common button colors
            button_colors = [
                {"name": "blue", "lower": [100, 50, 50], "upper": [130, 255, 255]},
                {"name": "green", "lower": [40, 50, 50], "upper": [80, 255, 255]},
                {"name": "red", "lower": [0, 50, 50], "upper": [20, 255, 255]}
            ]
            
            hsv = cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2HSV)
            
            for color_info in button_colors:
                mask = cv2.inRange(hsv, np.array(color_info["lower"]), np.array(color_info["upper"]))
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if 300 < area < 8000:
                        x, y, w, h = cv2.boundingRect(contour)
                        buttons.append({
                            "type": f"color_{color_info['name']}",
                            "x": x + w//2,
                            "y": y + h//2,
                            "width": w,
                            "height": h,
                            "confidence": 0.6
                        })
            
            return {
                "success": True,
                "buttons": buttons,
                "count": len(buttons)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_element_template(self, x, y, width, height, name):
        """Create a template from screen coordinates for future use"""
        try:
            # Take screenshot of the specified region
            screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))
            
            # Save as template
            template_path = f"templates/{name}.png"
            os.makedirs("templates", exist_ok=True)
            screenshot.save(template_path)
            
            return {
                "success": True,
                "template_path": template_path,
                "message": f"Template saved: {template_path}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": "Failed to load image"  # Fixed the unclosed string
            }

# Add to ActionExecutor
class ActionExecutor:
    def __init__(self, logger=print, api_key=None):
        # ...existing code...
        self.visual_detector = VisualElementDetector()
    
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