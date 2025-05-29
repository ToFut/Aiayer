#!/usr/bin/env python3
"""
Visual Coordinate Calibrator - Real-time coordinate learning and adjustment
"""

import pyautogui
import subprocess
import time
import json
import os
import logging
from typing import Tuple, Dict, Optional
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

class VisualCoordinateCalibrator:
    """Calibrates and learns optimal click coordinates through visual feedback"""
    
    def __init__(self):
        self.screen_width, self.screen_height = pyautogui.size()
        self.calibration_data_file = "coordinate_calibration_data.json"
        self.learned_coordinates = self._load_calibration_data()
        logger.info(f"🎯 Visual Coordinate Calibrator initialized")
    
    def _load_calibration_data(self) -> Dict[str, Tuple[int, int]]:
        """Load previously learned coordinates"""
        try:
            if os.path.exists(self.calibration_data_file):
                with open(self.calibration_data_file, 'r') as f:
                    data = json.load(f)
                    return {k: tuple(v) for k, v in data.items()}
        except Exception as e:
            logger.warning(f"Could not load calibration data: {e}")
        return {}
    
    def _save_calibration_data(self):
        """Save learned coordinates"""
        try:
            with open(self.calibration_data_file, 'w') as f:
                json.dump(self.learned_coordinates, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save calibration data: {e}")
    
    def get_google_search_coordinates(self) -> Tuple[int, int]:
        """Get optimized Google search box coordinates"""
        # Check if we have learned coordinates
        if "google_search_box" in self.learned_coordinates:
            coords = self.learned_coordinates["google_search_box"]
            logger.info(f"📚 Using learned coordinates for Google search: {coords}")
            return coords
        
        # Calculate based on screen size with improved algorithm
        if self.screen_width == 1470 and self.screen_height == 956:
            # Your specific screen - optimized coordinates
            x = 735  # Center horizontally
            y = 320  # Higher up for Google search box (was 382)
        elif self.screen_width <= 1366:
            x = self.screen_width // 2
            y = int(self.screen_height * 0.32)
        elif self.screen_width <= 1920:
            x = self.screen_width // 2
            y = int(self.screen_height * 0.34)
        else:
            x = self.screen_width // 2
            y = int(self.screen_height * 0.28)
        
        logger.info(f"🎯 Calculated Google search coordinates: ({x}, {y})")
        return (x, y)
    
    def create_visual_click_test(self) -> str:
        """Create a visual test to help calibrate coordinates"""
        try:
            # Take a screenshot
            screenshot = pyautogui.screenshot()
            
            # Draw target areas on screenshot
            draw = ImageDraw.Draw(screenshot)
            
            # Get current coordinates
            google_coords = self.get_google_search_coordinates()
            
            # Draw crosshairs at target location
            x, y = google_coords
            size = 20
            
            # Draw red crosshairs
            draw.line([(x-size, y), (x+size, y)], fill='red', width=3)
            draw.line([(x, y-size), (x, y+size)], fill='red', width=3)
            draw.ellipse([x-5, y-5, x+5, y+5], fill='red')
            
            # Add text label
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
            except:
                font = ImageFont.load_default()
            
            draw.text((x+25, y-10), f"Google Search ({x}, {y})", fill='red', font=font)
            
            # Save screenshot with annotations
            test_file = "coordinate_test_screenshot.png"
            screenshot.save(test_file)
            
            logger.info(f"📸 Visual test saved to {test_file}")
            return test_file
            
        except Exception as e:
            logger.error(f"Failed to create visual test: {e}")
            return ""
    
    def learn_from_success(self, element_type: str, coordinates: Tuple[int, int]):
        """Learn successful coordinates for future use"""
        self.learned_coordinates[element_type] = coordinates
        self._save_calibration_data()
        logger.info(f"📚 Learned successful coordinates for {element_type}: {coordinates}")
    
    def learn_from_failure(self, element_type: str, failed_coords: Tuple[int, int], attempt: int) -> Tuple[int, int]:
        """Adjust coordinates based on failure"""
        x, y = failed_coords
        
        # Progressive adjustment for Google search box
        if element_type == "google_search_box":
            adjustments = [
                (0, -30),    # Up significantly  
                (0, -60),    # Up more
                (0, 30),     # Down from original
                (-50, -30),  # Left and up
                (50, -30),   # Right and up
                (0, -90),    # Much higher up
                (-30, 0),    # Left
                (30, 0),     # Right
            ]
        else:
            # Generic adjustments
            adjustments = [
                (0, 20),     # Down
                (0, -20),    # Up
                (30, 0),     # Right
                (-30, 0),    # Left
                (20, 20),    # Diagonal
                (-20, -20),  # Opposite diagonal
            ]
        
        if attempt < len(adjustments):
            dx, dy = adjustments[attempt]
            new_x = max(0, min(self.screen_width - 1, x + dx))
            new_y = max(0, min(self.screen_height - 1, y + dy))
            
            logger.info(f"🔄 Failure learning: adjusting {element_type} from ({x}, {y}) to ({new_x}, {new_y})")
            return (new_x, new_y)
        
        return failed_coords
    
    def interactive_calibration(self):
        """Interactive calibration mode"""
        print("🎯 Visual Coordinate Calibrator")
        print("=" * 40)
        
        # Create visual test
        test_file = self.create_visual_click_test()
        if test_file:
            print(f"📸 Screenshot saved: {test_file}")
            print("🔍 Open the screenshot to see where the system thinks the Google search box is.")
            
            # Open the file
            subprocess.run(['open', test_file])
        
        print("\n🎯 Current Google search coordinates:", self.get_google_search_coordinates())
        print("\n📋 To improve accuracy:")
        print("1. Look at the red crosshairs in the screenshot")
        print("2. Note if they're positioned correctly on the Google search box")
        print("3. Run automation and observe where clicks actually land")
        print("4. The system will learn from successes and failures")
        
        return self.get_google_search_coordinates()

# Create singleton instance
visual_calibrator = VisualCoordinateCalibrator()

if __name__ == "__main__":
    # Run interactive calibration
    visual_calibrator.interactive_calibration()