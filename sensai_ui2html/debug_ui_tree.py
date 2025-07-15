#!/usr/bin/env python3
"""
Debug UI Tree - Examine the actual UI tree structure
"""

import json
import logging
from ui_scraper.base_scraper import get_ui_tree
from unified_backend import UnifiedBackend

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_ui_tree():
    """Debug the UI tree structure"""
    logger.info("🔍 Debugging UI Tree Structure")
    logger.info("=" * 50)
    
    try:
        # Get the UI tree
        ui_tree = get_ui_tree()
        
        if not ui_tree:
            logger.error("❌ No UI tree captured")
            return
        
        logger.info(f"✅ UI Tree captured successfully")
        logger.info(f"📊 Root node: {ui_tree.get('name', 'Unknown')}")
        logger.info(f"📊 Root type: {ui_tree.get('type', 'Unknown')}")
        logger.info(f"📊 Children count: {len(ui_tree.get('children', []))}")
        
        # Analyze the tree structure
        analyze_tree_structure(ui_tree)
        
        # Test button extraction
        backend = UnifiedBackend()
        buttons = backend._extract_buttons_from_ui_tree(ui_tree)
        
        logger.info(f"🔘 Buttons found: {len(buttons)}")
        for i, button in enumerate(buttons):
            logger.info(f"  {i+1}. {button['name']} ({button['type']}) - {button['bounds']}")
        
        # Save the tree to a file for inspection
        with open('debug_ui_tree.json', 'w') as f:
            json.dump(ui_tree, f, indent=2)
        logger.info("💾 UI tree saved to debug_ui_tree.json")
        
    except Exception as e:
        logger.error(f"❌ Error debugging UI tree: {e}")
        import traceback
        traceback.print_exc()

def analyze_tree_structure(node, depth=0, max_depth=3):
    """Recursively analyze tree structure"""
    if depth > max_depth:
        return
    
    indent = "  " * depth
    node_type = node.get('type', 'Unknown')
    node_name = node.get('name', 'Unknown')
    children_count = len(node.get('children', []))
    
    logger.info(f"{indent}📁 {node_name} ({node_type}) - {children_count} children")
    
    # Check for interesting elements
    if any(keyword in node_type.lower() for keyword in ['button', 'link', 'menu', 'input']):
        logger.info(f"{indent}🎯 INTERESTING: {node_name} ({node_type})")
    
    # Recursively analyze children
    for i, child in enumerate(node.get('children', [])[:5]):  # Limit to first 5 children
        analyze_tree_structure(child, depth + 1, max_depth)

if __name__ == "__main__":
    debug_ui_tree() 