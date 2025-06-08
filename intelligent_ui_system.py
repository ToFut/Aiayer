#!/usr/bin/env python3
"""
Intelligent UI System
Advanced UI understanding and interaction system that mimics human-like intelligence
for interacting with any interface.
"""

import asyncio
import json
import time
import logging
import os
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import subprocess
import threading
import queue
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/intelligent_ui_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("intelligent_ui_system")

# Try to import platform-specific modules
try:
    # macOS specific imports
    import Quartz
    import AppKit
    import objc
    PLATFORM = "darwin"
    logger.info("✅ macOS specific modules loaded")
except ImportError:
    try:
        # Windows specific imports
        import win32gui
        import win32con
        import win32api
        PLATFORM = "win32"
        logger.info("✅ Windows specific modules loaded")
    except ImportError:
        try:
            # Linux specific imports
            import Xlib
            import Xlib.display
            PLATFORM = "linux"
            logger.info("✅ Linux specific modules loaded")
        except ImportError:
            PLATFORM = "unknown"
            logger.warning("⚠️ No platform-specific UI modules available")

# Try to import optional dependencies
try:
    import cv2
    import pytesseract
    import tensorflow as tf
    ML_AVAILABLE = True
    logger.info("✅ ML/CV dependencies loaded")
except ImportError:
    ML_AVAILABLE = False
    logger.warning("⚠️ ML/CV dependencies not available, some features will be limited")

try:
    import pyautogui
    INPUT_AVAILABLE = True
    logger.info("✅ Input automation dependencies loaded")
except ImportError:
    INPUT_AVAILABLE = False
    logger.warning("⚠️ Input automation dependencies not available")

