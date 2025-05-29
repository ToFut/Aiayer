#!/usr/bin/env python3
"""
Corrected Coordinate Detector - Fixes coordinate scaling and validation issues
"""

import pyautogui
import subprocess
import time
import json
import logging
import cv2
import numpy as np
from typing import Tuple, Dict, Optional, List
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

class CorrectedCoordinateDetector:
    """Coordinate detector with proper validation and screen-aware positioning"""
    
    def __init__(self):
        self.screen_width, self.screen_height = pyautogui.size()
        logger.info(f"Corrected detector initialized for {self.screen_width}x{self.screen_height}")
    
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
    
    def validate_coordinates(self, x: int, y: int) -> Tuple[int, int]:
        """Validate and correct coordinates to ensure they're within screen bounds"""
        
        # Ensure coordinates are within screen bounds
        corrected_x = max(10, min(self.screen_width - 10, x))
        corrected_y = max(10, min(self.screen_height - 10, y))
        
        if corrected_x != x or corrected_y != y:
            logger.warning(f"⚠️ Coordinates corrected: ({x}, {y}) → ({corrected_x}, {corrected_y})")
        
        return (corrected_x, corrected_y)
    
    def analyze_query_for_target(self, query: str) -> Dict[str, any]:
        """Analyze query to determine what UI element to target"""
        
        query_lower = query.lower()
        analysis = {
            "target_type": "unknown",
            "app_context": self.get_active_application().lower(),
            "search_terms": [],
            "coordinates": None
        }
        
        # Determine target type
        if any(word in query_lower for word in ['search', 'find', 'look']):
            analysis["target_type"] = "search_box"
        elif any(word in query_lower for word in ['type', 'write', 'enter', 'input']):
            analysis["target_type"] = "text_input"
        elif any(word in query_lower for word in ['click', 'press', 'tap']):
            analysis["target_type"] = "button"
        elif any(word in query_lower for word in ['navigate', 'go to', 'visit']):
            analysis["target_type"] = "address_bar"
        
        # Extract search terms
        for word in query_lower.split():
            if len(word) > 3 and word not in ['search', 'for', 'the', 'and', 'in', 'on', 'at']:
                analysis["search_terms"].append(word)
        
        logger.info(f"🎯 Query analysis: {analysis}")
        return analysis
    
    def get_precise_coordinates_by_app_and_context(self, analysis: Dict) -> Tuple[int, int]:
        """Get precise coordinates based on app context and target type"""
        
        app = analysis["app_context"]
        target_type = analysis["target_type"]
        
        # Safari coordinates for different elements
        if 'safari' in app:
            if target_type == "search_box":
                # Check if we're currently on YouTube by looking at the URL/title
                try:
                    # Use AppleScript to get the current URL
                    result = subprocess.run([
                        'osascript', '-e', 
                        'tell application "Safari" to get URL of active tab of front window'
                    ], capture_output=True, text=True, timeout=2)
                    current_url = result.stdout.strip().lower()
                    
                    if 'youtube' in current_url:
                        # YouTube search box (measured from screenshot)
                        logger.info("🎯 Detected YouTube - using YouTube search coordinates")
                        return self.validate_coordinates(940, 151)
                    elif 'google' in current_url:
                        # Google search box
                        logger.info("🎯 Detected Google - using Google search coordinates")
                        return self.validate_coordinates(735, 320)
                except:
                    pass
                
                # Fallback: check search terms
                if any(term in ['youtube', 'video', 'omer', 'adam'] for term in analysis["search_terms"]):
                    # YouTube search box (center-right area)
                    logger.info("🎯 Search terms suggest YouTube - using YouTube coordinates")
                    return self.validate_coordinates(940, 151)
                else:
                    # Generic search (center area)
                    logger.info("🎯 Using generic search coordinates")
                    return self.validate_coordinates(735, 320)
            
            elif target_type == "address_bar":
                # Safari address bar (top center)
                return self.validate_coordinates(735, 101)
            
            elif target_type == "text_input":
                # Generic text input in Safari
                return self.validate_coordinates(735, 300)
        
        # TextEdit coordinates
        elif 'textedit' in app:
            if target_type in ["text_input", "search_box"]:
                # TextEdit document area (center-left)
                return self.validate_coordinates(600, 400)
        
        # Cursor editor coordinates  
        elif 'cursor' in app:
            if target_type in ["text_input", "search_box"]:
                # Cursor editor area (center)
                return self.validate_coordinates(735, 478)
        
        # Chrome coordinates
        elif 'chrome' in app:
            if target_type == "search_box":
                # Chrome address/search bar
                return self.validate_coordinates(735, 140)
        
        # Fallback coordinates based on target type only
        if target_type == "search_box":
            return self.validate_coordinates(self.screen_width // 2, self.screen_height // 3)
        elif target_type == "text_input":
            return self.validate_coordinates(self.screen_width // 2, self.screen_height // 2)
        elif target_type == "address_bar":
            return self.validate_coordinates(self.screen_width // 2, 100)
        else:
            return self.validate_coordinates(self.screen_width // 2, self.screen_height // 2)
    
    def detect_visual_elements_simplified(self, target_type: str) -> Optional[Tuple[int, int]]:
        """Simplified visual detection with proper coordinate validation"""
        
        try:
            screenshot = pyautogui.screenshot()
            img_array = np.array(screenshot)
            img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            if target_type == "search_box":
                # Look for search box patterns
                # Method 1: Look for rounded rectangles in upper area
                upper_region = img_gray[0:self.screen_height//2, :]
                edges = cv2.Canny(upper_region, 50, 150)
                contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if 1000 < area < 20000:  # Search box size range
                        x, y, w, h = cv2.boundingRect(contour)
                        aspect_ratio = w / h
                        
                        # Search boxes are wide and not too tall
                        if 3.0 < aspect_ratio < 15.0 and 20 < h < 80:
                            center_x = x + w // 2
                            center_y = y + h // 2
                            
                            # Validate coordinates are reasonable
                            if (100 < center_x < self.screen_width - 100 and 
                                50 < center_y < self.screen_height // 2):
                                
                                validated_coords = self.validate_coordinates(center_x, center_y)
                                logger.info(f"🔍 Visual detection found search box at {validated_coords}")
                                return validated_coords
            
            elif target_type == "text_input":
                # Look for text input areas (light colored rectangles)
                white_threshold = 220
                white_mask = cv2.threshold(img_gray, white_threshold, 255, cv2.THRESH_BINARY)[1]
                contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if 5000 < area < 200000:  # Text area size range
                        x, y, w, h = cv2.boundingRect(contour)
                        
                        # Text areas are typically wider than tall
                        aspect_ratio = w / h
                        if 1.2 < aspect_ratio < 10.0:
                            center_x = x + w // 2
                            center_y = y + h // 2
                            
                            # Validate coordinates
                            if (50 < center_x < self.screen_width - 50 and 
                                50 < center_y < self.screen_height - 50):
                                
                                validated_coords = self.validate_coordinates(center_x, center_y)
                                logger.info(f"🔍 Visual detection found text area at {validated_coords}")
                                return validated_coords
        
        except Exception as e:
            logger.warning(f"Visual detection failed: {e}")
        
        return None
    
    def get_corrected_coordinates(self, query: str, step_type: str = "unknown") -> Tuple[int, int]:
        """Main method: Get corrected coordinates with proper validation"""
        
        logger.info(f"🔧 Corrected coordinate detection for: '{query}'")
        
        # Step 1: Analyze query
        analysis = self.analyze_query_for_target(query)
        
        # Step 2: Try visual detection first
        visual_coords = self.detect_visual_elements_simplified(analysis["target_type"])
        if visual_coords:
            self._create_corrected_verification(visual_coords, "Visual Detection", query, analysis)
            return visual_coords
        
        # Step 3: Use app-context based coordinates
        context_coords = self.get_precise_coordinates_by_app_and_context(analysis)
        self._create_corrected_verification(context_coords, "Context-Based", query, analysis)
        
        return context_coords
    
    def _create_corrected_verification(self, coordinates: Tuple[int, int], method: str, query: str, analysis: Dict) -> str:
        """Create verification screenshot with corrected coordinates"""
        
        screenshot = pyautogui.screenshot()
        draw = ImageDraw.Draw(screenshot)
        
        x, y = coordinates
        
        # Draw highly visible target indicators
        crosshair_size = 30
        line_width = 5
        
        # Multiple colored outlines for maximum visibility
        colors = ['white', 'black', 'red']
        for i, color in enumerate(colors):
            size_offset = (2 - i) * 2
            width = line_width - i
            
            # Horizontal line
            draw.line([
                (x - crosshair_size - size_offset, y),
                (x + crosshair_size + size_offset, y)
            ], fill=color, width=width)
            
            # Vertical line
            draw.line([
                (x, y - crosshair_size - size_offset),
                (x, y + crosshair_size + size_offset)
            ], fill=color, width=width)
        
        # Add a circle for extra visibility
        circle_radius = 40
        draw.ellipse([
            (x - circle_radius, y - circle_radius),
            (x + circle_radius, y + circle_radius)
        ], outline='yellow', width=4)
        
        # Add coordinate info
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
        except:
            font = ImageFont.load_default()
        
        info_text = f"🔧 CORRECTED DETECTION\nMethod: {method}\nTarget: {analysis['target_type']}\nApp: {analysis['app_context']}\nCoords: {coordinates}\nQuery: {query[:25]}...\nScreen: {self.screen_width}x{self.screen_height}"
        
        # Position text to avoid overlap
        text_x = max(10, x - 200) if x > self.screen_width // 2 else x + 60
        text_y = max(10, y - 120) if y > 140 else y + 60
        
        # Ensure text stays on screen
        text_x = min(text_x, self.screen_width - 250)
        text_y = min(text_y, self.screen_height - 160)
        
        # Background for text
        text_lines = info_text.split('\n')
        max_width = max(draw.textlength(line, font=font) for line in text_lines)
        text_height = len(text_lines) * 20
        
        draw.rectangle([
            (text_x - 10, text_y - 10),
            (text_x + max_width + 20, text_y + text_height + 20)
        ], fill='black', outline='yellow', width=3)
        
        for i, line in enumerate(text_lines):
            draw.text((text_x, text_y + i * 20), line, fill='white', font=font)
        
        # Save with timestamp
        filename = f"corrected_detection_{int(time.time())}.png"
        screenshot.save(filename)
        logger.info(f"📸 Corrected detection verification: {filename}")
        
        return filename

# Create singleton instance
corrected_coordinate_detector = CorrectedCoordinateDetector()

if __name__ == "__main__":
    detector = CorrectedCoordinateDetector()
    
    # Test with the YouTube search scenario
    test_queries = [
        "Search for omeradam in YouTube",
        "Type text in TextEdit",
        "Navigate to website",
        "Click submit button"
    ]
    
    print("=== Corrected Coordinate Detection Tests ===")
    
    for query in test_queries:
        print(f"\n🔧 Testing: {query}")
        coords = detector.get_corrected_coordinates(query)
        print(f"   Corrected coordinates: {coords}")
        time.sleep(1)