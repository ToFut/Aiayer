#!/usr/bin/env python3
"""
Accessibility UI Detector - A specialized detector that uses accessibility APIs
to identify UI elements with high precision.

This module leverages system accessibility features to detect UI elements
accurately across different applications.
"""

import json
import logging
import os
import time
import traceback
from datetime import datetime

# Set up logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/accessibility_detector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('accessibility_detector')

# Platform detection
IS_MACOS = False
IS_WINDOWS = False
IS_LINUX = False

try:
    # macOS specific imports
    import Quartz
    import AppKit
    from PyObjCTools import AppHelper
    IS_MACOS = True
except ImportError:
    logger.warning("macOS accessibility APIs not available")

try:
    # Windows specific imports
    import ctypes
    import comtypes.client
    from comtypes.automation import VARIANT
    IS_WINDOWS = True
except ImportError:
    logger.warning("Windows accessibility APIs not available")

try:
    # Linux specific imports (using AT-SPI)
    import gi
    gi.require_version('Atspi', '2.0')
    from gi.repository import Atspi
    IS_LINUX = True
except (ImportError, ValueError):
    logger.warning("Linux accessibility APIs (AT-SPI) not available")

class AccessibilityUIDetector:
    """
    A class that detects UI elements using platform-specific accessibility APIs.
    """
    
    def __init__(self):
        """Initialize the detector based on the platform."""
        self.platform = self._detect_platform()
        logger.info(f"Initialized AccessibilityUIDetector on {self.platform} platform")
        
    def _detect_platform(self):
        """Detect the current platform."""
        if IS_MACOS:
            return "macos"
        elif IS_WINDOWS:
            return "windows"
        elif IS_LINUX:
            return "linux"
        else:
            return "unsupported"
    
    def scan_screen(self):
        """
        Scan the screen for UI elements using accessibility APIs.
        
        Returns:
            dict: JSON-serializable dictionary of detected UI elements
        """
        start_time = time.time()
        try:
            if self.platform == "macos":
                elements = self._scan_macos()
            elif self.platform == "windows":
                elements = self._scan_windows()
            elif self.platform == "linux":
                elements = self._scan_linux()
            else:
                logger.error("Unsupported platform for UI detection")
                return {"error": "Unsupported platform", "elements": []}
            
            duration = time.time() - start_time
            result = {
                "timestamp": datetime.now().isoformat(),
                "platform": self.platform,
                "scan_duration_ms": int(duration * 1000),
                "element_count": len(elements),
                "elements": elements
            }
            
            # Save results to cache for dashboard
            self._save_latest_scan(result)
            
            return result
        except Exception as e:
            logger.error(f"Error scanning screen: {str(e)}")
            logger.error(traceback.format_exc())
            return {"error": str(e), "elements": []}
    
    def _scan_macos(self):
        """
        Scan for UI elements using macOS accessibility API.
        
        Returns:
            list: List of detected UI elements with properties
        """
        if not IS_MACOS:
            return []
        
        elements = []
        
        try:
            # Get system-wide accessibility element
            system_wide_element = Quartz.AXUIElementCreateSystemWide()
            
            # Get the focused application
            focused_app_ref = ctypes.c_void_p()
            Quartz.AXUIElementCopyAttributeValue(
                system_wide_element,
                Quartz.kAXFocusedApplicationAttribute,
                ctypes.byref(focused_app_ref)
            )
            
            if focused_app_ref.value:
                # Get application name
                app_name = self._get_attribute(focused_app_ref.value, Quartz.kAXTitleAttribute)
                
                # Get all windows
                windows_ref = self._get_attribute_array(focused_app_ref.value, Quartz.kAXWindowsAttribute)
                
                if windows_ref:
                    for window in windows_ref:
                        # Process each window
                        window_elements = self._process_macos_element(window, app_name)
                        elements.extend(window_elements)
        except Exception as e:
            logger.error(f"Error in macOS accessibility scanning: {str(e)}")
            logger.error(traceback.format_exc())
        
        return elements
    
    def _process_macos_element(self, element, app_name, depth=0, max_depth=10):
        """
        Process a macOS accessibility element recursively.
        
        Args:
            element: The accessibility element to process
            app_name: The name of the application
            depth: Current recursion depth
            max_depth: Maximum recursion depth
            
        Returns:
            list: UI elements found
        """
        if depth > max_depth:
            return []
        
        elements = []
        
        try:
            # Get element role
            role = self._get_attribute(element, Quartz.kAXRoleAttribute) or "unknown"
            
            # Get element position and size
            position = self._get_attribute(element, Quartz.kAXPositionAttribute)
            size = self._get_attribute(element, Quartz.kAXSizeAttribute)
            
            if position and size:
                x, y = position.x, position.y
                width, height = size.width, size.height
                
                # Get other useful attributes
                title = self._get_attribute(element, Quartz.kAXTitleAttribute) or ""
                value = self._get_attribute(element, Quartz.kAXValueAttribute)
                
                if isinstance(value, (str, int, float, bool)):
                    value_str = str(value)
                else:
                    value_str = ""
                
                description = self._get_attribute(element, Quartz.kAXDescriptionAttribute) or ""
                
                # Create element dict
                element_dict = {
                    "type": role,
                    "app": app_name,
                    "bounds": {
                        "x": int(x),
                        "y": int(y),
                        "width": int(width),
                        "height": int(height)
                    },
                    "properties": {
                        "title": title,
                        "value": value_str,
                        "description": description
                    }
                }
                
                elements.append(element_dict)
            
            # Process children
            children = self._get_attribute_array(element, Quartz.kAXChildrenAttribute)
            if children:
                for child in children:
                    child_elements = self._process_macos_element(child, app_name, depth + 1, max_depth)
                    elements.extend(child_elements)
        except Exception as e:
            pass  # Skip elements that cause errors
        
        return elements
    
    def _get_attribute(self, element, attribute):
        """Get an attribute value from a macOS accessibility element."""
        if not element:
            return None
            
        value_ref = ctypes.c_void_p()
        result = Quartz.AXUIElementCopyAttributeValue(
            element, 
            attribute, 
            ctypes.byref(value_ref)
        )
        
        if result == Quartz.kAXErrorSuccess and value_ref.value:
            return value_ref.value
        return None
    
    def _get_attribute_array(self, element, attribute):
        """Get an array attribute from a macOS accessibility element."""
        attr_value = self._get_attribute(element, attribute)
        if not attr_value:
            return []
            
        count = Quartz.CFArrayGetCount(attr_value)
        return [Quartz.CFArrayGetValueAtIndex(attr_value, i) for i in range(count)]
    
    def _scan_windows(self):
        """
        Scan for UI elements using Windows UI Automation API.
        
        Returns:
            list: List of detected UI elements with properties
        """
        if not IS_WINDOWS:
            return []
            
        elements = []
        
        try:
            # Initialize UI Automation
            UIAutomation = comtypes.client.GetModule("UIAutomationCore.dll")
            IUIAutomation = comtypes.client.CreateObject(
                "{ff48dba4-60ef-4201-aa87-54103eef594e}", 
                interface=UIAutomation.IUIAutomation
            )
            
            # Get root element
            root = IUIAutomation.GetRootElement()
            
            # Get focused element
            focused = IUIAutomation.GetFocusedElement()
            
            # Get window containing focused element
            current_window = None
            element = focused
            
            while element:
                pattern = element.GetCurrentPattern(UIAutomation.UIA_WindowPatternId)
                if pattern:
                    current_window = element
                    break
                parent = IUIAutomation.TreeWalkerControlViewWalker.GetParentElement(element)
                if not parent:
                    break
                element = parent
            
            if current_window:
                # Process the window and its descendants
                app_name = current_window.GetCurrentPropertyValue(UIAutomation.UIA_NamePropertyId) or "Unknown"
                elements = self._process_windows_element(IUIAutomation, current_window, app_name)
        except Exception as e:
            logger.error(f"Error in Windows UI Automation: {str(e)}")
            logger.error(traceback.format_exc())
            
        return elements
    
    def _process_windows_element(self, automation, element, app_name, depth=0, max_depth=10):
        """
        Process a Windows UI Automation element recursively.
        
        Args:
            automation: The UI Automation interface
            element: The element to process
            app_name: The name of the application
            depth: Current recursion depth
            max_depth: Maximum recursion depth
            
        Returns:
            list: UI elements found
        """
        if depth > max_depth:
            return []
        
        elements = []
        
        try:
            # Get control type
            control_type_id = element.GetCurrentPropertyValue(automation.UIA_ControlTypePropertyId)
            control_type = "unknown"
            
            # Get element bounds
            bounds_rect = element.GetCurrentPropertyValue(automation.UIA_BoundingRectanglePropertyId)
            if bounds_rect:
                left, top, width, height = bounds_rect
                
                # Get name and value
                name = element.GetCurrentPropertyValue(automation.UIA_NamePropertyId) or ""
                value = element.GetCurrentPropertyValue(automation.UIA_ValuePropertyId) or ""
                
                # Create element dict
                element_dict = {
                    "type": control_type,
                    "app": app_name,
                    "bounds": {
                        "x": int(left),
                        "y": int(top),
                        "width": int(width),
                        "height": int(height)
                    },
                    "properties": {
                        "name": name,
                        "value": value
                    }
                }
                
                elements.append(element_dict)
            
            # Process children
            walker = automation.TreeWalkerControlViewWalker
            child = walker.GetFirstChildElement(element)
            while child:
                child_elements = self._process_windows_element(automation, child, app_name, depth + 1, max_depth)
                elements.extend(child_elements)
                child = walker.GetNextSiblingElement(child)
        except Exception as e:
            pass  # Skip elements that cause errors
        
        return elements
    
    def _scan_linux(self):
        """
        Scan for UI elements using Linux AT-SPI accessibility framework.
        
        Returns:
            list: List of detected UI elements with properties
        """
        if not IS_LINUX:
            return []
            
        elements = []
        
        try:
            # Initialize AT-SPI
            Atspi.init()
            
            # Get desktop
            desktop = Atspi.Registry.get_desktop(0)
            
            # Find the active application
            active_app = None
            for i in range(desktop.get_child_count()):
                app = desktop.get_child_at_index(i)
                if app and app.get_name() and app.get_state_set().contains(Atspi.StateType.ACTIVE):
                    active_app = app
                    break
            
            if active_app:
                app_name = active_app.get_name()
                
                # Process each window in the active application
                for i in range(active_app.get_child_count()):
                    window = active_app.get_child_at_index(i)
                    window_elements = self._process_atspi_element(window, app_name)
                    elements.extend(window_elements)
        except Exception as e:
            logger.error(f"Error in AT-SPI scanning: {str(e)}")
            logger.error(traceback.format_exc())
            Atspi.exit()
        
        Atspi.exit()
        return elements
    
    def _process_atspi_element(self, element, app_name, depth=0, max_depth=10):
        """
        Process an AT-SPI element recursively.
        
        Args:
            element: The AT-SPI element to process
            app_name: The name of the application
            depth: Current recursion depth
            max_depth: Maximum recursion depth
            
        Returns:
            list: UI elements found
        """
        if depth > max_depth or not element:
            return []
        
        elements = []
        
        try:
            # Get element role
            role = element.get_role_name()
            
            # Get element geometry
            component = element.get_component_iface()
            if component:
                x, y, width, height = component.get_extents(Atspi.CoordType.SCREEN)
                
                # Get text if available
                text = ""
                text_iface = element.get_text_iface()
                if text_iface:
                    text = text_iface.get_text(0, text_iface.get_character_count())
                
                # Get name
                name = element.get_name() or ""
                
                # Create element dict
                element_dict = {
                    "type": role,
                    "app": app_name,
                    "bounds": {
                        "x": x,
                        "y": y,
                        "width": width,
                        "height": height
                    },
                    "properties": {
                        "name": name,
                        "text": text
                    }
                }
                
                elements.append(element_dict)
            
            # Process children
            for i in range(element.get_child_count()):
                child = element.get_child_at_index(i)
                if child:
                    child_elements = self._process_atspi_element(child, app_name, depth + 1, max_depth)
                    elements.extend(child_elements)
        except Exception as e:
            pass  # Skip elements that cause errors
        
        return elements
    
    def _save_latest_scan(self, scan_result):
        """Save the latest scan result for the dashboard."""
        cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache', 'accessibility')
        os.makedirs(cache_dir, exist_ok=True)
        
        cache_file = os.path.join(cache_dir, 'latest_scan.json')
        try:
            with open(cache_file, 'w') as f:
                json.dump(scan_result, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save scan to cache: {str(e)}")

# API for the detector
class AccessibilityAPI:
    """
    API for the Accessibility UI Detector with simple HTTP endpoints.
    """
    
    def __init__(self):
        self.detector = AccessibilityUIDetector()
        
    def detect_ui_elements(self):
        """
        Detect UI elements on screen and return as JSON.
        
        Returns:
            dict: JSON-serializable dictionary of detected elements
        """
        return self.detector.scan_screen()
    
    def get_latest_scan(self):
        """
        Get the results of the latest scan from cache.
        
        Returns:
            dict: Latest scan results or empty dict if not available
        """
        cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache', 'accessibility')
        cache_file = os.path.join(cache_dir, 'latest_scan.json')
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load latest scan: {str(e)}")
                return {"error": "Failed to load latest scan", "elements": []}
        else:
            return {"error": "No scan available", "elements": []}
    
    def calculate_accuracy(self, ground_truth_file=None):
        """
        Calculate accuracy metrics if ground truth data is available.
        
        Args:
            ground_truth_file: Path to ground truth data file
            
        Returns:
            dict: Accuracy metrics
        """
        latest_scan = self.get_latest_scan()
        elements = latest_scan.get("elements", [])
        
        # If no ground truth provided, return basic statistics
        if not ground_truth_file or not os.path.exists(ground_truth_file):
            return {
                "timestamp": datetime.now().isoformat(),
                "elements_detected": len(elements),
                "element_types": {role: sum(1 for e in elements if e.get("type") == role) 
                                 for role in set(e.get("type", "unknown") for e in elements)},
                "by_application": {app: sum(1 for e in elements if e.get("app") == app)
                                 for app in set(e.get("app", "unknown") for e in elements)}
            }
        
        # Compare with ground truth if available
        try:
            with open(ground_truth_file, 'r') as f:
                ground_truth = json.load(f)
                
            gt_elements = ground_truth.get("elements", [])
            
            # Simple matching based on position and type
            matches = 0
            for gt_elem in gt_elements:
                gt_bounds = gt_elem.get("bounds", {})
                gt_type = gt_elem.get("type", "")
                
                for detected_elem in elements:
                    detected_bounds = detected_elem.get("bounds", {})
                    detected_type = detected_elem.get("type", "")
                    
                    # Check if bounds overlap and types match
                    if (self._bounds_overlap(gt_bounds, detected_bounds) and
                            gt_type.lower() == detected_type.lower()):
                        matches += 1
                        break
            
            precision = matches / len(elements) if elements else 0
            recall = matches / len(gt_elements) if gt_elements else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            
            return {
                "timestamp": datetime.now().isoformat(),
                "ground_truth_elements": len(gt_elements),
                "detected_elements": len(elements),
                "matches": matches,
                "precision": precision,
                "recall": recall,
                "f1_score": f1
            }
            
        except Exception as e:
            logger.error(f"Error calculating accuracy: {str(e)}")
            return {"error": str(e), "accuracy_metrics": None}
    
    def _bounds_overlap(self, bounds1, bounds2, threshold=0.5):
        """Check if two bounding boxes overlap with given threshold."""
        # Extract coordinates
        x1, y1 = bounds1.get("x", 0), bounds1.get("y", 0)
        w1, h1 = bounds1.get("width", 0), bounds1.get("height", 0)
        x2, y2 = bounds2.get("x", 0), bounds2.get("y", 0)
        w2, h2 = bounds2.get("width", 0), bounds2.get("height", 0)
        
        # Calculate intersection area
        x_overlap = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
        y_overlap = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
        intersection = x_overlap * y_overlap
        
        # Calculate union area
        area1 = w1 * h1
        area2 = w2 * h2
        union = area1 + area2 - intersection
        
        # Calculate IoU (Intersection over Union)
        iou = intersection / union if union > 0 else 0
        
        return iou >= threshold

# Main function to run as a standalone script
def main():
    """Run the accessibility detector once and print results."""
    detector = AccessibilityUIDetector()
    results = detector.scan_screen()
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()