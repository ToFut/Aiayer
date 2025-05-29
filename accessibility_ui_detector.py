#!/usr/bin/env python3
"""
Accessibility-First UI Detection
Direct access to UI elements without screen capture
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import sys

# Platform-specific accessibility imports
if sys.platform == "darwin":
    try:
        import ApplicationServices
        import Quartz.CoreGraphics as CG
        from AppKit import NSWorkspace, NSAccessibilityElement
        from PyObjCTools import AppHelper
        MACOS_ACCESSIBILITY_AVAILABLE = True
    except ImportError:
        MACOS_ACCESSIBILITY_AVAILABLE = False
elif sys.platform == "win32":
    try:
        import comtypes
        import comtypes.client
        from comtypes.gen import UIAutomationCore
        WINDOWS_UIAUTOMATION_AVAILABLE = True
    except ImportError:
        WINDOWS_UIAUTOMATION_AVAILABLE = False
else:
    try:
        import pyatspi
        LINUX_ATSPI_AVAILABLE = True
    except ImportError:
        LINUX_ATSPI_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UIElementType(Enum):
    BUTTON = "button"
    TEXT_FIELD = "text_field"
    LABEL = "label"
    MENU = "menu"
    MENU_ITEM = "menu_item"
    WINDOW = "window"
    TAB = "tab"
    CHECKBOX = "checkbox"
    RADIO_BUTTON = "radio_button"
    SLIDER = "slider"
    SCROLL_BAR = "scroll_bar"
    TABLE = "table"
    LIST = "list"
    TREE = "tree"
    IMAGE = "image"
    LINK = "link"
    UNKNOWN = "unknown"

@dataclass
class UIElement:
    """Accessible UI element - no visual data needed"""
    id: str
    element_type: UIElementType
    role: str
    title: str
    value: Optional[str]
    bounds: Tuple[int, int, int, int]  # x, y, width, height
    is_enabled: bool
    is_visible: bool
    is_focusable: bool
    parent_id: Optional[str]
    children_ids: List[str]
    app_name: str
    window_title: str
    actions: List[str]  # Available actions (click, type, etc.)
    properties: Dict[str, Any]
    timestamp: float

class MacOSAccessibilityDetector:
    """macOS Accessibility API integration"""
    
    def __init__(self):
        self.accessibility_enabled = False
        
    async def initialize(self) -> bool:
        """Initialize macOS accessibility"""
        if not MACOS_ACCESSIBILITY_AVAILABLE:
            return False
        
        try:
            # Check accessibility permissions
            trusted = ApplicationServices.AXIsProcessTrusted()
            if not trusted:
                logger.warning("⚠️  Accessibility permissions required")
                logger.info("Enable in: System Preferences > Security & Privacy > Accessibility")
                return False
            
            self.accessibility_enabled = True
            logger.info("✅ macOS Accessibility API enabled")
            return True
            
        except Exception as e:
            logger.error(f"macOS accessibility initialization failed: {e}")
            return False
    
    async def get_ui_elements(self) -> List[UIElement]:
        """Get UI elements from active application"""
        if not self.accessibility_enabled:
            return []
        
        elements = []
        
        try:
            # Get frontmost application
            workspace = NSWorkspace.sharedWorkspace()
            frontmost_app = workspace.activeApplication()
            
            if not frontmost_app:
                return elements
            
            app_name = frontmost_app.get('NSApplicationName', 'Unknown')
            app_pid = frontmost_app.get('NSApplicationProcessIdentifier')
            
            if app_pid:
                # Get accessibility element for app
                app_element = NSAccessibilityElement.accessibilityElementWithProcessIdentifier_(app_pid)
                
                if app_element:
                    # Get windows
                    windows = app_element.accessibilityAttributeValue_("AXWindows")
                    
                    if windows:
                        for window in windows:
                            window_elements = await self._process_window(window, app_name)
                            elements.extend(window_elements)
            
        except Exception as e:
            logger.error(f"Error getting macOS UI elements: {e}")
        
        return elements
    
    async def _process_window(self, window, app_name: str) -> List[UIElement]:
        """Process accessibility window and extract elements"""
        elements = []
        
        try:
            window_title = window.accessibilityAttributeValue_("AXTitle") or ""
            window_size = window.accessibilityAttributeValue_("AXSize")
            window_position = window.accessibilityAttributeValue_("AXPosition")
            
            # Process window itself
            window_element = UIElement(
                id=f"window_{id(window)}",
                element_type=UIElementType.WINDOW,
                role="window",
                title=window_title,
                value=None,
                bounds=(
                    int(window_position.x) if window_position else 0,
                    int(window_position.y) if window_position else 0,
                    int(window_size.width) if window_size else 0,
                    int(window_size.height) if window_size else 0
                ),
                is_enabled=True,
                is_visible=True,
                is_focusable=True,
                parent_id=None,
                children_ids=[],
                app_name=app_name,
                window_title=window_title,
                actions=["focus", "close", "minimize"],
                properties={},
                timestamp=time.time()
            )
            elements.append(window_element)
            
            # Get child elements recursively
            children = window.accessibilityAttributeValue_("AXChildren")
            if children:
                for child in children:
                    child_elements = await self._process_element_recursive(
                        child, app_name, window_title, window_element.id
                    )
                    elements.extend(child_elements)
                    window_element.children_ids.extend([e.id for e in child_elements])
            
        except Exception as e:
            logger.error(f"Error processing window: {e}")
        
        return elements
    
    async def _process_element_recursive(self, element, app_name: str, 
                                       window_title: str, parent_id: str) -> List[UIElement]:
        """Recursively process accessibility elements"""
        elements = []
        
        try:
            role = element.accessibilityAttributeValue_("AXRole") or "unknown"
            title = element.accessibilityAttributeValue_("AXTitle") or ""
            value = element.accessibilityAttributeValue_("AXValue") or ""
            
            # Get element bounds
            position = element.accessibilityAttributeValue_("AXPosition")
            size = element.accessibilityAttributeValue_("AXSize")
            
            # Map accessibility role to our enum
            element_type = self._map_role_to_type(role)
            
            # Get available actions
            actions = element.accessibilityAttributeValue_("AXActions") or []
            action_names = [str(action) for action in actions]
            
            ui_element = UIElement(
                id=f"element_{id(element)}",
                element_type=element_type,
                role=role,
                title=title,
                value=str(value) if value else None,
                bounds=(
                    int(position.x) if position else 0,
                    int(position.y) if position else 0,
                    int(size.width) if size else 0,
                    int(size.height) if size else 0
                ),
                is_enabled=element.accessibilityAttributeValue_("AXEnabled") or False,
                is_visible=not (element.accessibilityAttributeValue_("AXHidden") or False),
                is_focusable=element.accessibilityAttributeValue_("AXFocusable") or False,
                parent_id=parent_id,
                children_ids=[],
                app_name=app_name,
                window_title=window_title,
                actions=action_names,
                properties={
                    'role_description': element.accessibilityAttributeValue_("AXRoleDescription") or "",
                    'help': element.accessibilityAttributeValue_("AXHelp") or "",
                    'description': element.accessibilityAttributeValue_("AXDescription") or ""
                },
                timestamp=time.time()
            )
            
            elements.append(ui_element)
            
            # Process children
            children = element.accessibilityAttributeValue_("AXChildren")
            if children:
                for child in children:
                    child_elements = await self._process_element_recursive(
                        child, app_name, window_title, ui_element.id
                    )
                    elements.extend(child_elements)
                    ui_element.children_ids.extend([e.id for e in child_elements])
            
        except Exception as e:
            logger.debug(f"Error processing element: {e}")
        
        return elements
    
    def _map_role_to_type(self, role: str) -> UIElementType:
        """Map accessibility role to UI element type"""
        role_mapping = {
            "AXButton": UIElementType.BUTTON,
            "AXTextField": UIElementType.TEXT_FIELD,
            "AXStaticText": UIElementType.LABEL,
            "AXMenu": UIElementType.MENU,
            "AXMenuItem": UIElementType.MENU_ITEM,
            "AXWindow": UIElementType.WINDOW,
            "AXTab": UIElementType.TAB,
            "AXCheckBox": UIElementType.CHECKBOX,
            "AXRadioButton": UIElementType.RADIO_BUTTON,
            "AXSlider": UIElementType.SLIDER,
            "AXScrollBar": UIElementType.SCROLL_BAR,
            "AXTable": UIElementType.TABLE,
            "AXList": UIElementType.LIST,
            "AXOutline": UIElementType.TREE,
            "AXImage": UIElementType.IMAGE,
            "AXLink": UIElementType.LINK
        }
        
        return role_mapping.get(role, UIElementType.UNKNOWN)

class WindowsUIAutomationDetector:
    """Windows UI Automation integration"""
    
    def __init__(self):
        self.automation = None
        self.root_element = None
        
    async def initialize(self) -> bool:
        """Initialize Windows UI Automation"""
        if not WINDOWS_UIAUTOMATION_AVAILABLE:
            return False
        
        try:
            # Initialize COM
            comtypes.CoInitialize()
            
            # Get UI Automation
            self.automation = comtypes.client.CreateObject(
                "{ff48dba4-60ef-4201-aa87-54103eef594e}",
                interface=UIAutomationCore.IUIAutomation
            )
            
            self.root_element = self.automation.GetRootElement()
            
            logger.info("✅ Windows UI Automation enabled")
            return True
            
        except Exception as e:
            logger.error(f"Windows UI Automation initialization failed: {e}")
            return False
    
    async def get_ui_elements(self) -> List[UIElement]:
        """Get UI elements from active window"""
        if not self.automation or not self.root_element:
            return []
        
        elements = []
        
        try:
            # Get foreground window
            foreground_element = self.automation.GetForegroundElement()
            
            if foreground_element:
                window_elements = await self._process_element_recursive(
                    foreground_element, None
                )
                elements.extend(window_elements)
            
        except Exception as e:
            logger.error(f"Error getting Windows UI elements: {e}")
        
        return elements
    
    async def _process_element_recursive(self, element, parent_id: Optional[str]) -> List[UIElement]:
        """Recursively process UI Automation elements"""
        elements = []
        
        try:
            # Get element properties
            control_type = element.CurrentControlType
            name = element.CurrentName or ""
            automation_id = element.CurrentAutomationId or ""
            
            # Get bounding rectangle
            rect = element.CurrentBoundingRectangle
            
            ui_element = UIElement(
                id=f"element_{automation_id}_{id(element)}",
                element_type=self._map_control_type_to_type(control_type),
                role=f"UIA_{control_type}",
                title=name,
                value=getattr(element, 'CurrentValue', None),
                bounds=(int(rect.left), int(rect.top), 
                       int(rect.right - rect.left), int(rect.bottom - rect.top)),
                is_enabled=element.CurrentIsEnabled,
                is_visible=not element.CurrentIsOffscreen,
                is_focusable=element.CurrentIsKeyboardFocusable,
                parent_id=parent_id,
                children_ids=[],
                app_name=element.CurrentProcessId,
                window_title=name if control_type == 50032 else "",  # Window control type
                actions=self._get_available_patterns(element),
                properties={
                    'automation_id': automation_id,
                    'control_type': control_type,
                    'class_name': element.CurrentClassName or "",
                    'framework_id': element.CurrentFrameworkId or ""
                },
                timestamp=time.time()
            )
            
            elements.append(ui_element)
            
            # Get children
            children = element.FindAll(1, self.automation.CreateTrueCondition())  # TreeScope_Children
            if children:
                for i in range(children.Length):
                    child = children.GetElement(i)
                    child_elements = await self._process_element_recursive(child, ui_element.id)
                    elements.extend(child_elements)
                    ui_element.children_ids.extend([e.id for e in child_elements])
            
        except Exception as e:
            logger.debug(f"Error processing Windows element: {e}")
        
        return elements
    
    def _map_control_type_to_type(self, control_type: int) -> UIElementType:
        """Map Windows control type to UI element type"""
        type_mapping = {
            50000: UIElementType.BUTTON,      # Button
            50004: UIElementType.TEXT_FIELD,  # Edit
            50020: UIElementType.LABEL,       # Text
            50009: UIElementType.MENU,        # Menu
            50011: UIElementType.MENU_ITEM,   # MenuItem
            50032: UIElementType.WINDOW,      # Window
            50018: UIElementType.TAB,         # TabItem
            50002: UIElementType.CHECKBOX,    # CheckBox
            50003: UIElementType.RADIO_BUTTON, # RadioButton
            50033: UIElementType.SLIDER,      # Slider
            50001: UIElementType.SCROLL_BAR,  # ScrollBar
            50026: UIElementType.TABLE,       # Table
            50008: UIElementType.LIST,        # List
            50023: UIElementType.TREE,        # Tree
            50005: UIElementType.IMAGE,       # Image
            50005: UIElementType.LINK         # Hyperlink
        }
        
        return type_mapping.get(control_type, UIElementType.UNKNOWN)
    
    def _get_available_patterns(self, element) -> List[str]:
        """Get available interaction patterns for element"""
        patterns = []
        
        # Check common patterns
        pattern_checks = [
            ("Invoke", "click"),
            ("Value", "set_value"),
            ("Text", "set_text"),
            ("Toggle", "toggle"),
            ("Selection", "select"),
            ("ScrollItem", "scroll_into_view")
        ]
        
        for pattern_name, action_name in pattern_checks:
            try:
                pattern_id = getattr(UIAutomationCore, f"UIA_{pattern_name}PatternId", None)
                if pattern_id and element.GetCurrentPattern(pattern_id):
                    patterns.append(action_name)
            except:
                continue
        
        return patterns

class AccessibilityUIDetector:
    """Cross-platform accessibility-based UI detection"""
    
    def __init__(self):
        self.platform_detector = None
        self.initialized = False
        
    async def initialize(self) -> bool:
        """Initialize platform-specific accessibility detector"""
        if sys.platform == "darwin":
            self.platform_detector = MacOSAccessibilityDetector()
        elif sys.platform == "win32":
            self.platform_detector = WindowsUIAutomationDetector()
        else:
            logger.warning("Linux accessibility support limited")
            return False
        
        if self.platform_detector:
            self.initialized = await self.platform_detector.initialize()
            
        return self.initialized
    
    async def get_current_ui_elements(self) -> List[UIElement]:
        """Get current UI elements without screen capture"""
        if not self.initialized or not self.platform_detector:
            return []
        
        return await self.platform_detector.get_ui_elements()
    
    async def find_elements_by_type(self, element_type: UIElementType) -> List[UIElement]:
        """Find elements by type"""
        all_elements = await self.get_current_ui_elements()
        return [element for element in all_elements if element.element_type == element_type]
    
    async def find_elements_by_text(self, text: str) -> List[UIElement]:
        """Find elements containing specific text"""
        all_elements = await self.get_current_ui_elements()
        matching_elements = []
        
        for element in all_elements:
            if (text.lower() in element.title.lower() or 
                (element.value and text.lower() in element.value.lower())):
                matching_elements.append(element)
        
        return matching_elements
    
    async def get_clickable_elements(self) -> List[UIElement]:
        """Get all clickable elements"""
        all_elements = await self.get_current_ui_elements()
        return [element for element in all_elements 
                if element.is_enabled and "click" in element.actions]

# Example usage
async def main():
    """Test accessibility UI detection"""
    detector = AccessibilityUIDetector()
    
    success = await detector.initialize()
    if not success:
        logger.error("❌ Failed to initialize accessibility detector")
        return
    
    logger.info("✅ Accessibility detector initialized")
    
    # Get current UI elements
    elements = await detector.get_current_ui_elements()
    logger.info(f"📱 Found {len(elements)} UI elements")
    
    # Show buttons
    buttons = await detector.find_elements_by_type(UIElementType.BUTTON)
    logger.info(f"🔘 Found {len(buttons)} buttons")
    
    for button in buttons[:5]:  # Show first 5
        logger.info(f"  Button: '{button.title}' at {button.bounds}")
    
    # Show text fields
    text_fields = await detector.find_elements_by_type(UIElementType.TEXT_FIELD)
    logger.info(f"📝 Found {len(text_fields)} text fields")

if __name__ == "__main__":
    asyncio.run(main())