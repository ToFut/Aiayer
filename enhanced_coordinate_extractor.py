#!/usr/bin/env python3
"""
Enhanced Coordinate Extraction and Visual Verification System
Provides precise coordinate calculation and visual verification before actions
"""

import asyncio
import cv2
import numpy as np
import logging
from PIL import Image, ImageGrab, ImageDraw, ImageFont
from typing import Dict, List, Any, Optional, Tuple
import time
import json
import base64
from io import BytesIO

logger = logging.getLogger(__name__)

class CoordinateExtractor:
    """
    Professional coordinate extraction with multiple verification methods
    """
    
    def __init__(self):
        self.verification_cache = {}
        self.last_screenshot = None
        self.confidence_threshold = 0.7
        
    async def extract_precise_coordinates(self, element: Dict[str, Any], screenshot: Optional[Image.Image] = None) -> Optional[Tuple[int, int]]:
        """
        Extract precise coordinates with multiple fallback methods
        """
        try:
            if screenshot is None:
                screenshot = ImageGrab.grab()
            
            self.last_screenshot = screenshot
            
            # Method 1: Direct bounding box coordinates
            coords = self._extract_from_bounding_box(element)
            if coords and await self._verify_coordinates(coords, element, screenshot):
                logger.info(f"✅ Coordinates from bounding box: {coords}")
                return coords
            
            # Method 2: OCR-based coordinate refinement
            coords = await self._extract_with_ocr_refinement(element, screenshot)
            if coords and await self._verify_coordinates(coords, element, screenshot):
                logger.info(f"✅ Coordinates from OCR refinement: {coords}")
                return coords
            
            # Method 3: Visual template matching
            coords = await self._extract_with_template_matching(element, screenshot)
            if coords and await self._verify_coordinates(coords, element, screenshot):
                logger.info(f"✅ Coordinates from template matching: {coords}")
                return coords
            
            # Method 4: Color-based detection
            coords = await self._extract_with_color_detection(element, screenshot)
            if coords and await self._verify_coordinates(coords, element, screenshot):
                logger.info(f"✅ Coordinates from color detection: {coords}")
                return coords
            
            # Method 5: Smart heuristic positioning
            coords = await self._extract_with_smart_heuristics(element, screenshot)
            if coords:
                logger.warning(f"⚠️ Using heuristic coordinates: {coords}")
                return coords
            
            logger.error(f"❌ Failed to extract coordinates for element: {element.get('element_text', 'unknown')}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting coordinates: {e}")
            return None
    
    def _extract_from_bounding_box(self, element: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        """Extract coordinates from bounding box data"""
        try:
            bbox = element.get("bounding_box")
            if not bbox:
                return None
            
            if isinstance(bbox, dict):
                x = bbox.get("x", 0)
                y = bbox.get("y", 0)
                width = bbox.get("width", 0)
                height = bbox.get("height", 0)
                
                if width > 0 and height > 0:
                    # Calculate center point
                    center_x = x + width // 2
                    center_y = y + height // 2
                    return (center_x, center_y)
            
            elif isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
                x, y, width, height = bbox[:4]
                center_x = x + width // 2
                center_y = y + height // 2
                return (center_x, center_y)
            
            return None
            
        except Exception as e:
            logger.debug(f"Bounding box extraction failed: {e}")
            return None
    
    async def _extract_with_ocr_refinement(self, element: Dict[str, Any], screenshot: Image.Image) -> Optional[Tuple[int, int]]:
        """Refine coordinates using OCR text detection"""
        try:
            import pytesseract
            
            element_text = element.get("element_text", "").strip()
            if not element_text:
                return None
            
            # Get OCR data with bounding boxes
            data = pytesseract.image_to_data(screenshot, output_type=pytesseract.Output.DICT)
            
            # Look for exact text matches
            for i in range(len(data['text'])):
                detected_text = data['text'][i].strip()
                confidence = int(data['conf'][i])
                
                if confidence > 50 and detected_text == element_text:
                    x = data['left'][i]
                    y = data['top'][i]
                    w = data['width'][i]
                    h = data['height'][i]
                    
                    center_x = x + w // 2
                    center_y = y + h // 2
                    return (center_x, center_y)
            
            # Look for partial matches with high confidence
            for i in range(len(data['text'])):
                detected_text = data['text'][i].strip().lower()
                confidence = int(data['conf'][i])
                
                if confidence > 70 and element_text.lower() in detected_text:
                    x = data['left'][i]
                    y = data['top'][i]
                    w = data['width'][i]
                    h = data['height'][i]
                    
                    center_x = x + w // 2
                    center_y = y + h // 2
                    return (center_x, center_y)
            
            return None
            
        except Exception as e:
            logger.debug(f"OCR refinement failed: {e}")
            return None
    
    async def _extract_with_template_matching(self, element: Dict[str, Any], screenshot: Image.Image) -> Optional[Tuple[int, int]]:
        """Extract coordinates using template matching"""
        try:
            # Convert to OpenCV format
            cv_image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            gray_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            element_type = element.get("element_type", "").lower()
            
            # Create templates based on element type
            if "button" in element_type:
                template = self._create_button_template(element)
            elif "text" in element_type:
                template = self._create_text_field_template(element)
            else:
                return None
            
            if template is None:
                return None
            
            # Perform template matching
            result = cv2.matchTemplate(gray_image, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val > 0.8:  # High confidence match
                x, y = max_loc
                h, w = template.shape
                center_x = x + w // 2
                center_y = y + h // 2
                return (center_x, center_y)
            
            return None
            
        except Exception as e:
            logger.debug(f"Template matching failed: {e}")
            return None
    
    async def _extract_with_color_detection(self, element: Dict[str, Any], screenshot: Image.Image) -> Optional[Tuple[int, int]]:
        """Extract coordinates using color-based detection"""
        try:
            # Convert to OpenCV format
            cv_image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            hsv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
            
            element_type = element.get("element_type", "").lower()
            
            # Define color ranges based on element type
            if "text_area" in element_type or "text_field" in element_type:
                # Look for white/light backgrounds (text areas)
                lower_bound = np.array([0, 0, 200])
                upper_bound = np.array([179, 30, 255])
            elif "button" in element_type:
                # Look for button-like colors (gray/blue)
                lower_bound = np.array([100, 50, 50])
                upper_bound = np.array([130, 255, 255])
            else:
                return None
            
            # Create mask and find contours
            mask = cv2.inRange(hsv_image, lower_bound, upper_bound)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Look for large rectangular areas
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                
                # Filter by size and aspect ratio
                if area > 5000 and w > 100 and h > 30:
                    aspect_ratio = w / h
                    if 1 < aspect_ratio < 20:  # Reasonable aspect ratio
                        center_x = x + w // 2
                        center_y = y + h // 2
                        return (center_x, center_y)
            
            return None
            
        except Exception as e:
            logger.debug(f"Color detection failed: {e}")
            return None
    
    async def _extract_with_smart_heuristics(self, element: Dict[str, Any], screenshot: Image.Image) -> Optional[Tuple[int, int]]:
        """Smart heuristic positioning based on element context"""
        try:
            width, height = screenshot.size
            element_type = element.get("element_type", "").lower()
            element_text = element.get("element_text", "").lower()
            app_context = element.get("app_context", "")
            
            # App-specific heuristics
            if app_context == "notepad" or "notepad" in element_text:
                # For notepad, text area is usually in the center-left
                return (int(width * 0.4), int(height * 0.5))
            
            # Element type heuristics
            if "text_area" in element_type:
                # Text areas are usually in the center
                return (int(width * 0.5), int(height * 0.4))
            elif "button" in element_type:
                if "ok" in element_text or "submit" in element_text:
                    return (int(width * 0.6), int(height * 0.8))
                elif "cancel" in element_text:
                    return (int(width * 0.4), int(height * 0.8))
                else:
                    return (int(width * 0.5), int(height * 0.7))
            elif "text_field" in element_type:
                return (int(width * 0.5), int(height * 0.3))
            
            # Default center position
            return (int(width * 0.5), int(height * 0.5))
            
        except Exception as e:
            logger.debug(f"Heuristic positioning failed: {e}")
            return (int(screenshot.size[0] * 0.5), int(screenshot.size[1] * 0.5))
    
    async def _verify_coordinates(self, coords: Tuple[int, int], element: Dict[str, Any], screenshot: Image.Image) -> bool:
        """Verify coordinates by analyzing the target area"""
        try:
            x, y = coords
            width, height = screenshot.size
            
            # Check if coordinates are within screen bounds
            if not (0 <= x < width and 0 <= y < height):
                logger.debug(f"Coordinates {coords} out of bounds for screen {width}x{height}")
                return False
            
            # Extract region around coordinates for analysis
            region_size = 50
            left = max(0, x - region_size)
            top = max(0, y - region_size)
            right = min(width, x + region_size)
            bottom = min(height, y + region_size)
            
            region = screenshot.crop((left, top, right, bottom))
            
            # Analyze the region to verify it matches expected element type
            verification_score = await self._analyze_target_region(region, element)
            
            return verification_score > 0.5
            
        except Exception as e:
            logger.debug(f"Coordinate verification failed: {e}")
            return False
    
    async def _analyze_target_region(self, region: Image.Image, element: Dict[str, Any]) -> float:
        """Analyze a region to verify it matches the expected element"""
        try:
            element_type = element.get("element_type", "").lower()
            
            # Convert to OpenCV for analysis
            cv_region = cv2.cvtColor(np.array(region), cv2.COLOR_RGB2BGR)
            gray_region = cv2.cvtColor(cv_region, cv2.COLOR_BGR2GRAY)
            
            score = 0.0
            
            # Check for text areas (white/light backgrounds)
            if "text" in element_type:
                # Calculate percentage of light pixels
                light_pixels = np.sum(gray_region > 200)
                total_pixels = gray_region.size
                light_ratio = light_pixels / total_pixels
                
                if light_ratio > 0.5:  # Mostly light background
                    score += 0.4
                
                # Check for text content using OCR
                try:
                    import pytesseract
                    text = pytesseract.image_to_string(region).strip()
                    if len(text) > 0:
                        score += 0.3
                except:
                    pass
            
            # Check for button-like features
            elif "button" in element_type:
                # Look for edges (buttons have defined borders)
                edges = cv2.Canny(gray_region, 50, 150)
                edge_ratio = np.sum(edges > 0) / edges.size
                
                if 0.1 < edge_ratio < 0.5:  # Moderate edge density
                    score += 0.3
                
                # Check for uniform color (buttons often have solid colors)
                std_dev = np.std(gray_region)
                if std_dev < 30:  # Low variation (uniform color)
                    score += 0.2
            
            # General clickable element verification
            # Check if the region looks interactive
            edges = cv2.Canny(gray_region, 30, 100)
            if np.sum(edges > 0) > 0:
                score += 0.1
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.debug(f"Region analysis failed: {e}")
            return 0.0
    
    def _create_button_template(self, element: Dict[str, Any]) -> Optional[np.ndarray]:
        """Create a button template for matching"""
        try:
            # Create a simple button template
            template = np.ones((30, 80), dtype=np.uint8) * 128  # Gray background
            cv2.rectangle(template, (2, 2), (77, 27), 200, 2)  # Border
            return template
        except:
            return None
    
    def _create_text_field_template(self, element: Dict[str, Any]) -> Optional[np.ndarray]:
        """Create a text field template for matching"""
        try:
            # Create a simple text field template
            template = np.ones((25, 150), dtype=np.uint8) * 255  # White background
            cv2.rectangle(template, (1, 1), (148, 23), 128, 1)  # Thin border
            return template
        except:
            return None
    
    async def create_verification_preview(self, coords: Tuple[int, int], element: Dict[str, Any], action: str, screenshot: Optional[Image.Image] = None) -> str:
        """
        Create a visual preview showing where the action will occur
        Returns base64 encoded image
        """
        try:
            if screenshot is None:
                screenshot = ImageGrab.grab()
            
            # Create a copy for drawing
            preview_image = screenshot.copy()
            draw = ImageDraw.Draw(preview_image)
            
            x, y = coords
            
            # Draw crosshair at the target location
            crosshair_size = 20
            color = (255, 0, 0)  # Red
            
            # Draw crosshair
            draw.line([x - crosshair_size, y, x + crosshair_size, y], fill=color, width=3)
            draw.line([x, y - crosshair_size, x, y + crosshair_size], fill=color, width=3)
            
            # Draw circle around target
            draw.ellipse([x - 10, y - 10, x + 10, y + 10], outline=color, width=2)
            
            # Add action label
            try:
                font = ImageFont.truetype("Arial.ttf", 16)
            except:
                font = ImageFont.load_default()
            
            label = f"{action.upper()} HERE"
            draw.text((x + 15, y - 20), label, fill=color, font=font)
            
            # Convert to base64
            buffer = BytesIO()
            preview_image.save(buffer, format='PNG')
            buffer.seek(0)
            preview_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            logger.info(f"📷 Visual verification preview created for {action} at ({x}, {y})")
            return preview_base64
            
        except Exception as e:
            logger.error(f"Failed to create verification preview: {e}")
            return ""
    
    async def verify_action_feasibility(self, coords: Tuple[int, int], action: str, element: Dict[str, Any], screenshot: Optional[Image.Image] = None) -> Dict[str, Any]:
        """
        Verify if the action is feasible at the given coordinates
        """
        try:
            if screenshot is None:
                screenshot = ImageGrab.grab()
            
            x, y = coords
            width, height = screenshot.size
            
            # Check if coordinates are within screen bounds
            if x < 0 or y < 0 or x >= width or y >= height:
                return {
                    "feasible": False,
                    "reason": f"Coordinates ({x}, {y}) are outside screen bounds ({width}x{height})",
                    "confidence": 0.0
                }
            
            # Check if coordinates are too close to screen edges
            margin = 10
            if x < margin or y < margin or x > width - margin or y > height - margin:
                return {
                    "feasible": True,
                    "reason": "Coordinates are very close to screen edge",
                    "confidence": 0.6
                }
            
            # Action-specific feasibility checks
            if action == "click" or action == "double_click":
                return {
                    "feasible": True,
                    "reason": "Click action is feasible at this location",
                    "confidence": 0.9
                }
            elif action == "type":
                element_type = element.get("element_type", "").lower()
                if "text" in element_type or "input" in element_type:
                    return {
                        "feasible": True,
                        "reason": f"Text typing feasible in {element_type}",
                        "confidence": 0.8
                    }
                else:
                    return {
                        "feasible": True,
                        "reason": "Text typing attempted at non-text element",
                        "confidence": 0.5
                    }
            else:
                return {
                    "feasible": True,
                    "reason": f"Action {action} appears feasible",
                    "confidence": 0.7
                }
                
        except Exception as e:
            logger.error(f"Feasibility verification failed: {e}")
            return {
                "feasible": True,
                "reason": "Feasibility check failed, assuming feasible",
                "confidence": 0.5
            }

class VisualVerifier:
    """
    Visual verification system for automation actions
    """
    
    def __init__(self):
        self.verification_history = []
        
    async def create_verification_preview(self, coords: Tuple[int, int], element: Dict[str, Any], action: str, screenshot: Optional[Image.Image] = None) -> str:
        """
        Create a visual preview showing where the action will occur
        Returns base64 encoded image
        """
        try:
            if screenshot is None:
                screenshot = ImageGrab.grab()
            
            # Create a copy for drawing
            preview = screenshot.copy()
            draw = ImageDraw.Draw(preview)
            
            x, y = coords
            
            # Draw targeting indicators
            self._draw_target_indicator(draw, x, y, action, element)
            
            # Add information overlay
            self._add_info_overlay(draw, preview.size, element, action, coords)
            
            # Convert to base64
            buffer = BytesIO()
            preview.save(buffer, format='PNG')
            preview_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return preview_base64
            
        except Exception as e:
            logger.error(f"Failed to create verification preview: {e}")
            return ""
    
    def _draw_target_indicator(self, draw: ImageDraw.Draw, x: int, y: int, action: str, element: Dict[str, Any]):
        """Draw targeting indicator on the preview"""
        try:
            # Choose color based on action
            color_map = {
                "click": "red",
                "type": "blue",
                "double_click": "orange",
                "right_click": "purple"
            }
            color = color_map.get(action.lower(), "red")
            
            # Draw crosshair
            size = 20
            draw.line([(x - size, y), (x + size, y)], fill=color, width=3)
            draw.line([(x, y - size), (x, y + size)], fill=color, width=3)
            
            # Draw circle around target
            draw.ellipse([(x - size, y - size), (x + size, y + size)], outline=color, width=2)
            
            # Draw action label
            action_text = f"{action.upper()}"
            try:
                font = ImageFont.truetype("Arial.ttf", 12)
            except:
                font = ImageFont.load_default()
            
            # Calculate text position (above the target)
            text_bbox = draw.textbbox((0, 0), action_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_x = x - text_width // 2
            text_y = y - 40
            
            # Draw text background
            draw.rectangle([
                (text_x - 5, text_y - 5),
                (text_x + text_width + 5, text_y + 15)
            ], fill="white", outline=color)
            
            # Draw text
            draw.text((text_x, text_y), action_text, fill=color, font=font)
            
        except Exception as e:
            logger.debug(f"Failed to draw target indicator: {e}")
    
    def _add_info_overlay(self, draw: ImageDraw.Draw, screen_size: Tuple[int, int], element: Dict[str, Any], action: str, coords: Tuple[int, int]):
        """Add information overlay to the preview"""
        try:
            width, height = screen_size
            
            # Create info box in top-right corner
            info_lines = [
                f"Action: {action.upper()}",
                f"Target: {element.get('element_text', 'Unknown')[:20]}",
                f"Type: {element.get('element_type', 'unknown')}",
                f"Coordinates: ({coords[0]}, {coords[1]})",
                f"Confidence: {element.get('confidence', 0):.2f}"
            ]
            
            try:
                font = ImageFont.truetype("Arial.ttf", 10)
            except:
                font = ImageFont.load_default()
            
            # Calculate box size
            max_width = 0
            total_height = 0
            for line in info_lines:
                text_bbox = draw.textbbox((0, 0), line, font=font)
                line_width = text_bbox[2] - text_bbox[0]
                line_height = text_bbox[3] - text_bbox[1]
                max_width = max(max_width, line_width)
                total_height += line_height + 2
            
            # Position in top-right corner
            box_x = width - max_width - 20
            box_y = 10
            
            # Draw info box background
            draw.rectangle([
                (box_x - 10, box_y - 5),
                (box_x + max_width + 10, box_y + total_height + 5)
            ], fill="white", outline="black")
            
            # Draw info text
            current_y = box_y
            for line in info_lines:
                draw.text((box_x, current_y), line, fill="black", font=font)
                current_y += 12
            
        except Exception as e:
            logger.debug(f"Failed to add info overlay: {e}")
    
    async def verify_action_feasibility(self, coords: Tuple[int, int], action: str, element: Dict[str, Any], screenshot: Optional[Image.Image] = None) -> Dict[str, Any]:
        """
        Verify if an action is feasible at the given coordinates
        Returns verification result with confidence score
        """
        try:
            if screenshot is None:
                screenshot = ImageGrab.grab()
            
            x, y = coords
            width, height = screenshot.size
            
            # Basic feasibility checks
            feasibility_score = 1.0
            warnings = []
            
            # Check if coordinates are within screen
            if not (0 <= x < width and 0 <= y < height):
                return {
                    "feasible": False,
                    "confidence": 0.0,
                    "warnings": ["Coordinates outside screen bounds"],
                    "recommendation": "adjust_coordinates"
                }
            
            # Check if near screen edges (might be problematic)
            edge_margin = 10
            if x < edge_margin or x > width - edge_margin or y < edge_margin or y > height - edge_margin:
                feasibility_score -= 0.2
                warnings.append("Target near screen edge")
            
            # Analyze target region
            region_size = 30
            left = max(0, x - region_size)
            top = max(0, y - region_size)
            right = min(width, x + region_size)
            bottom = min(height, y + region_size)
            
            region = screenshot.crop((left, top, right, bottom))
            
            # Action-specific feasibility checks
            if action.lower() == "type":
                # For typing, verify it looks like a text input area
                text_area_score = await self._verify_text_input_area(region)
                feasibility_score *= text_area_score
                
                if text_area_score < 0.5:
                    warnings.append("Target doesn't appear to be a text input area")
            
            elif action.lower() in ["click", "double_click"]:
                # For clicking, verify it looks interactive
                interactive_score = await self._verify_interactive_element(region)
                feasibility_score *= interactive_score
                
                if interactive_score < 0.3:
                    warnings.append("Target doesn't appear to be interactive")
            
            # Overall assessment
            feasible = feasibility_score > 0.4
            confidence = feasibility_score
            
            recommendation = "proceed"
            if not feasible:
                recommendation = "find_alternative"
            elif feasibility_score < 0.7:
                recommendation = "proceed_with_caution"
            
            return {
                "feasible": feasible,
                "confidence": confidence,
                "warnings": warnings,
                "recommendation": recommendation,
                "analysis": {
                    "coordinates": coords,
                    "action": action,
                    "target_region_analyzed": True
                }
            }
            
        except Exception as e:
            logger.error(f"Feasibility verification failed: {e}")
            return {
                "feasible": False,
                "confidence": 0.0,
                "warnings": [f"Verification failed: {str(e)}"],
                "recommendation": "manual_intervention"
            }
    
    async def _verify_text_input_area(self, region: Image.Image) -> float:
        """Verify if a region looks like a text input area"""
        try:
            # Convert to grayscale
            gray_region = np.array(region.convert('L'))
            
            # Check for white/light background (common for text areas)
            light_pixels = np.sum(gray_region > 200)
            total_pixels = gray_region.size
            light_ratio = light_pixels / total_pixels
            
            score = 0.0
            
            # High light ratio suggests text area
            if light_ratio > 0.7:
                score += 0.6
            elif light_ratio > 0.4:
                score += 0.3
            
            # Check for cursor or text content
            try:
                import pytesseract
                text = pytesseract.image_to_string(region).strip()
                if len(text) > 0:
                    score += 0.2
            except:
                pass
            
            # Check for rectangular structure (text fields often have borders)
            edges = cv2.Canny(np.array(region), 50, 150)
            edge_pixels = np.sum(edges > 0)
            if edge_pixels > 10:  # Some edge structure
                score += 0.2
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.debug(f"Text area verification failed: {e}")
            return 0.0
    
    async def _verify_interactive_element(self, region: Image.Image) -> float:
        """Verify if a region looks like an interactive element"""
        try:
            # Convert to OpenCV format
            cv_region = cv2.cvtColor(np.array(region), cv2.COLOR_RGB2BGR)
            gray_region = cv2.cvtColor(cv_region, cv2.COLOR_BGR2GRAY)
            
            score = 0.0
            
            # Check for button-like features (edges, uniform color)
            edges = cv2.Canny(gray_region, 50, 150)
            edge_ratio = np.sum(edges > 0) / edges.size
            
            if 0.05 < edge_ratio < 0.3:  # Moderate edge density
                score += 0.4
            
            # Check color uniformity (buttons often have solid colors)
            std_dev = np.std(gray_region)
            if std_dev < 40:  # Relatively uniform
                score += 0.3
            
            # Check for text content (interactive elements often have labels)
            try:
                import pytesseract
                text = pytesseract.image_to_string(region).strip()
                if len(text) > 0:
                    score += 0.3
            except:
                pass
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.debug(f"Interactive element verification failed: {e}")
            return 0.0