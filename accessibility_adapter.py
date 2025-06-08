#!/usr/bin/env python3
"""
Accessibility Adapter Module
Platform-specific implementations for accessing accessibility APIs to get UI information
directly from the operating system rather than relying on computer vision alone.
"""

import asyncio
import json
import time
import logging
import os
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/accessibility_adapter.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("accessibility_adapter")

# Determine platform
import platform
PLATFORM = platform.system().lower()
logger.info(f"Running on platform: {PLATFORM}")

# Import platform-specific modules
if PLATFORM == "darwin":
    try:
        import Quartz
        import AppKit
        import objc
        ACCESSIBILITY_AVAILABLE = True
        logger.info("✅ macOS accessibility modules loaded")
    except ImportError as e:
        logger.error(f"Failed to load macOS accessibility modules: {e}")
        ACCESSIBILITY_AVAILABLE = False
elif PLATFORM == "windows":
    try:
        import win32gui
        import win32con
        import win32api
        import comtypes.client
        import ctypes
        ACCESSIBILITY_AVAILABLE = True
        logger.info("✅ Windows accessibility modules loaded")
    except ImportError as e:
        logger.error(f"Failed to load Windows accessibility modules: {e}")
        ACCESSIBILITY_AVAILABLE = False
elif PLATFORM == "linux":
    try:
        import gi
        gi.require_version('Atspi', '2.0')
        from gi.repository import Atspi
        ACCESSIBILITY_AVAILABLE = True
        logger.info("✅ Linux accessibility modules loaded")
    except ImportError as e:
        logger.error(f"Failed to load Linux accessibility modules: {e}")
        ACCESSIBILITY_AVAILABLE = False
else:
    logger.error(f"Unsupported platform: {PLATFORM}")
    ACCESSIBILITY_AVAILABLE = False

