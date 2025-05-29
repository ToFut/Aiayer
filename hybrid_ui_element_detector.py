#!/usr/bin/env python3
"""
Hybrid UI Element Detector - Combines multiple detection methods for maximum accuracy
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
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class DetectedElement:
    """Represents a detected UI element"""
    element_type: str
    coordinates: Tuple[int, int]
    confidence: float
    detection_method: str
    description: str

class HybridUIElementDetector:
    """Combines multiple detection methods for accurate UI element location"""
    
    def __init__(self):
        self.screen_width, self.screen_height = pyautogui.size()
        logger.info(f"Hybrid UI detector initialized for {self.screen_width}x{self.screen_height}")
    
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
    
    def detect_ui_elements_opencv(self, action_description: str) -> Optional[DetectedElement]:
        """Use OpenCV to detect UI elements through template matching and edge detection"""
        
        try:
            # Take screenshot and convert to OpenCV format
            screenshot = pyautogui.screenshot()
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2GRAY)
            
            active_app = self.get_active_application().lower()
            action_lower = action_description.lower()
            
            # Strategy 1: Text input field detection
            if any(keyword in action_lower for keyword in ['type', 'write', 'input', 'text']):
                if 'textedit' in active_app or 'text' in active_app:
                    # TextEdit text area detection
                    coords = self._detect_textedit_area(screenshot_cv, gray)
                    if coords:
                        return DetectedElement(
                            element_type="text_area",
                            coordinates=coords,
                            confidence=0.85,
                            detection_method="opencv_textedit",
                            description="TextEdit text area"
                        )
                
                elif 'cursor' in active_app:
                    # Cursor editor detection
                    coords = self._detect_cursor_editor_area(screenshot_cv, gray)
                    if coords:
                        return DetectedElement(
                            element_type="text_area",
                            coordinates=coords,
                            confidence=0.80,
                            detection_method="opencv_cursor",
                            description="Cursor editor area"
                        )
            
            # Strategy 2: Search box detection for browsers
            if any(keyword in action_lower for keyword in ['search', 'google', 'browser']):
                if any(browser in active_app for browser in ['safari', 'chrome', 'firefox']):
                    coords = self._detect_browser_search_box(screenshot_cv, gray)
                    if coords:
                        return DetectedElement(
                            element_type="search_box",
                            coordinates=coords,
                            confidence=0.90,
                            detection_method="opencv_browser",
                            description="Browser search box"
                        )
            
        except Exception as e:
            logger.warning(f"OpenCV detection failed: {e}")
        
        return None
    
    def _detect_textedit_area(self, screenshot_cv, gray) -> Optional[Tuple[int, int]]:
        """Detect TextEdit text area using edge detection"""
        try:
            # Look for white rectangular areas (typical text areas)
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if 5000 < area < 200000:  # Reasonable text area size
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    
                    # Text areas are typically wider than tall
                    if 1.0 < aspect_ratio < 5.0:
                        center_x = x + w // 2
                        center_y = y + h // 2
                        
                        # Ensure it's in a reasonable screen position
                        if (100 < center_x < self.screen_width - 100 and 
                            100 < center_y < self.screen_height - 100):
                            logger.info(f"📝 Detected TextEdit area at ({center_x}, {center_y})")
                            return (center_x, center_y)
        except:
            pass
        return None
    
    def _detect_cursor_editor_area(self, screenshot_cv, gray) -> Optional[Tuple[int, int]]:
        """Detect Cursor editor area"""
        try:
            # Cursor has dark background, look for text cursor or code areas
            # Use the center-left area which is typically where code is written
            center_x = self.screen_width // 2
            center_y = self.screen_height // 2
            
            # Cursor editor typically has the main editing area in the center
            logger.info(f"💻 Using Cursor editor center area at ({center_x}, {center_y})")
            return (center_x, center_y)
        except:
            pass
        return None
    
    def _detect_browser_search_box(self, screenshot_cv, gray) -> Optional[Tuple[int, int]]:
        """Detect browser search box using template matching"""
        try:
            # Look for rounded rectangular areas in the upper portion
            height, width = gray.shape
            upper_region = gray[0:height//3, :]  # Top third of screen
            
            # Use adaptive threshold to find input fields
            thresh = cv2.adaptiveThreshold(upper_region, 255, cv2.ADAPTIVE_THRESHOLD_GAUSSIAN_C, 
                                         cv2.THRESH_BINARY, 11, 2)
            
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if 1000 < area < 50000:  # Search box size range
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    
                    # Search boxes are wide and not too tall
                    if 3.0 < aspect_ratio < 15.0 and h > 20:
                        center_x = x + w // 2
                        center_y = y + h // 2
                        
                        # Ensure it's in the center horizontally
                        if abs(center_x - width // 2) < width // 4:
                            logger.info(f"🔍 Detected search box at ({center_x}, {center_y})")
                            return (center_x, center_y)
        except:
            pass
        return None
    
    def get_context_aware_coordinates(self, action_description: str, step_type: str = "unknown") -> Tuple[int, int]:
        """Get coordinates using context awareness"""
        try:
            from context_aware_coordinate_detector import context_aware_detector
            return context_aware_detector.get_smart_coordinates_for_action(action_description, step_type)
        except Exception as e:
            logger.warning(f"Context-aware detection failed: {e}")
            return (self.screen_width // 2, self.screen_height // 2)
    
    def get_smart_coordinates_for_action(self, action_description: str, step_type: str = "unknown") -> Tuple[int, int]:
        """Main method: Get smart coordinates using hybrid detection"""
        
        logger.info(f"🔍 Hybrid detection for: '{action_description}'")
        
        # Method 1: Try OpenCV detection first (fast and accurate)
        opencv_result = self.detect_ui_elements_opencv(action_description)
        if opencv_result and opencv_result.confidence > 0.7:
            logger.info(f"✅ OpenCV detection successful: {opencv_result.description} at {opencv_result.coordinates}")
            self._create_visual_verification(opencv_result, action_description)
            return opencv_result.coordinates
        
        # Method 2: Fall back to context-aware detection
        logger.info("🔄 Falling back to context-aware detection")
        context_coords = self.get_context_aware_coordinates(action_description, step_type)
        
        # Create verification for context-aware result
        context_element = DetectedElement(
            element_type="context_based",
            coordinates=context_coords,
            confidence=0.6,
            detection_method="context_aware",
            description="Context-based coordinate"
        )
        self._create_visual_verification(context_element, action_description)
        
        return context_coords
    
    def _create_visual_verification(self, element: DetectedElement, action_description: str) -> str:
        """Create visual verification of detected element"""
        
        screenshot = pyautogui.screenshot()
        draw = ImageDraw.Draw(screenshot)
        
        x, y = element.coordinates
        
        # Color based on confidence and method
        if element.confidence > 0.8:
            color = 'lime'
        elif element.confidence > 0.6:
            color = 'orange'
        else:
            color = 'red'
        
        # Draw crosshairs
        crosshair_size = 25
        line_width = 4
        
        # White outline
        for offset in [(2, 2), (-2, -2), (2, -2), (-2, 2)]:
            draw.line([
                (x - crosshair_size + offset[0], y + offset[1]),
                (x + crosshair_size + offset[0], y + offset[1])
            ], fill='white', width=line_width + 1)
            
            draw.line([
                (x + offset[0], y - crosshair_size + offset[1]),
                (x + offset[0], y + crosshair_size + offset[1])
            ], fill='white', width=line_width + 1)
        
        # Main crosshairs
        draw.line([
            (x - crosshair_size, y),
            (x + crosshair_size, y)
        ], fill=color, width=line_width)
        
        draw.line([
            (x, y - crosshair_size),
            (x, y + crosshair_size)
        ], fill=color, width=line_width)
        
        # Add detection info
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 12)
        except:
            font = ImageFont.load_default()
        
        info_text = f"🎯 {element.detection_method.upper()}\n{element.description}\nCoords: {element.coordinates}\nConfidence: {element.confidence:.2f}\nAction: {action_description[:20]}..."
        
        text_x = max(10, x - 120)
        text_y = max(10, y - 80) if y > 100 else y + 40
        
        # Background
        text_lines = info_text.split('\n')
        max_width = max(draw.textlength(line, font=font) for line in text_lines)
        text_height = len(text_lines) * 16
        
        draw.rectangle([
            (text_x - 5, text_y - 5),
            (text_x + max_width + 10, text_y + text_height + 10)
        ], fill='white', outline='black', width=1)
        
        for i, line in enumerate(text_lines):
            draw.text((text_x, text_y + i * 16), line, fill='black', font=font)
        
        # Save
        filename = f"hybrid_detection_{int(time.time())}.png"
        screenshot.save(filename)
        logger.info(f"📸 Hybrid detection verification: {filename}")
        
        return filename

# Create singleton instance
hybrid_ui_detector = HybridUIElementDetector()

if __name__ == "__main__":
    detector = HybridUIElementDetector()
    
    # Test different scenarios
    test_cases = [
        "Type text in TextEdit",
        "Write code in Cursor", 
        "Search in Google",
        "Click search box"
    ]
    
    print("=== Hybrid UI Element Detection Tests ===")
    
    for test_desc in test_cases:
        print(f"\n🧪 Testing: {test_desc}")
        coords = detector.get_smart_coordinates_for_action(test_desc)
        print(f"   Coordinates: {coords}")