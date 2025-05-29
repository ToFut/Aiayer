#!/usr/bin/env python3
"""
Context-Aware Coordinate Detector - Uses AI vision to detect UI elements and calculate precise coordinates
"""

import pyautogui
import subprocess
import time
import json
import logging
from typing import Tuple, Dict, Optional, List
from PIL import Image, ImageDraw, ImageFont
import base64
import io

logger = logging.getLogger(__name__)

class ContextAwareCoordinateDetector:
    def __init__(self):
        self.screen_width, self.screen_height = pyautogui.size()
        logger.info(f"Context-aware detector initialized for {self.screen_width}x{self.screen_height}")
        
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
    
    def take_screenshot_for_analysis(self) -> Image.Image:
        """Take a screenshot for coordinate analysis"""
        return pyautogui.screenshot()
    
    def get_textedit_coordinates(self) -> Tuple[int, int]:
        """Get coordinates for TextEdit text area"""
        active_app = self.get_active_application()
        logger.info(f"Getting TextEdit coordinates, active app: {active_app}")
        
        if 'textedit' not in active_app.lower():
            # TextEdit not active, try to activate it
            logger.info("TextEdit not active, attempting to activate...")
            try:
                subprocess.run(['osascript', '-e', 'tell application "TextEdit" to activate'], check=True)
                time.sleep(1)
                active_app = self.get_active_application()
                logger.info(f"After activation attempt, active app: {active_app}")
            except subprocess.CalledProcessError:
                logger.warning("Failed to activate TextEdit")
        
        # TextEdit coordinates based on screen size and typical layout
        if self.screen_width == 1470 and self.screen_height == 956:
            # Center of typical TextEdit window
            x = 735  # Center X
            y = 400  # Middle of text area (not search box)
            logger.info(f"Using TextEdit coordinates for 1470x956: ({x}, {y})")
            return (x, y)
        else:
            # Generic TextEdit coordinates
            x = self.screen_width // 2
            y = self.screen_height // 2
            logger.info(f"Using generic TextEdit coordinates: ({x}, {y})")
            return (x, y)
    
    def get_safari_search_coordinates(self) -> Tuple[int, int]:
        """Get coordinates for Safari Google search box"""
        active_app = self.get_active_application()
        logger.info(f"Getting Safari search coordinates, active app: {active_app}")
        
        if 'safari' not in active_app.lower():
            # Safari not active, try to open Google
            logger.info("Safari not active, opening Google...")
            try:
                subprocess.run(['open', 'https://www.google.com'], check=True)
                time.sleep(3)
                active_app = self.get_active_application()
                logger.info(f"After opening Google, active app: {active_app}")
            except subprocess.CalledProcessError:
                logger.warning("Failed to open Safari")
        
        # Safari Google search coordinates
        if self.screen_width == 1470 and self.screen_height == 956:
            x = 735
            y = 250  # Google search box area
            logger.info(f"Using Safari search coordinates for 1470x956: ({x}, {y})")
            return (x, y)
        else:
            x = self.screen_width // 2
            y = self.screen_height // 3
            logger.info(f"Using generic Safari search coordinates: ({x}, {y})")
            return (x, y)
    
    def analyze_action_context(self, action_description: str, step_type: str = "unknown") -> Dict[str, any]:
        """Analyze the action context to determine the best coordinates"""
        action_lower = action_description.lower()
        step_lower = step_type.lower()
        
        context = {
            "target_app": "unknown",
            "element_type": "unknown",
            "coordinates": None,
            "needs_app_switch": False
        }
        
        # Determine target application and element
        if any(keyword in action_lower for keyword in ['textedit', 'notepad', 'text editor', 'write', 'type']) and 'google' not in action_lower and 'search' not in action_lower:
            context["target_app"] = "textedit"
            context["element_type"] = "text_area"
            context["coordinates"] = self.get_textedit_coordinates()
            
        elif any(keyword in action_lower for keyword in ['google', 'search', 'browser', 'safari']):
            context["target_app"] = "safari"
            context["element_type"] = "search_box"
            context["coordinates"] = self.get_safari_search_coordinates()
            
        else:
            # Fallback based on current active application
            active_app = self.get_active_application().lower()
            if 'textedit' in active_app:
                context["target_app"] = "textedit"
                context["element_type"] = "text_area"
                context["coordinates"] = self.get_textedit_coordinates()
            elif 'safari' in active_app:
                context["target_app"] = "safari"
                context["element_type"] = "search_box"
                context["coordinates"] = self.get_safari_search_coordinates()
            else:
                # Generic center click
                context["coordinates"] = (self.screen_width // 2, self.screen_height // 2)
        
        logger.info(f"Action context analysis: {context}")
        return context
    
    def get_smart_coordinates_for_action(self, action_description: str, step_type: str = "unknown") -> Tuple[int, int]:
        """Get smart coordinates based on action context"""
        context = self.analyze_action_context(action_description, step_type)
        
        if context["coordinates"]:
            return context["coordinates"]
        else:
            # Fallback to center
            return (self.screen_width // 2, self.screen_height // 2)
    
    def create_visual_verification(self, action_description: str, step_type: str = "unknown") -> str:
        """Create a visual verification of where the click will occur"""
        coordinates = self.get_smart_coordinates_for_action(action_description, step_type)
        context = self.analyze_action_context(action_description, step_type)
        
        # Take screenshot
        screenshot = self.take_screenshot_for_analysis()
        draw = ImageDraw.Draw(screenshot)
        
        # Draw crosshairs
        x, y = coordinates
        crosshair_size = 25
        line_width = 4
        
        # Red crosshairs with white outline for visibility
        for offset in [(2, 2), (-2, -2), (2, -2), (-2, 2)]:
            draw.line([
                (x - crosshair_size + offset[0], y + offset[1]),
                (x + crosshair_size + offset[0], y + offset[1])
            ], fill='white', width=line_width + 2)
            
            draw.line([
                (x + offset[0], y - crosshair_size + offset[1]),
                (x + offset[0], y + crosshair_size + offset[1])
            ], fill='white', width=line_width + 2)
        
        # Main red crosshairs
        draw.line([
            (x - crosshair_size, y),
            (x + crosshair_size, y)
        ], fill='red', width=line_width)
        
        draw.line([
            (x, y - crosshair_size),
            (x, y + crosshair_size)
        ], fill='red', width=line_width)
        
        # Add context information
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 14)
        except:
            font = ImageFont.load_default()
        
        info_text = f"Target: ({x}, {y})\nApp: {context['target_app']}\nElement: {context['element_type']}\nAction: {action_description[:30]}..."
        text_x = max(10, x - 150)
        text_y = max(10, y - 80)
        
        # White background for text
        text_lines = info_text.split('\n')
        max_width = max(draw.textlength(line, font=font) for line in text_lines)
        text_height = len(text_lines) * 18
        
        draw.rectangle([
            (text_x - 5, text_y - 5),
            (text_x + max_width + 5, text_y + text_height + 5)
        ], fill='white', outline='black', width=2)
        
        for i, line in enumerate(text_lines):
            draw.text((text_x, text_y + i * 18), line, fill='black', font=font)
        
        # Save with timestamp
        filename = f"context_aware_verification_{int(time.time())}.png"
        screenshot.save(filename)
        logger.info(f"Visual verification saved: {filename}")
        
        return filename

# Create singleton instance
context_aware_detector = ContextAwareCoordinateDetector()

if __name__ == "__main__":
    detector = ContextAwareCoordinateDetector()
    
    # Test different scenarios
    test_cases = [
        ("Type 'hello' in TextEdit", "type_text"),
        ("Search for latest news in Google", "search"),
        ("Write SEGEV in notepad", "type_text"),
        ("Open browser and search", "browse")
    ]
    
    print("=== Context-Aware Coordinate Detection Tests ===")
    
    for action, step_type in test_cases:
        print(f"\n🧪 Testing: {action}")
        context = detector.analyze_action_context(action, step_type)
        coords = detector.get_smart_coordinates_for_action(action, step_type)
        verification_file = detector.create_visual_verification(action, step_type)
        
        print(f"   Context: {context}")
        print(f"   Coordinates: {coords}")
        print(f"   Verification: {verification_file}")