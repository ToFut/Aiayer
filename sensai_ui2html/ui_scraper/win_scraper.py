#!/usr/bin/env python3
"""
Windows UI Scraper - Uses uiautomation for UI tree extraction
"""

import logging
from typing import Dict, Any, List
import time

logger = logging.getLogger(__name__)

def scrape_windows_ui() -> Dict[str, Any]:
    """
    Scrape the Windows UI tree using uiautomation.
    
    Returns:
        Dict containing the UI tree structure
    """
    try:
        from uiautomation import GetRootControl
        
        def traverse_node(node) -> Dict[str, Any]:
            """Recursively traverse a UI node and extract its properties."""
            try:
                # Get basic properties
                name = getattr(node, 'Name', '')
                control_type = getattr(node, 'ControlTypeName', 'Unknown')
                automation_id = getattr(node, 'AutomationId', '')
                bounding_rect = getattr(node, 'BoundingRectangle', None)
                
                # Convert bounding rectangle to bounds format
                bounds = []
                if bounding_rect:
                    bounds = [bounding_rect.left, bounding_rect.top, 
                             bounding_rect.right - bounding_rect.left,
                             bounding_rect.bottom - bounding_rect.top]
                
                # Get children
                children = []
                try:
                    child_nodes = node.GetChildren()
                    children = [traverse_node(child) for child in child_nodes]
                except Exception as e:
                    logger.debug(f"Error getting children: {e}")
                
                return {
                    "name": name or control_type,
                    "type": control_type,
                    "id": automation_id or f"{control_type}_{hash(name)}_{int(time.time() * 1000)}",
                    "bounds": bounds,
                    "children": children
                }
            except Exception as e:
                logger.debug(f"Error traversing node: {e}")
                return {
                    "name": "error_node",
                    "type": "Unknown",
                    "id": f"error_{int(time.time() * 1000)}",
                    "bounds": [],
                    "children": []
                }
        
        # Get the root control
        try:
            root = GetRootControl()
            return traverse_node(root)
        except Exception as e:
            logger.error(f"Error getting root control: {e}")
            return _get_windows_fallback_tree()
            
    except ImportError:
        logger.error("uiautomation not available. Install with: pip install uiautomation")
        return _get_windows_fallback_tree()

def _get_windows_fallback_tree() -> Dict[str, Any]:
    """
    Fallback UI tree for Windows when uiautomation is not available.
    """
    return {
        "name": "Windows Desktop",
        "type": "Window",
        "id": "windows_desktop",
        "bounds": [0, 0, 1920, 1080],
        "children": [
            {
                "name": "Taskbar",
                "type": "ToolBar",
                "id": "taskbar",
                "bounds": [0, 1040, 1920, 40],
                "children": []
            },
            {
                "name": "Desktop",
                "type": "Group",
                "id": "desktop_group",
                "bounds": [0, 0, 1920, 1040],
                "children": []
            }
        ]
    } 