#!/usr/bin/env python3
"""
Precise Input Field Detector - More accurate detection of actual input fields
"""

import pyautogui
import cv2
import numpy as np
import time
import logging
from PIL import Image, ImageDraw, ImageFont
from typing import Tuple, List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PreciseElement:
    """A precisely detected UI element"""
    element_type: str
    coordinates: Tuple[int, int]
    confidence: float
    description: str
    bounds: Tuple[int, int, int, int]
    detection_method: str
    brightness: float
    uniformity: float

class PreciseInputDetector:
    """More precise input field detection system"""
    
    def __init__(self):
        self.screen_width, self.screen_height = pyautogui.size()
        logger.info(f"Precise detector initialized for {self.screen_width}x{self.screen_height}")
    
    def detect_precise_input_fields(self, step_description: str) -> Tuple[int, int]:
        """Detect input fields with higher precision"""
        
        print(f"🎯 PRECISE DETECTION: {step_description}")
        
        # Take screenshot
        screenshot = pyautogui.screenshot()
        img_array = np.array(screenshot)
        img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        candidates = []
        
        # Method 1: Template matching for common input field patterns
        candidates.extend(self._detect_by_template_matching(img_gray))
        
        # Method 2: Improved edge detection with better filtering
        candidates.extend(self._detect_by_improved_edges(img_gray))
        
        # Method 3: Color-based detection for white/light input fields
        candidates.extend(self._detect_by_color_analysis(img_array))
        
        # Method 4: Text-aware detection (look for cursor or placeholder text patterns)
        candidates.extend(self._detect_by_text_patterns(img_gray))
        
        # Select the best candidate
        best_candidate = self._select_best_candidate(candidates, step_description)
        
        if best_candidate:
            # Create verification image
            self._create_precise_verification(best_candidate, screenshot, step_description)
            return best_candidate.coordinates
        else:
            print("❌ No precise input fields detected")
            # Smart fallback based on common input field locations
            return self._smart_fallback(step_description)
    
    def _detect_by_template_matching(self, img_gray) -> List[PreciseElement]:
        """Detect using template matching for input field characteristics"""
        candidates = []
        
        try:
            # Create a template for typical input field appearance
            # Input fields are typically rectangular with slight borders
            template_height = 35
            template_width = 200
            
            # Create template - white rectangle with gray border
            template = np.ones((template_height, template_width), dtype=np.uint8) * 240
            template[0:2, :] = 180  # Top border
            template[-2:, :] = 180  # Bottom border  
            template[:, 0:2] = 180  # Left border
            template[:, -2:] = 180  # Right border
            
            # Match template
            result = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= 0.3)
            
            for pt in zip(*locations[::-1]):
                x, y = pt
                w, h = template_width, template_height
                center_x = x + w // 2
                center_y = y + h // 2
                
                # Check if this looks like a real input field
                confidence = self._calculate_precise_confidence(img_gray, x, y, w, h)
                
                if confidence > 0.6:
                    candidates.append(PreciseElement(
                        element_type="input_field",
                        coordinates=(center_x, center_y),
                        confidence=confidence,
                        description=f"Template input ({w}x{h})",
                        bounds=(x, y, x+w, y+h),
                        detection_method="template_matching",
                        brightness=np.mean(img_gray[y:y+h, x:x+w]),
                        uniformity=1.0 - np.std(img_gray[y:y+h, x:x+w]) / 255.0
                    ))
                    
        except Exception as e:
            logger.warning(f"Template matching failed: {e}")
        
        return candidates
    
    def _detect_by_improved_edges(self, img_gray) -> List[PreciseElement]:
        """Improved edge detection specifically for input fields"""
        candidates = []
        
        try:
            # Use adaptive threshold for better edge detection
            adaptive_thresh = cv2.adaptiveThreshold(
                img_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Find contours
            contours, _ = cv2.findContours(adaptive_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                
                # Input field size constraints
                if 2000 < area < 40000:
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    
                    # Input fields are wide and not too tall
                    if 3.0 < aspect_ratio < 15.0 and 20 < h < 60:
                        center_x = x + w // 2
                        center_y = y + h // 2
                        
                        # Additional validation
                        confidence = self._calculate_precise_confidence(img_gray, x, y, w, h)
                        
                        if confidence > 0.5:
                            candidates.append(PreciseElement(
                                element_type="input_field",
                                coordinates=(center_x, center_y),
                                confidence=confidence,
                                description=f"Edge input ({w}x{h})",
                                bounds=(x, y, x+w, y+h),
                                detection_method="improved_edges",
                                brightness=np.mean(img_gray[y:y+h, x:x+w]),
                                uniformity=1.0 - np.std(img_gray[y:y+h, x:x+w]) / 255.0
                            ))
                            
        except Exception as e:
            logger.warning(f"Improved edge detection failed: {e}")
        
        return candidates
    
    def _detect_by_color_analysis(self, img_array) -> List[PreciseElement]:
        """Detect input fields by color characteristics"""
        candidates = []
        
        try:
            # Convert to HSV for better color analysis
            img_hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
            img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Look for light areas (typical input field backgrounds)
            light_mask = cv2.inRange(img_gray, 200, 255)
            
            # Also look for medium-light areas  
            medium_mask = cv2.inRange(img_gray, 150, 220)
            
            combined_mask = cv2.bitwise_or(light_mask, medium_mask)
            
            # Find contours in light areas
            contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                
                if 1500 < area < 50000:
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    
                    if 2.5 < aspect_ratio < 20.0 and 25 < h < 80:
                        center_x = x + w // 2
                        center_y = y + h // 2
                        
                        confidence = self._calculate_precise_confidence(img_gray, x, y, w, h)
                        
                        if confidence > 0.4:
                            candidates.append(PreciseElement(
                                element_type="input_field",
                                coordinates=(center_x, center_y),
                                confidence=confidence,
                                description=f"Color input ({w}x{h})",
                                bounds=(x, y, x+w, y+h),
                                detection_method="color_analysis",
                                brightness=np.mean(img_gray[y:y+h, x:x+w]),
                                uniformity=1.0 - np.std(img_gray[y:y+h, x:x+w]) / 255.0
                            ))
                            
        except Exception as e:
            logger.warning(f"Color analysis failed: {e}")
        
        return candidates
    
    def _detect_by_text_patterns(self, img_gray) -> List[PreciseElement]:
        """Detect input fields by looking for text cursor or placeholder patterns"""
        candidates = []
        
        try:
            # Look for vertical lines (text cursors)
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 15))
            vertical_lines = cv2.morphologyEx(img_gray, cv2.MORPH_OPEN, vertical_kernel)
            
            # Find areas around vertical lines that might be input fields
            contours, _ = cv2.findContours(vertical_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Expand area around potential cursor to find input field
                expand_x = max(0, x - 100)
                expand_y = max(0, y - 10)
                expand_w = min(img_gray.shape[1] - expand_x, w + 200)
                expand_h = min(img_gray.shape[0] - expand_y, h + 20)
                
                if 2000 < expand_w * expand_h < 40000:
                    aspect_ratio = expand_w / expand_h
                    
                    if 3.0 < aspect_ratio < 20.0:
                        center_x = expand_x + expand_w // 2
                        center_y = expand_y + expand_h // 2
                        
                        confidence = self._calculate_precise_confidence(img_gray, expand_x, expand_y, expand_w, expand_h)
                        
                        if confidence > 0.3:
                            candidates.append(PreciseElement(
                                element_type="input_field",
                                coordinates=(center_x, center_y),
                                confidence=confidence,
                                description=f"Text cursor input ({expand_w}x{expand_h})",
                                bounds=(expand_x, expand_y, expand_x+expand_w, expand_y+expand_h),
                                detection_method="text_patterns",
                                brightness=np.mean(img_gray[expand_y:expand_y+expand_h, expand_x:expand_x+expand_w]),
                                uniformity=1.0 - np.std(img_gray[expand_y:expand_y+expand_h, expand_x:expand_x+expand_w]) / 255.0
                            ))
                            
        except Exception as e:
            logger.warning(f"Text pattern detection failed: {e}")
        
        return candidates
    
    def _calculate_precise_confidence(self, img_gray, x, y, w, h) -> float:
        """Calculate more precise confidence score"""
        
        confidence = 0.3  # Base confidence
        
        try:
            roi = img_gray[y:y+h, x:x+w]
            if roi.size == 0:
                return 0.0
            
            # Check brightness (input fields are often light)
            avg_brightness = np.mean(roi)
            if 180 < avg_brightness < 255:
                confidence += 0.3
            elif 120 < avg_brightness < 180:
                confidence += 0.2
            
            # Check uniformity (input fields have consistent color)
            brightness_std = np.std(roi)
            if brightness_std < 15:
                confidence += 0.25
            elif brightness_std < 30:
                confidence += 0.15
            
            # Check aspect ratio
            aspect_ratio = w / h
            if 4.0 < aspect_ratio < 12.0:
                confidence += 0.25
            elif 2.5 < aspect_ratio < 20.0:
                confidence += 0.15
            
            # Check size appropriateness
            if 3000 < w * h < 20000:
                confidence += 0.2
            elif 1000 < w * h < 40000:
                confidence += 0.1
            
            # Position bonus (input fields often in upper-middle area)
            center_y = y + h // 2
            if center_y < self.screen_height * 0.6:
                confidence += 0.1
            
            return min(1.0, confidence)
            
        except Exception as e:
            logger.warning(f"Confidence calculation failed: {e}")
            return 0.0
    
    def _select_best_candidate(self, candidates: List[PreciseElement], step_description: str) -> PreciseElement:
        """Select the best candidate with more sophisticated logic"""
        
        if not candidates:
            return None
        
        # Remove duplicates (candidates too close to each other)
        filtered_candidates = []
        for candidate in candidates:
            is_duplicate = False
            for existing in filtered_candidates:
                distance = abs(candidate.coordinates[0] - existing.coordinates[0]) + abs(candidate.coordinates[1] - existing.coordinates[1])
                if distance < 50:  # Too close, likely duplicate
                    if candidate.confidence > existing.confidence:
                        filtered_candidates.remove(existing)
                        break
                    else:
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                filtered_candidates.append(candidate)
        
        # Sort by combined score
        def combined_score(candidate):
            score = candidate.confidence
            
            # Bonus for being in expected search box location (upper area)
            if candidate.coordinates[1] < self.screen_height * 0.4:
                score += 0.2
            
            # Bonus for appropriate brightness
            if 150 < candidate.brightness < 240:
                score += 0.1
            
            # Bonus for high uniformity
            if candidate.uniformity > 0.8:
                score += 0.1
            
            return score
        
        filtered_candidates.sort(key=combined_score, reverse=True)
        
        best = filtered_candidates[0]
        print(f"🎯 Selected: {best.description} at {best.coordinates} (confidence: {best.confidence:.2f})")
        
        return best
    
    def _smart_fallback(self, step_description: str) -> Tuple[int, int]:
        """Intelligent fallback based on step description and common patterns"""
        
        if "search" in step_description.lower():
            # Search boxes are typically in upper-center area
            return (self.screen_width // 2, self.screen_height // 4)
        else:
            # Generic input field location
            return (self.screen_width // 2, self.screen_height // 3)
    
    def _create_precise_verification(self, element: PreciseElement, screenshot: Image, step_description: str) -> str:
        """Create detailed verification image"""
        
        draw = ImageDraw.Draw(screenshot)
        x, y = element.coordinates
        
        # Color based on confidence
        if element.confidence > 0.8:
            color = 'lime'
        elif element.confidence > 0.6:
            color = 'yellow'
        else:
            color = 'orange'
        
        # Draw precise crosshair
        crosshair_size = 20
        line_width = 3
        
        # Main crosshairs
        draw.line([(x - crosshair_size, y), (x + crosshair_size, y)], fill=color, width=line_width)
        draw.line([(x, y - crosshair_size), (x, y + crosshair_size)], fill=color, width=line_width)
        
        # Draw element bounds
        if element.bounds != (0, 0, 0, 0):
            x1, y1, x2, y2 = element.bounds
            draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
        
        # Add detailed info
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 11)
        except:
            font = ImageFont.load_default()
        
        info_text = f"🎯 PRECISE DETECTION\nStep: {step_description[:20]}...\nMethod: {element.detection_method}\nCoords: {element.coordinates}\nConfidence: {element.confidence:.2f}\nBrightness: {element.brightness:.1f}\nUniformity: {element.uniformity:.2f}"
        
        # Position text intelligently
        text_x = max(10, x - 150) if x > self.screen_width // 2 else x + 30
        text_y = max(10, y - 80) if y > 100 else y + 30
        
        text_lines = info_text.split('\n')
        max_width = max(len(line) * 7 for line in text_lines)  # Approximate width
        text_height = len(text_lines) * 14
        
        # Background for text
        draw.rectangle([
            (text_x - 5, text_y - 5),
            (text_x + max_width + 10, text_y + text_height + 10)
        ], fill='black', outline='white', width=1)
        
        for i, line in enumerate(text_lines):
            draw.text((text_x, text_y + i * 14), line, fill='white', font=font)
        
        # Save with timestamp
        timestamp = int(time.time())
        filename = f"precise_detection_{element.detection_method}_{timestamp}.png"
        screenshot.save(filename)
        print(f"📸 Precise verification: {filename}")
        
        return filename

# Test the precise detector
if __name__ == "__main__":
    detector = PreciseInputDetector()
    coords = detector.detect_precise_input_fields("Search for 'test'")
    print(f"📍 Precise coordinates: {coords}")