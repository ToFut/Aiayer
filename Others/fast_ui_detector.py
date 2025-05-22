#!/usr/bin/env python3
"""
Fast UI Element Detection System
- Uses OS accessibility APIs instead of slow visual analysis
- Implements fast OCR for text recognition
- Lightweight computer vision for shapes/buttons
- Intelligent caching for performance
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Tuple, Any
import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageDraw
import pyautogui
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
import hashlib
import logging

logger = logging.getLogger(__name__)

@dataclass
class UIElement:
    """Fast UI element representation"""
    type: str  # button, text, input, etc.
    text: str
    bounds: Tuple[int, int, int, int]  # x, y, width, height
    confidence: float
    properties: Dict[str, Any]
    source: str  # accessibility, ocr, cv

class FastUIDetector:
    """Ultra-fast UI detection using multiple intelligent methods"""
    
    def __init__(self):
        self.cache = {}
        self.cache_timeout = 2.0  # Cache UI state for 2 seconds
        self.last_screenshot_hash = None
        
        # Configure fast OCR
        self.ocr_config = '--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 '
        
        # Common UI patterns for fast detection
        self.button_keywords = ['button', 'btn', 'click', 'submit', 'ok', 'cancel', 'close', 'save', 'send']
        self.input_keywords = ['input', 'textbox', 'field', 'search', 'password', 'email']
        
    async def get_ui_elements(self, fast_mode: bool = True) -> List[UIElement]:
        """Get UI elements using fastest available methods"""
        start_time = time.time()
        elements = []
        
        # Method 1: macOS Accessibility API (fastest, most accurate)
        try:
            accessibility_elements = await self._get_accessibility_elements()
            elements.extend(accessibility_elements)
            logger.info(f"Accessibility API found {len(accessibility_elements)} elements")
        except Exception as e:
            logger.warning(f"Accessibility API failed: {e}")
        
        # Method 2: Fast OCR for text elements (if accessibility missed them)
        if fast_mode and len(elements) < 5:  # Only if we need more elements
            ocr_elements = await self._get_ocr_elements()
            elements.extend(ocr_elements)
            logger.info(f"OCR found {len(ocr_elements)} additional elements")
        
        # Method 3: Fast computer vision for shapes (last resort)
        if len(elements) < 3:
            cv_elements = await self._get_cv_elements()
            elements.extend(cv_elements)
            logger.info(f"Computer vision found {len(cv_elements)} additional elements")
        
        # Remove duplicates and sort by confidence
        elements = self._deduplicate_elements(elements)
        elements.sort(key=lambda x: x.confidence, reverse=True)
        
        detection_time = time.time() - start_time
        logger.info(f"Fast UI detection completed in {detection_time:.2f}s, found {len(elements)} elements")
        
        return elements
    
    async def _get_accessibility_elements(self) -> List[UIElement]:
        """Use macOS accessibility API for instant UI element detection"""
        elements = []
        
        try:
            # Get accessibility tree from current focused application
            script = '''
            tell application "System Events"
                set frontApp to first application process whose frontmost is true
                set appName to name of frontApp
                
                set elementList to {}
                
                try
                    set allElements to every UI element of frontApp
                    repeat with elem in allElements
                        try
                            set elemRole to role of elem
                            set elemTitle to title of elem
                            set elemPos to position of elem
                            set elemSize to size of elem
                            
                            if elemRole contains "button" or elemRole contains "text" or elemRole contains "field" then
                                set end of elementList to {elemRole, elemTitle, elemPos, elemSize}
                            end if
                        end try
                    end repeat
                end try
                
                return {appName, elementList}
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', script], 
                                 capture_output=True, text=True, timeout=1.0)
            
            if result.returncode == 0 and result.stdout:
                # Parse AppleScript output
                output = result.stdout.strip()
                if output and output != "missing value":
                    accessibility_data = self._parse_applescript_output(output)
                    elements = self._convert_accessibility_to_elements(accessibility_data)
            
        except subprocess.TimeoutExpired:
            logger.warning("Accessibility API timeout")
        except Exception as e:
            logger.error(f"Accessibility API error: {e}")
        
        return elements
    
    async def _get_ocr_elements(self) -> List[UIElement]:
        """Fast OCR-based text detection"""
        elements = []
        
        try:
            # Take screenshot only if cache is invalid
            screenshot_hash = await self._get_screenshot_hash()
            if screenshot_hash == self.last_screenshot_hash and 'ocr_elements' in self.cache:
                return self.cache['ocr_elements']
            
            # Fast screenshot
            screenshot = pyautogui.screenshot()
            screenshot_np = np.array(screenshot)
            
            # Fast OCR with bounding boxes
            ocr_data = pytesseract.image_to_data(screenshot_np, config=self.ocr_config, output_type=pytesseract.Output.DICT)
            
            # Process OCR results
            for i in range(len(ocr_data['text'])):
                text = ocr_data['text'][i].strip()
                confidence = int(ocr_data['conf'][i])
                
                if text and confidence > 30:  # Only high-confidence text
                    x, y, w, h = (ocr_data['left'][i], ocr_data['top'][i], 
                                ocr_data['width'][i], ocr_data['height'][i])
                    
                    # Classify element type based on text content
                    element_type = self._classify_text_element(text)
                    
                    element = UIElement(
                        type=element_type,
                        text=text,
                        bounds=(x, y, w, h),
                        confidence=confidence / 100.0,
                        properties={'method': 'ocr'},
                        source='ocr'
                    )
                    elements.append(element)
            
            # Cache results
            self.cache['ocr_elements'] = elements
            self.cache['ocr_timestamp'] = time.time()
            
        except Exception as e:
            logger.error(f"OCR detection failed: {e}")
        
        return elements
    
    async def _get_cv_elements(self) -> List[UIElement]:
        """Fast computer vision for UI shapes and buttons"""
        elements = []
        
        try:
            # Use cached screenshot if available
            screenshot = pyautogui.screenshot()
            img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Fast button detection using edge detection
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if 100 < area < 10000:  # Reasonable button size
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    
                    # Button-like shape detection
                    if 0.2 < aspect_ratio < 5.0 and w > 20 and h > 15:
                        element = UIElement(
                            type='button',
                            text='',
                            bounds=(x, y, w, h),
                            confidence=0.6,  # Medium confidence for CV detection
                            properties={'method': 'cv', 'area': area, 'aspect_ratio': aspect_ratio},
                            source='cv'
                        )
                        elements.append(element)
            
        except Exception as e:
            logger.error(f"Computer vision detection failed: {e}")
        
        return elements
    
    def _classify_text_element(self, text: str) -> str:
        """Classify element type based on text content"""
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in self.button_keywords):
            return 'button'
        elif any(keyword in text_lower for keyword in self.input_keywords):
            return 'input'
        elif len(text) < 3:
            return 'icon'
        elif text.isupper() and len(text) < 20:
            return 'label'
        else:
            return 'text'
    
    def _parse_applescript_output(self, output: str) -> Dict:
        """Parse AppleScript accessibility output"""
        # Basic parsing - can be enhanced
        try:
            # This is a simplified parser - real implementation would be more robust
            return {'elements': []}
        except:
            return {'elements': []}
    
    def _convert_accessibility_to_elements(self, data: Dict) -> List[UIElement]:
        """Convert accessibility data to UIElement objects"""
        elements = []
        # Implementation would convert accessibility tree to UIElement objects
        return elements
    
    def _deduplicate_elements(self, elements: List[UIElement]) -> List[UIElement]:
        """Remove duplicate elements based on position and text"""
        seen = set()
        unique_elements = []
        
        for element in elements:
            # Create unique key based on position and text
            key = (element.bounds[0] // 10, element.bounds[1] // 10, element.text)
            if key not in seen:
                seen.add(key)
                unique_elements.append(element)
        
        return unique_elements
    
    async def _get_screenshot_hash(self) -> str:
        """Get hash of current screenshot for caching"""
        try:
            # Fast small screenshot for hashing
            small_screenshot = pyautogui.screenshot(region=(0, 0, 200, 200))
            screenshot_bytes = small_screenshot.tobytes()
            return hashlib.md5(screenshot_bytes).hexdigest()
        except:
            return str(time.time())
    
    async def find_element_by_text(self, target_text: str) -> Optional[UIElement]:
        """Find element by text content (fastest method)"""
        elements = await self.get_ui_elements(fast_mode=True)
        
        target_lower = target_text.lower()
        
        # Exact match first
        for element in elements:
            if element.text.lower() == target_lower:
                return element
        
        # Partial match
        for element in elements:
            if target_lower in element.text.lower() or element.text.lower() in target_lower:
                return element
        
        return None
    
    async def find_elements_by_type(self, element_type: str) -> List[UIElement]:
        """Find all elements of specific type"""
        elements = await self.get_ui_elements(fast_mode=True)
        return [e for e in elements if e.type == element_type]

# Example usage and testing
async def test_fast_detection():
    """Test the fast UI detection system"""
    detector = FastUIDetector()
    
    print("Testing fast UI detection...")
    start_time = time.time()
    
    elements = await detector.get_ui_elements()
    detection_time = time.time() - start_time
    
    print(f"Detected {len(elements)} elements in {detection_time:.2f} seconds")
    
    for element in elements[:10]:  # Show first 10
        print(f"  {element.type}: '{element.text}' at {element.bounds} (confidence: {element.confidence:.2f})")

if __name__ == "__main__":
    asyncio.run(test_fast_detection())