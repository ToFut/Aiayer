#!/usr/bin/env python3
"""
Enhanced Google Search Detector - Specialized detection for Google search boxes and results
"""

import pyautogui
import time
import cv2
import numpy as np
import logging
from typing import Tuple, Dict, Optional, List, Any
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

@dataclass
class GoogleUIElement:
    """A detected Google UI element"""
    element_type: str
    coordinates: Tuple[int, int]
    confidence: float
    bounds: Optional[Tuple[int, int, int, int]] = None
    description: str = ""

class GoogleSearchDetector:
    """Specialized detector for Google search UI elements"""
    
    def __init__(self):
        """Initialize the Google search detector"""
        self.screen_width, self.screen_height = pyautogui.size()
        logger.info(f"Google search detector initialized for {self.screen_width}x{self.screen_height} screen")
        
        # Standard Google UI element positions (relative to screen)
        self.standard_positions = {
            "search_box": (self.screen_width // 2, 160),        # Main Google search box
            "search_button": (self.screen_width // 2 + 200, 160), # Search button beside box
            "first_result": (self.screen_width // 2, 270),      # First search result
            "second_result": (self.screen_width // 2, 330),     # Second search result
            "third_result": (self.screen_width // 2, 390),      # Third search result
            "fourth_result": (self.screen_width // 2, 450),     # Fourth search result
            "images_tab": (self.screen_width // 2 - 200, 200),  # Images tab
            "videos_tab": (self.screen_width // 2 - 120, 200),  # Videos tab
            "shopping_tab": (self.screen_width // 2 - 40, 200), # Shopping tab
            "maps_tab": (self.screen_width // 2 + 40, 200)      # Maps tab
        }
    
    def detect_google_search_box(self) -> Optional[GoogleUIElement]:
        """Detect Google search box using specialized techniques"""
        try:
            # Take screenshot for analysis
            screenshot = pyautogui.screenshot()
            img_array = np.array(screenshot)
            img_rgb = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
            
            # Method 1: Look for light rectangular areas (Google search box is typically light)
            light_threshold = 180  # Adjusted for Google's white search box
            light_mask = cv2.threshold(img_gray, light_threshold, 255, cv2.THRESH_BINARY)[1]
            
            # Find contours of light areas
            contours, _ = cv2.findContours(light_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            google_search_box = None
            best_confidence = 0.0
            
            for contour in contours:
                area = cv2.contourArea(contour)
                # Google search box is typically large but not massive
                if 5000 < area < 100000:
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    
                    # Google search box has a wide aspect ratio
                    if 4.0 < aspect_ratio < 25.0 and 30 < h < 80:
                        # Vertical position check - Google search box is typically in top part of screen
                        if 80 < y < 250:
                            # Horizontal position check - should be centered-ish
                            center_x = x + w // 2
                            if abs(center_x - (self.screen_width // 2)) < self.screen_width * 0.3:
                                # Calculate confidence based on how well it matches typical Google search box
                                confidence = self._calculate_google_search_box_confidence(x, y, w, h, img_gray)
                                
                                if confidence > best_confidence:
                                    best_confidence = confidence
                                    google_search_box = GoogleUIElement(
                                        element_type="google_search_box",
                                        coordinates=(center_x, y + h // 2),
                                        confidence=confidence,
                                        bounds=(x, y, x+w, y+h),
                                        description=f"Google search box ({w}x{h})"
                                    )
            
            # If we found a good match, create verification image and return it
            if google_search_box and google_search_box.confidence > 0.6:
                self._create_verification_image(screenshot, google_search_box, "google_search_box")
                logger.info(f"✓ Google search box detected at {google_search_box.coordinates} with confidence {google_search_box.confidence:.2f}")
                return google_search_box
            
            # Method 2: If no good match found, try template matching
            # This would use a template image of Google search box for better detection
            # Omitted for simplicity but could be added for improved robustness
            
            # Fallback to standard position if detection fails
            logger.warning("⚠ Google search box detection failed, using standard position")
            fallback = GoogleUIElement(
                element_type="google_search_box",
                coordinates=self.standard_positions["search_box"],
                confidence=0.4,
                description="Google search box (fallback position)"
            )
            self._create_verification_image(screenshot, fallback, "google_search_box_fallback")
            return fallback
            
        except Exception as e:
            logger.error(f"Error detecting Google search box: {e}")
            # Return fallback position in case of error
            return GoogleUIElement(
                element_type="google_search_box",
                coordinates=self.standard_positions["search_box"],
                confidence=0.3,
                description="Google search box (error fallback)"
            )
    
    def detect_search_result(self, result_number: int = 1) -> Optional[GoogleUIElement]:
        """Detect Google search result position"""
        try:
            # Take screenshot for analysis
            screenshot = pyautogui.screenshot()
            
            # For search results, we mostly rely on standard positions
            # as they are harder to detect programmatically
            if 1 <= result_number <= 4:
                result_key = f"{['first', 'second', 'third', 'fourth'][result_number-1]}_result"
                coords = self.standard_positions.get(result_key, self.standard_positions["first_result"])
                
                result = GoogleUIElement(
                    element_type="search_result",
                    coordinates=coords,
                    confidence=0.7,
                    description=f"Google search result #{result_number}"
                )
                
                # Create verification image
                self._create_verification_image(screenshot, result, f"search_result_{result_number}")
                logger.info(f"✓ Google search result #{result_number} position at {coords}")
                return result
            else:
                # Handle out of range result numbers
                logger.warning(f"⚠ Invalid result number: {result_number}, using first result")
                return self.detect_search_result(1)
                
        except Exception as e:
            logger.error(f"Error detecting Google search result: {e}")
            # Return fallback position for first result
            return GoogleUIElement(
                element_type="search_result",
                coordinates=self.standard_positions["first_result"],
                confidence=0.4,
                description=f"Google search result (error fallback)"
            )
    
    def _calculate_google_search_box_confidence(self, x, y, w, h, img_gray) -> float:
        """Calculate confidence that this element is a Google search box"""
        confidence = 0.5  # Base confidence
        
        # Position characteristics of Google search box
        # Vertical position - typically at the top area of the page
        if 80 < y < 200:
            confidence += 0.2
        elif 200 < y < 300:
            confidence += 0.1
        
        # Horizontal centering - Google search box is typically centered
        center_x = x + w // 2
        screen_center_x = self.screen_width // 2
        center_offset = abs(center_x - screen_center_x) / self.screen_width
        
        if center_offset < 0.1:  # Very centered
            confidence += 0.2
        elif center_offset < 0.2:  # Reasonably centered
            confidence += 0.1
        
        # Size characteristics
        # Width - Google search box is quite wide
        if 400 < w < 700:
            confidence += 0.2
        elif 300 < w < 800:
            confidence += 0.1
        
        # Height - Google search box has a specific height range
        if 40 < h < 60:
            confidence += 0.2
        elif 30 < h < 70:
            confidence += 0.1
        
        # Aspect ratio - Google search box is wide rectangle
        aspect_ratio = w / h
        if 7.0 < aspect_ratio < 15.0:
            confidence += 0.2
        elif 4.0 < aspect_ratio < 20.0:
            confidence += 0.1
        
        # Brightness uniformity - Google search box has consistent coloring
        roi = img_gray[y:y+h, x:x+w]
        brightness_std = np.std(roi)
        if brightness_std < 20:  # Very uniform
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _create_verification_image(self, screenshot: Image.Image, element: GoogleUIElement, name: str) -> str:
        """Create verification image with detected element highlighted"""
        try:
            # Create a copy of the screenshot
            verification_img = screenshot.copy()
            draw = ImageDraw.Draw(verification_img)
            
            x, y = element.coordinates
            
            # Choose color based on confidence
            if element.confidence > 0.8:
                color = 'lime'
            elif element.confidence > 0.6:
                color = 'yellow'
            elif element.confidence > 0.4:
                color = 'orange'
            else:
                color = 'red'
            
            # Draw crosshair
            crosshair_size = 30
            draw.line([(x - crosshair_size, y), (x + crosshair_size, y)], fill=color, width=3)
            draw.line([(x, y - crosshair_size), (x, y + crosshair_size)], fill=color, width=3)
            
            # Draw bounds if available
            if element.bounds:
                x1, y1, x2, y2 = element.bounds
                draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
            
            # Add text
            try:
                font = ImageFont.truetype("Arial", 16)
            except:
                font = ImageFont.load_default()
            
            info_text = f"{element.element_type}\n{element.coordinates}\nConfidence: {element.confidence:.2f}"
            
            # Position text
            text_x = x + 40
            text_y = y - 30
            
            # White background for readability
            text_width = max([draw.textlength(line, font=font) for line in info_text.split('\n')])
            text_height = len(info_text.split('\n')) * 20
            
            draw.rectangle(
                [text_x - 5, text_y - 5, text_x + text_width + 5, text_y + text_height + 5],
                fill='white', outline='black'
            )
            
            # Draw text
            for i, line in enumerate(info_text.split('\n')):
                draw.text((text_x, text_y + i * 20), line, fill='black', font=font)
            
            # Save image
            timestamp = int(time.time())
            filename = f"google_detection_{name}_{timestamp}.png"
            verification_img.save(filename)
            logger.info(f"📸 Saved verification image: {filename}")
            
            return filename
        except Exception as e:
            logger.error(f"Error creating verification image: {e}")
            return "verification_failed"

# Create singleton instance
google_search_detector = GoogleSearchDetector()

def get_google_search_box_coordinates() -> Tuple[int, int]:
    """Get coordinates for Google search box"""
    element = google_search_detector.detect_google_search_box()
    return element.coordinates if element else (0, 0)

def get_google_search_result_coordinates(result_number: int = 1) -> Tuple[int, int]:
    """Get coordinates for Google search result"""
    element = google_search_detector.detect_search_result(result_number)
    return element.coordinates if element else (0, 0)

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🔍 Google Search Element Detector Test")
    print("--------------------------------------")
    
    # Test search box detection
    print("\nDetecting Google search box...")
    search_box = google_search_detector.detect_google_search_box()
    if search_box:
        print(f"✓ Search box detected: {search_box.coordinates} (confidence: {search_box.confidence:.2f})")
    else:
        print("✗ Search box detection failed")
    
    # Test search result detection
    print("\nDetecting Google search results...")
    for i in range(1, 5):
        result = google_search_detector.detect_search_result(i)
        if result:
            print(f"✓ Result #{i} position: {result.coordinates} (confidence: {result.confidence:.2f})")
        else:
            print(f"✗ Result #{i} detection failed")
    
    print("\n📸 Check the current directory for verification images")