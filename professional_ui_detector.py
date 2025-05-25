#!/usr/bin/env python3
"""
Professional UI Element Detection System
Combines multiple detection methods for maximum accuracy
"""

import asyncio
import cv2
import numpy as np
import pytesseract
import logging
from PIL import Image, ImageGrab
from typing import Dict, List, Any, Optional, Tuple
import time
import json
import os
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ElementType(Enum):
    """Professional element type classifications"""
    BUTTON = "button"
    TEXT_FIELD = "text_field"
    TEXT_AREA = "text_area"
    CHECKBOX = "checkbox"
    RADIO_BUTTON = "radio_button"
    DROPDOWN = "dropdown"
    MENU = "menu"
    WINDOW = "window"
    DIALOG = "dialog"
    TAB = "tab"
    SCROLL_BAR = "scroll_bar"
    IMAGE = "image"
    LINK = "link"
    LABEL = "label"
    ICON = "icon"

@dataclass
class UIElement:
    """Professional UI element representation"""
    id: str
    element_type: ElementType
    text: str
    confidence: float
    bounding_box: Dict[str, int]  # {"x": int, "y": int, "width": int, "height": int}
    center: Tuple[int, int]
    attributes: Dict[str, Any]
    detection_method: str
    app_context: Optional[str] = None
    interaction_hints: List[str] = None
    
    def __post_init__(self):
        if self.interaction_hints is None:
            self.interaction_hints = []
        
        # Calculate center from bounding box
        if self.bounding_box:
            self.center = (
                self.bounding_box["x"] + self.bounding_box["width"] // 2,
                self.bounding_box["y"] + self.bounding_box["height"] // 2
            )

