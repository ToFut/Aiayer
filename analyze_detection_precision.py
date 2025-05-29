#!/usr/bin/env python3
"""
Analyze the exact precision of our detection system
"""

import pyautogui
import cv2
import numpy as np
from PIL import Image, ImageDraw
from universal_screen_detector import UniversalScreenDetector
import time

def analyze_detection_precision():
    """Analyze exactly where our detection is clicking vs where it should click"""
    
    print("🔍 ANALYZING DETECTION PRECISION")
    print("=" * 50)
    
    # Take a screenshot first
    screenshot = pyautogui.screenshot()
    screenshot.save("precision_analysis_before.png")
    
    # Run detection
    detector = UniversalScreenDetector()
    coords = detector.get_coordinates_for_step("Search for 'test'")
    
    print(f"📍 System detected coordinates: {coords}")
    
    # Let's manually examine the YouTube search box location
    # From the image, the search box appears to be around:
    search_box_left = 869    # Left edge of search input
    search_box_top = 140     # Top edge of search input  
    search_box_width = 150   # Approximate width
    search_box_height = 25   # Approximate height
    
    # Calculate actual center
    actual_center_x = search_box_left + search_box_width // 2
    actual_center_y = search_box_top + search_box_height // 2
    
    print(f"📍 Manual analysis - actual search box center: ({actual_center_x}, {actual_center_y})")
    print(f"📏 Detection offset: X={coords[0] - actual_center_x}, Y={coords[1] - actual_center_y}")
    
    # Create a precision analysis image
    img_array = np.array(screenshot)
    analysis_img = Image.fromarray(img_array)
    draw = ImageDraw.Draw(analysis_img)
    
    # Draw detected position (red)
    draw.ellipse([coords[0]-15, coords[1]-15, coords[0]+15, coords[1]+15], 
                outline='red', width=4)
    draw.text((coords[0]+20, coords[1]-20), f"DETECTED: {coords}", fill='red')
    
    # Draw actual position (green)
    draw.ellipse([actual_center_x-15, actual_center_y-15, actual_center_x+15, actual_center_y+15], 
                outline='lime', width=4)
    draw.text((actual_center_x+20, actual_center_y+20), f"ACTUAL: ({actual_center_x}, {actual_center_y})", fill='lime')
    
    # Draw the search box bounds
    draw.rectangle([search_box_left, search_box_top, 
                   search_box_left + search_box_width, search_box_top + search_box_height],
                  outline='yellow', width=2)
    
    analysis_img.save("precision_analysis.png")
    
    print("📸 Created precision_analysis.png showing:")
    print("   🔴 RED = Where system detected")
    print("   🟢 GREEN = Where search box actually is")
    print("   🟡 YELLOW = Search box bounds")
    
    # Test both positions
    print("\n🧪 TESTING BOTH POSITIONS:")
    
    print("1️⃣ Testing detected coordinates...")
    pyautogui.click(coords[0], coords[1])
    time.sleep(0.5)
    pyautogui.typewrite("DETECTED_POS")
    time.sleep(1)
    
    print("2️⃣ Testing actual coordinates...")
    pyautogui.click(actual_center_x, actual_center_y)
    time.sleep(0.5)
    pyautogui.typewrite("ACTUAL_POS")
    
    print("\n✅ Check which position successfully typed in the search box")

if __name__ == "__main__":
    analyze_detection_precision()