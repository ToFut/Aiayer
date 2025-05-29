#!/usr/bin/env python3
"""
Smart Coordinate Detector - Intelligent coordinate calculation for UI elements
"""

import logging
from typing import Tuple, Optional, Dict
import pyautogui
import subprocess
import time

logger = logging.getLogger(__name__)

class SmartCoordinateDetector:
    """Detects optimal coordinates for UI elements based on screen size and layout patterns"""
    
    def __init__(self):
        self.screen_width, self.screen_height = pyautogui.size()
        logger.info(f"🎯 Smart Coordinate Detector initialized for {self.screen_width}x{self.screen_height}")
    
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
    
    def ensure_browser_with_google(self) -> bool:
        """Ensure we're in a browser with Google open"""
        active_app = self.get_active_application()
        logger.info(f"Current active app: {active_app}")
        
        # Check if already in a browser
        if any(browser in active_app.lower() for browser in ['safari', 'chrome', 'firefox', 'edge']):
            logger.info(f"Already in browser: {active_app}")
            return True
        
        # Open Google in default browser
        logger.info("Opening Google in browser...")
        try:
            subprocess.run(['open', 'https://www.google.com'], check=True)
            time.sleep(3)  # Wait for browser to load
            
            new_active_app = self.get_active_application()
            logger.info(f"New active app: {new_active_app}")
            
            if any(browser in new_active_app.lower() for browser in ['safari', 'chrome', 'firefox', 'edge']):
                return True
            else:
                logger.warning("Browser may not have opened properly")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to open browser: {e}")
            return False
    
    def get_google_search_box_coordinates(self) -> Tuple[int, int]:
        """Get optimal coordinates for Google search box based on screen size and browser"""
        
        # Ensure we're in a browser first
        self.ensure_browser_with_google()
        active_app = self.get_active_application()
        
        # Screen-specific optimizations with browser awareness
        if self.screen_width == 1470 and self.screen_height == 956:
            if 'safari' in active_app.lower():
                x, y = 735, 250  # Safari-specific Google search coordinates
            elif 'chrome' in active_app.lower():
                x, y = 735, 280  # Chrome-specific coordinates  
            else:
                x, y = 735, 265  # Generic browser coordinates
            
            logger.info(f"📍 Using {active_app} coordinates for 1470x956: ({x}, {y})")
            return (x, y)
        elif self.screen_width <= 1366:  # Smaller screens
            x = self.screen_width // 2
            y = int(self.screen_height * 0.32)  # Higher up on smaller screens
        elif self.screen_width <= 1920:  # Standard HD screens
            x = self.screen_width // 2
            y = int(self.screen_height * 0.34)   # Adjusted position
        else:  # Large screens (4K, etc.)
            x = self.screen_width // 2
            y = int(self.screen_height * 0.28)   # Higher up on large screens
        
        logger.info(f"📍 Google search box coordinates: ({x}, {y}) for {self.screen_width}x{self.screen_height}")
        return (x, y)
    
    def get_youtube_search_box_coordinates(self) -> Tuple[int, int]:
        """Get optimal coordinates for YouTube search box"""
        # YouTube search is typically in the top area
        if self.screen_width <= 1366:
            x = int(self.screen_width * 0.5)
            y = int(self.screen_height * 0.12)
        elif self.screen_width <= 1920:
            x = int(self.screen_width * 0.5)
            y = int(self.screen_height * 0.15)
        else:
            x = int(self.screen_width * 0.5)
            y = int(self.screen_height * 0.1)
        
        logger.info(f"📍 YouTube search box coordinates: ({x}, {y})")
        return (x, y)
    
    def get_safari_address_bar_coordinates(self) -> Tuple[int, int]:
        """Get optimal coordinates for Safari address bar"""
        # Safari address bar is at the top
        x = self.screen_width // 2
        y = int(self.screen_height * 0.08)  # Very top of the screen
        
        logger.info(f"📍 Safari address bar coordinates: ({x}, {y})")
        return (x, y)
    
    def get_adaptive_coordinates(self, element_type: str, context: Optional[str] = None) -> Tuple[int, int]:
        """Get adaptive coordinates based on element type and context"""
        element_type = element_type.lower()
        
        coordinate_map = {
            "search_box": self.get_google_search_box_coordinates(),
            "google_search": self.get_google_search_box_coordinates(),
            "youtube_search": self.get_youtube_search_box_coordinates(),
            "address_bar": self.get_safari_address_bar_coordinates(),
        }
        
        if element_type in coordinate_map:
            return coordinate_map[element_type]
        
        # Fallback to center-based positioning
        logger.warning(f"⚠️ Unknown element type '{element_type}', using center-based coordinates")
        return (self.screen_width // 2, self.screen_height // 2)
    
    def get_retry_coordinates(self, original_coords: Tuple[int, int], attempt: int) -> Tuple[int, int]:
        """Get adjusted coordinates for retry attempts"""
        x, y = original_coords
        
        # Progressive adjustment patterns
        adjustments = [
            (0, 20),     # Down slightly
            (0, -20),    # Up slightly  
            (30, 0),     # Right slightly
            (-30, 0),    # Left slightly
            (20, 20),    # Diagonal down-right
            (-20, -20),  # Diagonal up-left
            (0, 40),     # Further down
            (0, -40),    # Further up
        ]
        
        if attempt < len(adjustments):
            dx, dy = adjustments[attempt]
            new_x = max(0, min(self.screen_width - 1, x + dx))
            new_y = max(0, min(self.screen_height - 1, y + dy))
            
            logger.info(f"🔄 Retry attempt {attempt + 1}: adjusting ({x}, {y}) → ({new_x}, {new_y})")
            return (new_x, new_y)
        
        # If we've exhausted adjustments, return original
        return original_coords

# Create singleton instance
smart_coordinate_detector = SmartCoordinateDetector()