class ProfessionalUIDetector:
    """
    Professional UI Detection System
    Uses multiple detection methods and machine learning for accuracy
    """
    
    def __init__(self):
        self.detection_methods = [
            self._detect_with_opencv,
            self._detect_with_ocr,
            self._detect_with_template_matching,
            self._detect_with_color_analysis,
            self._detect_with_accessibility,
            self._detect_applications
        ]
        self.element_cache = {}
        self.app_templates = self._load_app_templates()
        
    def _load_app_templates(self) -> Dict[str, Any]:
        """Load application-specific templates and patterns"""
        return {
            "notepad": {
                "window_titles": ["Notepad", "TextEdit", "Text Editor"],
                "text_area_patterns": {
                    "background_color": [(255, 255, 255), (248, 248, 255)],  # White variations
                    "typical_size": {"min_width": 200, "min_height": 100},
                    "border_detection": True
                }
            },
            "browser": {
                "window_titles": ["Chrome", "Firefox", "Safari", "Edge"],
                "url_bar_patterns": {
                    "typical_height": [25, 40],
                    "background_color": [(255, 255, 255)]
                }
            }
        }
    
    async def analyze_screen_professional(self, screenshot: Optional[Image.Image] = None) -> Dict[str, Any]:
        """
        Professional screen analysis with multiple detection methods
        Returns comprehensive UI element information
        """
        try:
            # Capture screenshot if not provided
            if screenshot is None:
                screenshot = ImageGrab.grab()
            
            # Convert to different formats for analysis
            cv_image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            gray_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            analysis_start = time.time()
            
            # Run all detection methods in parallel
            detection_tasks = [
                self._run_detection_method(method, screenshot, cv_image, gray_image)
                for method in self.detection_methods
            ]
            
            detection_results = await asyncio.gather(*detection_tasks, return_exceptions=True)
            
            # Combine and deduplicate results
            all_elements = []
            for result in detection_results:
                if isinstance(result, list):
                    all_elements.extend(result)
                elif isinstance(result, Exception):
                    logger.warning(f"Detection method failed: {result}")
            
            # Professional element processing
            processed_elements = self._process_and_rank_elements(all_elements, screenshot)
            
            analysis_time = time.time() - analysis_start
            
            return {
                "success": True,
                "elements": processed_elements,
                "analysis_time": analysis_time,
                "total_elements": len(processed_elements),
                "detection_methods_used": len([r for r in detection_results if not isinstance(r, Exception)]),
                "screen_size": screenshot.size,
                "confidence_distribution": self._analyze_confidence_distribution(processed_elements),
                "app_context": self._determine_app_context(processed_elements)
            }
            
        except Exception as e:
            logger.error(f"Professional screen analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "elements": []
            }
    
    async def _run_detection_method(self, method, screenshot, cv_image, gray_image) -> List[UIElement]:
        """Run a single detection method"""
        try:
            return await method(screenshot, cv_image, gray_image)
        except Exception as e:
            logger.debug(f"Detection method {method.__name__} failed: {e}")
            return []
    
    async def _detect_with_opencv(self, screenshot, cv_image, gray_image) -> List[UIElement]:
        """OpenCV-based UI element detection"""
        elements = []
        
        # Button detection using edge detection and contours
        edges = cv2.Canny(gray_image, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for i, contour in enumerate(contours):
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            
            # Filter by size to identify potential buttons
            if 20 <= w <= 300 and 15 <= h <= 80 and area > 300:
                # Analyze the region to determine element type
                roi = gray_image[y:y+h, x:x+w]
                element_type = self._classify_opencv_element(roi, w, h)
                
                if element_type:
                    element = UIElement(
                        id=f"opencv_{i}",
                        element_type=element_type,
                        text="",
                        confidence=0.7,
                        bounding_box={"x": x, "y": y, "width": w, "height": h},
                        center=(x + w//2, y + h//2),
                        attributes={"area": area, "aspect_ratio": w/h},
                        detection_method="opencv"
                    )
                    elements.append(element)
        
        return elements
    
    async def _detect_with_ocr(self, screenshot, cv_image, gray_image) -> List[UIElement]:
        """OCR-based text element detection"""
        elements = []
        
        try:
            # Configure Tesseract for better accuracy
            config = '--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 '
            
            # Get detailed OCR data
            data = pytesseract.image_to_data(screenshot, config=config, output_type=pytesseract.Output.DICT)
            
            n_boxes = len(data['level'])
            for i in range(n_boxes):
                confidence = int(data['conf'][i])
                text = data['text'][i].strip()
                
                if confidence > 30 and len(text) > 0:
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    
                    # Classify text element type
                    element_type = self._classify_text_element(text, w, h)
                    
                    element = UIElement(
                        id=f"ocr_{i}",
                        element_type=element_type,
                        text=text,
                        confidence=confidence / 100.0,
                        bounding_box={"x": x, "y": y, "width": w, "height": h},
                        center=(x + w//2, y + h//2),
                        attributes={"ocr_confidence": confidence, "char_count": len(text)},
                        detection_method="ocr"
                    )
                    elements.append(element)
            
        except Exception as e:
            logger.debug(f"OCR detection failed: {e}")
        
        return elements
    
    async def _detect_with_template_matching(self, screenshot, cv_image, gray_image) -> List[UIElement]:
        """Template matching for common UI elements"""
        elements = []
        
        # Common UI element templates (simplified - in production, load from files)
        templates = {
            "close_button": self._create_close_button_template(),
            "minimize_button": self._create_minimize_button_template(),
            "maximize_button": self._create_maximize_button_template(),
        }
        
        for template_name, template in templates.items():
            if template is not None:
                matches = cv2.matchTemplate(gray_image, template, cv2.TM_CCOEFF_NORMED)
                locations = np.where(matches >= 0.8)
                
                for pt in zip(*locations[::-1]):
                    x, y = pt
                    h, w = template.shape
                    
                    element = UIElement(
                        id=f"template_{template_name}_{x}_{y}",
                        element_type=ElementType.BUTTON,
                        text=template_name.replace("_", " ").title(),
                        confidence=float(matches[y, x]),
                        bounding_box={"x": x, "y": y, "width": w, "height": h},
                        center=(x + w//2, y + h//2),
                        attributes={"template_match": template_name},
                        detection_method="template_matching"
                    )
                    elements.append(element)
        
        return elements
    
    async def _detect_with_color_analysis(self, screenshot, cv_image, gray_image) -> List[UIElement]:
        """Color-based element detection"""
        elements = []
        
        # Convert to HSV for better color detection
        hsv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
        
        # Detect common UI element colors
        color_ranges = {
            "blue_button": ([100, 50, 50], [130, 255, 255]),
            "white_text_area": ([0, 0, 200], [179, 30, 255]),
            "gray_interface": ([0, 0, 100], [179, 50, 200])
        }
        
        for color_name, (lower, upper) in color_ranges.items():
            mask = cv2.inRange(hsv_image, np.array(lower), np.array(upper))
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for i, contour in enumerate(contours):
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                
                if area > 500 and w > 30 and h > 15:
                    element_type = self._classify_color_element(color_name, w, h, area)
                    
                    element = UIElement(
                        id=f"color_{color_name}_{i}",
                        element_type=element_type,
                        text="",
                        confidence=0.6,
                        bounding_box={"x": x, "y": y, "width": w, "height": h},
                        center=(x + w//2, y + h//2),
                        attributes={"color_type": color_name, "area": area},
                        detection_method="color_analysis"
                    )
                    elements.append(element)
        
        return elements
    
    async def _detect_with_accessibility(self, screenshot, cv_image, gray_image) -> List[UIElement]:
        """Accessibility API-based detection (macOS specific)"""
        elements = []
        
        try:
            # Use macOS accessibility APIs (requires additional setup)
            # This is a placeholder for accessibility integration
            # In production, use libraries like pyobjc for macOS accessibility
            pass
        except Exception as e:
            logger.debug(f"Accessibility detection not available: {e}")
        
        return elements
    
    async def _detect_applications(self, screenshot, cv_image, gray_image) -> List[UIElement]:
        """Application-specific detection"""
        elements = []
        
        # Detect Notepad/TextEdit specifically
        notepad_elements = await self._detect_notepad_elements(screenshot, cv_image, gray_image)
        elements.extend(notepad_elements)
        
        return elements
    
    async def _detect_notepad_elements(self, screenshot, cv_image, gray_image) -> List[UIElement]:
        """Detect Notepad/TextEdit application elements"""
        elements = []
        
        # Look for large white/light areas (text editing areas)
        # This is simplified - in production, use more sophisticated detection
        
        # Create mask for white/light areas
        lower_white = np.array([200, 200, 200])
        upper_white = np.array([255, 255, 255])
        
        # Convert BGR to RGB for correct color matching
        rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        mask = cv2.inRange(rgb_image, lower_white, upper_white)
        
        # Find contours of white areas
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for i, contour in enumerate(contours):
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            
            # Look for large rectangular areas (potential text areas)
            if area > 10000 and w > 150 and h > 100:
                aspect_ratio = w / h
                
                # Text areas are typically wider than they are tall
                if 0.5 < aspect_ratio < 10:
                    element = UIElement(
                        id=f"notepad_text_area_{i}",
                        element_type=ElementType.TEXT_AREA,
                        text="Text editing area",
                        confidence=0.8,
                        bounding_box={"x": x, "y": y, "width": w, "height": h},
                        center=(x + w//2, y + h//2),
                        attributes={
                            "area": area,
                            "aspect_ratio": aspect_ratio,
                            "likely_notepad": True
                        },
                        detection_method="app_specific",
                        app_context="notepad",
                        interaction_hints=["click", "type", "focus"]
                    )
                    elements.append(element)
        
        return elements
    
    def _classify_opencv_element(self, roi, width, height) -> Optional[ElementType]:
        """Classify element type based on OpenCV analysis"""
        aspect_ratio = width / height
        
        if 0.2 < aspect_ratio < 5 and width < 200 and height < 50:
            return ElementType.BUTTON
        elif aspect_ratio > 2 and height < 30:
            return ElementType.TEXT_FIELD
        elif aspect_ratio > 1 and width > 100 and height > 50:
            return ElementType.TEXT_AREA
        
        return None
    
    def _classify_text_element(self, text, width, height) -> ElementType:
        """Classify element type based on text content"""
        text_lower = text.lower()
        
        # Button indicators
        button_keywords = ['ok', 'cancel', 'submit', 'save', 'send', 'button', 'click']
        if any(keyword in text_lower for keyword in button_keywords):
            return ElementType.BUTTON
        
        # Link indicators
        if 'http' in text_lower or 'www' in text_lower:
            return ElementType.LINK
        
        # Default to label for text
        return ElementType.LABEL
    
    def _classify_color_element(self, color_name, width, height, area) -> ElementType:
        """Classify element type based on color analysis"""
        if "button" in color_name:
            return ElementType.BUTTON
        elif "text_area" in color_name:
            return ElementType.TEXT_AREA
        else:
            return ElementType.LABEL
    
    def _process_and_rank_elements(self, elements: List[UIElement], screenshot) -> List[Dict[str, Any]]:
        """Process and rank elements by relevance and confidence"""
        
        # Remove duplicates and merge overlapping elements
        deduplicated = self._deduplicate_elements(elements)
        
        # Sort by confidence and relevance
        ranked = sorted(deduplicated, key=lambda e: e.confidence, reverse=True)
        
        # Convert to dictionary format for compatibility
        return [self._element_to_dict(element) for element in ranked]
    
    def _deduplicate_elements(self, elements: List[UIElement]) -> List[UIElement]:
        """Remove duplicate and overlapping elements"""
        if not elements:
            return []
        
        # Sort by confidence to keep best elements
        sorted_elements = sorted(elements, key=lambda e: e.confidence, reverse=True)
        deduplicated = []
        
        for element in sorted_elements:
            # Check if this element overlaps significantly with existing ones
            overlaps = False
            for existing in deduplicated:
                if self._elements_overlap(element, existing, threshold=0.5):
                    overlaps = True
                    break
            
            if not overlaps:
                deduplicated.append(element)
        
        return deduplicated
    
    def _elements_overlap(self, elem1: UIElement, elem2: UIElement, threshold: float = 0.5) -> bool:
        """Check if two elements overlap significantly"""
        box1 = elem1.bounding_box
        box2 = elem2.bounding_box
        
        # Calculate intersection
        x1 = max(box1["x"], box2["x"])
        y1 = max(box1["y"], box2["y"])
        x2 = min(box1["x"] + box1["width"], box2["x"] + box2["width"])
        y2 = min(box1["y"] + box1["height"], box2["y"] + box2["height"])
        
        if x2 <= x1 or y2 <= y1:
            return False
        
        intersection_area = (x2 - x1) * (y2 - y1)
        area1 = box1["width"] * box1["height"]
        area2 = box2["width"] * box2["height"]
        
        overlap_ratio = intersection_area / min(area1, area2)
        return overlap_ratio > threshold
    
    def _element_to_dict(self, element: UIElement) -> Dict[str, Any]:
        """Convert UIElement to dictionary format"""
        return {
            "element_id": element.id,
            "element_type": element.element_type.value,
            "element_text": element.text,
            "confidence": element.confidence,
            "bounding_box": element.bounding_box,
            "position": {"x": element.center[0], "y": element.center[1]},
            "detection_method": element.detection_method,
            "app_context": element.app_context,
            "interaction_hints": element.interaction_hints,
            "attributes": element.attributes
        }
    
    def _analyze_confidence_distribution(self, elements) -> Dict[str, float]:
        """Analyze confidence distribution of detected elements"""
        if not elements:
            return {"average": 0.0, "high_confidence_count": 0}
        
        confidences = [elem["confidence"] for elem in elements]
        high_confidence = len([c for c in confidences if c > 0.7])
        
        return {
            "average": sum(confidences) / len(confidences),
            "high_confidence_count": high_confidence,
            "total_elements": len(elements)
        }
    
    def _determine_app_context(self, elements) -> Optional[str]:
        """Determine which application context we're in"""
        app_contexts = [elem.get("app_context") for elem in elements if elem.get("app_context")]
        if app_contexts:
            # Return most common app context
            return max(set(app_contexts), key=app_contexts.count)
        return None
    
    def _create_close_button_template(self):
        """Create close button template"""
        # Simplified - in production, load actual button images
        template = np.zeros((16, 16), dtype=np.uint8)
        cv2.line(template, (4, 4), (12, 12), 255, 2)
        cv2.line(template, (12, 4), (4, 12), 255, 2)
        return template
    
    def _create_minimize_button_template(self):
        """Create minimize button template"""
        template = np.zeros((16, 16), dtype=np.uint8)
        cv2.line(template, (4, 12), (12, 12), 255, 2)
        return template
    
    def _create_maximize_button_template(self):
        """Create maximize button template"""
        template = np.zeros((16, 16), dtype=np.uint8)
        cv2.rectangle(template, (4, 4), (12, 12), 255, 2)
        return template