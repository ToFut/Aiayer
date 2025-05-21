#!/usr/bin/env python3
"""
Fixed Screen Sensor Module
Captures screenshots for LLaVA processing with enhanced image and text handling.
Includes alternative screen analysis methods using local computer vision techniques.
"""
import mss
import mss.tools
import threading
import time
import logging
import os
import re
from datetime import datetime
import psutil
import io
import base64
import asyncio
from typing import Dict, Any, Optional, Union, List, Tuple
import hashlib
import json
from dataclasses import dataclass, asdict, field
from PIL import Image
import numpy as np
import pytesseract
from pytesseract import Output
import cv2
import requests
import aiohttp
import traceback
import torch
from collections import Counter

# Configure logging
os.makedirs('logs/sensors/screen_sensor', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sensors/screen_sensor/screen_sensor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AlternativeScreenAnalyzer:
    """Provides alternative methods for screen analysis beyond LLaVA.
    
    Uses a combination of:
    1. Advanced OCR with layout analysis
    2. UI element detection 
    3. Application pattern recognition
    4. Color and layout analysis
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__ + ".AlternativeScreenAnalyzer")
        
        # Initialize face detection for user interface analysis
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # OCR config for different scenarios
        self.ocr_configs = {
            'default': '--psm 3',  # Fully automatic page segmentation
            'single_line': '--psm 7',  # Single text line
            'single_word': '--psm 8',  # Single word
            'single_char': '--psm 10',  # Single character
            'sparse_text': '--psm 11',  # Sparse text, find as much text as possible
            'sparse_text_osd': '--psm 12'  # Sparse text with OSD
        }
        
        # UI element patterns (common UI elements by color/shape patterns)
        self.ui_patterns = {
            'button': {
                'aspect_ratio_range': (2.0, 6.0),  # Width typically 2-6x height
                'min_area': 1000,  # Minimum area in pixels
                'max_area': 20000,  # Maximum area in pixels
                'rect_similarity': 0.8,  # How rectangular it should be (1.0 = perfect rectangle)
            },
            'text_field': {
                'aspect_ratio_range': (3.0, 10.0),  # Width typically 3-10x height
                'min_area': 1000,
                'max_area': 50000,
                'rect_similarity': 0.9,  # Text fields are usually very rectangular
            },
            'dropdown': {
                'aspect_ratio_range': (3.0, 8.0),
                'min_area': 1000,
                'max_area': 15000,
                'rect_similarity': 0.85,
            },
            'checkbox': {
                'aspect_ratio_range': (0.8, 1.2),  # Nearly square
                'min_area': 100,
                'max_area': 2000,
                'rect_similarity': 0.85,
            }
        }
        
        # Common application color schemes for basic app recognition
        self.app_color_signatures = {
            'gmail': [(234, 67, 53), (66, 133, 244), (251, 188, 5), (52, 168, 83)],  # Google colors
            'slack': [(74, 21, 75), (230, 26, 88), (97, 197, 84), (250, 141, 0)],  # Slack colors
            'vscode': [(37, 37, 38), (53, 53, 53), (15, 121, 209)],  # VSCode dark theme colors
            'chrome': [(66, 133, 244), (234, 67, 53), (251, 188, 5), (52, 168, 83)],  # Google Chrome colors
            'terminal': [(0, 0, 0), (39, 40, 34), (13, 15, 14)]  # Common terminal background colors
        }
        
        # Initialize template matching database - basic UI elements
        self.templates = {}
        template_dir = os.path.join(os.path.dirname(__file__), 'ui_templates')
        if os.path.exists(template_dir):
            for filename in os.listdir(template_dir):
                if filename.endswith('.png') or filename.endswith('.jpg'):
                    template_name = os.path.splitext(filename)[0]
                    template_path = os.path.join(template_dir, filename)
                    self.templates[template_name] = cv2.imread(template_path, cv2.IMREAD_COLOR)
                    self.logger.info(f"Loaded UI template: {template_name}")
        else:
            self.logger.warning(f"UI template directory not found: {template_dir}")
    
    def analyze_screen(self, image: Image.Image) -> Dict[str, Any]:
        """Main entry point for alternative screen analysis.
        
        Performs:
        1. Enhanced OCR with layout analysis
        2. UI element detection
        3. Application identification
        4. Basic context extraction
        
        Args:
            image: PIL Image of the screen capture
            
        Returns:
            Dict containing analysis results
        """
        try:
            # Convert PIL image to OpenCV format for processing
            cv_image = self._pil_to_cv2(image)
            
            # Perform OCR with layout analysis
            ocr_results = self._enhanced_ocr_with_layout(cv_image)
            
            # Detect UI elements
            ui_elements = self._detect_ui_elements(cv_image)
            
            # Identify application
            app_info = self._identify_application(cv_image, ocr_results)
            
            # Basic context extraction
            context = self._extract_basic_context(ocr_results, ui_elements, app_info)
            
            # Combine all results
            analysis = {
                "analysis_method": "local_cv",
                "analysis_timestamp": time.time(),
                "ocr_data": ocr_results,
                "ui_elements": ui_elements,
                "application": app_info,
                "visual_context": context,
                "screen_elements": self._convert_to_screen_elements(ui_elements),
                "llava_description": context  # Use our context as a replacement for llava_description
            }
            
            return analysis
        except Exception as e:
            self.logger.error(f"Error in alternative screen analysis: {e}")
            self.logger.error(traceback.format_exc())
            return {
                "analysis_method": "local_cv_error",
                "error": str(e),
                "llava_description": f"Error analyzing screen: {str(e)}",
                "screen_elements": [],
                "visual_context": ""
            }
    
    def _pil_to_cv2(self, pil_image: Image.Image) -> np.ndarray:
        """Convert PIL Image to OpenCV format."""
        return np.array(pil_image)[:, :, ::-1].copy()  # Convert RGB to BGR for OpenCV
    
    def _enhanced_ocr_with_layout(self, cv_image: np.ndarray) -> Dict[str, Any]:
        """Perform enhanced OCR with layout analysis."""
        try:
            # Convert to grayscale for OCR
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Improve image quality for OCR
            # Adaptive thresholding to handle different lighting conditions
            thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                         cv2.THRESH_BINARY, 11, 2)
            
            # Use multiple OCR configurations to maximize text extraction
            results = {}
            
            # Primary pass - standard mode
            data = pytesseract.image_to_data(thresh, output_type=Output.DICT, 
                                            config=self.ocr_configs['default'])
            
            # Extract structured text with positions
            boxes = []
            line_text = []
            current_line = -1
            
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 60:  # Only consider text with confidence > 60%
                    text = data['text'][i].strip()
                    if text:
                        line_num = data['line_num'][i]
                        if line_num != current_line:
                            if current_line != -1 and line_text:
                                # Get filtered boxes for this line
                                line_boxes = [box for box in boxes if box.get('line_num') == current_line and 'left' in box and 'top' in box and 'width' in box and 'height' in box]
                                
                                # Only proceed if we have valid boxes with required fields
                                if line_boxes:
                                    boxes.append({
                                        'line_num': current_line,
                                        'text': ' '.join(line_text),
                                        'bbox': [
                                            min(box['left'] for box in line_boxes),
                                            min(box['top'] for box in line_boxes),
                                            max(box['left'] + box['width'] for box in line_boxes),
                                            max(box['top'] + box['height'] for box in line_boxes)
                                        ]
                                    })
                                else:
                                    # Fallback for when we don't have boxes with required fields
                                    boxes.append({
                                        'line_num': current_line,
                                        'text': ' '.join(line_text)
                                    })
                            line_text = []
                            current_line = line_num
                        
                        line_text.append(text)
                        
                        boxes.append({
                            'line_num': line_num,
                            'text': text,
                            'conf': data['conf'][i],
                            'left': data['left'][i],
                            'top': data['top'][i],
                            'width': data['width'][i],
                            'height': data['height'][i]
                        })
            
            # Add the last line
            if current_line != -1 and line_text:
                # Get filtered boxes for this line
                line_boxes = [box for box in boxes if box.get('line_num') == current_line and 'left' in box and 'top' in box and 'width' in box and 'height' in box]
                
                # Only proceed if we have valid boxes with required fields
                if line_boxes:
                    boxes.append({
                        'line_num': current_line,
                        'text': ' '.join(line_text),
                        'bbox': [
                            min(box['left'] for box in line_boxes),
                            min(box['top'] for box in line_boxes),
                            max(box['left'] + box['width'] for box in line_boxes),
                            max(box['top'] + box['height'] for box in line_boxes)
                        ]
                    })
                else:
                    # Fallback for when we don't have boxes with required fields
                    boxes.append({
                        'line_num': current_line,
                        'text': ' '.join(line_text)
                    })
            
            # Alternative pass for sparse text
            sparse_text = pytesseract.image_to_string(thresh, config=self.ocr_configs['sparse_text'])
            
            # Organize results
            results = {
                'boxes': boxes,
                'full_text': pytesseract.image_to_string(thresh, config=self.ocr_configs['default']),
                'sparse_text': sparse_text,
                'word_count': len([b for b in boxes if len(b['text'].split()) == 1]),
                'line_count': len(set(b.get('line_num', 0) for b in boxes))
            }
            
            # Advanced layout analysis - group text by regions
            results['regions'] = self._analyze_text_layout(boxes)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in enhanced OCR: {e}")
            self.logger.error(traceback.format_exc())
            return {
                'full_text': '',
                'boxes': [],
                'error': str(e)
            }
    
    def _analyze_text_layout(self, text_boxes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group text boxes into logical regions based on position."""
        if not text_boxes:
            return []
            
        regions = []
        
        # Filter out boxes missing required positional attributes
        valid_boxes = [box for box in text_boxes if all(k in box for k in ['top', 'left', 'height', 'width'])]
        
        if not valid_boxes:
            return []
            
        # Sort boxes by vertical position (top)
        sorted_boxes = sorted(valid_boxes, key=lambda box: box.get('top', 0))
        
        if not sorted_boxes:
            return []
            
        # Group into regions using a simple position-based clustering
        current_region = [sorted_boxes[0]]
        current_top = sorted_boxes[0].get('top', 0)
        
        for box in sorted_boxes[1:]:
            box_top = box.get('top', 0)
            
            # If this box is close to the previous one vertically, add to current region
            if abs(box_top - current_top) < 30:  # 30 pixels threshold
                current_region.append(box)
            else:
                # Finalize current region and start a new one
                if current_region:
                    region_text = ' '.join(box.get('text', '') for box in current_region)
                    if region_text.strip():
                        regions.append({
                            'text': region_text,
                            'boxes': current_region,
                            'top': min(box.get('top', 0) for box in current_region),
                            'left': min(box.get('left', 0) for box in current_region),
                            'bottom': max(box.get('top', 0) + box.get('height', 0) for box in current_region),
                            'right': max(box.get('left', 0) + box.get('width', 0) for box in current_region)
                        })
                
                # Start new region
                current_region = [box]
                current_top = box_top
        
        # Add the last region
        if current_region:
            region_text = ' '.join(box.get('text', '') for box in current_region)
            if region_text.strip():
                regions.append({
                    'text': region_text,
                    'boxes': current_region,
                    'top': min(box.get('top', 0) for box in current_region),
                    'left': min(box.get('left', 0) for box in current_region),
                    'bottom': max(box.get('top', 0) + box.get('height', 0) for box in current_region),
                    'right': max(box.get('left', 0) + box.get('width', 0) for box in current_region)
                })
        
        return regions
    
    def _detect_ui_elements(self, cv_image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect UI elements using contour analysis and pattern recognition."""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Adaptive threshold to handle different lighting conditions
            thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                         cv2.THRESH_BINARY_INV, 11, 2)
            
            # Find contours in the threshold image
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            ui_elements = []
            
            # Analyze each contour
            for contour in contours:
                area = cv2.contourArea(contour)
                
                # Skip very small contours
                if area < 100:
                    continue
                    
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = float(w) / h if h > 0 else 0
                
                # Calculate how rectangular the contour is
                rect_area = w * h
                rect_similarity = area / rect_area if rect_area > 0 else 0
                
                # Try to classify UI element type
                element_type = "unknown"
                confidence = 0.0
                
                for pattern_type, pattern in self.ui_patterns.items():
                    if (pattern['min_area'] <= area <= pattern['max_area'] and
                        pattern['aspect_ratio_range'][0] <= aspect_ratio <= pattern['aspect_ratio_range'][1] and
                        rect_similarity >= pattern['rect_similarity']):
                        
                        element_type = pattern_type
                        confidence = rect_similarity
                        break
                
                # Only keep elements with high confidence
                if confidence > 0.7:
                    # Extract the ROI for additional analysis
                    roi = cv_image[y:y+h, x:x+w]
                    
                    # Get the dominant colors
                    dominant_colors = self._get_dominant_colors(roi)
                    
                    # Check for text inside the element (useful for buttons with labels)
                    element_text = ""
                    if element_type in ["button", "text_field", "dropdown"]:
                        try:
                            # Use OCR to extract text from this element
                            roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                            element_text = pytesseract.image_to_string(roi_gray, 
                                                                     config=self.ocr_configs['single_line']).strip()
                        except Exception as e:
                            self.logger.debug(f"Error extracting text from UI element: {e}")
                    
                    ui_elements.append({
                        'type': element_type,
                        'confidence': confidence,
                        'bbox': [x, y, x+w, y+h],
                        'width': w,
                        'height': h,
                        'area': area,
                        'aspect_ratio': aspect_ratio,
                        'text': element_text,
                        'colors': dominant_colors
                    })
            
            # Additional template matching for common UI elements
            for template_name, template in self.templates.items():
                # Template image must exist
                if template is None:
                    continue
                    
                try:
                    # Try template matching
                    template_h, template_w = template.shape[:2]
                    if template_h > 0 and template_w > 0:
                        # Scale down template for faster matching if it's too large
                        if template_h > 200 or template_w > 200:
                            scale = min(200 / template_h, 200 / template_w)
                            template = cv2.resize(template, (int(template_w * scale), int(template_h * scale)))
                            template_h, template_w = template.shape[:2]
                        
                        # Ensure the template is smaller than the image
                        img_h, img_w = cv_image.shape[:2]
                        if template_h < img_h and template_w < img_w:
                            result = cv2.matchTemplate(cv_image, template, cv2.TM_CCOEFF_NORMED)
                            threshold = 0.7
                            loc = np.where(result >= threshold)
                            
                            for pt in zip(*loc[::-1]):
                                ui_elements.append({
                                    'type': template_name,
                                    'confidence': float(result[pt[1], pt[0]]),
                                    'bbox': [pt[0], pt[1], pt[0] + template_w, pt[1] + template_h],
                                    'width': template_w,
                                    'height': template_h,
                                    'area': template_w * template_h,
                                    'aspect_ratio': float(template_w) / template_h,
                                    'text': "",
                                    'match_type': 'template'
                                })
                except Exception as e:
                    self.logger.debug(f"Error in template matching for {template_name}: {e}")
            
            return ui_elements
            
        except Exception as e:
            self.logger.error(f"Error detecting UI elements: {e}")
            self.logger.error(traceback.format_exc())
            return []
    
    def _get_dominant_colors(self, image: np.ndarray, num_colors: int = 3) -> List[Tuple[int, int, int]]:
        """Extract dominant colors from the image."""
        try:
            # Resize image to speed up processing
            h, w = image.shape[:2]
            if h * w > 10000:  # If more than 10,000 pixels
                scale = 0.1  # Resize to 10%
                small = cv2.resize(image, (0, 0), fx=scale, fy=scale)
            else:
                small = image
                
            # Reshape the image to be a list of pixels
            pixels = small.reshape((-1, 3)).astype(np.float32)
            
            # Define criteria and apply kmeans()
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
            _, labels, centers = cv2.kmeans(pixels, num_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            
            # Convert back to uint8 and get counts
            centers = np.uint8(centers)
            unique_labels, counts = np.unique(labels, return_counts=True)
            
            # Sort colors by frequency
            sorted_indices = np.argsort(counts)[::-1]
            centers = centers[sorted_indices]
            
            # Convert from BGR to RGB and to tuples
            return [tuple(map(int, color[::-1])) for color in centers]
            
        except Exception as e:
            self.logger.debug(f"Error getting dominant colors: {e}")
            return [(0, 0, 0)]  # Return black as fallback

    def _identify_application(self, cv_image: np.ndarray, ocr_results: Dict[str, Any]) -> Dict[str, Any]:
        """Identify the application based on visual cues and text content."""
        try:
            # Get dominant colors
            dominant_colors = self._get_dominant_colors(cv_image, 5)
            
            # Match with known app color schemes
            app_scores = {}
            for app_name, color_signature in self.app_color_signatures.items():
                score = self._color_signature_match(dominant_colors, color_signature)
                app_scores[app_name] = score
            
            # Get full text for keyword matching
            full_text = ocr_results.get('full_text', '').lower()
            
            # Keyword matching for common applications
            keyword_matches = {}
            
            # Email client keywords
            email_keywords = ['inbox', 'compose', 'draft', 'sent', 'trash', 'gmail', 'outlook', 'mail']
            email_score = sum(2 for keyword in email_keywords if keyword in full_text)
            if email_score > 0:
                keyword_matches['email'] = email_score
                
                # Further identify specific email client
                if 'gmail' in full_text:
                    keyword_matches['gmail'] = email_score + 5
                elif 'outlook' in full_text:
                    keyword_matches['outlook'] = email_score + 5
            
            # Code editor keywords
            code_keywords = ['class', 'function', 'def', 'import', 'console', 'terminal', 'var', 'const']
            code_score = sum(2 for keyword in code_keywords if keyword in full_text)
            if code_score > 0:
                keyword_matches['code_editor'] = code_score
                
                # Specific editors
                if 'visual studio code' in full_text or 'vscode' in full_text:
                    keyword_matches['vscode'] = code_score + 5
                elif 'sublime' in full_text:
                    keyword_matches['sublime_text'] = code_score + 5
                elif 'intellij' in full_text or 'pycharm' in full_text or 'webstorm' in full_text:
                    keyword_matches['jetbrains_ide'] = code_score + 5
            
            # Browser keywords
            browser_keywords = ['http', 'https', 'www', 'search', 'bookmark', 'tab']
            browser_score = sum(2 for keyword in browser_keywords if keyword in full_text)
            if browser_score > 0:
                keyword_matches['browser'] = browser_score
                
                # Specific browsers
                if 'chrome' in full_text:
                    keyword_matches['chrome'] = browser_score + 5
                elif 'firefox' in full_text:
                    keyword_matches['firefox'] = browser_score + 5
                elif 'safari' in full_text:
                    keyword_matches['safari'] = browser_score + 5
            
            # Combine color matching and keyword matching
            app_candidates = {}
            
            # Add color-based scores
            for app, score in app_scores.items():
                if score > 0.5:  # Only consider reasonable matches
                    app_candidates[app] = score * 10  # Weight for color matching
            
            # Add keyword-based scores
            for app, score in keyword_matches.items():
                if app in app_candidates:
                    app_candidates[app] += score
                else:
                    app_candidates[app] = score
            
            # Determine the best match
            best_app = None
            best_score = 0
            for app, score in app_candidates.items():
                if score > best_score:
                    best_app = app
                    best_score = score
            
            # Determine the application view/mode
            app_view = ""
            if best_app:
                # Email client views
                if best_app in ['email', 'gmail', 'outlook']:
                    if 'compose' in full_text.lower():
                        app_view = 'compose'
                    elif 'inbox' in full_text.lower():
                        app_view = 'inbox'
                    elif 'sent' in full_text.lower():
                        app_view = 'sent'
                    elif 'draft' in full_text.lower():
                        app_view = 'drafts'
                
                # Code editor views
                elif best_app in ['code_editor', 'vscode', 'sublime_text', 'jetbrains_ide']:
                    if 'terminal' in full_text.lower() or 'console' in full_text.lower():
                        app_view = 'terminal'
                    elif 'debug' in full_text.lower():
                        app_view = 'debugger'
                    else:
                        app_view = 'editor'
                
                # Browser views
                elif best_app in ['browser', 'chrome', 'firefox', 'safari']:
                    if 'gmail' in full_text.lower():
                        app_view = 'gmail'
                    elif 'google doc' in full_text.lower():
                        app_view = 'google_docs'
                    elif 'youtube' in full_text.lower():
                        app_view = 'youtube'
                    else:
                        app_view = 'web_page'
            
            return {
                'name': best_app if best_app else 'unknown',
                'view': app_view,
                'confidence': best_score / 20.0 if best_score > 0 else 0,  # Normalize to 0-1 range
                'color_signatures': dominant_colors[:3],  # Top 3 colors
                'candidates': app_candidates
            }
            
        except Exception as e:
            self.logger.error(f"Error identifying application: {e}")
            self.logger.error(traceback.format_exc())
            return {
                'name': 'unknown',
                'view': '',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _color_signature_match(self, colors1: List[Tuple[int, int, int]], colors2: List[Tuple[int, int, int]]) -> float:
        """Calculate similarity between two color signatures."""
        if not colors1 or not colors2:
            return 0.0
            
        # Calculate color distances between each pair
        total_score = 0.0
        for c1 in colors1:
            best_match = min(self._color_distance(c1, c2) for c2 in colors2)
            # Convert distance to similarity score (0-1)
            # 150 is a reasonable threshold for considering colors different
            similarity = max(0, 1 - (best_match / 150.0))
            total_score += similarity
            
        # Normalize by number of colors
        return total_score / len(colors1)
    
    def _color_distance(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
        """Calculate Euclidean distance between two colors in RGB space."""
        return sum((c1 - c2) ** 2 for c1, c2 in zip(color1, color2)) ** 0.5
    
    def _extract_basic_context(self, ocr_results: Dict[str, Any], ui_elements: List[Dict[str, Any]], app_info: Dict[str, Any]) -> str:
        """Extract basic context information from analysis results."""
        try:
            context_parts = []
            
            # Add application information
            app_name = app_info.get('name', 'unknown')
            app_view = app_info.get('view', '')
            if app_name != 'unknown':
                context_parts.append(f"Application: {app_name}")
                if app_view:
                    context_parts.append(f"View: {app_view}")
            
            # Extract important text content
            full_text = ocr_results.get('full_text', '')
            if full_text:
                # Truncate for context description
                text_summary = full_text[:500] + ('...' if len(full_text) > 500 else '')
                context_parts.append(f"Text content: {text_summary}")
            
            # Summarize UI elements
            element_types = Counter(element.get('type') for element in ui_elements)
            if element_types:
                elements_summary = ", ".join(f"{count} {element_type}" 
                                          for element_type, count in element_types.most_common(5))
                context_parts.append(f"UI elements: {elements_summary}")
            
            # Look for meaningful buttons or interactive elements
            interactive_elements = []
            for element in ui_elements:
                if element.get('type') in ['button', 'dropdown', 'text_field'] and element.get('text'):
                    interactive_elements.append(f"{element.get('text')} ({element.get('type')})")
            
            if interactive_elements:
                interactive_summary = ", ".join(interactive_elements[:5])
                if len(interactive_elements) > 5:
                    interactive_summary += f" and {len(interactive_elements) - 5} more"
                context_parts.append(f"Interactive elements: {interactive_summary}")
            
            # Try to detect email-specific information
            if app_name in ['email', 'gmail', 'outlook'] or 'email' in app_view:
                email_info = self._extract_email_info(ocr_results)
                if email_info:
                    for key, value in email_info.items():
                        context_parts.append(f"{key}: {value}")
            
            # Try to detect form fields
            form_fields = self._extract_form_fields(ui_elements, ocr_results)
            if form_fields:
                fields_summary = ", ".join(field for field in form_fields[:5])
                if len(form_fields) > 5:
                    fields_summary += f" and {len(form_fields) - 5} more"
                context_parts.append(f"Form fields: {fields_summary}")
            
            # Combine all context parts
            context = "\n".join(context_parts)
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error extracting basic context: {e}")
            self.logger.error(traceback.format_exc())
            return f"Error extracting context: {str(e)}"
    
    def _extract_email_info(self, ocr_results: Dict[str, Any]) -> Dict[str, str]:
        """Extract email-specific information from OCR results."""
        email_info = {}
        full_text = ocr_results.get('full_text', '').lower()
        
        # Look for common email patterns
        from_match = re.search(r'from:?\s*([^\n]+)', full_text)
        if from_match:
            email_info['From'] = from_match.group(1).strip()
        
        to_match = re.search(r'to:?\s*([^\n]+)', full_text)
        if to_match:
            email_info['To'] = to_match.group(1).strip()
        
        subject_match = re.search(r'subject:?\s*([^\n]+)', full_text)
        if subject_match:
            email_info['Subject'] = subject_match.group(1).strip()
        
        return email_info
    
    def _extract_form_fields(self, ui_elements: List[Dict[str, Any]], ocr_results: Dict[str, Any]) -> List[str]:
        """Extract form fields from UI elements and OCR results."""
        form_fields = []
        
        # Extract from UI elements
        for element in ui_elements:
            if element.get('type') in ['text_field', 'dropdown', 'checkbox']:
                text = element.get('text', '').strip()
                if text:
                    form_fields.append(text)
        
        # Look for form field patterns in OCR text
        full_text = ocr_results.get('full_text', '')
        
        # Common form field labels
        field_patterns = [
            r'(?:name|username):\s*([^\n]+)',
            r'(?:email|e-mail):\s*([^\n]+)',
            r'(?:password|pwd):\s*([^\n]+)',
            r'(?:address|addr):\s*([^\n]+)',
            r'(?:phone|tel):\s*([^\n]+)'
        ]
        
        for pattern in field_patterns:
            matches = re.finditer(pattern, full_text, re.IGNORECASE)
            for match in matches:
                form_fields.append(match.group(0).strip())
        
        return form_fields
    
    def _convert_to_screen_elements(self, ui_elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert UI elements to the format expected by the ScreenData class."""
        screen_elements = []
        
        for element in ui_elements:
            # Skip elements with low confidence
            if element.get('confidence', 0) < 0.6:
                continue
                
            element_type = element.get('type', 'unknown')
            
            # Create formatted element
            formatted_element = {
                'element': element.get('text', '') or f"{element_type} element",
                'type': element_type,
                'name': element.get('text', '') or element_type,
            }
            
            # Add state if available
            if 'state' in element:
                formatted_element['state'] = element['state']
            
            # Add bounding box if available
            if 'bbox' in element:
                formatted_element['bbox'] = element['bbox']
            
            screen_elements.append(formatted_element)
        
        return screen_elements

@dataclass
class ScreenData:
    """Data class for screen capture results with enhanced LLaVA integration."""
    timestamp: float
    image: Optional[bytes] = None
    image_hash: Optional[str] = None
    text: Optional[str] = None  # OCR extracted text
    text_content: Optional[str] = None  # Same as text, for backward compatibility
    active_window: Optional[str] = None
    active_apps: Optional[list] = None
    error: Optional[str] = None
    llava_description: Optional[str] = None  # LLaVA's description of the screen
    screen_elements: Optional[List[Dict[str, Any]]] = field(default_factory=list)  # Detected UI elements
    visual_context: Optional[str] = None  # High-level context description from LLaVA

class ScreenCapture:
    def __init__(self):
        self.sct = None
        self.last_capture_time = 0
        self.min_capture_interval = 0.5  # Minimum time between captures
        self.image_cache = {}  # Cache for recent captures
        self.max_cache_size = 10  # Maximum number of cached images
        try:
            self.sct = mss.mss()
            logger.info("Screen capture initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing screen capture: {e}")
        
    async def capture(self):
        """Capture the current screen with rate limiting and caching"""
        try:
            current_time = time.time()
            if current_time - self.last_capture_time < self.min_capture_interval:
                # Return cached result if available
                if self.image_cache:
                    return list(self.image_cache.values())[-1]
                await asyncio.sleep(self.min_capture_interval)
            
            if not self.sct:
                self.sct = mss.mss()
                
            # Get primary monitor (usually monitor 1)
            monitor = self.sct.monitors[1]
            screenshot = self.sct.grab(monitor)
            
            # Convert to PIL Image
            img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
            
            # Calculate image hash for change detection
            img_hash = self._calculate_hash(img)
            
            # Compress and convert to base64
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='JPEG', quality=70, optimize=True)
            img_base64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
            
            result = {
                "timestamp": datetime.now().isoformat(),
                "image_data": img_base64,
                "image_hash": img_hash,
                "screen_size": img.size,
                "changed": img_hash != last_image_hash
            }
            
            # Update cache
            self.image_cache[img_hash] = result
            if len(self.image_cache) > self.max_cache_size:
                # Remove oldest entry
                self.image_cache.pop(next(iter(self.image_cache)))
            
            self.last_capture_time = current_time
            return result
            
        except Exception as e:
            logger.error(f"Error during screen capture: {e}")
            # Try to reinitialize
            try:
                if self.sct:
                    self.sct.close()
                self.sct = mss.mss()
                logger.info("Re-initialized screen capture")
            except Exception as re_e:
                logger.error(f"Failed to reinitialize screen capture: {re_e}")
            return None

class FixedScreenSensor:
    """
    Captures screenshots for LLaVA processing with enhanced image analysis.
    Runs in a background thread at specified intervals.
    Integrates with LLaVA for detailed screen content analysis.
    """
    
    def __init__(self, llava_url="http://localhost:11434"):
        self.interval = 2.0  # Default interval
        self.sct = None
        self.last_data: Optional[ScreenData] = None
        self.cache_dir = "cache/screen_sensor"
        self.cache_file = f"{self.cache_dir}/last_screen.json"
        self.unchanged_count = 0
        self.max_unchanged = 5  # Skip processing after 5 unchanged frames
        
        # LLaVA integration settings
        self.llava_url = llava_url
        self.llava_endpoint = f"{llava_url}/api/chat"
        self.llava_model = "llava"  # The model name for LLaVA in Ollama
        self.use_llava = True  # Enable/disable LLaVA analysis
        self.llava_timeout = 15  # Reduced timeout from 60 to 15 seconds
        self.llava_retry_count = 0
        self.max_llava_retries = 2  # Reduced from 3 to 2 retries
        self.llava_backoff_time = 2  # Reduced initial backoff time from 5 to 2 seconds
        
        # Alternative analysis settings
        self.use_alternative_analysis = True  # Enable local computer vision analysis
        self.always_run_alternative = False  # Changed to False - only run when LLaVA fails
        self.hybrid_mode = False  # Changed to False - use either LLaVA or alternative, not both
        
        # Initialize alternative analyzer
        self.alt_analyzer = AlternativeScreenAnalyzer()
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Load last screen data from cache
        self._load_cache()
        
        self.latest_image = None
        self.running = False
        self.thread = None
        
        # Error tracking
        self.error_count = 0
        self.max_errors = 5
        self.error_reset_time = 300  # 5 minutes
        self.last_error_time = 0
        
        # Performance tracking
        self.processing_times = []
        self.max_processing_times = 10  # Keep track of last 10 processing times
        
        self.logger = logging.getLogger(__name__)
        self.has_images = False
        self.has_videos = False
        self._stop_event = threading.Event()
        self.sensor_type = "screen"
        self._last_update = time.time()
        
        # Create results directory if it doesn't exist
        self.results_dir = "results"
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Initialize screen capture immediately
        logger.info("Initializing screen capture in constructor...")
        try:
            self.sct = mss.mss()
            if self.sct:
                logger.info("Screen capture initialized successfully in constructor")
                monitors = self.sct.monitors
                logger.info(f"Found {len(monitors)} monitors: {monitors}")
            else:
                logger.error("Failed to initialize screen capture in constructor")
        except Exception as e:
            logger.error(f"Error initializing screen capture in constructor: {e}")
        
        # Initialize OCR settings
        self.ocr_config = {
            'lang': 'eng',
            'config': '--psm 3'  # Assume a single uniform block of text
        }
    
    def _test_llava_connection(self):
        """Test connection to LLaVA service"""
        try:
            response = requests.get(f"{self.llava_url}/api/version", timeout=2)
            if response.status_code == 200:
                logger.info(f"Successfully connected to Ollama API at {self.llava_url}")
                self.use_llava = True
            else:
                logger.warning(f"Failed to connect to Ollama API at {self.llava_url}: {response.status_code}")
                self.use_llava = False
        except Exception as e:
            logger.warning(f"Error connecting to LLaVA service: {e}")
            self.use_llava = False
    
    def _extract_text(self, image: Image.Image) -> str:
        """Extract text from image using OCR with enhanced processing"""
        try:
            # Convert image to grayscale for better OCR
            gray_image = image.convert('L')
            
            # Apply some image processing to improve OCR results
            # Resizing can improve OCR quality for some texts
            width, height = gray_image.size
            if width > 1920:  # Resizing very large images can help OCR
                ratio = 1920 / width
                new_size = (int(width * ratio), int(height * ratio))
                gray_image = gray_image.resize(new_size, Image.LANCZOS)
            
            # Convert to numpy array for OpenCV processing
            img_np = np.array(gray_image)
            
            # Apply adaptive thresholding for better text extraction
            # This helps with varying lighting conditions
            try:
                # Use adaptive thresholding to deal with varying background
                thresholded = cv2.adaptiveThreshold(
                    img_np, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                    cv2.THRESH_BINARY, 11, 2
                )
                
                # Noise removal
                kernel = np.ones((1, 1), np.uint8)
                opening = cv2.morphologyEx(thresholded, cv2.MORPH_OPEN, kernel)
                
                # Convert back to PIL for pytesseract
                enhanced_image = Image.fromarray(opening)
            except Exception as e:
                logger.warning(f"Error in image enhancement, using original: {e}")
                enhanced_image = gray_image
            
            # Use pytesseract to extract text
            data = pytesseract.image_to_data(enhanced_image, output_type=Output.DICT, 
                                            config='--psm 11 --oem 3')
            
            # Combine all text blocks with better confidence filtering
            text_blocks = []
            for i in range(len(data['text'])):
                # Higher confidence threshold of 70% instead of 60%
                if int(data['conf'][i]) > 70 and data['text'][i].strip():
                    text_blocks.append(data['text'][i])
            
            result = ' '.join(text_blocks)
            logger.info(f"OCR extracted {len(text_blocks)} text blocks, total length: {len(result)}")
            return result
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return ""
            
    async def _analyze_with_alternative_methods(self, image: Image.Image) -> Dict[str, Any]:
        """
        Analyze the screen image using local computer vision techniques
        
        This method serves as an alternative to LLaVA for screen analysis,
        using computer vision techniques that run entirely locally.
        
        Args:
            image: The screen image to analyze
            
        Returns:
            Dict containing analysis results
        """
        try:
            logger.info("Performing alternative screen analysis with local computer vision")
            
            # Use the alternative analyzer
            analysis = self.alt_analyzer.analyze_screen(image)
            
            # Log results
            logger.info(f"Alternative analysis complete: {len(analysis.get('screen_elements', []))} UI elements detected")
            if 'application' in analysis and analysis['application'].get('name') != 'unknown':
                logger.info(f"Detected application: {analysis['application'].get('name')}")
                
            return analysis
        except Exception as e:
            logger.error(f"Error in alternative screen analysis: {e}")
            logger.error(traceback.format_exc())
            return {
                "analysis_method": "local_cv_error",
                "error": str(e),
                "llava_description": f"Error analyzing screen: {str(e)}",
                "screen_elements": [],
                "visual_context": ""
            }
            
    async def _analyze_with_llava(self, image: Image.Image) -> Dict[str, Any]:
        """Analyze screen with LLaVA with enhanced error handling and fallbacks"""
        if not self.use_llava:
            logger.info("LLaVA analysis disabled, skipping")
            return None
            
        try:
            start_time = time.time()
            
            # Check if we should retry LLaVA based on error count and backoff
            if self.llava_retry_count >= self.max_llava_retries:
                logger.warning("Max LLaVA retries reached, falling back to alternative analysis")
                self.use_llava = False
                return None
                
            # Convert image to base64
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            # Prepare LLaVA prompt
            prompt = {
                "model": self.llava_model,
                "messages": [
                    {
                        "role": "user",
                        "content": "Analyze this screen capture and provide: 1) A detailed description of the content, 2) List of UI elements and their states, 3) Any text content visible, 4) The main application or context. Format the response as JSON with these fields: description, elements, text_content, application."
                    }
                ],
                "stream": False,
                "images": [img_base64]
            }
            
            # Make request to LLaVA with timeout
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.llava_endpoint,
                    json=prompt,
                    timeout=self.llava_timeout
                ) as response:
                    if response.status != 200:
                        raise Exception(f"LLaVA API returned status {response.status}")
                        
                    result = await response.json()
                    
            # Process LLaVA response
            if not result or 'message' not in result:
                raise Exception("Invalid response from LLaVA")
                
            # Parse LLaVA response
            try:
                content = result['message']['content']
                analysis = json.loads(content)
            except json.JSONDecodeError:
                # If response isn't valid JSON, try to extract structured data
                analysis = self._parse_llava_text_response(content)
            
            # Reset error tracking on success
            self.llava_retry_count = 0
            self.error_count = 0
            
            # Track processing time
            processing_time = time.time() - start_time
            self.processing_times.append(processing_time)
            if len(self.processing_times) > self.max_processing_times:
                self.processing_times.pop(0)
            
            return analysis
            
        except asyncio.TimeoutError:
            logger.warning("LLaVA analysis timed out")
            self.llava_retry_count += 1
            await asyncio.sleep(self.llava_backoff_time * (2 ** self.llava_retry_count))
            return None
            
        except Exception as e:
            logger.error(f"Error in LLaVA analysis: {e}")
            self.llava_retry_count += 1
            self.error_count += 1
            
            # Check if we should disable LLaVA temporarily
            if self.error_count >= self.max_errors:
                logger.warning("Too many errors, temporarily disabling LLaVA")
                self.use_llava = False
                self.last_error_time = time.time()
            
            return None

    def _parse_llava_text_response(self, content: str) -> Dict[str, Any]:
        """Parse unstructured LLaVA response into structured data"""
        try:
            # Initialize result structure
            result = {
                "description": "",
                "elements": [],
                "text_content": "",
                "application": {"name": "unknown", "confidence": 0.0}
            }
            
            # Extract description
            if "description:" in content.lower():
                desc_parts = content.split("description:", 1)[1].split("\n", 1)
                result["description"] = desc_parts[0].strip()
            
            # Extract elements
            if "elements:" in content.lower():
                elements_text = content.split("elements:", 1)[1]
                if "text_content:" in elements_text:
                    elements_text = elements_text.split("text_content:", 1)[0]
                elements = elements_text.strip().split("\n")
                for element in elements:
                    if element.strip():
                        result["elements"].append({
                            "name": element.strip(),
                            "type": "unknown",
                            "confidence": 0.7
                        })
            
            # Extract text content
            if "text_content:" in content.lower():
                text_parts = content.split("text_content:", 1)[1]
                if "application:" in text_parts:
                    text_parts = text_parts.split("application:", 1)[0]
                result["text_content"] = text_parts.strip()
            
            # Extract application
            if "application:" in content.lower():
                app_parts = content.split("application:", 1)[1].strip()
                result["application"]["name"] = app_parts.split("\n")[0].strip()
                result["application"]["confidence"] = 0.8
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing LLaVA text response: {e}")
            return {
                "description": content,
                "elements": [],
                "text_content": "",
                "application": {"name": "unknown", "confidence": 0.0}
            }

    def _load_cache(self):
        """Load screen data from cache with proper handling of new LLaVA fields"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    if data:
                        # Handle base64 encoded image data
                        image_data = data.get('image')
                        if image_data and isinstance(image_data, str):
                            try:
                                image_bytes = base64.b64decode(image_data)
                            except Exception as e:
                                logger.warning(f"Error decoding image from cache: {e}")
                                image_bytes = None
                        else:
                            image_bytes = None
                            
                        # Create ScreenData object with all fields including LLaVA analysis
                        self.last_data = ScreenData(
                            timestamp=data['timestamp'],
                            image=image_bytes,
                            image_hash=data.get('image_hash'),
                            text=data.get('text'),
                            text_content=data.get('text_content'),
                            active_window=data.get('active_window'),
                            active_apps=data.get('active_apps', []),
                            error=data.get('error'),
                            llava_description=data.get('llava_description'),
                            screen_elements=data.get('screen_elements', []),
                            visual_context=data.get('visual_context')
                        )
                        
                        # Log successful load
                        has_llava = bool(data.get('llava_description'))
                        logger.info(f"Loaded screen cache from {self.cache_file} " +
                                   f"(contains LLaVA data: {has_llava})")
        except Exception as e:
            logger.warning(f"Failed to load screen cache: {e}")

    def _save_cache(self, data: ScreenData):
        """Save screen data to cache with proper handling of binary data and LLaVA results"""
        try:
            # Convert to dict for serialization
            cache_data = asdict(data)
            
            # Handle binary image data: encode as base64 for storage
            if data.image:
                try:
                    cache_data['image'] = base64.b64encode(data.image).decode('utf-8')
                except Exception as e:
                    logger.warning(f"Error encoding image for cache: {e}")
                    cache_data['image'] = None
            
            # Ensure all LLaVA fields are properly serializable
            if not cache_data.get('llava_description'):
                cache_data['llava_description'] = ""
                
            if not cache_data.get('visual_context'):
                cache_data['visual_context'] = ""
                
            if not cache_data.get('screen_elements') or not isinstance(cache_data['screen_elements'], list):
                cache_data['screen_elements'] = []
            
            # Save to file with pretty formatting for readability
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
            logger.debug(f"Saved screen cache to {self.cache_file}, size: {os.path.getsize(self.cache_file)} bytes")
        except Exception as e:
            logger.warning(f"Failed to save screen cache: {e}")

    async def initialize(self):
        """Initialize the sensor with proper error handling and retries"""
        max_retries = 3
        retry_delay = 2.0
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Initializing ScreenSensor (attempt {attempt + 1}/{max_retries})")
                
                # Initialize screen capture with explicit monitor selection
                self.sct = mss.mss()
                if not self.sct:
                    raise Exception("Failed to initialize mss")
                
                # Get monitor information
                monitors = self.sct.monitors
                if not monitors:
                    raise Exception("No monitors found")
                
                # Use primary monitor (usually index 1)
                primary_monitor = monitors[1]
                logger.info(f"Using primary monitor: {primary_monitor}")
                
                # Test capture
                test_screenshot = self.sct.grab(primary_monitor)
                if not test_screenshot:
                    raise Exception("Failed to capture test screenshot")
                
                test_image = Image.frombytes('RGB', test_screenshot.size, test_screenshot.rgb)
                if not test_image:
                    raise Exception("Failed to convert screenshot to image")
                
                logger.info("ScreenSensor initialized successfully")
                return True
                
            except Exception as e:
                logger.error(f"ScreenSensor initialization failed (attempt {attempt + 1}): {str(e)}")
                if self.sct:
                    try:
                        self.sct.close()
                    except:
                        pass
                    self.sct = None
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error("ScreenSensor initialization failed after all retries")
                    return False

    def _calculate_image_hash(self, image: Image.Image) -> str:
        """Calculate a hash of the image for change detection"""
        return hashlib.md5(image.tobytes()).hexdigest()

    def _should_process_image(self, current_time: float, image_hash: str) -> bool:
        """Determine if image should be processed based on various factors"""
        if self.last_data and image_hash == self.last_data.image_hash:
            self.unchanged_count += 1
            if self.unchanged_count >= self.max_unchanged:
                return False
        else:
            self.unchanged_count = 0
            
        return True

    async def capture_screen(self) -> ScreenData:
        """Capture and process screen content with enhanced error handling and fallbacks"""
        try:
            current_time = time.time()
            
            # Check if we should re-enable LLaVA after error timeout
            if not self.use_llava and (current_time - self.last_error_time) > self.error_reset_time:
                logger.info("Re-enabling LLaVA after error timeout")
                self.use_llava = True
                self.error_count = 0
                self.llava_retry_count = 0
            
            # Ensure screen capture is initialized
            if not self.sct:
                logger.error("Screen capture not initialized")
                raise Exception("Screen capture not initialized")
            
            # Get primary monitor
            monitors = self.sct.monitors
            if not monitors:
                raise Exception("No monitors found")
            primary_monitor = monitors[1]
            
            # Capture screen
            screenshot = self.sct.grab(primary_monitor)
            if not screenshot:
                raise Exception("Failed to capture screenshot")
                
            image = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
            if not image:
                raise Exception("Failed to convert screenshot to image")
            
            # Calculate image hash
            image_hash = self._calculate_image_hash(image)
            
            # Check if we should process this image
            if not self._should_process_image(current_time, image_hash):
                if self.last_data:
                    return self.last_data
                return ScreenData(timestamp=current_time)
            
            # Create new screen data
            screen_data = ScreenData(
                timestamp=current_time,
                image_hash=image_hash
            )
            
            # Extract text using OCR
            screen_data.text = self._extract_text(image)
            screen_data.text_content = screen_data.text
            
            # Get window info
            window_info = self._get_window_info()
            screen_data.active_window = window_info.get('active_window', '')
            screen_data.active_apps = window_info.get('active_apps', [])
            
            # Run analysis in parallel
            analysis_tasks = []
            if self.use_llava:
                analysis_tasks.append(self._analyze_with_llava(image))
            if self.use_alternative_analysis:
                analysis_tasks.append(self._analyze_with_alternative_methods(image))
            
            # Wait for analysis results
            results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            # Process results
            if self.hybrid_mode:
                # Handle hybrid mode results
                llava_analysis = None
                alt_analysis = None
                
                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"Analysis failed: {result}")
                        continue
                    if result and 'llava_description' in result:
                        llava_analysis = result
                    else:
                        alt_analysis = result
                
                # Combine results
                if llava_analysis:
                    screen_data.llava_description = llava_analysis.get('llava_description', '')
                    screen_data.screen_elements.extend(llava_analysis.get('screen_elements', []))
                
                if alt_analysis:
                    # Add alternative analysis results
                    alt_elements = alt_analysis.get('screen_elements', [])
                    for alt_elem in alt_elements:
                        # Check for duplicates
                        is_duplicate = False
                        for existing_elem in screen_data.screen_elements:
                            if self._is_similar_element(alt_elem, existing_elem):
                                is_duplicate = True
                                break
                        if not is_duplicate:
                            screen_data.screen_elements.append(alt_elem)
            else:
                # Use first successful result
                for result in results:
                    if not isinstance(result, Exception) and result:
                        if 'llava_description' in result:
                            screen_data.llava_description = result.get('llava_description', '')
                        screen_data.screen_elements.extend(result.get('screen_elements', []))
                        break
            
            # Update cache
            self._save_cache(screen_data)
            self.last_data = screen_data
            
            return screen_data
            
        except Exception as e:
            logger.error(f"Error capturing screen: {e}")
            logger.error(traceback.format_exc())
            return ScreenData(
                timestamp=time.time(),
                error=str(e)
            )

    def _is_similar_element(self, elem1: Dict[str, Any], elem2: Dict[str, Any]) -> bool:
        """Check if two UI elements are similar enough to be considered the same"""
        # Compare names
        name1 = elem1.get('name', '').lower()
        name2 = elem2.get('name', '').lower()
        
        if name1 and name2:
            # Check for exact match
            if name1 == name2:
                return True
            # Check for substring match
            if name1 in name2 or name2 in name1:
                return True
            # Check for high similarity
            if self._calculate_similarity(name1, name2) > 0.8:
                return True
        
        # Compare types
        type1 = elem1.get('type', '').lower()
        type2 = elem2.get('type', '').lower()
        if type1 and type2 and type1 == type2:
            # If types match and names are similar, consider them the same
            if self._calculate_similarity(name1, name2) > 0.6:
                return True
        
        return False

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity using Levenshtein distance"""
        if not str1 or not str2:
            return 0.0
            
        # Convert to lowercase for comparison
        str1 = str1.lower()
        str2 = str2.lower()
        
        # Calculate Levenshtein distance
        if len(str1) < len(str2):
            str1, str2 = str2, str1
            
        if len(str2) == 0:
            return 0.0
            
        previous_row = range(len(str2) + 1)
        for i, c1 in enumerate(str1):
            current_row = [i + 1]
            for j, c2 in enumerate(str2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
            
        # Calculate similarity ratio
        max_len = max(len(str1), len(str2))
        if max_len == 0:
            return 1.0
        return 1.0 - (previous_row[-1] / max_len)

    def _get_window_info(self) -> Dict[str, Any]:
        """Get information about the active window and applications with fallbacks"""
        active_window = ""
        active_apps = []
        
        try:
            # Try multiple AppleScript approaches for active window
            scripts = [
                # Try getting frontmost window
                'tell application "System Events" to get name of first window of first process whose frontmost is true',
                # Try getting focused window
                'tell application "System Events" to get name of window 1 of process 1 whose frontmost is true',
                # Try getting active window
                'tell application "System Events" to get name of window 1 of application process (name of first process whose frontmost is true)'
            ]
            
            for script in scripts:
                try:
                    result = os.popen(f'osascript -e \'{script}\'').read().strip()
                    if result and not result.startswith("execution error"):
                        active_window = result
                        break
                except Exception:
                    continue
            
            # Get list of active applications with multiple approaches
            app_scripts = [
                # Get visible processes
                'tell application "System Events" to get name of every process whose visible is true',
                # Get running applications
                'tell application "System Events" to get name of every process whose background only is false',
                # Get processes with windows
                'tell application "System Events" to get name of every process whose exists window 1'
            ]
            
            for script in app_scripts:
                try:
                    apps_raw = os.popen(f'osascript -e \'{script}\'').read().strip()
                    if apps_raw and not apps_raw.startswith("execution error"):
                        active_apps = [app.strip() for app in apps_raw.split(',') if app.strip()]
                        if active_apps:
                            break
                except Exception:
                    continue
            
        except Exception as e:
            logger.warning(f"Error getting window info with AppleScript: {e}")
        
        # If AppleScript fails, try using 'ps' to get running processes
        if not active_apps:
            try:
                logger.debug("Falling back to ps command for process info")
                # Get visible applications using ps with better filtering
                ps_output = os.popen("ps -e -o comm= | grep -v 'Helper\\|daemon\\|update\\|agent\\|grep\\|ps\\|sort\\|uniq' | sort | uniq").read()
                if ps_output:
                    # Extract app names from paths and filter out system processes
                    ps_apps = []
                    for line in ps_output.strip().split('\n'):
                        app_name = os.path.basename(line.strip())
                        if app_name and app_name not in ['grep', 'ps', 'sort', 'uniq', 'sh', 'bash', 'zsh']:
                            ps_apps.append(app_name)
                    
                    # Use these as fallback
                    active_apps = ps_apps
            except Exception as e:
                logger.warning(f"Error getting process info with ps: {e}")
        
        # If we still don't have active apps, try one last approach with lsappinfo
        if not active_apps:
            try:
                logger.debug("Trying lsappinfo for process info")
                lsappinfo_output = os.popen("lsappinfo front").read().strip()
                if lsappinfo_output:
                    app_name = lsappinfo_output.split('"')[1] if '"' in lsappinfo_output else lsappinfo_output
                    if app_name:
                        active_apps = [app_name]
            except Exception as e:
                logger.warning(f"Error getting process info with lsappinfo: {e}")
        
        # Return window info with whatever we could get
        result = {
            'active_window': active_window,
            'active_apps': active_apps
        }
        
        logger.debug(f"Window info: {result}")
        return result

    async def get_current_state(self) -> Dict[str, Any]:
        """Get current screen state with enhanced application-aware LLaVA analysis results"""
        try:
            screen_data = await self.capture_screen()
            
            # Create complete state including enhanced LLaVA analysis with application awareness
            state = {
                'timestamp': screen_data.timestamp,
                'image_hash': screen_data.image_hash,
                'text': screen_data.text,
                'active_window': screen_data.active_window,
                'active_apps': screen_data.active_apps,
                'error': screen_data.error,
                # Include basic LLaVA results
                'llava_description': screen_data.llava_description,
                'screen_elements': screen_data.screen_elements,
                'visual_context': screen_data.visual_context,
                # Add a flag indicating if LLaVA analysis was performed
                'has_llava_data': bool(screen_data.llava_description)
            }
            
            # Add application-specific data if available
            application_data = getattr(screen_data, 'application', None)
            if application_data:
                state['application'] = application_data
            
            # Add email-specific data if available
            email_data = getattr(screen_data, 'email_data', None)
            if email_data:
                state['email_data'] = email_data
                
            # Add form-specific data if available
            form_data = getattr(screen_data, 'form_data', None)
            if form_data:
                state['form_data'] = form_data
                
            # Determine if this state represents an important user action
            # This helps memory system prioritize significant interactions
            is_significant_action = False
            
            # Check if we have detected a specific workflow stage
            if application_data and application_data.get('workflow_stage'):
                is_significant_action = True
                
            # Check if we have identified a specific application view
            if application_data and application_data.get('view'):
                is_significant_action = True
                
            # Check if this is email interaction
            if email_data:
                is_significant_action = True
                
            # Check if this is form interaction
            if form_data:
                is_significant_action = True
                
            # Add significance flag to help memory system prioritize this state
            state['is_significant_action'] = is_significant_action
            
            return state
        except Exception as e:
            logger.error(f"Error getting current state: {e}")
            return {
                'timestamp': time.time(),
                'error': str(e),
                'has_llava_data': False
            }

    async def cleanup(self):
        """Clean up resources"""
        try:
            logger.info("Cleaning up screen sensor...")
            self.running = False
            if self.sct:
                self.sct.close()
            logger.info("Screen sensor cleaned up successfully")
        except Exception as e:
            logger.error(f"Error cleaning up screen sensor: {e}")

async def main():
    """Main function."""
    sensor = FixedScreenSensor()
    if not await sensor.initialize():
        logger.error("Failed to initialize screen sensor")
        return
    
    logger.info("Screen sensor initialized")
    
    try:
        while True:
            try:
                # Get current state
                state = await sensor.get_current_state()
                
                # Log heartbeat occasionally
                if int(time.time()) % 60 == 0:  # Log every minute
                    logger.info("Screen sensor heartbeat")
                
                # Sleep
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(5)
    except KeyboardInterrupt:
        logger.info("Stopping screen sensor...")
    finally:
        await sensor.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 