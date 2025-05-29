"""
Intelligent Application Detection and Navigation System
Uses computer vision and OCR to detect, identify, and navigate applications on screen.
"""

import cv2
import numpy as np
import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)

@dataclass
class ApplicationInfo:
    """Information about a detected application."""
    name: str
    confidence: float
    window_bounds: Tuple[int, int, int, int]  # x, y, width, height
    process_id: Optional[int] = None
    window_title: Optional[str] = None
    app_type: Optional[str] = None  # browser, email, file_manager, etc.
    is_active: bool = False
    screenshot_region: Optional[np.ndarray] = None

@dataclass
class UIElement:
    """Information about a UI element within an application."""
    element_type: str  # button, input, menu, etc.
    confidence: float
    bounds: Tuple[int, int, int, int]
    text: Optional[str] = None
    accessibility_label: Optional[str] = None
    is_clickable: bool = False

class ApplicationDetector:
    """Detects and identifies applications on screen using computer vision."""
    
    def __init__(self, backend_instance):
        self.backend = backend_instance
        self.logger = logging.getLogger(f"{__name__}.ApplicationDetector")
        
        # Application signatures for detection
        self.app_signatures = {
            "Mail": {
                "window_titles": ["Mail", "Inbox", "Compose"],
                "ui_elements": ["inbox", "compose", "send", "reply"],
                "colors": [(70, 130, 180), (65, 105, 225)],  # Mail app blue
                "type": "email"
            },
            "Gmail": {
                "window_titles": ["Gmail", "Google"],
                "ui_elements": ["compose", "inbox", "gmail"],
                "url_patterns": ["mail.google.com", "gmail.com"],
                "type": "email"
            },
            "Chrome": {
                "window_titles": ["Chrome", "Google Chrome"],
                "ui_elements": ["address bar", "tabs", "bookmark"],
                "colors": [(238, 238, 238), (245, 245, 245)],
                "type": "browser"
            },
            "Safari": {
                "window_titles": ["Safari"],
                "ui_elements": ["address bar", "tabs", "bookmark"],
                "colors": [(248, 248, 248), (240, 240, 240)],
                "type": "browser"
            },
            "Finder": {
                "window_titles": ["Finder"],
                "ui_elements": ["sidebar", "toolbar", "search"],
                "colors": [(235, 235, 235), (245, 245, 245)],
                "type": "file_manager"
            },
            "Activity Monitor": {
                "window_titles": ["Activity Monitor"],
                "ui_elements": ["cpu", "memory", "process"],
                "type": "system_monitor"
            }
        }
    
    async def detect_applications(self, screen: Optional[np.ndarray] = None) -> List[ApplicationInfo]:
        """Detect all visible applications on screen."""
        if screen is None:
            screen = await self.backend.capture_screen_fast()
        
        applications = []
        
        # Get OCR text from entire screen
        screen_text = await self._perform_ocr(screen)
        
        # Detect applications using multiple methods
        for app_name, signature in self.app_signatures.items():
            confidence = await self._calculate_app_confidence(screen, screen_text, signature)
            
            if confidence > 0.3:  # Threshold for detection
                bounds = await self._find_app_bounds(screen, screen_text, signature)
                window_title = await self._extract_window_title(screen_text, signature)
                
                app_info = ApplicationInfo(
                    name=app_name,
                    confidence=confidence,
                    window_bounds=bounds,
                    window_title=window_title,
                    app_type=signature.get("type"),
                    is_active=await self._is_app_active(screen, bounds),
                    screenshot_region=self._extract_region(screen, bounds)
                )
                
                applications.append(app_info)
        
        # Sort by confidence
        applications.sort(key=lambda x: x.confidence, reverse=True)
        
        self.logger.info(f"Detected {len(applications)} applications")
        return applications
    
    async def _calculate_app_confidence(self, screen: np.ndarray, screen_text: str, 
                                      signature: Dict[str, Any]) -> float:
        """Calculate confidence score for application detection."""
        confidence = 0.0
        
        # Check window titles
        title_matches = 0
        for title in signature.get("window_titles", []):
            if title.lower() in screen_text.lower():
                title_matches += 1
        
        if title_matches > 0:
            confidence += 0.4 * (title_matches / len(signature.get("window_titles", [1])))
        
        # Check UI elements
        ui_matches = 0
        for element in signature.get("ui_elements", []):
            if element.lower() in screen_text.lower():
                ui_matches += 1
        
        if ui_matches > 0:
            confidence += 0.3 * (ui_matches / len(signature.get("ui_elements", [1])))
        
        # Check colors if present
        if "colors" in signature:
            color_confidence = await self._check_color_signature(screen, signature["colors"])
            confidence += 0.2 * color_confidence
        
        # Check URL patterns for browsers
        if "url_patterns" in signature:
            url_confidence = await self._check_url_patterns(screen_text, signature["url_patterns"])
            confidence += 0.3 * url_confidence
        
        return min(confidence, 1.0)
    
    async def _find_app_bounds(self, screen: np.ndarray, screen_text: str, 
                             signature: Dict[str, Any]) -> Tuple[int, int, int, int]:
        """Find the bounds of an application window."""
        # For now, return full screen bounds
        # In a real implementation, this would use window detection algorithms
        height, width = screen.shape[:2]
        return (0, 0, width, height)
    
    async def _extract_window_title(self, screen_text: str, signature: Dict[str, Any]) -> Optional[str]:
        """Extract window title from screen text."""
        for title in signature.get("window_titles", []):
            # Look for title patterns in the text
            pattern = rf"({re.escape(title)}[^\n]*)"
            match = re.search(pattern, screen_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    async def _is_app_active(self, screen: np.ndarray, bounds: Tuple[int, int, int, int]) -> bool:
        """Determine if an application is currently active/focused."""
        # Simple heuristic: check if the window region has focus indicators
        x, y, w, h = bounds
        region = screen[y:y+h, x:x+w] if h > 0 and w > 0 else screen
        
        # Look for common focus indicators (bright title bars, etc.)
        # This is a simplified implementation
        return True  # For now, assume detected apps are active
    
    async def _check_color_signature(self, screen: np.ndarray, colors: List[Tuple[int, int, int]]) -> float:
        """Check if application-specific colors are present."""
        confidence = 0.0
        
        for target_color in colors:
            # Convert screen to BGR and look for similar colors
            color_mask = np.zeros(screen.shape[:2], dtype=np.uint8)
            
            for i, color_channel in enumerate(target_color):
                lower_bound = max(0, color_channel - 20)
                upper_bound = min(255, color_channel + 20)
                
                if len(screen.shape) == 3:
                    channel = screen[:, :, i]
                    mask = (channel >= lower_bound) & (channel <= upper_bound)
                    color_mask = cv2.bitwise_or(color_mask, mask.astype(np.uint8))
            
            # Calculate percentage of matching pixels
            match_percentage = np.sum(color_mask > 0) / color_mask.size
            confidence = max(confidence, match_percentage)
        
        return confidence
    
    async def _check_url_patterns(self, screen_text: str, url_patterns: List[str]) -> float:
        """Check if browser URL patterns are present."""
        confidence = 0.0
        
        for pattern in url_patterns:
            if pattern.lower() in screen_text.lower():
                confidence = 1.0
                break
        
        return confidence
    
    def _extract_region(self, screen: np.ndarray, bounds: Tuple[int, int, int, int]) -> np.ndarray:
        """Extract a region from the screen."""
        x, y, w, h = bounds
        if h > 0 and w > 0:
            return screen[y:y+h, x:x+w]
        return screen
    
    async def _perform_ocr(self, screen: np.ndarray) -> str:
        """Perform OCR on screen image."""
        # Placeholder for OCR functionality
        # In real implementation, this would use pytesseract or similar
        return "OCR extracted text placeholder"

class UIElementDetector:
    """Detects UI elements within applications."""
    
    def __init__(self, backend_instance):
        self.backend = backend_instance
        self.logger = logging.getLogger(f"{__name__}.UIElementDetector")
        
        # UI element patterns
        self.element_patterns = {
            "button": {
                "text_patterns": ["button", "click", "submit", "send", "ok", "cancel"],
                "visual_cues": ["rounded_rectangle", "border"],
                "size_range": (20, 200)
            },
            "input_field": {
                "text_patterns": ["search", "enter", "type", "input"],
                "visual_cues": ["white_background", "border", "cursor"],
                "size_range": (100, 600)
            },
            "menu": {
                "text_patterns": ["menu", "file", "edit", "view", "help"],
                "visual_cues": ["horizontal_list", "dropdown"],
                "size_range": (50, 300)
            },
            "search_box": {
                "text_patterns": ["search", "find", "filter", "query"],
                "visual_cues": ["magnifying_glass", "white_background"],
                "size_range": (100, 400)
            }
        }
    
    async def detect_elements(self, app_info: ApplicationInfo) -> List[UIElement]:
        """Detect UI elements within an application."""
        if app_info.screenshot_region is None:
            return []
        
        elements = []
        screen_region = app_info.screenshot_region
        region_text = await self._perform_ocr(screen_region)
        
        # Detect different types of UI elements
        for element_type, pattern in self.element_patterns.items():
            detected = await self._detect_element_type(
                screen_region, region_text, element_type, pattern
            )
            elements.extend(detected)
        
        # Filter and rank elements
        elements = await self._filter_and_rank_elements(elements)
        
        self.logger.info(f"Detected {len(elements)} UI elements in {app_info.name}")
        return elements
    
    async def _detect_element_type(self, screen: np.ndarray, text: str, 
                                 element_type: str, pattern: Dict[str, Any]) -> List[UIElement]:
        """Detect specific type of UI elements."""
        elements = []
        
        # Text-based detection
        for text_pattern in pattern.get("text_patterns", []):
            matches = re.finditer(rf"\b{re.escape(text_pattern)}\b", text, re.IGNORECASE)
            
            for match in matches:
                # Estimate bounds based on text position
                # This is simplified - real implementation would use text localization
                bounds = await self._estimate_element_bounds(screen, match.start(), match.end())
                
                element = UIElement(
                    element_type=element_type,
                    confidence=0.7,
                    bounds=bounds,
                    text=match.group(),
                    is_clickable=element_type in ["button", "menu", "search_box"]
                )
                
                elements.append(element)
        
        # Visual detection
        visual_elements = await self._detect_visual_elements(screen, element_type, pattern)
        elements.extend(visual_elements)
        
        return elements
    
    async def _estimate_element_bounds(self, screen: np.ndarray, start_pos: int, 
                                     end_pos: int) -> Tuple[int, int, int, int]:
        """Estimate UI element bounds based on text position."""
        # Simplified estimation - real implementation would use more sophisticated methods
        height, width = screen.shape[:2]
        
        # Assume text is distributed evenly across screen
        chars_per_line = 80  # Estimate
        lines = height // 20  # Estimate line height
        
        line_num = start_pos // chars_per_line
        char_in_line = start_pos % chars_per_line
        
        x = int((char_in_line / chars_per_line) * width)
        y = int((line_num / lines) * height)
        w = int(((end_pos - start_pos) / chars_per_line) * width)
        h = 20  # Estimated element height
        
        return (x, y, w, h)
    
    async def _detect_visual_elements(self, screen: np.ndarray, element_type: str,
                                    pattern: Dict[str, Any]) -> List[UIElement]:
        """Detect UI elements using visual cues."""
        elements = []
        
        # Convert to grayscale for edge detection
        if len(screen.shape) == 3:
            gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
        else:
            gray = screen
        
        # Edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        size_min, size_max = pattern.get("size_range", (20, 200))
        
        for contour in contours:
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter by size
            if size_min <= w <= size_max and size_min <= h <= size_max:
                # Calculate confidence based on shape and visual cues
                confidence = await self._calculate_visual_confidence(
                    gray[y:y+h, x:x+w], element_type, pattern
                )
                
                if confidence > 0.5:
                    element = UIElement(
                        element_type=element_type,
                        confidence=confidence,
                        bounds=(x, y, w, h),
                        is_clickable=element_type in ["button", "menu", "search_box"]
                    )
                    elements.append(element)
        
        return elements
    
    async def _calculate_visual_confidence(self, element_region: np.ndarray, 
                                         element_type: str, pattern: Dict[str, Any]) -> float:
        """Calculate confidence for visual element detection."""
        confidence = 0.0
        
        # Basic shape analysis
        if element_type == "button":
            # Look for rectangular shapes with uniform color
            if element_region.size > 0:
                std_dev = np.std(element_region)
                if std_dev < 30:  # Uniform color
                    confidence += 0.3
                
                # Check for rounded corners (simplified)
                height, width = element_region.shape
                if 0.3 <= height/width <= 3.0:  # Reasonable aspect ratio
                    confidence += 0.4
        
        elif element_type == "input_field":
            # Look for white/light background with borders
            if element_region.size > 0:
                mean_intensity = np.mean(element_region)
                if mean_intensity > 200:  # Light background
                    confidence += 0.5
        
        return confidence
    
    async def _filter_and_rank_elements(self, elements: List[UIElement]) -> List[UIElement]:
        """Filter overlapping elements and rank by confidence."""
        # Remove overlapping elements (keep highest confidence)
        filtered = []
        
        for element in sorted(elements, key=lambda x: x.confidence, reverse=True):
            overlap = False
            for existing in filtered:
                if self._elements_overlap(element.bounds, existing.bounds):
                    overlap = True
                    break
            
            if not overlap:
                filtered.append(element)
        
        return filtered
    
    def _elements_overlap(self, bounds1: Tuple[int, int, int, int], 
                         bounds2: Tuple[int, int, int, int]) -> bool:
        """Check if two element bounds overlap significantly."""
        x1, y1, w1, h1 = bounds1
        x2, y2, w2, h2 = bounds2
        
        # Calculate overlap area
        left = max(x1, x2)
        top = max(y1, y2)
        right = min(x1 + w1, x2 + w2)
        bottom = min(y1 + h1, y2 + h2)
        
        if left < right and top < bottom:
            overlap_area = (right - left) * (bottom - top)
            area1 = w1 * h1
            area2 = w2 * h2
            
            # Consider overlapping if more than 50% of smaller element overlaps
            min_area = min(area1, area2)
            return overlap_area / min_area > 0.5
        
        return False
    
    async def _perform_ocr(self, screen: np.ndarray) -> str:
        """Perform OCR on screen image."""
        # Placeholder for OCR functionality
        return "OCR extracted text placeholder"

class ApplicationNavigator:
    """Navigates and interacts with detected applications."""
    
    def __init__(self, backend_instance):
        self.backend = backend_instance
        self.detector = ApplicationDetector(backend_instance)
        self.ui_detector = UIElementDetector(backend_instance)
        self.logger = logging.getLogger(f"{__name__}.ApplicationNavigator")
    
    async def navigate_to_application(self, app_name: str) -> bool:
        """Navigate to or activate a specific application."""
        self.logger.info(f"Navigating to application: {app_name}")
        
        # First, check if app is already visible
        applications = await self.detector.detect_applications()
        
        for app in applications:
            if app.name.lower() == app_name.lower():
                if app.is_active:
                    self.logger.info(f"{app_name} is already active")
                    return True
                else:
                    # Try to activate the window
                    return await self._activate_application(app)
        
        # App not visible, try to launch it
        return await self._launch_application(app_name)
    
    async def find_and_interact_with_element(self, app_name: str, element_type: str, 
                                           element_text: Optional[str] = None) -> bool:
        """Find and interact with a specific UI element."""
        self.logger.info(f"Looking for {element_type} in {app_name}")
        
        # Get application info
        applications = await self.detector.detect_applications()
        target_app = None
        
        for app in applications:
            if app.name.lower() == app_name.lower():
                target_app = app
                break
        
        if not target_app:
            self.logger.error(f"Application {app_name} not found")
            return False
        
        # Detect UI elements
        elements = await self.ui_detector.detect_elements(target_app)
        
        # Find matching element
        target_element = None
        for element in elements:
            if element.element_type == element_type:
                if element_text is None or (element.text and element_text.lower() in element.text.lower()):
                    target_element = element
                    break
        
        if not target_element:
            self.logger.error(f"Element {element_type} not found in {app_name}")
            return False
        
        # Interact with element
        return await self._interact_with_element(target_element)
    
    async def perform_application_search(self, app_name: str, search_terms: List[str]) -> bool:
        """Perform search within an application."""
        self.logger.info(f"Performing search in {app_name}: {search_terms}")
        
        # Navigate to application
        if not await self.navigate_to_application(app_name):
            return False
        
        # Find search box
        if not await self.find_and_interact_with_element(app_name, "search_box"):
            # Try activating search with keyboard shortcut
            search_action = {
                "type": "keyboard_shortcut",
                "shortcut": "cmd+f"
            }
            await self.backend.execute_action_with_verification(search_action)
            await asyncio.sleep(1)
        
        # Type search terms
        search_query = " ".join(search_terms)
        type_action = {
            "type": "type_text",
            "text": search_query
        }
        
        result = await self.backend.execute_action_with_verification(type_action)
        
        if result.get("success"):
            # Press Enter to execute search
            enter_action = {
                "type": "keyboard_key",
                "key": "Return"
            }
            await self.backend.execute_action_with_verification(enter_action)
            return True
        
        return False
    
    async def _activate_application(self, app_info: ApplicationInfo) -> bool:
        """Activate/focus an application window."""
        # Click on the application window to activate it
        x, y, w, h = app_info.window_bounds
        center_x = x + w // 2
        center_y = y + h // 2
        
        click_action = {
            "type": "click",
            "coordinates": (center_x, center_y)
        }
        
        result = await self.backend.execute_action_with_verification(click_action)
        return result.get("success", False)
    
    async def _launch_application(self, app_name: str) -> bool:
        """Launch an application."""
        # Try using Spotlight (macOS) or Start Menu (Windows)
        launch_actions = [
            {"type": "keyboard_shortcut", "shortcut": "cmd+space"},  # Spotlight
            {"type": "keyboard_shortcut", "shortcut": "win"}  # Start Menu
        ]
        
        for launch_action in launch_actions:
            result = await self.backend.execute_action_with_verification(launch_action)
            
            if result.get("success"):
                await asyncio.sleep(1)
                
                # Type application name
                type_action = {
                    "type": "type_text",
                    "text": app_name
                }
                
                await self.backend.execute_action_with_verification(type_action)
                await asyncio.sleep(1)
                
                # Press Enter to launch
                enter_action = {
                    "type": "keyboard_key",
                    "key": "Return"
                }
                
                launch_result = await self.backend.execute_action_with_verification(enter_action)
                
                if launch_result.get("success"):
                    await asyncio.sleep(3)  # Wait for app to launch
                    return True
        
        return False
    
    async def _interact_with_element(self, element: UIElement) -> bool:
        """Interact with a UI element."""
        if not element.is_clickable:
            self.logger.warning(f"Element {element.element_type} is not clickable")
            return False
        
        # Click on the element
        x, y, w, h = element.bounds
        center_x = x + w // 2
        center_y = y + h // 2
        
        click_action = {
            "type": "click",
            "coordinates": (center_x, center_y)
        }
        
        result = await self.backend.execute_action_with_verification(click_action)
        return result.get("success", False)

# Integration with existing backend
async def integrate_intelligent_app_detection(backend_instance):
    """
    Integrate intelligent application detection system into the existing backend.
    """
    navigator = ApplicationNavigator(backend_instance)
    detector = ApplicationDetector(backend_instance)
    ui_detector = UIElementDetector(backend_instance)
    
    # Add components to backend instance
    backend_instance.app_navigator = navigator
    backend_instance.app_detector = detector
    backend_instance.ui_detector = ui_detector
    
    # Add new handler methods
    async def detect_screen_applications(self) -> List[ApplicationInfo]:
        """Detect all applications visible on screen."""
        return await self.app_detector.detect_applications()
    
    async def navigate_to_app(self, app_name: str) -> bool:
        """Navigate to a specific application."""
        return await self.app_navigator.navigate_to_application(app_name)
    
    async def find_ui_element(self, app_name: str, element_type: str, 
                            element_text: Optional[str] = None) -> bool:
        """Find and interact with a UI element."""
        return await self.app_navigator.find_and_interact_with_element(
            app_name, element_type, element_text
        )
    
    # Bind methods to backend instance
    import types
    backend_instance.detect_screen_applications = types.MethodType(
        detect_screen_applications, backend_instance
    )
    backend_instance.navigate_to_app = types.MethodType(
        navigate_to_app, backend_instance
    )
    backend_instance.find_ui_element = types.MethodType(
        find_ui_element, backend_instance
    )
    
    return backend_instance

if __name__ == "__main__":
    # Test the detection system
    async def test_detection():
        print("Intelligent Application Detection System initialized")
        print("Components:")
        print("  - ApplicationDetector: Detects applications on screen")
        print("  - UIElementDetector: Detects UI elements within applications")
        print("  - ApplicationNavigator: Navigates and interacts with applications")
    
    asyncio.run(test_detection())