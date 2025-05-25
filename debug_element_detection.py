#!/usr/bin/env python3
"""
Debug script to see what elements are being detected by the total screen analyzer
"""

import asyncio
import logging
from enhanced_agent_automation import EnhancedAgentAutomation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('debug_elements')

async def debug_element_detection():
    try:
        automation = EnhancedAgentAutomation()
        
        # Analyze current screen
        result = await automation._analyze_current_screen()
        
        if result.get("success"):
            elements = result.get("elements", [])
            logger.info(f"Found {len(elements)} total elements")
            
            # Group by source and type
            by_source = {}
            by_type = {}
            
            for element in elements:
                source = element.get("source", "unknown")
                elem_type = element.get("element_type", "unknown")
                text = element.get("element_text", "").strip()
                
                if source not in by_source:
                    by_source[source] = []
                by_source[source].append(element)
                
                if elem_type not in by_type:
                    by_type[elem_type] = []
                by_type[elem_type].append(element)
            
            # Show breakdown by source
            logger.info("\n📊 Elements by source:")
            for source, source_elements in by_source.items():
                logger.info(f"  {source}: {len(source_elements)} elements")
            
            # Show breakdown by type
            logger.info("\n📊 Elements by type:")
            for elem_type, type_elements in by_type.items():
                logger.info(f"  {elem_type}: {len(type_elements)} elements")
            
            # Show some interesting elements (buttons, clickable text)
            interesting_types = ["button", "icon", "link", "tab", "menu"]
            clickable_text = []
            
            logger.info("\n🎯 Potentially clickable elements:")
            count = 0
            for element in elements:
                elem_type = element.get("element_type", "unknown")
                text = element.get("element_text", "").strip()
                hints = element.get("interaction_hints", [])
                
                if (elem_type in interesting_types or 
                    "click" in hints or 
                    (text and len(text) < 30 and any(word in text.lower() for word in ["button", "click", "close", "open", "calculator", "menu"]))):
                    
                    bbox = element.get("bounding_box", {})
                    x = bbox.get("x", 0) if bbox else 0
                    y = bbox.get("y", 0) if bbox else 0
                    
                    logger.info(f"  {count+1}. '{text}' ({elem_type}) at ({x}, {y}) - hints: {hints}")
                    count += 1
                    
                    if count >= 10:  # Limit output
                        break
            
            # Search for calculator-related elements
            logger.info("\n🔍 Calculator-related elements:")
            calc_elements = []
            for element in elements:
                text = element.get("element_text", "").lower()
                if any(term in text for term in ["calc", "calculator", "math"]):
                    calc_elements.append(element)
                    bbox = element.get("bounding_box", {})
                    x = bbox.get("x", 0) if bbox else 0
                    y = bbox.get("y", 0) if bbox else 0
                    logger.info(f"  '{element.get('element_text', 'N/A')}' ({element.get('element_type', 'unknown')}) at ({x}, {y})")
            
            if not calc_elements:
                logger.info("  No calculator-related elements found")
                
        else:
            logger.error(f"Screen analysis failed: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_element_detection())