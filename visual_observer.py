# visual_observer.py

from PIL import ImageGrab
import pytesseract

# Set the path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

import datetime
import os

# Optional: specify your tesseract path manually if needed
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

class VisualObserver:
    def __init__(self, screenshot_dir="screenshots"):
        self.screenshot_dir = screenshot_dir
        os.makedirs(screenshot_dir, exist_ok=True)

    def take_screenshot(self, label="screen"):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.screenshot_dir, f"{label}_{timestamp}.png")
        image = ImageGrab.grab()
        image.save(filename)
        print(f"[Observer] Screenshot saved: {filename}")
        return filename

    def extract_text_from_screen(self):
        image = ImageGrab.grab()
        text = pytesseract.image_to_string(image)
        print("[Observer] Extracted Text:")
        print(text)
        return text
