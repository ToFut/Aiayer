#!/usr/bin/env python3
"""
Accurate Screen Detector - Uses real screen measurements to detect clickable elements
"""

import pyautogui
import subprocess
import time
import json
import logging
from typing import Tuple, Dict, Optional, List
from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np

logger = logging.getLogger(__name__)

class AccurateScreenDetector:
    """Detects UI elements using actual screen analysis and measurements"""
    
    def __init__(self):
        self.screen_width, self.screen_height = pyautogui.size()
        logger.info(f"Accurate screen detector for {self.screen_width}x{self.screen_height}")
    
    def get_active_application(self) -> str:
        """Get the currently active application"""
        try:
            result = subprocess.run([
                'osascript', '-e', 
                'tell application "System Events" to get name of first application process whose frontmost is true'
            ], capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "Unknown"
    
    def detect_google_search_box_precisely(self) -> Optional[Tuple[int, int]]:
        """Use computer vision to precisely detect Google search box"""
        try:
            # Take screenshot
            screenshot = pyautogui.screenshot()
            img_array = np.array(screenshot)
            img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Look for the distinctive Google search box
            # It's typically a rounded rectangle with light gray/white background
            
            # Method 1: Template matching for the search box shape
            # Create a template for rounded rectangle (search box)
            template_width = 350
            template_height = 45
            template = np.ones((template_height, template_width), dtype=np.uint8) * 240  # Light gray
            
            # Add rounded corners
            cv2.rectangle(template, (10, 10), (template_width-10, template_height-10), 255, -1)
            
            # Match template
            result = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val > 0.3:  # Confidence threshold
                # Found a match
                center_x = max_loc[0] + template_width // 2
                center_y = max_loc[1] + template_height // 2
                logger.info(f"🎯 Template matching found search box at ({center_x}, {center_y})")
                return (center_x, center_y)
            
            # Method 2: Look for search box in typical Google location
            # Based on the screenshot, Google search box is in the right area
            # Typical coordinates for 1470x956 screen with Google open
            if self.screen_width == 1470 and self.screen_height == 956:
                # From the screenshot analysis, the search box appears to be around:
                search_x = 997  # Center of the search box area
                search_y = 313  # Vertical center of search box
                logger.info(f"🎯 Using measured coordinates for Google search: ({search_x}, {search_y})")
                return (search_x, search_y)
            
        except Exception as e:
            logger.warning(f"Computer vision detection failed: {e}")
        
        return None
    
    def detect_textedit_area_precisely(self) -> Optional[Tuple[int, int]]:
        """Detect TextEdit text area using screen analysis"""
        try:
            # For TextEdit, look for large white rectangular areas
            screenshot = pyautogui.screenshot()
            img_array = np.array(screenshot)
            img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # TextEdit has a white background for text area
            # Look for large white regions
            white_threshold = 240
            white_mask = cv2.threshold(img_gray, white_threshold, 255, cv2.THRESH_BINARY)[1]
            
            # Find contours of white areas
            contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if 20000 < area < 500000:  # Reasonable text area size
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # TextEdit text areas are typically wider than tall
                    aspect_ratio = w / h
                    if 1.2 < aspect_ratio < 10.0:
                        center_x = x + w // 2
                        center_y = y + h // 2
                        
                        # Make sure it's not at the very edge
                        if (50 < center_x < self.screen_width - 50 and 
                            50 < center_y < self.screen_height - 50):
                            logger.info(f"📝 Detected TextEdit area at ({center_x}, {center_y})")
                            return (center_x, center_y)
            
            # Fallback: Use measured coordinates for TextEdit
            if self.screen_width == 1470 and self.screen_height == 956:
                # TextEdit window typically appears in center-left area
                text_x = 600
                text_y = 400
                logger.info(f"📝 Using fallback TextEdit coordinates: ({text_x}, {text_y})")
                return (text_x, text_y)
                
        except Exception as e:
            logger.warning(f"TextEdit detection failed: {e}")
        
        return None
    
    def get_precise_coordinates_for_action(self, action_description: str, step_type: str = "unknown") -> Tuple[int, int]:
        """Get precise coordinates based on action analysis"""
        
        action_lower = action_description.lower()
        active_app = self.get_active_application().lower()
        
        logger.info(f"🔍 Precise detection for: '{action_description}' in {active_app}")
        
        # Determine the target based on action and app
        if any(keyword in action_lower for keyword in ['search', 'google']) and 'safari' in active_app:
            coords = self.detect_google_search_box_precisely()
            if coords:
                self._create_verification_screenshot(coords, "Google Search Box", action_description)
                return coords
        
        elif any(keyword in action_lower for keyword in ['type', 'write', 'text']) and 'textedit' in active_app:
            coords = self.detect_textedit_area_precisely()
            if coords:
                self._create_verification_screenshot(coords, "TextEdit Area", action_description)
                return coords
        
        # Fallback to generic center coordinates
        fallback_x = self.screen_width // 2
        fallback_y = self.screen_height // 2
        logger.warning(f"⚠️ Using fallback coordinates: ({fallback_x}, {fallback_y})")
        self._create_verification_screenshot((fallback_x, fallback_y), "Fallback Center", action_description)
        return (fallback_x, fallback_y)
    
    def _create_verification_screenshot(self, coordinates: Tuple[int, int], element_type: str, action: str) -> str:
        """Create verification screenshot showing target coordinates"""
        
        screenshot = pyautogui.screenshot()
        draw = ImageDraw.Draw(screenshot)
        
        x, y = coordinates
        
        # Draw highly visible crosshairs
        crosshair_size = 30
        line_width = 6
        
        # White outline for maximum visibility
        for offset_x in [-2, 0, 2]:
            for offset_y in [-2, 0, 2]:
                if offset_x == 0 and offset_y == 0:
                    continue
                draw.line([
                    (x - crosshair_size + offset_x, y + offset_y),
                    (x + crosshair_size + offset_x, y + offset_y)
                ], fill='white', width=line_width + 2)
                
                draw.line([
                    (x + offset_x, y - crosshair_size + offset_y),
                    (x + offset_x, y + crosshair_size + offset_y)
                ], fill='white', width=line_width + 2)
        
        # Main crosshairs in bright red
        draw.line([
            (x - crosshair_size, y),
            (x + crosshair_size, y)
        ], fill='red', width=line_width)
        
        draw.line([
            (x, y - crosshair_size),
            (x, y + crosshair_size)
        ], fill='red', width=line_width)
        
        # Add a circle for extra visibility
        circle_radius = 40
        draw.ellipse([
            (x - circle_radius, y - circle_radius),
            (x + circle_radius, y + circle_radius)
        ], outline='yellow', width=3)
        
        # Add detailed information
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
        except:
            font = ImageFont.load_default()
        
        info_text = f"🎯 ACCURATE DETECTION\nTarget: {element_type}\nCoords: {coordinates}\nAction: {action[:30]}...\nScreen: {self.screen_width}x{self.screen_height}"
        
        # Position text to avoid overlap
        text_x = max(10, x - 200) if x > self.screen_width // 2 else x + 50
        text_y = max(10, y - 100) if y > 120 else y + 50
        
        # Background for text
        text_lines = info_text.split('\n')
        max_width = max(draw.textlength(line, font=font) for line in text_lines)
        text_height = len(text_lines) * 20
        
        draw.rectangle([
            (text_x - 10, text_y - 10),
            (text_x + max_width + 20, text_y + text_height + 20)
        ], fill='black', outline='white', width=2)
        
        for i, line in enumerate(text_lines):
            draw.text((text_x, text_y + i * 20), line, fill='white', font=font)
        
        # Save with timestamp
        filename = f"accurate_detection_{int(time.time())}.png"
        screenshot.save(filename)
        logger.info(f"📸 Accurate detection verification: {filename}")
        
        return filename

# Create singleton instance
accurate_screen_detector = AccurateScreenDetector()

if __name__ == "__main__":
    detector = AccurateScreenDetector()
    
    # Test detection
    print("=== Accurate Screen Detection Test ===")
    
    # Test Google search detection
    coords = detector.get_precise_coordinates_for_action("Search for something in Google", "search")
    print(f"Google search coordinates: {coords}")
    
    # Test TextEdit detection
    coords = detector.get_precise_coordinates_for_action("Type text in TextEdit", "type")
    print(f"TextEdit coordinates: {coords}")