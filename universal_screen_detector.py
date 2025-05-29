#!/usr/bin/env python3
"""
Universal Screen Detector - Dynamically identifies UI elements for any automation step
"""

import pyautogui
import subprocess
import time
import json
import logging
import cv2
import numpy as np
import requests
import base64
import io
from typing import Tuple, Dict, Optional, List, Any
from PIL import Image, ImageDraw, ImageFont
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class DetectedElement:
    """A UI element detected on screen"""
    element_type: str
    coordinates: Tuple[int, int]
    confidence: float
    description: str
    bounds: Tuple[int, int, int, int]
    detection_method: str

class UniversalScreenDetector:
    """Universal detector that can find any UI element for any automation step"""
    
    def __init__(self):
        self.screen_width, self.screen_height = pyautogui.size()
        self.ollama_url = "http://localhost:11434/api/generate"
        logger.info(f"Universal screen detector initialized for {self.screen_width}x{self.screen_height}")
    
    def analyze_step_requirements(self, step_description: str) -> Dict[str, Any]:
        """Analyze what UI element is needed for a specific automation step"""
        
        step_lower = step_description.lower()
        requirements = {
            "action_type": "unknown",
            "target_element": "unknown",
            "element_characteristics": [],
            "search_hints": [],
            "interaction_goal": ""
        }
        
        # Determine action type
        if any(word in step_lower for word in ['click', 'press', 'tap', 'select']):
            requirements["action_type"] = "click"
            if 'search' in step_lower or 'box' in step_lower:
                requirements["target_element"] = "search_input"
                requirements["element_characteristics"] = ["rectangular", "input_field", "light_background"]
            elif 'button' in step_lower:
                requirements["target_element"] = "button"
                requirements["element_characteristics"] = ["clickable", "rounded", "distinct_color"]
            elif 'link' in step_lower:
                requirements["target_element"] = "link"
                requirements["element_characteristics"] = ["text", "underlined", "colored"]
            else:
                requirements["target_element"] = "clickable_element"
                requirements["element_characteristics"] = ["interactive"]
        
        elif any(word in step_lower for word in ['type', 'enter', 'input', 'write', 'fill']):
            requirements["action_type"] = "type"
            requirements["target_element"] = "text_input"
            requirements["element_characteristics"] = ["input_field", "text_area", "editable", "light_background"]
        
        elif any(word in step_lower for word in ['search']):
            requirements["action_type"] = "search"
            requirements["target_element"] = "search_input"
            requirements["element_characteristics"] = ["search_box", "input_field", "rectangular", "light_background"]
        
        elif any(word in step_lower for word in ['navigate', 'go to', 'visit']):
            requirements["action_type"] = "navigate"
            requirements["target_element"] = "address_bar"
            requirements["element_characteristics"] = ["url_bar", "address_field", "top_area"]
        
        # Extract search hints from step description
        for word in step_lower.split():
            if len(word) > 3:
                requirements["search_hints"].append(word)
        
        requirements["interaction_goal"] = step_description
        
        logger.info(f"🎯 Step requirements: {requirements}")
        return requirements
    
    def take_screen_analysis(self) -> Dict[str, Any]:
        """Take a screenshot and perform basic analysis"""
        
        screenshot = pyautogui.screenshot()
        img_array = np.array(screenshot)
        img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        analysis = {
            "screenshot": screenshot,
            "gray_image": img_gray,
            "dimensions": (self.screen_width, self.screen_height),
            "active_app": self.get_active_application(),
            "timestamp": time.time()
        }
        
        return analysis
    
    def get_active_application(self) -> str:
        """Get currently active application"""
        try:
            result = subprocess.run([
                'osascript', '-e', 
                'tell application "System Events" to get name of first application process whose frontmost is true'
            ], capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except:
            return "Unknown"
    
    def detect_input_fields(self, screen_analysis: Dict, requirements: Dict) -> List[DetectedElement]:
        """Detect input fields and text areas"""
        
        elements = []
        img_gray = screen_analysis["gray_image"]
        
        try:
            # Method 1: Look for rectangular input fields with light backgrounds
            light_threshold = 200
            light_mask = cv2.threshold(img_gray, light_threshold, 255, cv2.THRESH_BINARY)[1]
            
            # Find contours of light areas
            contours, _ = cv2.findContours(light_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if 800 < area < 50000:
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    
                    if 2.0 < aspect_ratio < 20.0 and 25 < h < 80:
                        center_x = x + w // 2
                        center_y = y + h // 2
                        
                        if (50 < center_x < self.screen_width - 50 and 
                            50 < center_y < self.screen_height - 50):
                            
                            confidence = self._calculate_input_confidence(img_gray, x, y, w, h, requirements)
                            
                            if confidence > 0.3:
                                elements.append(DetectedElement(
                                    element_type="input_field",
                                    coordinates=(center_x, center_y),
                                    confidence=confidence,
                                    description=f"Light input field ({w}x{h})",
                                    bounds=(x, y, x+w, y+h),
                                    detection_method="cv_light_area_detection"
                                ))
            
            # Method 2: Look for rectangular input fields with dark backgrounds
            dark_threshold = 50
            dark_mask = cv2.threshold(img_gray, dark_threshold, 255, cv2.THRESH_BINARY_INV)[1]
            
            # Find contours of dark areas
            contours, _ = cv2.findContours(dark_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if 800 < area < 50000:
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    
                    if 2.0 < aspect_ratio < 20.0 and 25 < h < 80:
                        center_x = x + w // 2
                        center_y = y + h // 2
                        
                        if (50 < center_x < self.screen_width - 50 and 
                            50 < center_y < self.screen_height - 50):
                            
                            confidence = self._calculate_input_confidence(img_gray, x, y, w, h, requirements)
                            
                            if confidence > 0.3:
                                elements.append(DetectedElement(
                                    element_type="input_field",
                                    coordinates=(center_x, center_y),
                                    confidence=confidence,
                                    description=f"Dark input field ({w}x{h})",
                                    bounds=(x, y, x+w, y+h),
                                    detection_method="cv_dark_area_detection"
                                ))
            
            # Method 3: Edge-based detection for outlined input fields
            edges = cv2.Canny(img_gray, 30, 100)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if 500 < area < 40000:
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    
                    if 2.0 < aspect_ratio < 20.0 and 20 < h < 80:
                        center_x = x + w // 2
                        center_y = y + h // 2
                        
                        if (50 < center_x < self.screen_width - 50 and 
                            50 < center_y < self.screen_height - 50):
                            
                            confidence = self._calculate_input_confidence(img_gray, x, y, w, h, requirements)
                            
                            if confidence > 0.25:
                                elements.append(DetectedElement(
                                    element_type="input_field",
                                    coordinates=(center_x, center_y),
                                    confidence=confidence,
                                    description=f"Outlined input ({w}x{h})",
                                    bounds=(x, y, x+w, y+h),
                                    detection_method="cv_edge_detection"
                                ))
            
            # Method 4: Template-based detection for common patterns
            # Look for rectangular regions with specific characteristics
            height, width = img_gray.shape
            
            # Use morphological operations to find rectangular structures
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
            morph = cv2.morphologyEx(img_gray, cv2.MORPH_GRADIENT, kernel)
            
            # Threshold the morphological gradient
            _, thresh = cv2.threshold(morph, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if 1000 < area < 50000:
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    
                    if 3.0 < aspect_ratio < 25.0 and 25 < h < 80:
                        center_x = x + w // 2
                        center_y = y + h // 2
                        
                        if (50 < center_x < self.screen_width - 50 and 
                            50 < center_y < self.screen_height - 50):
                            
                            confidence = self._calculate_input_confidence(img_gray, x, y, w, h, requirements)
                            
                            if confidence > 0.2:
                                elements.append(DetectedElement(
                                    element_type="input_field",
                                    coordinates=(center_x, center_y),
                                    confidence=confidence,
                                    description=f"Morphological input ({w}x{h})",
                                    bounds=(x, y, x+w, y+h),
                                    detection_method="cv_morphological_detection"
                                ))
        
        except Exception as e:
            logger.warning(f"Input field detection failed: {e}")
        
        return elements
    
    def detect_buttons(self, screen_analysis: Dict, requirements: Dict) -> List[DetectedElement]:
        """Detect buttons and clickable elements"""
        
        elements = []
        img_gray = screen_analysis["gray_image"]
        
        try:
            # Look for button-like shapes
            edges = cv2.Canny(img_gray, 30, 100)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if 300 < area < 15000:  # Button size range
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    
                    # Buttons can be various shapes but typically not too extreme
                    if 0.3 < aspect_ratio < 8.0 and 15 < h < 100:
                        center_x = x + w // 2
                        center_y = y + h // 2
                        
                        if (20 < center_x < self.screen_width - 20 and 
                            20 < center_y < self.screen_height - 20):
                            
                            confidence = self._calculate_button_confidence(img_gray, x, y, w, h, requirements)
                            
                            if confidence > 0.3:
                                elements.append(DetectedElement(
                                    element_type="button",
                                    coordinates=(center_x, center_y),
                                    confidence=confidence,
                                    description=f"Button ({w}x{h})",
                                    bounds=(x, y, x+w, y+h),
                                    detection_method="cv_button_detection"
                                ))
        
        except Exception as e:
            logger.warning(f"Button detection failed: {e}")
        
        return elements
    
    def _calculate_input_confidence(self, img_gray, x, y, w, h, requirements) -> float:
        """Calculate confidence score for input field detection"""
        
        confidence = 0.4  # Base confidence
        
        # Check if it's in the right area for input fields
        screen_third = self.screen_height // 3
        if y < screen_third * 2:  # Upper 2/3 of screen
            confidence += 0.15
        
        # Check aspect ratio - good input fields are wide
        aspect_ratio = w / h
        if 4.0 < aspect_ratio < 15.0:
            confidence += 0.25
        elif 2.5 < aspect_ratio < 20.0:
            confidence += 0.15
        
        # Check size - reasonable input field size
        if 300 < w < 700 and 30 < h < 70:
            confidence += 0.25
        elif 200 < w < 900 and 25 < h < 80:
            confidence += 0.15
        
        # Check brightness characteristics (both light and dark input fields)
        roi = img_gray[y:y+h, x:x+w]
        avg_brightness = np.mean(roi)
        
        # Light input fields
        if avg_brightness > 180:
            confidence += 0.2
        # Dark input fields
        elif avg_brightness < 80:
            confidence += 0.2
        # Medium brightness (potential input fields)
        elif 80 <= avg_brightness <= 180:
            confidence += 0.1
        
        # Check for uniform color (input fields typically have consistent background)
        brightness_std = np.std(roi)
        if brightness_std < 15:
            confidence += 0.15
        elif brightness_std < 30:
            confidence += 0.1
        
        # Bonus for search-related requirements
        target_element = requirements.get("target_element", "")
        if target_element in ["search_input", "text_input"]:
            if 400 < w < 600 and 35 < h < 55:  # Typical search box dimensions
                confidence += 0.2
        
        # Position bonus for center-ish locations (where search boxes often are)
        center_x = x + w // 2
        screen_center_x = self.screen_width // 2
        if abs(center_x - screen_center_x) < self.screen_width * 0.3:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _calculate_button_confidence(self, img_gray, x, y, w, h, requirements) -> float:
        """Calculate confidence score for button detection"""
        
        confidence = 0.4  # Base confidence
        
        # Buttons can be anywhere on screen
        if y > self.screen_height // 4:  # Not in very top area
            confidence += 0.1
        
        # Check size - reasonable button size
        if 50 < w < 300 and 20 < h < 80:
            confidence += 0.2
        
        # Check aspect ratio
        aspect_ratio = w / h
        if 1.0 < aspect_ratio < 6.0:
            confidence += 0.2
        
        # Buttons often have consistent coloring
        roi = img_gray[y:y+h, x:x+w]
        brightness_std = np.std(roi)
        if brightness_std < 25:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def select_best_element(self, elements: List[DetectedElement], requirements: Dict) -> Optional[DetectedElement]:
        """Select the best element based on requirements and confidence"""
        
        if not elements:
            return None
        
        # Filter by target element type if specified
        target_type = requirements.get("target_element", "")
        if target_type in ["search_input", "text_input"]:
            input_elements = [e for e in elements if e.element_type == "input_field"]
            if input_elements:
                elements = input_elements
        
        elif target_type == "button":
            button_elements = [e for e in elements if e.element_type == "button"]
            if button_elements:
                elements = button_elements
        
        # Sort by confidence and select the best
        elements.sort(key=lambda e: e.confidence, reverse=True)
        best_element = elements[0]
        
        logger.info(f"🎯 Selected best element: {best_element.description} at {best_element.coordinates} (confidence: {best_element.confidence:.2f})")
        
        return best_element
    
    def get_coordinates_for_step(self, step_description: str) -> Tuple[int, int]:
        """Main method: Get coordinates for any automation step"""
        
        logger.info(f"🔍 Universal detection for step: '{step_description}'")
        
        # Step 1: Analyze what this step requires
        requirements = self.analyze_step_requirements(step_description)
        
        # Step 2: Take and analyze current screen
        screen_analysis = self.take_screen_analysis()
        
        # Step 3: Detect relevant UI elements
        detected_elements = []
        
        if requirements["target_element"] in ["search_input", "text_input", "input_field"]:
            input_elements = self.detect_input_fields(screen_analysis, requirements)
            detected_elements.extend(input_elements)
        
        if requirements["target_element"] == "button":
            button_elements = self.detect_buttons(screen_analysis, requirements)
            detected_elements.extend(button_elements)
        
        # If no specific target, detect all types
        if requirements["target_element"] == "unknown":
            input_elements = self.detect_input_fields(screen_analysis, requirements)
            button_elements = self.detect_buttons(screen_analysis, requirements)
            detected_elements.extend(input_elements)
            detected_elements.extend(button_elements)
        
        # Step 4: Select the best element
        best_element = self.select_best_element(detected_elements, requirements)
        
        if best_element:
            # Create verification screenshot
            self._create_universal_verification(best_element, step_description, screen_analysis, requirements)
            return best_element.coordinates
        
        else:
            # Intelligent fallback based on step requirements
            logger.warning("🤔 No elements detected, using intelligent fallback")
            fallback_coords = self._get_intelligent_fallback(requirements)
            
            # Create fallback verification
            fallback_element = DetectedElement(
                element_type="fallback",
                coordinates=fallback_coords,
                confidence=0.3,
                description="Intelligent fallback",
                bounds=(0, 0, 0, 0),
                detection_method="intelligent_fallback"
            )
            self._create_universal_verification(fallback_element, step_description, screen_analysis, requirements)
            
            return fallback_coords
    
    def _get_intelligent_fallback(self, requirements: Dict) -> Tuple[int, int]:
        """Get intelligent fallback coordinates based on step requirements"""
        
        target_element = requirements.get("target_element", "")
        action_type = requirements.get("action_type", "")
        
        if target_element in ["search_input", "text_input"]:
            # Input fields typically in upper-center area
            return (self.screen_width // 2, self.screen_height // 3)
        
        elif target_element == "button":
            # Buttons often in lower-right or center areas
            return (int(self.screen_width * 0.6), int(self.screen_height * 0.7))
        
        elif target_element == "address_bar":
            # Address bars at the top
            return (self.screen_width // 2, 80)
        
        else:
            # Generic center
            return (self.screen_width // 2, self.screen_height // 2)
    
    def _create_universal_verification(self, element: DetectedElement, step_description: str, 
                                     screen_analysis: Dict, requirements: Dict) -> str:
        """Create detailed verification screenshot"""
        
        screenshot = screen_analysis["screenshot"]
        draw = ImageDraw.Draw(screenshot)
        
        x, y = element.coordinates
        
        # Color based on confidence
        if element.confidence > 0.8:
            color = 'lime'
        elif element.confidence > 0.6:
            color = 'yellow'
        elif element.confidence > 0.4:
            color = 'orange'
        else:
            color = 'red'
        
        # Draw targeting indicators
        crosshair_size = 30
        line_width = 5
        
        # White outline for visibility
        for offset in [(3, 3), (-3, -3), (3, -3), (-3, 3)]:
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
        
        # Draw element bounds if available
        if element.bounds != (0, 0, 0, 0):
            x1, y1, x2, y2 = element.bounds
            draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
        
        # Add comprehensive information
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 12)
        except:
            font = ImageFont.load_default()
        
        info_text = f"🔍 UNIVERSAL DETECTION\nStep: {step_description[:25]}...\nTarget: {element.element_type}\nMethod: {element.detection_method}\nCoords: {element.coordinates}\nConfidence: {element.confidence:.2f}\nApp: {screen_analysis['active_app']}\nAction: {requirements['action_type']}"
        
        # Position text intelligently
        text_x = max(10, x - 200) if x > self.screen_width // 2 else x + 50
        text_y = max(10, y - 100) if y > 120 else y + 50
        
        # Ensure text stays on screen
        text_x = min(text_x, self.screen_width - 250)
        text_y = min(text_y, self.screen_height - 150)
        
        # Background for text
        text_lines = info_text.split('\n')
        max_width = max(draw.textlength(line, font=font) for line in text_lines)
        text_height = len(text_lines) * 16
        
        draw.rectangle([
            (text_x - 8, text_y - 8),
            (text_x + max_width + 16, text_y + text_height + 16)
        ], fill='black', outline='white', width=2)
        
        for i, line in enumerate(text_lines):
            draw.text((text_x, text_y + i * 16), line, fill='white', font=font)
        
        # Save with descriptive filename
        timestamp = int(time.time())
        filename = f"universal_detection_{element.element_type}_{timestamp}.png"
        screenshot.save(filename)
        logger.info(f"📸 Universal detection verification: {filename}")
        
        return filename

# Create singleton instance
universal_screen_detector = UniversalScreenDetector()

if __name__ == "__main__":
    detector = UniversalScreenDetector()
    
    # Test with various automation steps
    test_steps = [
        "Click on YouTube search box",
        "Type 'Omer Adam' in search field",
        "Press the search button",
        "Fill in username field",
        "Click submit button",
        "Enter password in login form"
    ]
    
    print("=== Universal Screen Detection Tests ===")
    
    for step in test_steps:
        print(f"\n🔍 Testing step: {step}")
        coords = detector.get_coordinates_for_step(step)
        print(f"   Detected coordinates: {coords}")
        time.sleep(1)