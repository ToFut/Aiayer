#!/usr/bin/env python3
"""
Application-Aware Coordinate Detector - Ensures clicks target the correct application
"""

import pyautogui
import subprocess
import time
import json
from typing import Tuple, Dict, Optional
from PIL import Image, ImageDraw, ImageFont

class ApplicationAwareCoordinateDetector:
    def __init__(self):
        self.screen_width, self.screen_height = pyautogui.size()
        print(f"Screen resolution: {self.screen_width}x{self.screen_height}")
        
    def get_active_application(self) -> str:
        """Get the currently active application using AppleScript"""
        try:
            result = subprocess.run([
                'osascript', '-e', 
                'tell application "System Events" to get name of first application process whose frontmost is true'
            ], capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "Unknown"
    
    def open_browser_and_navigate_to_google(self) -> bool:
        """Opens browser and navigates to Google, returns success status"""
        try:
            print("Opening browser and navigating to Google...")
            
            # Method 1: Try opening Google directly
            subprocess.run(['open', 'https://www.google.com'], check=True)
            time.sleep(3)  # Wait for browser to load
            
            # Verify we're in a browser
            active_app = self.get_active_application()
            print(f"Active application after opening Google: {active_app}")
            
            if any(browser in active_app.lower() for browser in ['safari', 'chrome', 'firefox', 'edge']):
                print(f"✅ Successfully opened Google in {active_app}")
                return True
            else:
                print(f"❌ Browser not detected. Active app: {active_app}")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to open browser: {e}")
            return False
    
    def get_browser_specific_coordinates(self, browser_name: str) -> Dict[str, Tuple[int, int]]:
        """Get browser-specific coordinates for common elements"""
        browser_name = browser_name.lower()
        
        # Base coordinates for 1470x956 screen
        if self.screen_width == 1470 and self.screen_height == 956:
            if 'safari' in browser_name:
                return {
                    'search_box': (735, 250),  # Safari Google search box
                    'address_bar': (735, 80),  # Safari address bar
                    'center': (735, 478)       # Screen center
                }
            elif 'chrome' in browser_name:
                return {
                    'search_box': (735, 280),  # Chrome Google search box
                    'address_bar': (735, 120), # Chrome address bar
                    'center': (735, 478)       # Screen center
                }
            elif 'firefox' in browser_name:
                return {
                    'search_box': (735, 270),  # Firefox Google search box
                    'address_bar': (735, 100), # Firefox address bar
                    'center': (735, 478)       # Screen center
                }
        
        # Fallback for other screen sizes
        return {
            'search_box': (self.screen_width // 2, self.screen_height // 3),
            'address_bar': (self.screen_width // 2, 100),
            'center': (self.screen_width // 2, self.screen_height // 2)
        }
    
    def get_smart_coordinates(self, element_type: str = 'search_box') -> Tuple[int, int]:
        """Get smart coordinates based on current application and element type"""
        active_app = self.get_active_application()
        print(f"Getting coordinates for '{element_type}' in {active_app}")
        
        # If not in a browser, try to open one
        if not any(browser in active_app.lower() for browser in ['safari', 'chrome', 'firefox', 'edge']):
            print("Not currently in a browser. Opening Google...")
            if self.open_browser_and_navigate_to_google():
                active_app = self.get_active_application()
            else:
                print("Failed to open browser, using fallback coordinates")
                return (self.screen_width // 2, self.screen_height // 3)
        
        # Get browser-specific coordinates
        coords = self.get_browser_specific_coordinates(active_app)
        target_coords = coords.get(element_type, coords['search_box'])
        
        print(f"Using coordinates {target_coords} for {element_type} in {active_app}")
        return target_coords
    
    def create_visual_test_with_app_context(self, element_type: str = 'search_box') -> str:
        """Create a visual test showing where we'll click, with application context"""
        
        # Get coordinates for the specified element
        target_x, target_y = self.get_smart_coordinates(element_type)
        active_app = self.get_active_application()
        
        # Take screenshot
        screenshot = pyautogui.screenshot()
        draw = ImageDraw.Draw(screenshot)
        
        # Draw crosshairs at target location
        crosshair_size = 20
        line_width = 3
        
        # Red crosshairs
        draw.line([
            (target_x - crosshair_size, target_y),
            (target_x + crosshair_size, target_y)
        ], fill='red', width=line_width)
        
        draw.line([
            (target_x, target_y - crosshair_size),
            (target_x, target_y + crosshair_size)
        ], fill='red', width=line_width)
        
        # Draw coordinate text
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
        except:
            font = ImageFont.load_default()
        
        coord_text = f"Target: ({target_x}, {target_y})\nApp: {active_app}\nElement: {element_type}"
        text_x = max(10, target_x - 100)
        text_y = max(10, target_y - 60)
        
        # White background for text
        text_bbox = draw.textbbox((text_x, text_y), coord_text, font=font)
        draw.rectangle(text_bbox, fill='white', outline='black')
        draw.text((text_x, text_y), coord_text, fill='black', font=font)
        
        # Save screenshot
        filename = f"app_aware_coordinate_test_{int(time.time())}.png"
        screenshot.save(filename)
        print(f"Visual test saved as: {filename}")
        return filename
    
    def test_click_accuracy(self, element_type: str = 'search_box') -> Dict:
        """Test click accuracy by taking before/after screenshots"""
        
        print(f"Testing click accuracy for {element_type}")
        
        # Take before screenshot
        before_file = self.create_visual_test_with_app_context(element_type)
        
        # Get coordinates and perform click
        target_x, target_y = self.get_smart_coordinates(element_type)
        active_app = self.get_active_application()
        
        print(f"Clicking at ({target_x}, {target_y}) in {active_app}")
        pyautogui.click(target_x, target_y)
        
        time.sleep(2)  # Wait for click effect
        
        # Take after screenshot
        after_screenshot = pyautogui.screenshot()
        after_file = f"after_click_test_{int(time.time())}.png"
        after_screenshot.save(after_file)
        
        return {
            'target_coordinates': (target_x, target_y),
            'active_application': active_app,
            'element_type': element_type,
            'before_screenshot': before_file,
            'after_screenshot': after_file,
            'screen_resolution': f"{self.screen_width}x{self.screen_height}"
        }

if __name__ == "__main__":
    detector = ApplicationAwareCoordinateDetector()
    
    print("=== Application-Aware Coordinate Detection Test ===")
    
    # Test the system
    result = detector.test_click_accuracy('search_box')
    
    print("\n=== Test Results ===")
    print(json.dumps(result, indent=2))
    
    print(f"\n📸 Check the screenshots:")
    print(f"Before: {result['before_screenshot']}")
    print(f"After: {result['after_screenshot']}")
    print(f"\nThis will help verify if the click hit the intended target!")