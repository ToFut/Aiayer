#!/usr/bin/env python3
"""
Unified UI Detection API - A simplified interface for accessing all UI detection capabilities
with improved accuracy and accessibility

Features:
1. Simplified API for UI element detection
2. Improved classification for buttons, inputs, and forms
3. Better browser integration
4. Specialized detection patterns
5. Performance optimizations
6. Accessibility support
"""

import os
import sys
import json
import time
import logging
import asyncio
import base64
import hashlib
from typing import Dict, Any, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field, asdict, fields
from PIL import Image
import numpy as np
import pyautogui

# Configure logging
os.makedirs('logs/sensors', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sensors/unified_ui_detection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("unified_ui_detection")

# Try importing optional dependencies, but don't fail if missing
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV (cv2) not available - some visual detection features limited")

try:
    import easyocr
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logger.warning("EasyOCR not available - text recognition features limited")

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    BROWSER_AUTOMATION_AVAILABLE = True
except ImportError:
    BROWSER_AUTOMATION_AVAILABLE = False
    logger.warning("Selenium not available - browser-based detection limited")

try:
    # Platform-specific accessibility imports
    if sys.platform == "darwin":  # macOS
        import Quartz
        from ApplicationServices import AXUIElementCreateSystemWide
        ACCESSIBILITY_AVAILABLE = True
    elif sys.platform == "win32":  # Windows
        import win32gui
        import win32con
        ACCESSIBILITY_AVAILABLE = True
    else:  # Linux
        try:
            import pyatspi
            ACCESSIBILITY_AVAILABLE = True
        except ImportError:
            ACCESSIBILITY_AVAILABLE = False
    
    if ACCESSIBILITY_AVAILABLE:
        logger.info(f"Accessibility APIs available for platform: {sys.platform}")
    else:
        logger.warning(f"Accessibility APIs not available for platform: {sys.platform}")
except ImportError:
    ACCESSIBILITY_AVAILABLE = False
    logger.warning("Accessibility APIs not available - platform integration limited")

@dataclass
class UIElement:
    """Unified representation of a detected UI element"""
    element_id: str
    element_type: str
    text: str = ""
    bounding_box: Optional[List[int]] = None  # [x1, y1, x2, y2]
    center_point: Optional[Tuple[int, int]] = None
    confidence: float = 0.0
    
    # Enhanced properties
    role: str = ""  # Accessibility role
    state: str = ""  # e.g., "enabled", "disabled", "focused"
    properties: Dict[str, Any] = field(default_factory=dict)
    children: List[str] = field(default_factory=list)  # IDs of child elements
    parent_id: str = ""
    
    # Detection metadata
    detection_method: str = ""
    detection_time: float = 0.0
    
    # Interaction hints
    can_click: bool = False
    can_type: bool = False
    can_scroll: bool = False
    placeholder: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, ensuring all values are JSON serializable"""
        result = asdict(self)
        # Convert numpy values to Python native types
        for key, value in result.items():
            if isinstance(value, np.integer):
                result[key] = int(value)
            elif isinstance(value, np.floating):
                result[key] = float(value)
            elif isinstance(value, np.ndarray):
                result[key] = value.tolist()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UIElement':
        """Create from dictionary"""
        # Filter out keys not in the dataclass
        valid_keys = {f.name for f in fields(cls)}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered_data)

@dataclass
class DetectionResult:
    """Result from a UI detection operation"""
    timestamp: float
    elements: List[UIElement]
    screenshot_hash: str = ""
    detection_methods: List[str] = field(default_factory=list)
    detection_time: float = 0.0
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, ensuring all values are JSON serializable"""
        return {
            "timestamp": self.timestamp,
            "elements": [elem.to_dict() for elem in self.elements],
            "screenshot_hash": self.screenshot_hash,
            "detection_methods": self.detection_methods,
            "detection_time": self.detection_time,
            "context": self.context
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DetectionResult':
        """Create from dictionary"""
        elements = [UIElement.from_dict(elem) for elem in data.get("elements", [])]
        return cls(
            timestamp=data.get("timestamp", time.time()),
            elements=elements,
            screenshot_hash=data.get("screenshot_hash", ""),
            detection_methods=data.get("detection_methods", []),
            detection_time=data.get("detection_time", 0.0),
            context=data.get("context", {})
        )
    
    def get_elements_by_type(self, element_type: str) -> List[UIElement]:
        """Get all elements of a specific type"""
        return [elem for elem in self.elements if elem.element_type == element_type]
    
    def get_element_by_id(self, element_id: str) -> Optional[UIElement]:
        """Get element by ID"""
        for elem in self.elements:
            if elem.element_id == element_id:
                return elem
        return None
    
    def get_elements_containing_text(self, text: str, case_sensitive: bool = False) -> List[UIElement]:
        """Get elements containing the specified text"""
        if not case_sensitive:
            text = text.lower()
            return [elem for elem in self.elements if text in elem.text.lower()]
        return [elem for elem in self.elements if text in elem.text]
    
    def count_by_type(self) -> Dict[str, int]:
        """Count elements by type"""
        counts = {}
        for elem in self.elements:
            counts[elem.element_type] = counts.get(elem.element_type, 0) + 1
        return counts

class ElementClassifier:
    """Improved classifier for UI element types"""
    
    def __init__(self):
        # Element type patterns (text content that suggests element type)
        self.button_patterns = [
            "button", "submit", "click", "send", "search", "post", "add", "create", 
            "delete", "remove", "update", "cancel", "save", "ok", "yes", "no", "apply"
        ]
        
        self.input_patterns = [
            "input", "enter", "type", "text", "field", "name", "email", "password",
            "phone", "address", "search", "query", "message"
        ]
        
        self.dropdown_patterns = [
            "select", "dropdown", "choose", "option", "menu", "list"
        ]
        
        self.checkbox_patterns = [
            "checkbox", "check", "toggle", "enable", "agree", "terms", "remember"
        ]
        
        self.radio_patterns = [
            "radio", "option", "select one", "choose one"
        ]
        
        self.link_patterns = [
            "link", "href", "url", "visit", "click here", "learn more", "details", "view"
        ]
        
        self.form_patterns = [
            "form", "submit", "registration", "contact", "login", "sign", "register"
        ]
    
    def classify_by_content(self, text: str, tag_name: str = "", attributes: Dict[str, str] = None) -> Tuple[str, float]:
        """Classify element type by content and attributes"""
        if attributes is None:
            attributes = {}
        
        text = text.lower()
        tag_name = tag_name.lower()
        
        # First check HTML tags and attributes (most reliable)
        if tag_name in ["button", "input"] and attributes.get("type") == "button":
            return "button", 0.95
        elif tag_name == "a" or attributes.get("href"):
            return "link", 0.95
        elif tag_name == "input":
            input_type = attributes.get("type", "").lower()
            if input_type in ["text", "email", "password", "tel", "url", "search"]:
                return "textfield", 0.95
            elif input_type == "checkbox":
                return "checkbox", 0.95
            elif input_type == "radio":
                return "radio", 0.95
            elif input_type in ["submit", "button", "reset"]:
                return "button", 0.95
        elif tag_name == "textarea":
            return "textfield", 0.95
        elif tag_name == "select":
            return "dropdown", 0.95
        elif tag_name == "form":
            return "form", 0.95
        
        # If no HTML clues, analyze text content
        confidence = 0.7  # Base confidence for text analysis
        
        # Check element role or class attributes for clues
        role = attributes.get("role", "").lower()
        class_name = attributes.get("class", "").lower()
        
        if role in ["button", "link", "textbox", "combobox", "checkbox", "radio", "form"]:
            element_type = {"textbox": "textfield", "combobox": "dropdown"}.get(role, role)
            return element_type, 0.9
        
        # Check class name for clues
        if any(pattern in class_name for pattern in ["btn", "button"]):
            return "button", 0.85
        elif any(pattern in class_name for pattern in ["input", "text-field", "form-control"]):
            return "textfield", 0.85
        elif any(pattern in class_name for pattern in ["dropdown", "select"]):
            return "dropdown", 0.85
        elif any(pattern in class_name for pattern in ["checkbox", "check"]):
            return "checkbox", 0.85
        elif any(pattern in class_name for pattern in ["radio"]):
            return "radio", 0.85
        elif any(pattern in class_name for pattern in ["link", "nav-link"]):
            return "link", 0.85
        elif any(pattern in class_name for pattern in ["form"]):
            return "form", 0.85
        
        # Text content analysis
        for pattern in self.button_patterns:
            if pattern in text:
                return "button", confidence
        
        for pattern in self.input_patterns:
            if pattern in text:
                return "textfield", confidence
        
        for pattern in self.dropdown_patterns:
            if pattern in text:
                return "dropdown", confidence
        
        for pattern in self.checkbox_patterns:
            if pattern in text:
                return "checkbox", confidence
        
        for pattern in self.radio_patterns:
            if pattern in text:
                return "radio", confidence
        
        for pattern in self.link_patterns:
            if pattern in text:
                return "link", confidence
        
        for pattern in self.form_patterns:
            if pattern in text:
                return "form", confidence
        
        # If still unknown, use visual clues and size
        return "unknown", 0.5
    
    def classify_by_visual(self, shape_data: Dict[str, Any]) -> Tuple[str, float]:
        """Classify element type by visual characteristics"""
        width = shape_data.get("width", 0)
        height = shape_data.get("height", 0)
        aspect_ratio = width / max(height, 1)  # Avoid division by zero
        
        # Common UI patterns based on shape
        if 20 <= width <= 200 and 20 <= height <= 60 and 1.5 <= aspect_ratio <= 5:
            return "button", 0.7
        elif width > 150 and 20 <= height <= 40:
            return "textfield", 0.7
        elif 20 <= width <= 200 and 20 <= height <= 40 and aspect_ratio > 3:
            return "dropdown", 0.65
        elif 10 <= width <= 30 and 10 <= height <= 30 and 0.8 <= aspect_ratio <= 1.2:
            return "checkbox", 0.65
        elif width > 300 and height > 100:
            return "form", 0.6
        
        return "unknown", 0.5

class BrowserDetector:
    """Improved browser-based UI element detection"""
    
    def __init__(self):
        self.available = BROWSER_AUTOMATION_AVAILABLE
        self.driver = None
        self.classifier = ElementClassifier()
    
    async def initialize(self) -> bool:
        """Initialize browser detector"""
        if not self.available:
            return False
        
        try:
            # Try connecting to existing session
            chrome_options = ChromeOptions()
            chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
            
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
                logger.info("Connected to existing Chrome session")
                return True
            except Exception as e:
                logger.warning(f"Failed to connect to existing Chrome session: {e}")
                
                # Start new Chrome session with minimal overhead
                chrome_options = ChromeOptions()
                chrome_options.add_argument("--remote-debugging-port=9222")
                chrome_options.add_argument("--headless=new")  # Use headless mode for better performance
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                
                self.driver = webdriver.Chrome(options=chrome_options)
                logger.info("Started new Chrome session (headless)")
                return True
                
        except Exception as e:
            logger.error(f"Error initializing browser detector: {e}")
            return False
    
    async def detect_elements(self, url: Optional[str] = None) -> List[UIElement]:
        """Detect elements in the browser"""
        if not self.driver:
            if not await self.initialize():
                return []
        
        try:
            # Navigate to URL if provided
            if url:
                self.driver.get(url)
                # Wait for page to load
                time.sleep(2)
            
            elements = []
            element_id_counter = 0
            
            # Find all interactive elements
            interactive_selectors = [
                ("button", By.TAG_NAME, "button"),
                ("input_submit", By.CSS_SELECTOR, "input[type='submit']"),
                ("input_button", By.CSS_SELECTOR, "input[type='button']"),
                ("input_text", By.CSS_SELECTOR, "input[type='text']"),
                ("input_email", By.CSS_SELECTOR, "input[type='email']"),
                ("input_password", By.CSS_SELECTOR, "input[type='password']"),
                ("input_checkbox", By.CSS_SELECTOR, "input[type='checkbox']"),
                ("input_radio", By.CSS_SELECTOR, "input[type='radio']"),
                ("textarea", By.TAG_NAME, "textarea"),
                ("select", By.TAG_NAME, "select"),
                ("a", By.TAG_NAME, "a"),
                ("form", By.TAG_NAME, "form"),
                ("div_button", By.CSS_SELECTOR, "div[role='button']"),
                ("div_clickable", By.CSS_SELECTOR, "div.clickable, div.btn, div.button")
            ]
            
            for (elem_key, by_method, selector) in interactive_selectors:
                try:
                    dom_elements = self.driver.find_elements(by_method, selector)
                    
                    for dom_elem in dom_elements:
                        try:
                            # Extract element attributes
                            tag_name = dom_elem.tag_name
                            elem_text = dom_elem.text.strip()
                            
                            # Extract important attributes
                            attributes = {
                                "id": dom_elem.get_attribute("id") or "",
                                "class": dom_elem.get_attribute("class") or "",
                                "type": dom_elem.get_attribute("type") or "",
                                "role": dom_elem.get_attribute("role") or "",
                                "name": dom_elem.get_attribute("name") or "",
                                "placeholder": dom_elem.get_attribute("placeholder") or "",
                                "value": dom_elem.get_attribute("value") or "",
                                "href": dom_elem.get_attribute("href") or ""
                            }
                            
                            # Skip elements without text or key attributes
                            if not (elem_text or attributes["id"] or attributes["placeholder"] or attributes["value"]):
                                continue
                            
                            # Try to get location and size
                            try:
                                location = dom_elem.location
                                size = dom_elem.size
                                
                                x1 = location["x"]
                                y1 = location["y"]
                                x2 = x1 + size["width"]
                                y2 = y1 + size["height"]
                                
                                bounding_box = [x1, y1, x2, y2]
                                center_point = (x1 + size["width"] // 2, y1 + size["height"] // 2)
                            except:
                                bounding_box = None
                                center_point = None
                            
                            # Get element state
                            is_enabled = dom_elem.is_enabled()
                            is_displayed = dom_elem.is_displayed()
                            
                            state = "enabled" if is_enabled else "disabled"
                            if not is_displayed:
                                state += "_hidden"
                            
                            # Determine element type
                            element_type, confidence = self.classifier.classify_by_content(
                                elem_text or attributes["placeholder"] or attributes["value"], 
                                tag_name, 
                                attributes
                            )
                            
                            # Create element object
                            ui_element = UIElement(
                                element_id=f"dom_{element_id_counter}",
                                element_type=element_type,
                                text=elem_text or attributes["placeholder"] or attributes["value"],
                                bounding_box=bounding_box,
                                center_point=center_point,
                                confidence=confidence,
                                role=attributes["role"] or tag_name,
                                state=state,
                                properties=attributes,
                                detection_method="browser_api",
                                detection_time=time.time(),
                                can_click=element_type in ["button", "link", "checkbox", "radio"],
                                can_type=element_type in ["textfield", "textarea"],
                                can_scroll=tag_name in ["div", "ul", "ol"],
                                placeholder=attributes["placeholder"]
                            )
                            
                            elements.append(ui_element)
                            element_id_counter += 1
                        
                        except Exception as e:
                            logger.warning(f"Error processing DOM element: {e}")
                            continue
                
                except Exception as e:
                    logger.warning(f"Error finding elements with selector '{selector}': {e}")
            
            logger.info(f"Browser detector found {len(elements)} elements")
            return elements
            
        except Exception as e:
            logger.error(f"Error detecting browser elements: {e}")
            return []

class AccessibilityDetector:
    """Enhanced accessibility API-based detection"""
    
    def __init__(self):
        self.available = ACCESSIBILITY_AVAILABLE
    
    async def get_accessibility_tree(self) -> Dict[str, Any]:
        """Get the accessibility tree for the current application"""
        if not self.available:
            return {}
        
        try:
            if sys.platform == "darwin":
                return await self._get_macos_accessibility_tree()
            elif sys.platform == "win32":
                return await self._get_windows_accessibility_tree()
            else:
                return await self._get_linux_accessibility_tree()
        except Exception as e:
            logger.error(f"Error getting accessibility tree: {e}")
            return {}
    
    async def _get_macos_accessibility_tree(self) -> Dict[str, Any]:
        """Get accessibility tree on macOS"""
        try:
            # Create system-wide accessibility element
            system_element = AXUIElementCreateSystemWide()
            
            # This is a simplified implementation that would need to be expanded
            # with proper macOS accessibility API calls to build the full tree
            return {
                "platform": "macOS",
                "elements": []  # This would contain actual accessibility elements
            }
        except Exception as e:
            logger.error(f"macOS accessibility error: {e}")
            return {}
    
    async def _get_windows_accessibility_tree(self) -> Dict[str, Any]:
        """Get accessibility tree on Windows"""
        try:
            # Get foreground window
            hwnd = win32gui.GetForegroundWindow()
            window_text = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            
            # This is a simplified implementation that would need to be expanded
            # with proper Windows accessibility API calls to build the full tree
            return {
                "platform": "Windows",
                "foreground_window": {
                    "handle": hwnd,
                    "title": window_text,
                    "class": class_name
                },
                "elements": []  # This would contain actual accessibility elements
            }
        except Exception as e:
            logger.error(f"Windows accessibility error: {e}")
            return {}
    
    async def _get_linux_accessibility_tree(self) -> Dict[str, Any]:
        """Get accessibility tree on Linux"""
        try:
            # This would require proper AT-SPI implementation
            return {
                "platform": "Linux",
                "elements": []  # This would contain actual accessibility elements
            }
        except Exception as e:
            logger.error(f"Linux accessibility error: {e}")
            return {}
    
    async def detect_elements(self) -> List[UIElement]:
        """Detect elements using accessibility APIs"""
        if not self.available:
            return []
        
        tree = await self.get_accessibility_tree()
        
        # This is a placeholder that would need to be implemented
        # to convert accessibility tree to UIElement objects
        return []

class OCRDetector:
    """Text recognition-based UI element detection"""
    
    def __init__(self):
        self.available = OCR_AVAILABLE
        self.reader = None
        self.classifier = ElementClassifier()
        
        if self.available:
            try:
                self.reader = easyocr.Reader(['en'])
                logger.info("OCR detector initialized")
            except Exception as e:
                logger.error(f"Error initializing OCR detector: {e}")
                self.available = False
    
    async def detect_elements(self, image_path: str) -> List[UIElement]:
        """Detect elements using OCR"""
        if not self.available or not self.reader:
            return []
        
        try:
            # Run OCR on image
            results = self.reader.readtext(image_path)
            
            elements = []
            element_id_counter = 0
            
            for (bbox, text, confidence) in results:
                if confidence < 0.5:  # Skip low-confidence results
                    continue
                
                # Convert bbox to [x1, y1, x2, y2] format
                x_coords = [point[0] for point in bbox]
                y_coords = [point[1] for point in bbox]
                
                x1, x2 = min(x_coords), max(x_coords)
                y1, y2 = min(y_coords), max(y_coords)
                bounding_box = [int(x1), int(y1), int(x2), int(y2)]
                
                width = x2 - x1
                height = y2 - y1
                
                # Center point
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                center_point = (center_x, center_y)
                
                # Try to classify element type by text content
                element_type, type_confidence = self.classifier.classify_by_content(text)
                
                # If text classification gave low confidence, try visual classification
                if type_confidence < 0.6:
                    visual_type, visual_confidence = self.classifier.classify_by_visual({
                        "width": width,
                        "height": height
                    })
                    
                    if visual_confidence > type_confidence:
                        element_type = visual_type
                        type_confidence = visual_confidence
                
                # Create element
                ui_element = UIElement(
                    element_id=f"ocr_{element_id_counter}",
                    element_type=element_type,
                    text=text,
                    bounding_box=bounding_box,
                    center_point=center_point,
                    confidence=confidence * type_confidence,  # Combined confidence
                    detection_method="ocr",
                    detection_time=time.time(),
                    can_click=element_type in ["button", "link", "checkbox", "radio"],
                    can_type=element_type in ["textfield", "textarea"]
                )
                
                elements.append(ui_element)
                element_id_counter += 1
            
            logger.info(f"OCR detector found {len(elements)} elements")
            return elements
            
        except Exception as e:
            logger.error(f"Error in OCR detection: {e}")
            return []

class CVDetector:
    """Computer vision-based UI element detection"""
    
    def __init__(self):
        self.available = CV2_AVAILABLE
        self.classifier = ElementClassifier()
    
    async def detect_elements(self, image_path: str) -> List[UIElement]:
        """Detect elements using computer vision"""
        if not self.available:
            return []
        
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Failed to load image: {image_path}")
                return []
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            elements = []
            element_id_counter = 0
            
            # Detect buttons (rectangles with rounded corners)
            binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                
                # Filter by size (buttons are usually medium-sized)
                if 500 < area < 20000:
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    
                    # Typical button aspect ratios
                    if 1.5 < aspect_ratio < 6 and h > 20:
                        element_type = "button"
                        confidence = 0.7
                        
                        # Create element
                        ui_element = UIElement(
                            element_id=f"cv_{element_id_counter}",
                            element_type=element_type,
                            text="",  # No text available from CV detection
                            bounding_box=[x, y, x+w, y+h],
                            center_point=(x + w//2, y + h//2),
                            confidence=confidence,
                            detection_method="computer_vision",
                            detection_time=time.time(),
                            can_click=True
                        )
                        
                        elements.append(ui_element)
                        element_id_counter += 1
            
            # Detect input fields (rectangles with consistent borders)
            edges = cv2.Canny(gray, 50, 150)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)
            
            # This is a simplified approach that would need to be expanded
            # with more sophisticated algorithms to detect various UI elements
            
            logger.info(f"CV detector found {len(elements)} elements")
            return elements
            
        except Exception as e:
            logger.error(f"Error in CV detection: {e}")
            return []

class UnifiedUIDetectionAPI:
    """Main unified API for UI element detection"""
    
    def __init__(self, cache_dir: str = "cache/ui_detection"):
        self.browser_detector = BrowserDetector()
        self.accessibility_detector = AccessibilityDetector()
        self.ocr_detector = OCRDetector()
        self.cv_detector = CVDetector()
        self.classifier = ElementClassifier()
        
        # Create cache directory
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # Detection configuration
        self.detection_methods = {
            "browser": True,
            "accessibility": True,
            "ocr": True,
            "cv": True
        }
        
        logger.info("Unified UI Detection API initialized")
    
    def enable_detection_method(self, method: str, enabled: bool = True):
        """Enable or disable a detection method"""
        if method in self.detection_methods:
            self.detection_methods[method] = enabled
            logger.info(f"Detection method '{method}' {'enabled' if enabled else 'disabled'}")
    
    async def detect_ui_elements(self, 
                                image_path: Optional[str] = None, 
                                url: Optional[str] = None,
                                context: Optional[Dict[str, Any]] = None) -> DetectionResult:
        """Main method to detect UI elements using all available methods"""
        start_time = time.time()
        
        # If neither image nor URL provided, take screenshot
        if not image_path and not url:
            image_path = f"{self.cache_dir}/screenshot_{int(time.time())}.png"
            pyautogui.screenshot().save(image_path)
            logger.info(f"Captured screenshot: {image_path}")
        
        # Initialize result
        result = DetectionResult(
            timestamp=time.time(),
            elements=[],
            context=context or {}
        )
        
        # Calculate image hash if available
        if image_path:
            try:
                with open(image_path, "rb") as f:
                    image_data = f.read()
                    result.screenshot_hash = hashlib.md5(image_data).hexdigest()
            except Exception as e:
                logger.error(f"Error calculating image hash: {e}")
        
        # Run detection methods in parallel
        tasks = []
        
        if self.detection_methods["browser"] and url:
            tasks.append(self.browser_detector.detect_elements(url))
        elif self.detection_methods["browser"]:
            tasks.append(self.browser_detector.detect_elements())
        
        if self.detection_methods["accessibility"]:
            tasks.append(self.accessibility_detector.detect_elements())
        
        if self.detection_methods["ocr"] and image_path:
            tasks.append(self.ocr_detector.detect_elements(image_path))
        
        if self.detection_methods["cv"] and image_path:
            tasks.append(self.cv_detector.detect_elements(image_path))
        
        # Execute all detection methods
        all_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        all_elements = []
        used_methods = []
        
        for i, res in enumerate(all_results):
            if isinstance(res, Exception):
                logger.error(f"Detection method {i} failed: {res}")
                continue
            
            if isinstance(res, list):
                all_elements.extend(res)
                
                # Track which detection methods were used
                if res:
                    method = res[0].detection_method
                    if method not in used_methods:
                        used_methods.append(method)
        
        # Deduplicate and merge elements
        merged_elements = self._merge_duplicate_elements(all_elements)
        result.elements = merged_elements
        result.detection_methods = used_methods
        result.detection_time = time.time() - start_time
        
        # Save result
        self._save_result(result)
        
        logger.info(f"UI detection completed: {len(result.elements)} elements found using {', '.join(used_methods)}")
        logger.info(f"Detection time: {result.detection_time:.2f}s")
        
        return result
    
    def _merge_duplicate_elements(self, elements: List[UIElement]) -> List[UIElement]:
        """Merge duplicate elements (same position or very similar)"""
        if not elements:
            return []
        
        # Group by position (if elements overlap significantly, they're likely the same)
        position_groups = {}
        
        for elem in elements:
            if not elem.bounding_box:
                continue
            
            x1, y1, x2, y2 = elem.bounding_box
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            
            # Use grid-based position grouping (round to nearest 20 pixels)
            grid_key = (center_x // 20, center_y // 20)
            
            if grid_key not in position_groups:
                position_groups[grid_key] = []
            
            position_groups[grid_key].append(elem)
        
        # Merge elements in each position group
        merged_elements = []
        
        for group in position_groups.values():
            if len(group) == 1:
                merged_elements.append(group[0])
            else:
                # Sort by confidence
                group.sort(key=lambda e: e.confidence, reverse=True)
                
                # Start with the highest confidence element
                best_elem = group[0]
                
                # Combine properties from other elements
                for other_elem in group[1:]:
                    # Use text from other element if best element has none
                    if not best_elem.text and other_elem.text:
                        best_elem.text = other_elem.text
                    
                    # Use element type from other element if best element is unknown
                    if best_elem.element_type == "unknown" and other_elem.element_type != "unknown":
                        best_elem.element_type = other_elem.element_type
                    
                    # Combine detection methods
                    if other_elem.detection_method and other_elem.detection_method != best_elem.detection_method:
                        best_elem.detection_method = f"{best_elem.detection_method},{other_elem.detection_method}"
                    
                    # Use role from other element if best element has none
                    if not best_elem.role and other_elem.role:
                        best_elem.role = other_elem.role
                    
                    # Combine interaction capabilities
                    best_elem.can_click = best_elem.can_click or other_elem.can_click
                    best_elem.can_type = best_elem.can_type or other_elem.can_type
                    best_elem.can_scroll = best_elem.can_scroll or other_elem.can_scroll
                
                merged_elements.append(best_elem)
        
        # Add elements without bounding boxes
        for elem in elements:
            if not elem.bounding_box:
                merged_elements.append(elem)
        
        return merged_elements
    
    def _save_result(self, result: DetectionResult):
        """Save detection result to cache"""
        try:
            filename = f"{self.cache_dir}/detection_{int(result.timestamp)}.json"
            
            with open(filename, 'w') as f:
                json.dump(result.to_dict(), f, indent=2)
            
            # Also save as latest
            with open(f"{self.cache_dir}/latest.json", 'w') as f:
                json.dump(result.to_dict(), f, indent=2)
            
            logger.info(f"Detection result saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving detection result: {e}")
    
    @staticmethod
    def load_result(filepath: str) -> DetectionResult:
        """Load detection result from file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            return DetectionResult.from_dict(data)
            
        except Exception as e:
            logger.error(f"Error loading detection result: {e}")
            return DetectionResult(timestamp=time.time(), elements=[])
    
    def get_latest_result(self) -> Optional[DetectionResult]:
        """Get the latest detection result"""
        latest_file = f"{self.cache_dir}/latest.json"
        
        if os.path.exists(latest_file):
            return self.load_result(latest_file)
        
        return None
    
    def find_element_by_text(self, text: str, result: Optional[DetectionResult] = None) -> Optional[UIElement]:
        """Find an element by text content"""
        if not result:
            result = self.get_latest_result()
        
        if not result:
            return None
        
        # Try exact match first
        for elem in result.elements:
            if elem.text == text:
                return elem
        
        # Try case-insensitive match
        for elem in result.elements:
            if elem.text.lower() == text.lower():
                return elem
        
        # Try contains match
        for elem in result.elements:
            if text.lower() in elem.text.lower():
                return elem
        
        return None
    
    def find_element_by_type(self, element_type: str, index: int = 0, result: Optional[DetectionResult] = None) -> Optional[UIElement]:
        """Find an element by type and index"""
        if not result:
            result = self.get_latest_result()
        
        if not result:
            return None
        
        elements = [elem for elem in result.elements if elem.element_type == element_type]
        
        if not elements or index >= len(elements):
            return None
        
        return elements[index]
    
    def find_element_at_position(self, x: int, y: int, result: Optional[DetectionResult] = None) -> Optional[UIElement]:
        """Find an element at the specified position"""
        if not result:
            result = self.get_latest_result()
        
        if not result:
            return None
        
        candidates = []
        
        for elem in result.elements:
            if not elem.bounding_box:
                continue
            
            x1, y1, x2, y2 = elem.bounding_box
            
            if x1 <= x <= x2 and y1 <= y <= y2:
                candidates.append(elem)
        
        if not candidates:
            return None
        
        # Return the smallest containing element (most specific)
        return min(candidates, key=lambda e: (e.bounding_box[2] - e.bounding_box[0]) * (e.bounding_box[3] - e.bounding_box[1]))
    
    def visualize_detection(self, result: DetectionResult, output_path: str, show_labels: bool = True):
        """Create a visualization of the detection result"""
        if not CV2_AVAILABLE:
            logger.error("OpenCV required for visualization")
            return False
        
        try:
            # Take screenshot if we don't have one
            screenshot_path = f"{self.cache_dir}/screenshot_for_vis_{int(time.time())}.png"
            pyautogui.screenshot().save(screenshot_path)
            
            # Load image
            image = cv2.imread(screenshot_path)
            
            # Draw bounding boxes
            for elem in result.elements:
                if not elem.bounding_box:
                    continue
                
                x1, y1, x2, y2 = elem.bounding_box
                
                # Color based on element type
                color_map = {
                    "button": (0, 255, 0),    # Green
                    "textfield": (255, 0, 0),  # Blue
                    "link": (0, 0, 255),       # Red
                    "checkbox": (255, 255, 0), # Cyan
                    "radio": (255, 0, 255),    # Magenta
                    "dropdown": (0, 255, 255), # Yellow
                    "form": (128, 128, 255),   # Light blue
                    "unknown": (128, 128, 128) # Gray
                }
                
                color = color_map.get(elem.element_type, (128, 128, 128))
                
                # Draw rectangle
                cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
                
                # Draw label
                if show_labels:
                    label = f"{elem.element_type}: {elem.text[:20]}" if elem.text else elem.element_type
                    cv2.putText(image, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            # Save image
            cv2.imwrite(output_path, image)
            
            # Clean up
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
            
            logger.info(f"Visualization saved to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating visualization: {e}")
            return False

# Create global API instance
ui_detection_api = UnifiedUIDetectionAPI()

async def main():
    """Main function for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Unified UI Detection API")
    parser.add_argument("--image", help="Path to image for analysis")
    parser.add_argument("--url", help="URL to analyze")
    parser.add_argument("--output", default="ui_detection_result.json", help="Output file path")
    parser.add_argument("--visualize", action="store_true", help="Create visualization")
    parser.add_argument("--vis-output", default="ui_detection_vis.png", help="Visualization output path")
    parser.add_argument("--methods", default="browser,accessibility,ocr,cv", 
                        help="Comma-separated list of detection methods to use")
    
    args = parser.parse_args()
    
    # Configure detection methods
    for method in ["browser", "accessibility", "ocr", "cv"]:
        enabled = method in args.methods.split(",")
        ui_detection_api.enable_detection_method(method, enabled)
    
    # Run detection
    result = await ui_detection_api.detect_ui_elements(args.image, args.url)
    
    # Print summary
    print(f"\n===== UI DETECTION RESULTS =====")
    print(f"Found {len(result.elements)} elements using methods: {', '.join(result.detection_methods)}")
    print(f"Detection time: {result.detection_time:.2f}s")
    
    # Count by type
    type_counts = result.count_by_type()
    print("\nElement counts by type:")
    for element_type, count in type_counts.items():
        print(f"  - {element_type}: {count}")
    
    # Save result
    with open(args.output, 'w') as f:
        json.dump(result.to_dict(), f, indent=2)
    print(f"\nFull results saved to {args.output}")
    
    # Create visualization if requested
    if args.visualize:
        ui_detection_api.visualize_detection(result, args.vis_output)
        print(f"Visualization saved to {args.vis_output}")
    
    return 0

if __name__ == "__main__":
    asyncio.run(main())