@dataclass
class UIElement:
    """Comprehensive UI element representation with hierarchical information"""
    element_id: str
    element_type: str  # button, text_field, checkbox, dropdown, etc.
    text: Optional[str] = None
    bounds: Optional[Tuple[int, int, int, int]] = None  # x1, y1, x2, y2
    center: Optional[Tuple[int, int]] = None
    parent_id: Optional[str] = None
    children_ids: List[str] = None
    attributes: Dict[str, Any] = None
    confidence: float = 1.0
    z_index: int = 0
    visible: bool = True
    enabled: bool = True
    focused: bool = False
    last_updated: float = 0.0
    
    def __post_init__(self):
        if self.children_ids is None:
            self.children_ids = []
        if self.attributes is None:
            self.attributes = {}
        self.last_updated = time.time()
        
        # Calculate center if bounds are available but center isn't
        if self.bounds and not self.center:
            x1, y1, x2, y2 = self.bounds
            self.center = ((x1 + x2) // 2, (y1 + y2) // 2)

@dataclass
class UITree:
    """Hierarchical representation of the UI with complete element relationships"""
    elements: Dict[str, UIElement]
    root_id: str
    timestamp: float
    screenshot_path: Optional[str] = None
    window_title: Optional[str] = None
    application_name: Optional[str] = None
    
    def get_element_by_text(self, text: str, partial: bool = True) -> Optional[UIElement]:
        """Find element by text content"""
        for element_id, element in self.elements.items():
            if element.text:
                if partial and text.lower() in element.text.lower():
                    return element
                elif not partial and text.lower() == element.text.lower():
                    return element
        return None
    
    def get_elements_by_type(self, element_type: str) -> List[UIElement]:
        """Get all elements of a specific type"""
        return [element for element in self.elements.values() 
                if element.element_type == element_type and element.visible]
    
    def get_element_path(self, element_id: str) -> List[str]:
        """Get path from root to element"""
        path = []
        current_id = element_id
        
        while current_id and current_id != self.root_id:
            path.append(current_id)
            element = self.elements.get(current_id)
            if not element:
                break
            current_id = element.parent_id
            
        path.append(self.root_id)
        return list(reversed(path))
    
    def get_clickable_elements(self) -> List[UIElement]:
        """Get all elements that are typically clickable"""
        clickable_types = ["button", "link", "checkbox", "radio", "tab", "menu_item", "dropdown"]
        return [element for element in self.elements.values() 
                if element.element_type in clickable_types and element.visible and element.enabled]

@dataclass
class InteractionPlan:
    """Detailed plan for interacting with UI elements"""
    plan_id: str
    goal: str
    steps: List[Dict[str, Any]]
    target_elements: List[str]
    estimated_duration: float
    created_at: float = 0.0
    confidence: float = 0.0
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.time()

class AccessibilityAdapter:
    """Platform-specific accessibility API adapter"""
    
    def __init__(self):
        self.initialized = False
        self.platform = PLATFORM
        
        try:
            if self.platform == "darwin":
                self._init_macos()
            elif self.platform == "win32":
                self._init_windows()
            elif self.platform == "linux":
                self._init_linux()
            else:
                logger.error(f"Unsupported platform: {self.platform}")
                return
                
            self.initialized = True
            logger.info(f"✅ Accessibility adapter initialized for {self.platform}")
        except Exception as e:
            logger.error(f"Failed to initialize accessibility adapter: {e}")
    
    def _init_macos(self):
        """Initialize macOS accessibility API"""
        # Request accessibility permissions if needed
        try:
            # Check if we have accessibility permissions
            trusted = Quartz.AXIsProcessTrusted()
            if not trusted:
                logger.warning("⚠️ Application doesn't have accessibility permissions")
                # Prompt user to grant permissions
                subprocess.run(["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"])
        except Exception as e:
            logger.error(f"Error checking accessibility permissions: {e}")
    
    def _init_windows(self):
        """Initialize Windows accessibility API"""
        # Initialize UI Automation COM objects
        pass
    
    def _init_linux(self):
        """Initialize Linux accessibility API (AT-SPI)"""
        pass
    
    async def get_ui_tree(self) -> Optional[UITree]:
        """Get complete UI tree from the active window"""
        if not self.initialized:
            logger.error("Accessibility adapter not initialized")
            return None
            
        try:
            if self.platform == "darwin":
                return await self._get_macos_ui_tree()
            elif self.platform == "win32":
                return await self._get_windows_ui_tree()
            elif self.platform == "linux":
                return await self._get_linux_ui_tree()
            else:
                logger.error(f"Unsupported platform: {self.platform}")
                return None
        except Exception as e:
            logger.error(f"Error getting UI tree: {e}")
            return None
    
    async def _get_macos_ui_tree(self) -> Optional[UITree]:
        """Get UI tree using macOS accessibility APIs"""
        # This is a simplified version - a real implementation would be more complex
        
        elements = {}
        
        # Get the frontmost application
        frontmost_app = AppKit.NSWorkspace.sharedWorkspace().frontmostApplication()
        if not frontmost_app:
            logger.warning("No frontmost application found")
            return None
            
        app_name = frontmost_app.localizedName()
        pid = frontmost_app.processIdentifier()
        
        # Get the application's accessibility object
        app_ref = Quartz.AXUIElementCreateApplication(pid)
        
        # Get the focused window
        focused_attr = Quartz.kAXFocusedWindowAttribute
        window_ref = Quartz.AXUIElementCopyAttributeValue(app_ref, focused_attr, None)
        
        if not window_ref:
            logger.warning("No focused window found")
            return None
        
        # Get window title
        title_attr = Quartz.kAXTitleAttribute
        window_title = Quartz.AXUIElementCopyAttributeValue(window_ref, title_attr, None)
        
        # Get window position and size
        position_attr = Quartz.kAXPositionAttribute
        size_attr = Quartz.kAXSizeAttribute
        
        position = Quartz.AXUIElementCopyAttributeValue(window_ref, position_attr, None)
        size = Quartz.AXUIElementCopyAttributeValue(window_ref, size_attr, None)
        
        if position and size:
            x, y = position.value()
            width, height = size.value()
            window_bounds = (x, y, x + width, y + height)
        else:
            window_bounds = (0, 0, 0, 0)
        
        # Create root element for the window
        root_id = f"window_{int(time.time())}"
        root_element = UIElement(
            element_id=root_id,
            element_type="window",
            text=window_title,
            bounds=window_bounds,
            attributes={"application": app_name, "pid": pid}
        )
        
        elements[root_id] = root_element
        
        # TODO: Recursively traverse the accessibility hierarchy
        # This would involve getting the children of the window and building
        # the complete element tree with all properties
        
        # For now, we return a minimal tree with just the window
        return UITree(
            elements=elements,
            root_id=root_id,
            timestamp=time.time(),
            window_title=window_title,
            application_name=app_name
        )
    
    async def _get_windows_ui_tree(self) -> Optional[UITree]:
        """Get UI tree using Windows UI Automation"""
        # Placeholder implementation
        return None
    
    async def _get_linux_ui_tree(self) -> Optional[UITree]:
        """Get UI tree using Linux AT-SPI"""
        # Placeholder implementation
        return None

class ComputerVisionAnalyzer:
    """Advanced computer vision-based UI analysis"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.initialized = False
        self.model = None
        
        if not ML_AVAILABLE:
            logger.warning("ML dependencies not available, CV analyzer disabled")
            return
            
        try:
            # Initialize OpenCV
            self.initialized = True
            
            # Load ML model if specified
            if model_path and os.path.exists(model_path):
                self.model = tf.saved_model.load(model_path)
                logger.info(f"✅ Loaded UI detection model from {model_path}")
            else:
                logger.info("No ML model specified, using classical CV techniques")
                
            logger.info("✅ Computer vision analyzer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize CV analyzer: {e}")
    
    async def analyze_screenshot(self, screenshot_path: str) -> Dict[str, Any]:
        """Analyze screenshot to detect UI elements"""
        if not self.initialized or not ML_AVAILABLE:
            logger.error("CV analyzer not initialized or ML not available")
            return {}
            
        try:
            # Load image
            image = cv2.imread(screenshot_path)
            if image is None:
                logger.error(f"Failed to load image from {screenshot_path}")
                return {}
                
            # Convert to RGB for processing
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            height, width = image.shape[:2]
            
            results = {
                "timestamp": time.time(),
                "image_size": (width, height),
                "elements": []
            }
            
            # Run text detection with OCR
            text_elements = await self._detect_text(image_rgb)
            results["text_elements"] = text_elements
            
            # Run edge detection to find UI boundaries
            boundaries = await self._detect_boundaries(image_rgb)
            results["boundaries"] = boundaries
            
            # Detect buttons and clickable elements
            clickable = await self._detect_clickable(image_rgb)
            results["clickable"] = clickable
            
            # Detect input fields
            input_fields = await self._detect_input_fields(image_rgb)
            results["input_fields"] = input_fields
            
            # Combine all detected elements
            all_elements = text_elements + clickable + input_fields
            
            # Remove duplicates and overlaps
            filtered_elements = self._filter_overlapping_elements(all_elements)
            results["elements"] = filtered_elements
            
            return results
        except Exception as e:
            logger.error(f"Error in CV analysis: {e}")
            return {}
    
    async def _detect_text(self, image) -> List[Dict[str, Any]]:
        """Detect text elements using OCR"""
        try:
            # Convert to grayscale for OCR
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # Run OCR
            ocr_result = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
            
            text_elements = []
            
            # Process OCR results
            for i in range(len(ocr_result["text"])):
                # Skip empty results
                if not ocr_result["text"][i].strip():
                    continue
                    
                # Get bounding box
                x = ocr_result["left"][i]
                y = ocr_result["top"][i]
                w = ocr_result["width"][i]
                h = ocr_result["height"][i]
                
                # Skip very small text (likely noise)
                if w < 10 or h < 10:
                    continue
                
                # Calculate confidence
                conf = float(ocr_result["conf"][i]) / 100.0
                if conf < 0.4:  # Skip low confidence detections
                    continue
                
                text_elements.append({
                    "type": "text",
                    "text": ocr_result["text"][i],
                    "bounds": (x, y, x + w, y + h),
                    "center": (x + w // 2, y + h // 2),
                    "confidence": conf
                })
            
            return text_elements
        except Exception as e:
            logger.error(f"Error in text detection: {e}")
            return []
    
    async def _detect_boundaries(self, image) -> List[Dict[str, Any]]:
        """Detect UI element boundaries using edge detection"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Use Canny edge detection
            edges = cv2.Canny(blurred, 50, 150)
            
            # Dilate edges to connect nearby lines
            dilated = cv2.dilate(edges, None, iterations=2)
            
            # Find contours
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            boundaries = []
            
            for contour in contours:
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter out very small rectangles (likely noise)
                if w < 20 or h < 20:
                    continue
                
                # Filter out very large rectangles (likely background)
                if w > image.shape[1] * 0.9 or h > image.shape[0] * 0.9:
                    continue
                
                boundaries.append({
                    "type": "boundary",
                    "bounds": (x, y, x + w, y + h),
                    "center": (x + w // 2, y + h // 2),
                    "area": w * h,
                    "confidence": 0.7  # Default confidence for boundaries
                })
            
            return boundaries
        except Exception as e:
            logger.error(f"Error in boundary detection: {e}")
            return []
    
    async def _detect_clickable(self, image) -> List[Dict[str, Any]]:
        """Detect clickable elements like buttons"""
        try:
            # This is a simplified implementation
            # A real implementation would use more sophisticated techniques
            
            # Convert to HSV for color-based detection
            hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
            
            # Define color ranges for common button colors
            color_ranges = [
                # Blue buttons
                (np.array([100, 50, 50]), np.array([130, 255, 255])),
                # Green buttons
                (np.array([40, 50, 50]), np.array([80, 255, 255])),
                # Red buttons (wraps around in HSV)
                (np.array([0, 50, 50]), np.array([10, 255, 255])),
                (np.array([170, 50, 50]), np.array([180, 255, 255]))
            ]
            
            clickable = []
            
            # Detect regions with button-like colors
            for lower, upper in color_ranges:
                # Create mask for this color range
                mask = cv2.inRange(hsv, lower, upper)
                
                # Dilate to connect nearby regions
                dilated = cv2.dilate(mask, None, iterations=2)
                
                # Find contours in the mask
                contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    # Get bounding rectangle
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Filter by size (typical button sizes)
                    if w < 30 or h < 20 or w > 300 or h > 100:
                        continue
                    
                    # Check aspect ratio (buttons are usually wider than tall)
                    aspect_ratio = float(w) / h
                    if aspect_ratio < 1.0 or aspect_ratio > 5.0:
                        continue
                    
                    clickable.append({
                        "type": "button",
                        "bounds": (x, y, x + w, y + h),
                        "center": (x + w // 2, y + h // 2),
                        "confidence": 0.6  # Default confidence for color-based detection
                    })
            
            return clickable
        except Exception as e:
            logger.error(f"Error in clickable detection: {e}")
            return []
    
    async def _detect_input_fields(self, image) -> List[Dict[str, Any]]:
        """Detect input fields like text boxes"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # Apply thresholding to find light regions (typical for input fields)
            _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            input_fields = []
            
            for contour in contours:
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter by size (typical input field sizes)
                if w < 100 or h < 20 or w > 500 or h > 100:
                    continue
                
                # Check aspect ratio (input fields are usually much wider than tall)
                aspect_ratio = float(w) / h
                if aspect_ratio < 3.0 or aspect_ratio > 20.0:
                    continue
                
                input_fields.append({
                    "type": "input_field",
                    "bounds": (x, y, x + w, y + h),
                    "center": (x + w // 2, y + h // 2),
                    "confidence": 0.5  # Default confidence for input fields
                })
            
            return input_fields
        except Exception as e:
            logger.error(f"Error in input field detection: {e}")
            return []
    
    def _filter_overlapping_elements(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out overlapping elements"""
        if not elements:
            return []
            
        # Sort by confidence (highest first)
        sorted_elements = sorted(elements, key=lambda e: e.get("confidence", 0), reverse=True)
        
        filtered = []
        
        for element in sorted_elements:
            # Check if this element significantly overlaps with any already filtered element
            overlap = False
            e1_x1, e1_y1, e1_x2, e1_y2 = element["bounds"]
            e1_area = (e1_x2 - e1_x1) * (e1_y2 - e1_y1)
            
            for filtered_element in filtered:
                e2_x1, e2_y1, e2_x2, e2_y2 = filtered_element["bounds"]
                
                # Calculate intersection
                x_overlap = max(0, min(e1_x2, e2_x2) - max(e1_x1, e2_x1))
                y_overlap = max(0, min(e1_y2, e2_y2) - max(e1_y1, e2_y1))
                overlap_area = x_overlap * y_overlap
                
                # If overlap is significant (>50% of the smaller element)
                if overlap_area > 0:
                    e2_area = (e2_x2 - e2_x1) * (e2_y2 - e2_y1)
                    smaller_area = min(e1_area, e2_area)
                    
                    if overlap_area / smaller_area > 0.5:
                        overlap = True
                        break
            
            if not overlap:
                filtered.append(element)
        
        return filtered

class IntelligentUICoordinator:
    """Core intelligence for understanding and interacting with UI"""
    
    def __init__(self):
        self.accessibility_adapter = AccessibilityAdapter()
        self.cv_analyzer = ComputerVisionAnalyzer()
        
        # Queue for screenshot analysis
        self.analysis_queue = queue.Queue()
        self.analysis_thread = None
        self.analysis_running = False
        
        # Latest UI state
        self.latest_ui_tree = None
        self.latest_cv_analysis = None
        self.latest_unified_elements = {}
        
        # History for learning
        self.interaction_history = []
        self.max_history = 100
        
        # Initialize input controller if available
        if INPUT_AVAILABLE:
            self.input_controller = pyautogui
            logger.info("✅ Input controller initialized")
        else:
            self.input_controller = None
            logger.warning("⚠️ Input controller not available")
        
        logger.info("✅ Intelligent UI Coordinator initialized")
    
    def start(self):
        """Start the analysis thread"""
        if self.analysis_thread is not None and self.analysis_thread.is_alive():
            logger.warning("Analysis thread already running")
            return
            
        self.analysis_running = True
        self.analysis_thread = threading.Thread(target=self._analysis_worker)
        self.analysis_thread.daemon = True
        self.analysis_thread.start()
        logger.info("✅ Analysis thread started")
    
    def stop(self):
        """Stop the analysis thread"""
        self.analysis_running = False
        if self.analysis_thread:
            self.analysis_thread.join(timeout=2.0)
        logger.info("✅ Analysis thread stopped")
    
    def _analysis_worker(self):
        """Worker thread for processing screenshots"""
        while self.analysis_running:
            try:
                # Get next screenshot from queue
                item = self.analysis_queue.get(timeout=1.0)
                if item is None:
                    continue
                    
                screenshot_path = item.get("screenshot_path")
                if not screenshot_path or not os.path.exists(screenshot_path):
                    logger.error(f"Invalid screenshot path: {screenshot_path}")
                    continue
                
                # Run analysis asynchronously
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    # Get UI tree from accessibility APIs
                    ui_tree = loop.run_until_complete(
                        self.accessibility_adapter.get_ui_tree()
                    )
                    
                    # Run computer vision analysis
                    cv_analysis = loop.run_until_complete(
                        self.cv_analyzer.analyze_screenshot(screenshot_path)
                    )
                    
                    # Unify the results
                    unified_elements = self._unify_analysis_results(ui_tree, cv_analysis)
                    
                    # Update latest state
                    self.latest_ui_tree = ui_tree
                    self.latest_cv_analysis = cv_analysis
                    self.latest_unified_elements = unified_elements
                    
                    # Call the callback if provided
                    callback = item.get("callback")
                    if callback:
                        callback({
                            "ui_tree": ui_tree,
                            "cv_analysis": cv_analysis,
                            "unified_elements": unified_elements,
                            "timestamp": time.time()
                        })
                finally:
                    loop.close()
                
                self.analysis_queue.task_done()
                
            except queue.Empty:
                pass
            except Exception as e:
                logger.error(f"Error in analysis worker: {e}")
    
    def _unify_analysis_results(self, ui_tree, cv_analysis) -> Dict[str, Any]:
        """Combine accessibility API results with computer vision analysis"""
        unified = {
            "timestamp": time.time(),
            "elements": []
        }
        
        # If we have a UI tree from accessibility APIs
        if ui_tree and hasattr(ui_tree, "elements"):
            # Convert UIElement objects to dictionaries
            for element_id, element in ui_tree.elements.items():
                unified["elements"].append({
                    "id": element_id,
                    "type": element.element_type,
                    "text": element.text,
                    "bounds": element.bounds,
                    "center": element.center,
                    "confidence": element.confidence,
                    "source": "accessibility"
                })
        
        # If we have CV analysis results
        if cv_analysis and "elements" in cv_analysis:
            # Add elements from CV analysis
            for element in cv_analysis["elements"]:
                # Generate a unique ID
                element_id = f"cv_{len(unified['elements'])}"
                
                unified["elements"].append({
                    "id": element_id,
                    "type": element.get("type", "unknown"),
                    "text": element.get("text", ""),
                    "bounds": element.get("bounds"),
                    "center": element.get("center"),
                    "confidence": element.get("confidence", 0.5),
                    "source": "computer_vision"
                })
        
        # Additional metadata
        unified["element_count"] = len(unified["elements"])
        unified["sources"] = {
            "accessibility": ui_tree is not None,
            "computer_vision": cv_analysis is not None and len(cv_analysis.get("elements", [])) > 0
        }
        
        return unified
    
    async def analyze_current_screen(self, callback=None) -> Dict[str, Any]:
        """Take screenshot and analyze the current screen"""
        try:
            # Take screenshot
            screenshot_path = f"cache/intelligent_ui/screenshot_{int(time.time())}.png"
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
            
            if INPUT_AVAILABLE:
                screenshot = pyautogui.screenshot()
                screenshot.save(screenshot_path)
                logger.info(f"✅ Screenshot saved to {screenshot_path}")
            else:
                logger.error("Input automation not available, can't take screenshot")
                return {}
            
            # Queue for analysis
            self.analysis_queue.put({
                "screenshot_path": screenshot_path,
                "callback": callback
            })
            
            # If we want to wait for results, we can use a threading event
            if callback is None:
                # Wait for a short time to let analysis complete
                await asyncio.sleep(1.0)
                
                # Return the latest results
                return {
                    "ui_tree": self.latest_ui_tree,
                    "cv_analysis": self.latest_cv_analysis,
                    "unified_elements": self.latest_unified_elements,
                    "screenshot_path": screenshot_path,
                    "timestamp": time.time()
                }
            
            # If using callback, return minimal information
            return {
                "queued": True,
                "screenshot_path": screenshot_path,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing current screen: {e}")
            return {"error": str(e)}
    
    async def click_element(self, element_identifier, click_type="single") -> Dict[str, Any]:
        """Click on a UI element using smart targeting"""
        try:
            if not self.input_controller:
                return {"success": False, "error": "Input controller not available"}
            
            # Get latest unified elements
            elements = self.latest_unified_elements.get("elements", [])
            if not elements:
                return {"success": False, "error": "No UI elements available"}
            
            # Find the target element
            target_element = None
            
            # If identifier is a dictionary with specific criteria
            if isinstance(element_identifier, dict):
                element_type = element_identifier.get("type")
                element_text = element_identifier.get("text")
                element_id = element_identifier.get("id")
                
                for element in elements:
                    # Match by ID
                    if element_id and element.get("id") == element_id:
                        target_element = element
                        break
                    
                    # Match by type and text
                    if element_type and element.get("type") == element_type:
                        if not element_text or (element.get("text") and element_text.lower() in element.get("text").lower()):
                            target_element = element
                            break
            
            # If identifier is a string, try to match by text or ID
            elif isinstance(element_identifier, str):
                for element in elements:
                    if element.get("id") == element_identifier:
                        target_element = element
                        break
                    
                    if element.get("text") and element_identifier.lower() in element.get("text").lower():
                        target_element = element
                        break
            
            # If no element found
            if not target_element:
                return {
                    "success": False, 
                    "error": f"Element not found: {element_identifier}",
                    "available_elements": [
                        {"id": e.get("id"), "type": e.get("type"), "text": e.get("text")} 
                        for e in elements[:5]  # Show first 5 elements
                    ]
                }
            
            # Get center coordinates
            center = target_element.get("center")
            if not center:
                bounds = target_element.get("bounds")
                if bounds:
                    x1, y1, x2, y2 = bounds
                    center = ((x1 + x2) // 2, (y1 + y2) // 2)
                else:
                    return {"success": False, "error": "Element has no coordinates"}
            
            # Perform the click
            x, y = center
            
            # Visual verification (optional)
            verification_path = await self._create_click_verification(x, y, target_element)
            
            if click_type == "double":
                self.input_controller.doubleClick(x, y)
            elif click_type == "right":
                self.input_controller.rightClick(x, y)
            else:  # single click
                self.input_controller.click(x, y)
            
            # Record in history
            self._record_interaction("click", target_element, {"x": x, "y": y, "click_type": click_type})
            
            return {
                "success": True,
                "element": {
                    "id": target_element.get("id"),
                    "type": target_element.get("type"),
                    "text": target_element.get("text")
                },
                "coordinates": {"x": x, "y": y},
                "verification_path": verification_path
            }
            
        except Exception as e:
            logger.error(f"Error clicking element: {e}")
            return {"success": False, "error": str(e)}
    
    async def type_text(self, text, element_identifier=None) -> Dict[str, Any]:
        """Type text, optionally clicking on an element first"""
        try:
            if not self.input_controller:
                return {"success": False, "error": "Input controller not available"}
            
            # If element specified, click it first
            if element_identifier:
                click_result = await self.click_element(element_identifier)
                if not click_result.get("success", False):
                    return click_result
            
            # Type the text
            self.input_controller.typewrite(text)
            
            # Record in history
            self._record_interaction("type", {"text": text}, {"element": element_identifier})
            
            return {
                "success": True,
                "text": text,
                "target_element": element_identifier
            }
            
        except Exception as e:
            logger.error(f"Error typing text: {e}")
            return {"success": False, "error": str(e)}
    
    async def press_key(self, key) -> Dict[str, Any]:
        """Press a keyboard key"""
        try:
            if not self.input_controller:
                return {"success": False, "error": "Input controller not available"}
            
            # Press the key
            self.input_controller.press(key)
            
            # Record in history
            self._record_interaction("key_press", {"key": key}, {})
            
            return {
                "success": True,
                "key": key
            }
            
        except Exception as e:
            logger.error(f"Error pressing key: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_click_verification(self, x, y, element) -> str:
        """Create a visual verification of the click location"""
        try:
            # Take screenshot
            if not INPUT_AVAILABLE:
                return ""
                
            screenshot = pyautogui.screenshot()
            
            # Draw on the screenshot
            draw = ImageDraw.Draw(screenshot)
            
            # Draw crosshair
            crosshair_size = 20
            draw.line([(x - crosshair_size, y), (x + crosshair_size, y)], fill="red", width=2)
            draw.line([(x, y - crosshair_size), (x, y + crosshair_size)], fill="red", width=2)
            
            # Draw circle
            draw.ellipse([(x - 10, y - 10), (x + 10, y + 10)], outline="red", width=2)
            
            # If element has bounds, draw rectangle
            if "bounds" in element and element["bounds"]:
                x1, y1, x2, y2 = element["bounds"]
                draw.rectangle([x1, y1, x2, y2], outline="blue", width=2)
            
            # Save verification image
            verification_path = f"cache/intelligent_ui/click_{int(time.time())}.png"
            os.makedirs(os.path.dirname(verification_path), exist_ok=True)
            screenshot.save(verification_path)
            
            return verification_path
        except Exception as e:
            logger.error(f"Error creating click verification: {e}")
            return ""
    
    def _record_interaction(self, action_type, target, details):
        """Record interaction for learning"""
        interaction = {
            "timestamp": time.time(),
            "action_type": action_type,
            "target": target,
            "details": details,
            "success": True
        }
        
        self.interaction_history.append(interaction)
        
        # Limit history size
        if len(self.interaction_history) > self.max_history:
            self.interaction_history = self.interaction_history[-self.max_history:]

class IntelligentUISystem:
    """Main entry point for the intelligent UI system"""
    
    def __init__(self):
        self.coordinator = IntelligentUICoordinator()
        self.coordinator.start()
        logger.info("✅ Intelligent UI System initialized")
    
    async def analyze_screen(self) -> Dict[str, Any]:
        """Analyze the current screen"""
        result = await self.coordinator.analyze_current_screen()
        return result
    
    async def click_element(self, element_identifier, click_type="single") -> Dict[str, Any]:
        """Click on a UI element"""
        result = await self.coordinator.click_element(element_identifier, click_type)
        return result
    
    async def type_text(self, text, element_identifier=None) -> Dict[str, Any]:
        """Type text, optionally clicking on an element first"""
        result = await self.coordinator.type_text(text, element_identifier)
        return result
    
    async def press_key(self, key) -> Dict[str, Any]:
        """Press a keyboard key"""
        result = await self.coordinator.press_key(key)
        return result
    
    async def get_clickable_elements(self) -> List[Dict[str, Any]]:
        """Get all clickable elements on screen"""
        await self.analyze_screen()
        elements = self.coordinator.latest_unified_elements.get("elements", [])
        
        # Filter to likely clickable types
        clickable_types = ["button", "link", "checkbox", "radio", "tab", "menu_item"]
        clickable = [
            element for element in elements
            if element.get("type") in clickable_types
        ]
        
        return clickable
    
    async def find_element_by_text(self, text, partial_match=True) -> Optional[Dict[str, Any]]:
        """Find element containing specific text"""
        await self.analyze_screen()
        elements = self.coordinator.latest_unified_elements.get("elements", [])
        
        for element in elements:
            element_text = element.get("text", "")
            if not element_text:
                continue
                
            if partial_match and text.lower() in element_text.lower():
                return element
            elif not partial_match and text.lower() == element_text.lower():
                return element
        
        return None
    
    async def execute_action(self, action_type, target, **kwargs) -> Dict[str, Any]:
        """Execute a specific UI action"""
        if action_type == "click":
            return await self.click_element(target, kwargs.get("click_type", "single"))
        elif action_type == "type":
            return await self.type_text(kwargs.get("text", ""), target)
        elif action_type == "key":
            return await self.press_key(kwargs.get("key", ""))
        elif action_type == "analyze":
            return await self.analyze_screen()
        else:
            return {"success": False, "error": f"Unknown action type: {action_type}"}
    
    def stop(self):
        """Stop the system"""
        self.coordinator.stop()
        logger.info("✅ Intelligent UI System stopped")

# Create singleton instance
intelligent_ui = IntelligentUISystem()

async def main():
    """Example usage"""
    try:
        # Analyze screen
        print("Analyzing screen...")
        analysis = await intelligent_ui.analyze_screen()
        
        # Get clickable elements
        print("Finding clickable elements...")
        clickable = await intelligent_ui.get_clickable_elements()
        print(f"Found {len(clickable)} clickable elements")
        
        # Find search box
        print("Looking for search box...")
        search_box = await intelligent_ui.find_element_by_text("search")
        
        if search_box:
            print(f"Found search box: {search_box.get('text')}")
            
            # Click the search box
            print("Clicking search box...")
            click_result = await intelligent_ui.click_element(search_box["id"])
            
            if click_result.get("success"):
                # Type text
                print("Typing text...")
                await intelligent_ui.type_text("Hello from Intelligent UI System")
        else:
            print("Search box not found, clicking in center of screen...")
            screen_width, screen_height = pyautogui.size()
            await intelligent_ui.click_element({
                "type": "fallback",
                "center": (screen_width // 2, screen_height // 2)
            })
        
        print("Done!")
    finally:
        # Stop the system
        intelligent_ui.stop()

if __name__ == "__main__":
    # Run the example
    asyncio.run(main())