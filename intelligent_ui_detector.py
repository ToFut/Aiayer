#!/usr/bin/env python3
"""
Intelligent UI Detector - Uses AI vision to identify any UI element based on query intent
"""

import pyautogui
import subprocess
import time
import json
import logging
import cv2
import numpy as np
from typing import Tuple, Dict, Optional, List, Any
from PIL import Image, ImageDraw, ImageFont
import base64
import io
import requests
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class UIElement:
    """Detected UI element with metadata"""
    element_type: str
    coordinates: Tuple[int, int]
    confidence: float
    description: str
    bounds: Tuple[int, int, int, int]  # x1, y1, x2, y2
    detection_method: str

class IntelligentUIDetector:
    """Intelligent UI detector that analyzes screen content to find appropriate elements for any query"""
    
    def __init__(self):
        self.screen_width, self.screen_height = pyautogui.size()
        self.ollama_url = "http://localhost:11434/api/generate"
        logger.info(f"Intelligent UI detector initialized for {self.screen_width}x{self.screen_height}")
    
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
    
    def analyze_intent_and_ui_needs(self, query: str, step_type: str = "unknown") -> Dict[str, Any]:
        """Analyze what UI elements are needed based on the query"""
        
        query_lower = query.lower()
        intent_analysis = {
            "target_element_types": [],
            "search_keywords": [],
            "interaction_type": "click",
            "context_clues": []
        }
        
        # Text input needs
        if any(word in query_lower for word in ['type', 'write', 'enter', 'input', 'fill']):
            intent_analysis["target_element_types"].extend(["text_input", "text_area", "search_box", "input_field"])
            intent_analysis["interaction_type"] = "type"
            intent_analysis["search_keywords"].extend(["input", "text", "field", "box", "area"])
        
        # Search needs
        if any(word in query_lower for word in ['search', 'find', 'look', 'google', 'browse']):
            intent_analysis["target_element_types"].extend(["search_box", "address_bar", "text_input"])
            intent_analysis["search_keywords"].extend(["search", "google", "address", "url"])
        
        # Button/click needs
        if any(word in query_lower for word in ['click', 'press', 'tap', 'select', 'choose']):
            intent_analysis["target_element_types"].extend(["button", "link", "menu_item", "tab"])
            intent_analysis["search_keywords"].extend(["button", "link", "menu", "tab"])
        
        # App-specific context
        if any(word in query_lower for word in ['open', 'launch', 'start']):
            intent_analysis["target_element_types"].extend(["app_icon", "launcher", "dock_item"])
            intent_analysis["search_keywords"].extend(["icon", "app", "application"])
        
        # Navigation needs
        if any(word in query_lower for word in ['go to', 'navigate', 'visit', 'browse to']):
            intent_analysis["target_element_types"].extend(["address_bar", "url_bar", "navigation"])
            intent_analysis["search_keywords"].extend(["address", "url", "navigation"])
        
        # Extract specific targets from query
        intent_analysis["context_clues"] = self._extract_context_clues(query)
        
        logger.info(f"🧠 Intent analysis for '{query}': {intent_analysis}")
        return intent_analysis
    
    def _extract_context_clues(self, query: str) -> List[str]:
        """Extract specific context clues from the query"""
        clues = []
        
        # Common app names
        apps = ['safari', 'chrome', 'firefox', 'textedit', 'cursor', 'notes', 'mail', 'messages']
        for app in apps:
            if app in query.lower():
                clues.append(f"app_{app}")
        
        # Common UI elements mentioned
        ui_elements = ['button', 'menu', 'toolbar', 'sidebar', 'tab', 'window', 'dialog']
        for element in ui_elements:
            if element in query.lower():
                clues.append(f"ui_{element}")
        
        # Specific actions
        actions = ['login', 'signup', 'download', 'upload', 'save', 'delete', 'edit', 'settings']
        for action in actions:
            if action in query.lower():
                clues.append(f"action_{action}")
        
        return clues
    
    def detect_ui_elements_with_cv(self, intent_analysis: Dict[str, Any]) -> List[UIElement]:
        """Use computer vision to detect UI elements based on intent"""
        
        elements = []
        screenshot = pyautogui.screenshot()
        img_array = np.array(screenshot)
        img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        target_types = intent_analysis["target_element_types"]
        
        # Strategy 1: Detect text input fields
        if any(t in target_types for t in ["text_input", "search_box", "input_field", "text_area"]):
            text_inputs = self._detect_text_inputs(img_gray, img_array)
            elements.extend(text_inputs)
        
        # Strategy 2: Detect buttons
        if "button" in target_types:
            buttons = self._detect_buttons(img_gray, img_array)
            elements.extend(buttons)
        
        # Strategy 3: Detect clickable areas
        if any(t in target_types for t in ["link", "menu_item", "tab"]):
            clickables = self._detect_clickable_areas(img_gray, img_array)
            elements.extend(clickables)
        
        # Strategy 4: Detect app-specific elements
        active_app = self.get_active_application().lower()
        app_elements = self._detect_app_specific_elements(img_gray, img_array, active_app, intent_analysis)
        elements.extend(app_elements)
        
        # Sort by confidence
        elements.sort(key=lambda e: e.confidence, reverse=True)
        
        logger.info(f"🔍 Computer vision detected {len(elements)} elements")
        return elements
    
    def _detect_text_inputs(self, img_gray, img_array) -> List[UIElement]:
        """Detect text input fields, search boxes, and text areas"""
        elements = []
        
        try:
            # Method 1: Look for rounded rectangles (typical input fields)
            edges = cv2.Canny(img_gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if 500 < area < 50000:  # Reasonable input field size
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    
                    # Input fields are typically wider than tall
                    if 2.0 < aspect_ratio < 20.0 and h > 15:
                        center_x = x + w // 2
                        center_y = y + h // 2
                        
                        # Check if it looks like an input field (light colored background)
                        roi = img_gray[y:y+h, x:x+w]
                        avg_brightness = np.mean(roi)
                        
                        if avg_brightness > 180:  # Light background
                            confidence = min(0.9, (avg_brightness - 180) / 75 + 0.5)
                            
                            elements.append(UIElement(
                                element_type="text_input",
                                coordinates=(center_x, center_y),
                                confidence=confidence,
                                description=f"Text input field ({w}x{h})",
                                bounds=(x, y, x+w, y+h),
                                detection_method="cv_input_detection"
                            ))
            
            # Method 2: Look for search box patterns (Google-style)
            # Template matching for search box shapes
            template_sizes = [(350, 45), (300, 40), (400, 50)]
            
            for temp_w, temp_h in template_sizes:
                # Create search box template
                template = np.ones((temp_h, temp_w), dtype=np.uint8) * 245
                cv2.rectangle(template, (5, 5), (temp_w-5, temp_h-5), 255, -1)
                
                # Match template
                result = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
                locations = np.where(result >= 0.4)
                
                for pt in zip(*locations[::-1]):
                    center_x = pt[0] + temp_w // 2
                    center_y = pt[1] + temp_h // 2
                    confidence = result[pt[1], pt[0]]
                    
                    elements.append(UIElement(
                        element_type="search_box",
                        coordinates=(center_x, center_y),
                        confidence=confidence,
                        description=f"Search box template match",
                        bounds=(pt[0], pt[1], pt[0]+temp_w, pt[1]+temp_h),
                        detection_method="cv_template_matching"
                    ))
        
        except Exception as e:
            logger.warning(f"Text input detection failed: {e}")
        
        return elements
    
    def _detect_buttons(self, img_gray, img_array) -> List[UIElement]:
        """Detect buttons and clickable elements"""
        elements = []
        
        try:
            # Look for button-like shapes (rectangles with specific characteristics)
            edges = cv2.Canny(img_gray, 30, 100)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if 200 < area < 10000:  # Button size range
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    
                    # Buttons are typically not too wide or tall
                    if 0.3 < aspect_ratio < 6.0 and 15 < h < 100:
                        center_x = x + w // 2
                        center_y = y + h // 2
                        
                        # Check for button-like appearance
                        roi = img_gray[y:y+h, x:x+w]
                        brightness_std = np.std(roi)
                        
                        # Buttons often have consistent coloring
                        if brightness_std < 30:
                            confidence = 0.6
                            
                            elements.append(UIElement(
                                element_type="button",
                                coordinates=(center_x, center_y),
                                confidence=confidence,
                                description=f"Button candidate ({w}x{h})",
                                bounds=(x, y, x+w, y+h),
                                detection_method="cv_button_detection"
                            ))
        
        except Exception as e:
            logger.warning(f"Button detection failed: {e}")
        
        return elements
    
    def _detect_clickable_areas(self, img_gray, img_array) -> List[UIElement]:
        """Detect other clickable areas like links, tabs, menu items"""
        elements = []
        
        try:
            # Look for text-like regions that might be clickable
            # These often have distinct colors or are underlined
            
            # Method: Look for horizontal lines (underlines) near text
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
            detect_horizontal = cv2.morphologyEx(img_gray, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
            
            contours, _ = cv2.findContours(detect_horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if 50 < area < 5000:
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Look for text above the line
                    if y > 20:
                        text_area_y = max(0, y - 20)
                        text_roi = img_gray[text_area_y:y, x:x+w]
                        
                        if np.mean(text_roi) < 200:  # Dark text area
                            center_x = x + w // 2
                            center_y = text_area_y + 10
                            
                            elements.append(UIElement(
                                element_type="link",
                                coordinates=(center_x, center_y),
                                confidence=0.5,
                                description=f"Potential link with underline",
                                bounds=(x, text_area_y, x+w, y),
                                detection_method="cv_link_detection"
                            ))
        
        except Exception as e:
            logger.warning(f"Clickable area detection failed: {e}")
        
        return elements
    
    def _detect_app_specific_elements(self, img_gray, img_array, active_app: str, intent_analysis: Dict) -> List[UIElement]:
        """Detect elements specific to the current application"""
        elements = []
        
        try:
            # Safari-specific detection
            if 'safari' in active_app:
                # Look for address bar (top area, light colored)
                if any('address' in keyword for keyword in intent_analysis["search_keywords"]):
                    top_region = img_gray[0:100, :]
                    # Find light horizontal bars
                    light_areas = np.where(top_region > 200)
                    if len(light_areas[0]) > 0:
                        y_coords = light_areas[0]
                        x_coords = light_areas[1]
                        
                        if len(x_coords) > 100:  # Sufficient width
                            center_x = self.screen_width // 2
                            center_y = int(np.mean(y_coords))
                            
                            elements.append(UIElement(
                                element_type="address_bar",
                                coordinates=(center_x, center_y),
                                confidence=0.8,
                                description="Safari address bar",
                                bounds=(0, center_y-15, self.screen_width, center_y+15),
                                detection_method="app_specific_safari"
                            ))
            
            # TextEdit-specific detection
            elif 'textedit' in active_app:
                # Look for large white areas (text editing area)
                white_mask = cv2.threshold(img_gray, 240, 255, cv2.THRESH_BINARY)[1]
                contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area > 10000:  # Large white area
                        x, y, w, h = cv2.boundingRect(contour)
                        center_x = x + w // 2
                        center_y = y + h // 2
                        
                        elements.append(UIElement(
                            element_type="text_area",
                            coordinates=(center_x, center_y),
                            confidence=0.9,
                            description="TextEdit document area",
                            bounds=(x, y, x+w, y+h),
                            detection_method="app_specific_textedit"
                        ))
        
        except Exception as e:
            logger.warning(f"App-specific detection failed: {e}")
        
        return elements
    
    def get_intelligent_coordinates(self, query: str, step_type: str = "unknown") -> Tuple[int, int]:
        """Main method: Get intelligent coordinates for any query"""
        
        logger.info(f"🧠 Intelligent coordinate detection for: '{query}'")
        
        # Step 1: Analyze intent
        intent_analysis = self.analyze_intent_and_ui_needs(query, step_type)
        
        # Step 2: Detect UI elements using computer vision
        detected_elements = self.detect_ui_elements_with_cv(intent_analysis)
        
        # Step 3: Select best element based on intent and confidence
        if detected_elements:
            # Filter elements by target types
            target_types = intent_analysis["target_element_types"]
            relevant_elements = [e for e in detected_elements if e.element_type in target_types]
            
            if not relevant_elements:
                relevant_elements = detected_elements  # Fall back to all detected elements
            
            # Select highest confidence element
            best_element = relevant_elements[0]
            logger.info(f"🎯 Selected: {best_element.description} at {best_element.coordinates} (confidence: {best_element.confidence:.2f})")
            
            # Create verification
            self._create_intelligent_verification(best_element, query, intent_analysis)
            
            return best_element.coordinates
        
        # Step 4: Fallback to smart positioning
        else:
            logger.warning("🤔 No elements detected, using intelligent fallback")
            fallback_coords = self._get_intelligent_fallback(query, intent_analysis)
            
            # Create fallback verification
            fallback_element = UIElement(
                element_type="fallback",
                coordinates=fallback_coords,
                confidence=0.3,
                description="Intelligent fallback position",
                bounds=(0, 0, 0, 0),
                detection_method="intelligent_fallback"
            )
            self._create_intelligent_verification(fallback_element, query, intent_analysis)
            
            return fallback_coords
    
    def _get_intelligent_fallback(self, query: str, intent_analysis: Dict) -> Tuple[int, int]:
        """Get intelligent fallback coordinates based on common UI patterns"""
        
        active_app = self.get_active_application().lower()
        
        # Text input fallbacks
        if any(t in intent_analysis["target_element_types"] for t in ["text_input", "search_box"]):
            if 'safari' in active_app:
                # Safari search/address area
                return (self.screen_width // 2, self.screen_height // 4)
            else:
                # General text input area
                return (self.screen_width // 2, self.screen_height // 3)
        
        # Button fallbacks
        elif "button" in intent_analysis["target_element_types"]:
            # Buttons often in lower or right areas
            return (int(self.screen_width * 0.6), int(self.screen_height * 0.7))
        
        # Navigation fallbacks
        elif any(t in intent_analysis["target_element_types"] for t in ["address_bar", "navigation"]):
            # Top area for navigation
            return (self.screen_width // 2, int(self.screen_height * 0.1))
        
        # Default center
        else:
            return (self.screen_width // 2, self.screen_height // 2)
    
    def _create_intelligent_verification(self, element: UIElement, query: str, intent_analysis: Dict) -> str:
        """Create detailed verification screenshot"""
        
        screenshot = pyautogui.screenshot()
        draw = ImageDraw.Draw(screenshot)
        
        x, y = element.coordinates
        
        # Color based on confidence and detection method
        if element.confidence > 0.8:
            color = 'lime'
        elif element.confidence > 0.6:
            color = 'yellow'
        elif element.confidence > 0.4:
            color = 'orange'
        else:
            color = 'red'
        
        # Draw target indicators
        crosshair_size = 35
        line_width = 6
        
        # White outline for visibility
        for offset in [(3, 3), (-3, -3), (3, -3), (-3, 3)]:
            draw.line([
                (x - crosshair_size + offset[0], y + offset[1]),
                (x + crosshair_size + offset[0], y + offset[1])
            ], fill='white', width=line_width + 2)
            
            draw.line([
                (x + offset[0], y - crosshair_size + offset[1]),
                (x + offset[0], y + crosshair_size + offset[1])
            ], fill='white', width=line_width + 2)
        
        # Main crosshairs
        draw.line([
            (x - crosshair_size, y),
            (x + crosshair_size, y)
        ], fill=color, width=line_width)
        
        draw.line([
            (x, y - crosshair_size),
            (x, y + crosshair_size)
        ], fill=color, width=line_width)
        
        # Draw element bounds if available
        if element.bounds != (0, 0, 0, 0):
            x1, y1, x2, y2 = element.bounds
            draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
        
        # Add detailed information
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 14)
        except:
            font = ImageFont.load_default()
        
        info_text = f"🧠 INTELLIGENT DETECTION\nQuery: {query[:30]}...\nTarget: {element.element_type}\nDescription: {element.description}\nMethod: {element.detection_method}\nCoords: {element.coordinates}\nConfidence: {element.confidence:.2f}\nApp: {self.get_active_application()}"
        
        # Position text intelligently
        text_x = max(10, x - 250) if x > self.screen_width // 2 else x + 50
        text_y = max(10, y - 120) if y > 150 else y + 50
        
        # Ensure text doesn't go off screen
        text_x = min(text_x, self.screen_width - 300)
        text_y = min(text_y, self.screen_height - 200)
        
        # Background for text
        text_lines = info_text.split('\n')
        max_width = max(draw.textlength(line, font=font) for line in text_lines)
        text_height = len(text_lines) * 18
        
        draw.rectangle([
            (text_x - 10, text_y - 10),
            (text_x + max_width + 20, text_y + text_height + 20)
        ], fill='black', outline='white', width=2)
        
        for i, line in enumerate(text_lines):
            draw.text((text_x, text_y + i * 18), line, fill='white', font=font)
        
        # Save with detailed filename
        timestamp = int(time.time())
        filename = f"intelligent_detection_{element.element_type}_{timestamp}.png"
        screenshot.save(filename)
        logger.info(f"📸 Intelligent detection verification: {filename}")
        
        return filename

# Create singleton instance
intelligent_ui_detector = IntelligentUIDetector()

if __name__ == "__main__":
    detector = IntelligentUIDetector()
    
    # Test with various queries
    test_queries = [
        "Search for python tutorials in Google",
        "Type my name in the text editor",
        "Click the save button",
        "Navigate to github.com",
        "Fill in the username field",
        "Press the submit button"
    ]
    
    print("=== Intelligent UI Detection Tests ===")
    
    for query in test_queries:
        print(f"\n🧪 Testing: {query}")
        coords = detector.get_intelligent_coordinates(query)
        print(f"   Coordinates: {coords}")
        time.sleep(1)  # Brief pause between tests