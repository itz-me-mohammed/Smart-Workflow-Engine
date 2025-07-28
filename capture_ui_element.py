import pyautogui
import time
import os
import tkinter as tk
from datetime import datetime

def capture_ui_element():
    # Create UI images directory if it doesn't exist
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ui_images_dir = os.path.join(base_dir, 'ui_images')
    os.makedirs(ui_images_dir, exist_ok=True)
    
    # Create a simple GUI
    root = tk.Tk()
    root.title("UI Element Capture Tool")
    root.geometry("400x250")
    
    label = tk.Label(root, text="Element name (e.g., cisco_end_devices_button):")
    label.pack(pady=10)
    
    name_entry = tk.Entry(root, width=40)
    name_entry.pack(pady=5)
    name_entry.focus()
    
    info_label = tk.Label(root, 
                        text="After clicking 'Start Capture', you'll have 3 seconds\n"
                             "to position your mouse over the UI element.")
    info_label.pack(pady=10)
    
    status_var = tk.StringVar()
    status_var.set("Ready")
    status_label = tk.Label(root, textvariable=status_var)
    status_label.pack(pady=5)
    
    def start_capture():
        element_name = name_entry.get().strip()
        if not element_name:
            status_var.set("Please enter an element name")
            return
        
        status_var.set("Positioning in 3 seconds...")
        root.update()
        
        # Hide the window during capture
        root.withdraw()
        
        # Wait to allow positioning
        time.sleep(3)
        
        # Get current mouse position
        x, y = pyautogui.position()
        
        # Capture a small region around the mouse pointer
        region_size = 200  # pixels in each direction
        screenshot = pyautogui.screenshot(
            region=(x-region_size//2, y-region_size//2, region_size, region_size))
        
        # Save with timestamp to avoid overwriting
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{element_name}_{timestamp}.png"
        filepath = os.path.join(ui_images_dir, filename)
        screenshot.save(filepath)
        
        # Show the window again
        root.deiconify()
        
        status_var.set(f"Captured! Saved as {filename}")
        print(f"Element captured at ({x}, {y}) and saved to {filepath}")
        
        # Also save the coordinates for reference
        coords_file = os.path.join(ui_images_dir, f"{element_name}_{timestamp}_coords.txt")
        with open(coords_file, 'w') as f:
            f.write(f"x={x}\ny={y}\n")
    
    capture_button = tk.Button(root, text="Start Capture", command=start_capture)
    capture_button.pack(pady=20)
    
    root.mainloop()

if __name__ == "__main__":
    capture_ui_element()