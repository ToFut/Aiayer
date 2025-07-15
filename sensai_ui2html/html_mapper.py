#!/usr/bin/env python3
"""
HTML Mapper - Converts UI tree nodes to semantic HTML
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def ui_node_to_html(node: Dict[str, Any]) -> str:
    """
    Convert a UI node to HTML representation.
    
    Args:
        node: UI tree node dictionary
        
    Returns:
        HTML string representation of the node
    """
    try:
        # Map UI type to HTML tag
        tag = map_ui_to_html(node)
        
        # Get children HTML
        children_html = ''.join([ui_node_to_html(child) for child in node.get("children", [])])
        
        # Get text content
        text = node.get("name", "") or node.get("value", "") or ""
        
        # Get HTML attributes
        attrs = html_attrs(node)
        
        # Build HTML element
        if tag.startswith("input"):
            # Self-closing input elements
            return f"<{tag} {attrs}/>"
        else:
            return f"<{tag} {attrs}>{text}{children_html}</{tag}>"
            
    except Exception as e:
        logger.error(f"Error converting node to HTML: {e}")
        return f"<div class='error'>Error: {e}</div>"

def map_ui_to_html(node: Dict[str, Any]) -> str:
    """
    Map UI control type to HTML tag.
    
    Args:
        node: UI tree node dictionary
        
    Returns:
        HTML tag name
    """
    ui_type = node.get("type", "").lower()
    
    # Windows UI Automation mappings
    if ui_type in ["button", "pushbutton"]:
        return "button"
    elif ui_type in ["edit", "textbox", "textfield"]:
        return "input type='text'"
    elif ui_type in ["checkbox"]:
        return "input type='checkbox'"
    elif ui_type in ["radiobutton", "radio"]:
        return "input type='radio'"
    elif ui_type in ["list", "listbox"]:
        return "ul"
    elif ui_type in ["listitem"]:
        return "li"
    elif ui_type in ["combobox", "dropdown"]:
        return "select"
    elif ui_type in ["menu", "menubar"]:
        return "nav"
    elif ui_type in ["menuitem"]:
        return "a"
    elif ui_type in ["window", "dialog"]:
        return "section"
    elif ui_type in ["group", "panel"]:
        return "div"
    elif ui_type in ["text", "label", "statictext"]:
        return "span"
    elif ui_type in ["image", "picture"]:
        return "img"
    elif ui_type in ["link", "hyperlink"]:
        return "a"
    elif ui_type in ["table"]:
        return "table"
    elif ui_type in ["tab"]:
        return "div"
    elif ui_type in ["toolbar"]:
        return "div"
    elif ui_type in ["statusbar"]:
        return "footer"
    elif ui_type in ["scrollbar"]:
        return "div"
    
    # macOS Accessibility mappings
    elif ui_type in ["axbutton"]:
        return "button"
    elif ui_type in ["axtextfield", "axtextarea"]:
        return "input type='text'"
    elif ui_type in ["axcheckbox"]:
        return "input type='checkbox'"
    elif ui_type in ["axradiobutton"]:
        return "input type='radio'"
    elif ui_type in ["axlist", "axtable"]:
        return "ul"
    elif ui_type in ["axrow"]:
        return "li"
    elif ui_type in ["axpopupbutton", "axcombobox"]:
        return "select"
    elif ui_type in ["axmenu", "axmenubar"]:
        return "nav"
    elif ui_type in ["axmenuitem"]:
        return "a"
    elif ui_type in ["axwindow", "axdialog"]:
        return "section"
    elif ui_type in ["axgroup", "axsplitter"]:
        return "div"
    elif ui_type in ["axstatictext", "axtext"]:
        return "span"
    elif ui_type in ["aximage"]:
        return "img"
    elif ui_type in ["axlink"]:
        return "a"
    elif ui_type in ["axtabgroup"]:
        return "div"
    elif ui_type in ["axtoolbar"]:
        return "div"
    elif ui_type in ["axscrollbar"]:
        return "div"
    
    # Default fallback
    else:
        return "div"

def html_attrs(node: Dict[str, Any]) -> str:
    """
    Generate HTML attributes from UI node properties.
    
    Args:
        node: UI tree node dictionary
        
    Returns:
        HTML attributes string
    """
    attrs = []
    
    # ID attribute
    node_id = node.get("id")
    if node_id:
        attrs.append(f'id="{node_id}"')
    
    # Class attribute based on type
    ui_type = node.get("type", "").lower()
    attrs.append(f'class="ui-{ui_type}"')
    
    # Style attribute for positioning
    bounds = node.get("bounds", [])
    if len(bounds) == 4:
        x, y, width, height = bounds
        style = f'style="position:absolute;left:{x}px;top:{y}px;width:{width}px;height:{height}px;"'
        attrs.append(style)
    
    # Data attributes for additional properties
    if node.get("value"):
        attrs.append(f'data-value="{node["value"]}"')
    
    # Role attribute for accessibility
    attrs.append(f'role="{ui_type}"')
    
    return " ".join(attrs) 