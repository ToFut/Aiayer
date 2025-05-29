#!/usr/bin/env python3
"""
Enhanced UI Detection Engine
Uses multiple advanced techniques for accurate UI element detection
"""

import cv2
import numpy as np
import pytesseract
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from PIL import Image, ImageGrab
import time
import json
import os

logger = logging.getLogger(__name__)

@dataclass
class UIElement:
    """Enhanced UI element with rich detection data"""
    id: str
    element_type: str
    text: str
    confidence: float
    center: Tuple[int, int]
    bounding_box: Dict[str, int]
    detection_method: str
    clickable: bool = True
    typeable: bool = False
    ocr_text: str = ""
    color_info: Dict[str, Any] = None
    visual_features: Dict[str, Any] = None

class EnhancedUIDetectionEngine:
    """Advanced UI detection using multiple computer vision techniques"""
    
    def __init__(self):
        self.debug_mode = True
        self.save_debug_images = True
        self.detection_threshold = 0.5
        
        # Create debug directory
        if self.save_debug_images:
            os.makedirs("ui_detection_debug", exist_ok=True)
        
        logger.info("🔬 Enhanced UI Detection Engine initialized")
    
    async def detect_ui_elements(self, screenshot: np.ndarray) -> List[UIElement]:
        """Master function that combines all detection methods"""
        elements = []
        timestamp = int(time.time())
        
        try:
            if screenshot.size == 0:
                return elements
            
            logger.info(f"🔍 Starting enhanced UI detection on {screenshot.shape} image")
            
            # Method 1: OCR-based text detection (most reliable)
            text_elements = await self.detect_text_elements(screenshot, timestamp)
            elements.extend(text_elements)
            
            # Method 2: Color-based button detection
            button_elements = await self.detect_buttons_by_color(screenshot, timestamp)
            elements.extend(button_elements)
            
            # Method 3: Template matching for common UI patterns
            template_elements = await self.detect_template_elements(screenshot, timestamp)
            elements.extend(template_elements)
            
            # Method 4: Accessibility-based detection
            accessible_elements = await self.detect_accessible_elements(screenshot, timestamp)
            elements.extend(accessible_elements)
            
            # Method 5: Machine learning-based detection (if available)
            ml_elements = await self.detect_ml_elements(screenshot, timestamp)
            elements.extend(ml_elements)
            
            # Remove duplicates and merge overlapping elements
            elements = await self.merge_overlapping_elements(elements)
            
            # Rank elements by confidence and likelihood
            elements = await self.rank_elements_by_confidence(elements)
            
            logger.info(f"🎯 Enhanced detection found {len(elements)} high-quality UI elements")
            
            if self.debug_mode:
                await self.save_debug_visualization(screenshot, elements, timestamp)
            
            return elements
            
        except Exception as e:
            logger.error(f"Error in enhanced UI detection: {e}")
            return elements
    
    async def detect_text_elements(self, screenshot: np.ndarray, timestamp: int) -> List[UIElement]:
        """Detect UI elements using OCR - most reliable method"""
        elements = []
        
        try:
            # Convert to PIL Image for OCR
            pil_image = Image.fromarray(cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB))
            
            # Use pytesseract to detect text with bounding boxes
            ocr_data = pytesseract.image_to_data(pil_image, output_type=pytesseract.Output.DICT)
            
            for i in range(len(ocr_data['text'])):
                text = ocr_data['text'][i].strip()
                confidence = int(ocr_data['conf'][i])
                
                # Filter out low confidence and empty text
                if confidence > 30 and len(text) > 0:
                    x = ocr_data['left'][i]
                    y = ocr_data['top'][i]
                    w = ocr_data['width'][i]
                    h = ocr_data['height'][i]
                    
                    # Calculate center
                    center_x = x + w // 2
                    center_y = y + h // 2
                    
                    # Determine element type based on text content
                    element_type = self.classify_text_element(text)
                    
                    # Check if it's clickable based on text patterns
                    clickable = self.is_text_clickable(text)
                    typeable = element_type in ['text_field', 'search_box']
                    
                    element = UIElement(
                        id=f"text_{i}",
                        element_type=element_type,
                        text=text,
                        confidence=confidence / 100.0,
                        center=(center_x, center_y),
                        bounding_box={"x": x, "y": y, "width": w, "height": h},
                        detection_method="ocr_text",
                        clickable=clickable,
                        typeable=typeable,
                        ocr_text=text
                    )
                    elements.append(element)
            
            logger.debug(f"📝 OCR detected {len(elements)} text elements")
            return elements
            
        except Exception as e:
            logger.error(f"Error in OCR text detection: {e}")
            return elements
    
    async def detect_buttons_by_color(self, screenshot: np.ndarray, timestamp: int) -> List[UIElement]:
        """Advanced button detection using color analysis and morphology"""
        elements = []
        
        try:
            # Convert to different color spaces for better analysis
            hsv = cv2.cvtColor(screenshot, cv2.COLOR_BGR2HSV)
            lab = cv2.cvtColor(screenshot, cv2.COLOR_BGR2LAB)
            
            # Define multiple color ranges for different button types
            button_color_ranges = [
                # Blue buttons (common in many UIs)
                {"name": "blue_button", "lower": np.array([100, 50, 50]), "upper": np.array([130, 255, 255])},
                # Green buttons (submit, confirm)
                {"name": "green_button", "lower": np.array([35, 50, 50]), "upper": np.array([85, 255, 255])},
                # Red buttons (delete, cancel)
                {"name": "red_button", "lower": np.array([0, 50, 50]), "upper": np.array([10, 255, 255])},
                # Orange buttons
                {"name": "orange_button", "lower": np.array([10, 50, 50]), "upper": np.array([25, 255, 255])},
                # Gray buttons (neutral actions)
                {"name": "gray_button", "lower": np.array([0, 0, 100]), "upper": np.array([180, 50, 200])},
            ]
            
            for color_range in button_color_ranges:
                # Create mask for this color range
                mask = cv2.inRange(hsv, color_range["lower"], color_range["upper"])
                
                # Apply morphological operations to clean up the mask
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
                
                # Find contours
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for i, contour in enumerate(contours):
                    area = cv2.contourArea(contour)
                    
                    # Filter by area (buttons should be reasonably sized)
                    if 1000 < area < 100000:
                        x, y, w, h = cv2.boundingRect(contour)
                        
                        # Check aspect ratio (buttons are usually not too tall or too wide)
                        aspect_ratio = w / h if h > 0 else 0
                        if 0.2 < aspect_ratio < 8:
                            # Check if contour is roughly rectangular
                            contour_area = cv2.contourArea(contour)
                            rect_area = w * h
                            rectangularity = contour_area / rect_area if rect_area > 0 else 0
                            
                            if rectangularity > 0.7:  # At least 70% rectangular
                                center_x = x + w // 2
                                center_y = y + h // 2
                                
                                # Calculate confidence based on multiple factors
                                confidence = min(1.0, (rectangularity + (area / 10000)) / 2)
                                
                                element = UIElement(
                                    id=f"color_button_{color_range['name']}_{i}",
                                    element_type="button",
                                    text=f"{color_range['name'].replace('_', ' ').title()}",
                                    confidence=confidence,
                                    center=(center_x, center_y),
                                    bounding_box={"x": x, "y": y, "width": w, "height": h},
                                    detection_method="color_analysis",
                                    clickable=True,
                                    color_info={"color_type": color_range["name"], "area": area}
                                )
                                elements.append(element)
            
            logger.debug(f"🎨 Color analysis detected {len(elements)} button elements")
            return elements
            
        except Exception as e:
            logger.error(f"Error in color-based button detection: {e}")
            return elements
    
    async def detect_template_elements(self, screenshot: np.ndarray, timestamp: int) -> List[UIElement]:
        """Template matching for common UI patterns"""
        elements = []
        
        try:
            # This would require pre-created templates for common UI elements
            # For now, we'll do pattern-based detection using image features
            
            gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            
            # Detect corners (buttons often have corners)
            corners = cv2.goodFeaturesToTrack(gray, maxCorners=100, qualityLevel=0.01, minDistance=30)
            
            if corners is not None:
                for i, corner in enumerate(corners):
                    x, y = corner.ravel().astype(int)
                    
                    # Check surrounding area for button-like characteristics
                    region_size = 50
                    x1, y1 = max(0, x - region_size), max(0, y - region_size)
                    x2, y2 = min(screenshot.shape[1], x + region_size), min(screenshot.shape[0], y + region_size)
                    
                    region = gray[y1:y2, x1:x2]
                    
                    if region.size > 0:
                        # Check if region has button-like characteristics
                        std_dev = np.std(region)
                        mean_intensity = np.mean(region)
                        
                        # Buttons often have moderate contrast and are not too dark or bright
                        if 20 < std_dev < 80 and 50 < mean_intensity < 200:
                            element = UIElement(
                                id=f"template_{i}",
                                element_type="interactive",
                                text=f"Interactive element at corner",
                                confidence=0.6,
                                center=(x, y),
                                bounding_box={"x": x1, "y": y1, "width": x2-x1, "height": y2-y1},
                                detection_method="template_matching",
                                clickable=True,
                                visual_features={"std_dev": float(std_dev), "mean_intensity": float(mean_intensity)}
                            )
                            elements.append(element)
            
            logger.debug(f"📐 Template matching detected {len(elements)} elements")
            return elements
            
        except Exception as e:
            logger.error(f"Error in template matching: {e}")
            return elements
    
    async def detect_accessible_elements(self, screenshot: np.ndarray, timestamp: int) -> List[UIElement]:
        """Detect elements using accessibility patterns"""
        elements = []
        
        try:
            # This is a simplified version - real accessibility detection would use system APIs
            # For now, we'll detect common accessibility patterns visually
            
            # Look for focus indicators (blue outlines, etc.)
            hsv = cv2.cvtColor(screenshot, cv2.COLOR_BGR2HSV)
            
            # Focus indicators are often blue
            focus_lower = np.array([100, 100, 100])
            focus_upper = np.array([130, 255, 255])
            focus_mask = cv2.inRange(hsv, focus_lower, focus_upper)
            
            # Find contours that might be focus indicators
            contours, _ = cv2.findContours(focus_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for i, contour in enumerate(contours):
                area = cv2.contourArea(contour)
                if 500 < area < 50000:
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Check if it's a thin outline (focus indicator)
                    filled_area = cv2.contourArea(contour)
                    rect_area = w * h
                    fill_ratio = filled_area / rect_area if rect_area > 0 else 0
                    
                    if fill_ratio < 0.3:  # Likely an outline
                        center_x = x + w // 2
                        center_y = y + h // 2
                        
                        element = UIElement(
                            id=f"accessible_{i}",
                            element_type="focusable",
                            text="Focusable element",
                            confidence=0.7,
                            center=(center_x, center_y),
                            bounding_box={"x": x, "y": y, "width": w, "height": h},
                            detection_method="accessibility",
                            clickable=True
                        )
                        elements.append(element)
            
            logger.debug(f"♿ Accessibility detection found {len(elements)} elements")
            return elements
            
        except Exception as e:
            logger.error(f"Error in accessibility detection: {e}")
            return elements
    
    async def detect_ml_elements(self, screenshot: np.ndarray, timestamp: int) -> List[UIElement]:
        """Machine learning-based detection (placeholder for future ML models)"""
        elements = []
        
        try:
            # This is where you would integrate ML models like:
            # - YOLO for object detection
            # - Custom trained models for UI elements
            # - TensorFlow/PyTorch models
            
            # For now, we'll use a simple ML-like approach with clustering
            from sklearn.cluster import KMeans
            
            # Reshape image for clustering
            pixels = screenshot.reshape(-1, 3)
            
            # Use K-means to find dominant colors (ML approach)
            kmeans = KMeans(n_clusters=8, random_state=42, n_init=10)
            kmeans.fit(pixels)
            
            # Find regions with dominant colors that might be UI elements
            labels = kmeans.labels_.reshape(screenshot.shape[:2])
            
            for cluster_id in range(8):
                cluster_mask = (labels == cluster_id).astype(np.uint8) * 255
                
                # Find contours in this cluster
                contours, _ = cv2.findContours(cluster_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for i, contour in enumerate(contours):
                    area = cv2.contourArea(contour)
                    if 2000 < area < 200000:  # Reasonable size for UI elements
                        x, y, w, h = cv2.boundingRect(contour)
                        
                        # Check if it's a reasonable shape for UI element
                        aspect_ratio = w / h if h > 0 else 0
                        if 0.1 < aspect_ratio < 15:
                            center_x = x + w // 2
                            center_y = y + h // 2
                            
                            # Get dominant color for this cluster
                            dominant_color = kmeans.cluster_centers_[cluster_id]
                            
                            element = UIElement(
                                id=f"ml_cluster_{cluster_id}_{i}",
                                element_type="ml_detected",
                                text=f"ML detected element (cluster {cluster_id})",
                                confidence=0.5,
                                center=(center_x, center_y),
                                bounding_box={"x": x, "y": y, "width": w, "height": h},
                                detection_method="machine_learning",
                                clickable=True,
                                color_info={"dominant_color": dominant_color.tolist()}
                            )
                            elements.append(element)
            
            logger.debug(f"🤖 ML detection found {len(elements)} elements")
            return elements[:5]  # Limit to avoid too many false positives
            
        except Exception as e:
            logger.debug(f"ML detection not available (sklearn not installed): {e}")
            return elements
    
    def classify_text_element(self, text: str) -> str:
        """Classify text into UI element types"""
        text_lower = text.lower()
        
        # Button keywords
        button_keywords = ['click', 'button', 'submit', 'send', 'save', 'cancel', 'ok', 'yes', 'no', 'apply', 'close', 'add', 'delete', 'edit', 'download', 'upload', 'login', 'sign in', 'sign up', 'register']
        
        # Link keywords
        link_keywords = ['http', 'www.', '.com', '.org', '.net', 'click here', 'learn more', 'read more']
        
        # Input field indicators
        input_keywords = ['enter', 'type', 'search', 'find', 'email', 'password', 'username', 'name', 'address']
        
        if any(keyword in text_lower for keyword in button_keywords):
            return 'button'
        elif any(keyword in text_lower for keyword in link_keywords):
            return 'link'
        elif any(keyword in text_lower for keyword in input_keywords):
            return 'text_field'
        elif len(text) < 3:
            return 'label'
        else:
            return 'text'
    
    def is_text_clickable(self, text: str) -> bool:
        """Determine if text is likely clickable"""
        text_lower = text.lower()
        
        clickable_indicators = [
            'click', 'button', 'submit', 'send', 'save', 'cancel', 'ok', 'yes', 'no',
            'apply', 'close', 'add', 'delete', 'edit', 'download', 'upload', 'login',
            'sign in', 'sign up', 'register', 'http', 'www.', '.com', 'learn more'
        ]
        
        return any(indicator in text_lower for indicator in clickable_indicators)
    
    async def merge_overlapping_elements(self, elements: List[UIElement]) -> List[UIElement]:
        """Remove duplicate and overlapping elements"""
        if len(elements) <= 1:
            return elements
        
        merged = []
        used_indices = set()
        
        for i, elem1 in enumerate(elements):
            if i in used_indices:
                continue
                
            # Find overlapping elements
            overlapping = [elem1]
            used_indices.add(i)
            
            for j, elem2 in enumerate(elements[i+1:], i+1):
                if j in used_indices:
                    continue
                    
                # Check if bounding boxes overlap
                if self.boxes_overlap(elem1.bounding_box, elem2.bounding_box):
                    overlapping.append(elem2)
                    used_indices.add(j)
            
            # Merge overlapping elements by taking the one with highest confidence
            best_element = max(overlapping, key=lambda e: e.confidence)
            merged.append(best_element)
        
        return merged
    
    def boxes_overlap(self, box1: Dict[str, int], box2: Dict[str, int]) -> bool:
        """Check if two bounding boxes overlap significantly"""
        x1, y1, w1, h1 = box1['x'], box1['y'], box1['width'], box1['height']
        x2, y2, w2, h2 = box2['x'], box2['y'], box2['width'], box2['height']
        
        # Calculate overlap area
        left = max(x1, x2)
        top = max(y1, y2)
        right = min(x1 + w1, x2 + w2)
        bottom = min(y1 + h1, y2 + h2)
        
        if left < right and top < bottom:
            overlap_area = (right - left) * (bottom - top)
            area1 = w1 * h1
            area2 = w2 * h2
            
            # Consider overlapping if overlap is more than 30% of either box
            overlap_ratio1 = overlap_area / area1 if area1 > 0 else 0
            overlap_ratio2 = overlap_area / area2 if area2 > 0 else 0
            
            return overlap_ratio1 > 0.3 or overlap_ratio2 > 0.3
        
        return False
    
    async def rank_elements_by_confidence(self, elements: List[UIElement]) -> List[UIElement]:
        """Rank elements by confidence and other quality factors"""
        def quality_score(element: UIElement) -> float:
            score = element.confidence
            
            # Boost score for elements with OCR text
            if element.ocr_text and len(element.ocr_text) > 2:
                score += 0.2
            
            # Boost score for clickable elements
            if element.clickable:
                score += 0.1
            
            # Boost score for reasonable sizes
            area = element.bounding_box['width'] * element.bounding_box['height']
            if 1000 < area < 50000:
                score += 0.1
            
            # Penalize elements that are too small or too large
            if area < 500 or area > 100000:
                score -= 0.2
            
            return min(1.0, score)
        
        # Sort by quality score
        elements.sort(key=quality_score, reverse=True)
        
        # Update confidence scores
        for element in elements:
            element.confidence = quality_score(element)
        
        return elements
    
    async def save_debug_visualization(self, screenshot: np.ndarray, elements: List[UIElement], timestamp: int):
        """Save debug visualization showing detected elements"""
        if not self.save_debug_images:
            return
        
        try:
            debug_image = screenshot.copy()
            
            # Draw bounding boxes for each element
            colors = {
                'button': (0, 255, 0),      # Green
                'text_field': (255, 0, 0),  # Blue
                'link': (0, 0, 255),        # Red
                'text': (255, 255, 0),      # Cyan
                'interactive': (255, 0, 255), # Magenta
                'focusable': (0, 255, 255),  # Yellow
                'ml_detected': (128, 128, 128) # Gray
            }
            
            for element in elements:
                color = colors.get(element.element_type, (255, 255, 255))
                bbox = element.bounding_box
                
                # Draw bounding box
                cv2.rectangle(debug_image, 
                            (bbox['x'], bbox['y']), 
                            (bbox['x'] + bbox['width'], bbox['y'] + bbox['height']), 
                            color, 2)
                
                # Draw center point
                cv2.circle(debug_image, element.center, 5, color, -1)
                
                # Add label
                label = f"{element.element_type} ({element.confidence:.2f})"
                cv2.putText(debug_image, label, 
                          (bbox['x'], bbox['y'] - 10), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            # Save debug image
            debug_path = f"ui_detection_debug/detection_{timestamp}.png"
            cv2.imwrite(debug_path, debug_image)
            logger.info(f"🖼️ Debug visualization saved: {debug_path}")
            
        except Exception as e:
            logger.error(f"Error saving debug visualization: {e}")

# Example usage
async def test_enhanced_detection():
    """Test the enhanced detection system"""
    engine = EnhancedUIDetectionEngine()
    
    # Capture screen
    screenshot = ImageGrab.grab()
    screenshot_np = np.array(screenshot)
    screenshot_cv = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
    
    # Detect elements
    elements = await engine.detect_ui_elements(screenshot_cv)
    
    print(f"🔍 Enhanced detection found {len(elements)} elements:")
    for i, element in enumerate(elements[:10]):  # Show top 10
        print(f"  {i+1}. {element.element_type}: '{element.text}' at {element.center} (confidence: {element.confidence:.2f})")

if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_enhanced_detection())