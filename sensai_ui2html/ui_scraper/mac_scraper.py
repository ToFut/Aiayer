#!/usr/bin/env python3
"""
macOS UI Scraper - Uses atomacos for accessibility tree extraction
"""

import logging
from typing import Dict, Any, List
import time
import subprocess

logger = logging.getLogger(__name__)

def scrape_macos_ui() -> Dict[str, Any]:
    """
    Scrape the macOS UI tree using atomacos.
    
    Returns:
        Dict containing the UI tree structure
    """
    try:
        import atomacos
        
        def traverse_node(node) -> Dict[str, Any]:
            """Recursively traverse a UI node and extract its properties, ensuring all values are JSON-serializable."""
            try:
                # Get basic properties
                role = getattr(node, 'AXRole', 'Unknown')
                title = getattr(node, 'AXTitle', '')
                value = getattr(node, 'AXValue', '')
                frame = getattr(node, 'AXFrame', None)
                description = getattr(node, 'AXDescription', '')
                help_text = getattr(node, 'AXHelp', '')

                # Convert frame to bounds format
                bounds = []
                if frame and isinstance(frame, (list, tuple)) and len(frame) == 4:
                    bounds = [float(frame[0]), float(frame[1]), float(frame[2]) - float(frame[0]), float(frame[3]) - float(frame[1])]

                # Get children
                children = []
                try:
                    child_nodes = getattr(node, 'AXChildren', []) or []
                    # Only traverse if child is a valid atomacos element
                    for child in child_nodes:
                        # Defensive: skip if not atomacos element
                        if hasattr(child, 'AXRole'):
                            children.append(traverse_node(child))
                except Exception as e:
                    logger.debug(f"Error getting children: {e}")

                # Ensure all values are serializable
                def safe(val):
                    """Safely convert any value to a serializable type."""
                    if val is None:
                        return None
                    if isinstance(val, (str, int, float, bool, list, dict)):
                        return val
                    try:
                        # Handle Objective-C types and other non-standard types
                        if hasattr(val, '__str__'):
                            return str(val)
                        else:
                            return repr(val)
                    except Exception:
                        return str(type(val).__name__)

                # Create a more descriptive name
                name_parts = []
                if safe(title):
                    name_parts.append(safe(title))
                if safe(value):
                    name_parts.append(safe(value))
                if safe(description):
                    name_parts.append(safe(description))
                if safe(help_text):
                    name_parts.append(safe(help_text))
                
                name = " - ".join(name_parts) if name_parts else safe(role)

                return {
                    "name": name,
                    "type": safe(role),
                    "id": f"{safe(role)}_{hash(name)}_{int(time.time() * 1000)}",
                    "bounds": bounds,
                    "value": safe(value),
                    "title": safe(title),
                    "description": safe(description),
                    "help": safe(help_text),
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
        
        # Try multiple methods to get comprehensive UI information
        methods = [
            ("System UI", lambda: _get_system_ui_tree()),
            ("Active Application", lambda: _get_active_app_tree()),
            ("Finder App", lambda: atomacos.getAppRefByBundleId('com.apple.finder')),
            ("Safari App", lambda: atomacos.getAppRefByBundleId('com.apple.Safari')),
            ("Terminal App", lambda: atomacos.getAppRefByBundleId('com.apple.Terminal')),
        ]
        
        ui_trees = []
        
        for method_name, method_func in methods:
            try:
                logger.info(f"Trying method: {method_name}")
                result = method_func()
                if result:
                    logger.info(f"Successfully got UI with {method_name}")
                    ui_trees.append({
                        "source": method_name,
                        "tree": result
                    })
            except Exception as e:
                logger.debug(f"Method {method_name} failed: {e}")
                continue
        
        # Combine all UI trees into a comprehensive view
        if ui_trees:
            return _combine_ui_trees(ui_trees)
        
        logger.warning("All atomacos methods failed, using fallback")
        return _get_mac_fallback_tree()
            
    except ImportError:
        logger.error("atomacos not available. Install with: pip install atomacos")
        return _get_mac_fallback_tree()

def _get_system_ui_tree():
    """Get system-wide UI tree including menu bar, dock, etc."""
    try:
        import atomacos
        
        def traverse_node(node) -> Dict[str, Any]:
            """Recursively traverse a UI node and extract its properties."""
            try:
                role = getattr(node, 'AXRole', 'Unknown')
                title = getattr(node, 'AXTitle', '')
                value = getattr(node, 'AXValue', '')
                frame = getattr(node, 'AXFrame', None)
                
                bounds = []
                if frame and isinstance(frame, (list, tuple)) and len(frame) == 4:
                    bounds = [float(frame[0]), float(frame[1]), float(frame[2]) - float(frame[0]), float(frame[3]) - float(frame[1])]
                
                children = []
                try:
                    child_nodes = getattr(node, 'AXChildren', []) or []
                    for child in child_nodes:
                        if hasattr(child, 'AXRole'):
                            children.append(traverse_node(child))
                except Exception as e:
                    pass
                
                def safe(val):
                    if val is None:
                        return None
                    if isinstance(val, (str, int, float, bool, list, dict)):
                        return val
                    try:
                        if hasattr(val, '__str__'):
                            return str(val)
                        else:
                            return repr(val)
                    except Exception:
                        return str(type(val).__name__)
                
                return {
                    "name": safe(title) or safe(value) or safe(role),
                    "type": safe(role),
                    "id": f"{safe(role)}_{hash(safe(title))}_{int(time.time() * 1000)}",
                    "bounds": bounds,
                    "value": safe(value),
                    "children": children
                }
            except Exception as e:
                return {
                    "name": "error_node",
                    "type": "Unknown",
                    "id": f"error_{int(time.time() * 1000)}",
                    "bounds": [],
                    "children": []
                }
        
        # Get system UI elements
        system_ui = {
            "name": "macOS System UI",
            "type": "AXApplication",
            "id": "system_ui",
            "bounds": [0, 0, 1920, 1080],
            "children": []
        }
        
        # Try to get menu bar
        try:
            menu_bar = atomacos.getAppRefByBundleId('com.apple.systemuiserver')
            if menu_bar:
                system_ui["children"].append(traverse_node(menu_bar))
        except:
            pass
            
        return system_ui
    except:
        return None

def _get_active_app_tree():
    """Get the currently active application's UI tree."""
    try:
        import atomacos
        
        def traverse_node(node) -> Dict[str, Any]:
            """Recursively traverse a UI node and extract its properties."""
            try:
                role = getattr(node, 'AXRole', 'Unknown')
                title = getattr(node, 'AXTitle', '')
                value = getattr(node, 'AXValue', '')
                frame = getattr(node, 'AXFrame', None)
                
                bounds = []
                if frame and isinstance(frame, (list, tuple)) and len(frame) == 4:
                    bounds = [float(frame[0]), float(frame[1]), float(frame[2]) - float(frame[0]), float(frame[3]) - float(frame[1])]
                
                children = []
                try:
                    child_nodes = getattr(node, 'AXChildren', []) or []
                    for child in child_nodes:
                        if hasattr(child, 'AXRole'):
                            children.append(traverse_node(child))
                except Exception as e:
                    pass
                
                def safe(val):
                    if val is None:
                        return None
                    if isinstance(val, (str, int, float, bool, list, dict)):
                        return val
                    try:
                        if hasattr(val, '__str__'):
                            return str(val)
                        else:
                            return repr(val)
                    except Exception:
                        return str(type(val).__name__)
                
                return {
                    "name": safe(title) or safe(value) or safe(role),
                    "type": safe(role),
                    "id": f"{safe(role)}_{hash(safe(title))}_{int(time.time() * 1000)}",
                    "bounds": bounds,
                    "value": safe(value),
                    "children": children
                }
            except Exception as e:
                return {
                    "name": "error_node",
                    "type": "Unknown",
                    "id": f"error_{int(time.time() * 1000)}",
                    "bounds": [],
                    "children": []
                }
        
        # Get active application
        active_app = atomacos.getActiveApp()
        if active_app:
            return traverse_node(active_app)
    except:
        pass
    return None

def _combine_ui_trees(ui_trees):
    """Combine multiple UI trees into a comprehensive view."""
    import copy
    combined = {
        "name": "macOS Comprehensive UI",
        "type": "AXApplication",
        "id": "comprehensive_ui",
        "bounds": [0, 0, 1920, 1080],
        "children": []
    }
    
    for ui_tree in ui_trees:
        tree = ui_tree["tree"]
        if isinstance(tree, dict):
            # Safe to copy and add source
            tree_copy = copy.deepcopy(tree)
            tree_copy["source"] = ui_tree["source"]
            combined["children"].append(tree_copy)
        elif hasattr(tree, 'AXRole'):
            # This is an atomacos NativeUIElement - traverse it properly
            try:
                def traverse_atomacos_node(node):
                    """Recursively traverse an atomacos node and extract its properties."""
                    try:
                        role = getattr(node, 'AXRole', 'Unknown')
                        title = getattr(node, 'AXTitle', '')
                        value = getattr(node, 'AXValue', '')
                        frame = getattr(node, 'AXFrame', None)
                        
                        bounds = []
                        if frame and isinstance(frame, (list, tuple)) and len(frame) == 4:
                            bounds = [float(frame[0]), float(frame[1]), float(frame[2]) - float(frame[0]), float(frame[3]) - float(frame[1])]
                        
                        children = []
                        try:
                            child_nodes = getattr(node, 'AXChildren', []) or []
                            for child in child_nodes:
                                if hasattr(child, 'AXRole'):
                                    children.append(traverse_atomacos_node(child))
                        except Exception as e:
                            pass
                        
                        def safe(val):
                            if val is None:
                                return None
                            if isinstance(val, (str, int, float, bool, list, dict)):
                                return val
                            try:
                                if hasattr(val, '__str__'):
                                    return str(val)
                                else:
                                    return repr(val)
                            except Exception:
                                return str(type(val).__name__)
                        
                        return {
                            "name": safe(title) or safe(value) or safe(role),
                            "type": safe(role),
                            "id": f"{safe(role)}_{hash(safe(title))}_{int(time.time() * 1000)}",
                            "bounds": bounds,
                            "value": safe(value),
                            "children": children
                        }
                    except Exception as e:
                        return {
                            "name": "error_node",
                            "type": "Unknown",
                            "id": f"error_{int(time.time() * 1000)}",
                            "bounds": [],
                            "children": []
                        }
                
                # Traverse the atomacos object properly
                processed_tree = traverse_atomacos_node(tree)
                processed_tree["source"] = ui_tree["source"]
                combined["children"].append(processed_tree)
                
            except Exception as e:
                logger.error(f"Error processing atomacos tree: {e}")
                # Fallback to string representation
                combined["children"].append({
                    "name": str(tree),
                    "type": "Unknown",
                    "id": f"unknown_{int(time.time() * 1000)}",
                    "bounds": [],
                    "children": [],
                    "source": ui_tree["source"]
                })
        else:
            # If not a dict or atomacos element, skip or convert to string for debug
            combined["children"].append({
                "name": str(tree),
                "type": "Unknown",
                "id": f"unknown_{int(time.time() * 1000)}",
                "bounds": [],
                "children": [],
                "source": ui_tree["source"]
            })
    
    return combined

def _get_mac_fallback_tree() -> Dict[str, Any]:
    """
    Fallback UI tree for macOS when atomacos is not available or fails.
    """
    return {
        "name": "macOS Desktop",
        "type": "AXApplication",
        "id": "macos_desktop",
        "bounds": [0, 0, 1920, 1080],
        "children": [
            {
                "name": "Menu Bar",
                "type": "AXMenuBar",
                "id": "menu_bar",
                "bounds": [0, 0, 1920, 24],
                "children": []
            },
            {
                "name": "Desktop",
                "type": "AXGroup",
                "id": "desktop_group",
                "bounds": [0, 24, 1920, 1056],
                "children": []
            }
        ]
    } 