@dataclass
class AccessibilityElement:
    """Representation of a UI element from accessibility APIs"""
    element_id: str
    element_type: str
    role: str
    name: Optional[str] = None
    value: Optional[str] = None
    description: Optional[str] = None
    bounds: Optional[Tuple[int, int, int, int]] = None  # x1, y1, x2, y2
    center: Optional[Tuple[int, int]] = None
    parent_id: Optional[str] = None
    children_ids: List[str] = None
    attributes: Dict[str, Any] = None
    actions: List[str] = None
    states: List[str] = None
    is_clickable: bool = False
    is_focusable: bool = False
    is_editable: bool = False
    is_visible: bool = True
    
    def __post_init__(self):
        if self.children_ids is None:
            self.children_ids = []
        if self.attributes is None:
            self.attributes = {}
        if self.actions is None:
            self.actions = []
        if self.states is None:
            self.states = []
        
        # Calculate center if bounds are available but center isn't
        if self.bounds and not self.center:
            x1, y1, x2, y2 = self.bounds
            self.center = ((x1 + x2) // 2, (y1 + y2) // 2)
        
        # Determine if element is likely clickable
        clickable_roles = ["button", "menuitem", "link", "checkbox", "radio", "tab", "combobox"]
        if self.role in clickable_roles or "click" in self.actions:
            self.is_clickable = True
        
        # Determine if element is focusable
        focusable_roles = ["textbox", "combobox", "editcombo", "spinbutton", "text"]
        if self.role in focusable_roles or "focus" in self.actions or "focused" in self.states:
            self.is_focusable = True
        
        # Determine if element is editable
        editable_roles = ["textbox", "text"]
        if self.role in editable_roles or "editable" in self.states:
            self.is_editable = True

@dataclass
class AccessibilityTree:
    """Hierarchical representation of UI accessibility tree"""
    elements: Dict[str, AccessibilityElement]
    root_id: str
    timestamp: float
    application_name: Optional[str] = None
    window_title: Optional[str] = None
    platform: str = PLATFORM
    
    def get_element_by_id(self, element_id: str) -> Optional[AccessibilityElement]:
        """Get element by ID"""
        return self.elements.get(element_id)
    
    def get_element_by_name(self, name: str, partial: bool = True) -> Optional[AccessibilityElement]:
        """Find element by name"""
        for element_id, element in self.elements.items():
            if element.name:
                if partial and name.lower() in element.name.lower():
                    return element
                elif not partial and name.lower() == element.name.lower():
                    return element
        return None
    
    def get_clickable_elements(self) -> List[AccessibilityElement]:
        """Get all clickable elements"""
        return [element for element in self.elements.values() 
                if element.is_clickable and element.is_visible]
    
    def get_editable_elements(self) -> List[AccessibilityElement]:
        """Get all editable text elements"""
        return [element for element in self.elements.values() 
                if element.is_editable and element.is_visible]
    
    def get_path_to_element(self, element_id: str) -> List[str]:
        """Get path from root to element"""
        path = []
        current_id = element_id
        
        while current_id and current_id in self.elements and current_id != self.root_id:
            path.append(current_id)
            element = self.elements[current_id]
            current_id = element.parent_id
            
        if self.root_id in self.elements:
            path.append(self.root_id)
            
        return list(reversed(path))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tree to dictionary for serialization"""
        return {
            "elements": {k: asdict(v) for k, v in self.elements.items()},
            "root_id": self.root_id,
            "timestamp": self.timestamp,
            "application_name": self.application_name,
            "window_title": self.window_title,
            "platform": self.platform,
            "element_count": len(self.elements)
        }

class MacOSAccessibilityAdapter:
    """macOS-specific implementation of accessibility API"""
    
    def __init__(self):
        self.initialized = False
        
        try:
            # Check if we have accessibility permissions
            trusted = Quartz.AXIsProcessTrusted()
            if not trusted:
                logger.warning("⚠️ Application doesn't have accessibility permissions")
                logger.warning("Please enable accessibility permissions in System Preferences > Security & Privacy > Privacy > Accessibility")
                # Attempt to open preferences
                try:
                    import subprocess
                    subprocess.run(["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"])
                except Exception as e:
                    logger.error(f"Failed to open preferences: {e}")
            
            self.initialized = True
            logger.info("✅ macOS Accessibility Adapter initialized")
        except Exception as e:
            logger.error(f"Failed to initialize macOS Accessibility Adapter: {e}")
    
    async def get_ui_tree(self) -> Optional[AccessibilityTree]:
        """Get UI tree from macOS accessibility APIs"""
        if not self.initialized:
            logger.error("macOS Accessibility Adapter not initialized")
            return None
        
        try:
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
            window_ref, error = Quartz.AXUIElementCopyAttributeValue(app_ref, focused_attr, None)
            
            if error or not window_ref:
                logger.warning(f"No focused window found: {error}")
                return None
            
            # Get window title
            title_attr = Quartz.kAXTitleAttribute
            window_title, error = Quartz.AXUIElementCopyAttributeValue(window_ref, title_attr, None)
            
            if error or not window_title:
                window_title = "Unknown Window"
                logger.warning(f"Failed to get window title: {error}")
            
            # Get window position and size
            position_attr = Quartz.kAXPositionAttribute
            size_attr = Quartz.kAXSizeAttribute
            
            position, pos_error = Quartz.AXUIElementCopyAttributeValue(window_ref, position_attr, None)
            size, size_error = Quartz.AXUIElementCopyAttributeValue(window_ref, size_attr, None)
            
            if not pos_error and not size_error and position and size:
                x, y = position.value()
                width, height = size.value()
                window_bounds = (x, y, x + width, y + height)
            else:
                window_bounds = (0, 0, 0, 0)
                logger.warning(f"Failed to get window bounds: {pos_error}, {size_error}")
            
            # Create root element for the window
            root_id = f"window_{int(time.time())}"
            
            # Create accessibility tree
            elements = {}
            root_element = AccessibilityElement(
                element_id=root_id,
                element_type="window",
                role="window",
                name=window_title,
                bounds=window_bounds,
                attributes={"pid": pid, "application": app_name}
            )
            
            elements[root_id] = root_element
            
            # Build the element tree recursively
            self._build_element_tree(window_ref, root_id, elements)
            
            # Create and return the accessibility tree
            tree = AccessibilityTree(
                elements=elements,
                root_id=root_id,
                timestamp=time.time(),
                application_name=app_name,
                window_title=window_title
            )
            
            logger.info(f"✅ Generated UI tree with {len(elements)} elements")
            return tree
            
        except Exception as e:
            logger.error(f"Error getting UI tree: {e}")
            return None
    
    def _build_element_tree(self, ax_element, parent_id, elements_dict, depth=0, max_depth=10):
        """Recursively build the element tree"""
        if depth >= max_depth:
            return
        
        try:
            # Get children
            children_attr = Quartz.kAXChildrenAttribute
            children, error = Quartz.AXUIElementCopyAttributeValue(ax_element, children_attr, None)
            
            if error or not children:
                return
            
            # Iterate through children
            for i in range(children.count()):
                child = children.objectAtIndex_(i)
                
                # Generate a unique ID for this element
                element_id = f"element_{len(elements_dict)}_{int(time.time())}"
                
                # Get element properties
                element_data = self._get_element_properties(child)
                
                # Create element object
                element = AccessibilityElement(
                    element_id=element_id,
                    element_type=element_data.get("type", "unknown"),
                    role=element_data.get("role", "unknown"),
                    name=element_data.get("name"),
                    value=element_data.get("value"),
                    description=element_data.get("description"),
                    bounds=element_data.get("bounds"),
                    parent_id=parent_id,
                    attributes=element_data.get("attributes", {})
                )
                
                # Add to dictionary
                elements_dict[element_id] = element
                
                # Add to parent's children
                if parent_id in elements_dict:
                    parent = elements_dict[parent_id]
                    parent.children_ids.append(element_id)
                
                # Recursively process this element's children
                self._build_element_tree(child, element_id, elements_dict, depth + 1, max_depth)
                
        except Exception as e:
            logger.error(f"Error building element tree: {e}")
    
    def _get_element_properties(self, ax_element) -> Dict[str, Any]:
        """Get properties of an accessibility element"""
        properties = {
            "attributes": {}
        }
        
        try:
            # Get role
            role_attr = Quartz.kAXRoleAttribute
            role, error = Quartz.AXUIElementCopyAttributeValue(ax_element, role_attr, None)
            if not error and role:
                properties["role"] = role
                
                # Map role to element type
                role_to_type = {
                    "AXButton": "button",
                    "AXTextField": "textfield",
                    "AXTextArea": "textarea",
                    "AXCheckBox": "checkbox",
                    "AXRadioButton": "radio",
                    "AXStaticText": "text",
                    "AXLink": "link",
                    "AXMenu": "menu",
                    "AXMenuItem": "menuitem",
                    "AXMenuBar": "menubar",
                    "AXWindow": "window",
                    "AXSlider": "slider",
                    "AXScrollBar": "scrollbar",
                    "AXPopUpButton": "dropdown",
                    "AXTable": "table",
                    "AXList": "list",
                    "AXImage": "image"
                }
                
                properties["type"] = role_to_type.get(role, "unknown")
            
            # Get title/name
            title_attr = Quartz.kAXTitleAttribute
            title, error = Quartz.AXUIElementCopyAttributeValue(ax_element, title_attr, None)
            if not error and title:
                properties["name"] = title
            
            # Get value
            value_attr = Quartz.kAXValueAttribute
            value, error = Quartz.AXUIElementCopyAttributeValue(ax_element, value_attr, None)
            if not error and value:
                properties["value"] = str(value)
            
            # Get description
            desc_attr = Quartz.kAXDescriptionAttribute
            desc, error = Quartz.AXUIElementCopyAttributeValue(ax_element, desc_attr, None)
            if not error and desc:
                properties["description"] = desc
            
            # Get position and size to calculate bounds
            position_attr = Quartz.kAXPositionAttribute
            size_attr = Quartz.kAXSizeAttribute
            
            position, pos_error = Quartz.AXUIElementCopyAttributeValue(ax_element, position_attr, None)
            size, size_error = Quartz.AXUIElementCopyAttributeValue(ax_element, size_attr, None)
            
            if not pos_error and not size_error and position and size:
                x, y = position.value()
                width, height = size.value()
                properties["bounds"] = (x, y, x + width, y + height)
            
            # Get enabled state
            enabled_attr = Quartz.kAXEnabledAttribute
            enabled, error = Quartz.AXUIElementCopyAttributeValue(ax_element, enabled_attr, None)
            if not error:
                properties["attributes"]["enabled"] = bool(enabled)
            
            # Get focused state
            focused_attr = Quartz.kAXFocusedAttribute
            focused, error = Quartz.AXUIElementCopyAttributeValue(ax_element, focused_attr, None)
            if not error:
                properties["attributes"]["focused"] = bool(focused)
            
            # Get actions
            actions_array, error = Quartz.AXUIElementCopyActionNames(ax_element)
            if not error and actions_array:
                actions = [actions_array.objectAtIndex_(i) for i in range(actions_array.count())]
                properties["attributes"]["actions"] = actions
            
            return properties
            
        except Exception as e:
            logger.error(f"Error getting element properties: {e}")
            return properties

class WindowsAccessibilityAdapter:
    """Windows-specific implementation of accessibility API"""
    
    def __init__(self):
        self.initialized = False
        
        try:
            # Initialize UI Automation
            import comtypes.client
            self.uia = comtypes.client.CreateObject("UIAutomationClient.CUIAutomation")
            self.initialized = True
            logger.info("✅ Windows Accessibility Adapter initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Windows Accessibility Adapter: {e}")
    
    async def get_ui_tree(self) -> Optional[AccessibilityTree]:
        """Get UI tree from Windows UI Automation"""
        if not self.initialized:
            logger.error("Windows Accessibility Adapter not initialized")
            return None
            
        # Implementation will be platform-specific
        # This is a placeholder
        logger.warning("Windows UI tree implementation not available yet")
        return None

class LinuxAccessibilityAdapter:
    """Linux-specific implementation of accessibility API"""
    
    def __init__(self):
        self.initialized = False
        
        try:
            # Initialize AT-SPI
            Atspi.init()
            self.initialized = True
            logger.info("✅ Linux Accessibility Adapter initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Linux Accessibility Adapter: {e}")
    
    async def get_ui_tree(self) -> Optional[AccessibilityTree]:
        """Get UI tree from Linux AT-SPI"""
        if not self.initialized:
            logger.error("Linux Accessibility Adapter not initialized")
            return None
            
        # Implementation will be platform-specific
        # This is a placeholder
        logger.warning("Linux UI tree implementation not available yet")
        return None

class AccessibilityAdapter:
    """Platform-agnostic accessibility adapter that uses the appropriate platform-specific implementation"""
    
    def __init__(self):
        self.platform = PLATFORM
        self.adapter = None
        
        if not ACCESSIBILITY_AVAILABLE:
            logger.warning("Accessibility APIs not available on this platform")
            return
        
        try:
            if self.platform == "darwin":
                self.adapter = MacOSAccessibilityAdapter()
            elif self.platform == "windows":
                self.adapter = WindowsAccessibilityAdapter()
            elif self.platform == "linux":
                self.adapter = LinuxAccessibilityAdapter()
            else:
                logger.error(f"Unsupported platform: {self.platform}")
                return
                
            logger.info(f"✅ Accessibility Adapter initialized for {self.platform}")
        except Exception as e:
            logger.error(f"Failed to initialize Accessibility Adapter: {e}")
    
    async def get_ui_tree(self) -> Optional[AccessibilityTree]:
        """Get UI tree from platform-specific accessibility APIs"""
        if not self.adapter:
            logger.error("No platform adapter available")
            return None
            
        return await self.adapter.get_ui_tree()
    
    async def find_element_by_name(self, name: str, partial: bool = True) -> Optional[Dict[str, Any]]:
        """Find an element by name/text"""
        tree = await self.get_ui_tree()
        if not tree:
            return None
            
        element = tree.get_element_by_name(name, partial)
        if not element:
            return None
            
        return {
            "element_id": element.element_id,
            "type": element.element_type,
            "name": element.name,
            "bounds": element.bounds,
            "center": element.center,
            "clickable": element.is_clickable,
            "editable": element.is_editable
        }
    
    async def get_clickable_elements(self) -> List[Dict[str, Any]]:
        """Get all clickable elements"""
        tree = await self.get_ui_tree()
        if not tree:
            return []
            
        elements = tree.get_clickable_elements()
        return [
            {
                "element_id": e.element_id,
                "type": e.element_type,
                "name": e.name,
                "bounds": e.bounds,
                "center": e.center,
                "role": e.role
            }
            for e in elements
        ]
    
    async def get_active_application(self) -> Dict[str, Any]:
        """Get information about the active application"""
        tree = await self.get_ui_tree()
        if not tree:
            return {"name": "Unknown", "title": "Unknown"}
            
        return {
            "name": tree.application_name,
            "title": tree.window_title,
            "element_count": len(tree.elements)
        }

# Create singleton instance
accessibility = AccessibilityAdapter()

async def main():
    """Test the accessibility adapter"""
    print("Testing Accessibility Adapter...")
    print(f"Platform: {PLATFORM}")
    print(f"Accessibility available: {ACCESSIBILITY_AVAILABLE}")
    
    if not ACCESSIBILITY_AVAILABLE:
        print("Accessibility APIs not available on this platform")
        return
    
    # Get UI tree
    print("Getting UI tree...")
    tree = await accessibility.get_ui_tree()
    
    if not tree:
        print("Failed to get UI tree")
        return
    
    print(f"Got UI tree with {len(tree.elements)} elements")
    print(f"Application: {tree.application_name}")
    print(f"Window title: {tree.window_title}")
    
    # Get clickable elements
    print("\nGetting clickable elements...")
    clickable = tree.get_clickable_elements()
    print(f"Found {len(clickable)} clickable elements")
    
    for i, element in enumerate(clickable[:5]):  # Show first 5
        print(f"{i+1}. {element.name} ({element.element_type}) at {element.center}")
    
    # Get editable elements
    print("\nGetting editable elements...")
    editable = tree.get_editable_elements()
    print(f"Found {len(editable)} editable elements")
    
    for i, element in enumerate(editable[:5]):  # Show first 5
        print(f"{i+1}. {element.name} ({element.element_type}) at {element.center}")

if __name__ == "__main__":
    # Run the test
    asyncio.run(main())