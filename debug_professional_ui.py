#!/usr/bin/env python3
"""
Debug script for professional UI detector
"""

import asyncio
import logging
import sys
import os
from PIL import Image, ImageGrab

# Add the current directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from professional_ui_detector import ProfessionalUIDetector

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('debug_professional_ui')

async def debug_professional_ui():
    """Debug the professional UI detector"""
    try:
        logger.info("🔧 Debugging Professional UI Detector")
        
        # Take a screenshot
        screenshot = ImageGrab.grab()
        if screenshot.mode == 'RGBA':
            screenshot = screenshot.convert('RGB')
        
        logger.info(f"Screenshot captured: {screenshot.size}")
        
        # Initialize professional UI detector
        detector = ProfessionalUIDetector()
        logger.info("Professional UI detector initialized")
        
        # Run the analysis
        result = await detector.analyze_screen_professional(screenshot)
        
        logger.info(f"Analysis result: {result}")
        
        if result.get("success"):
            elements = result.get("ui_elements", [])
            logger.info(f"Found {len(elements)} elements")
            
            for i, element in enumerate(elements[:5]):  # Show first 5
                logger.info(f"Element {i+1}: {element}")
        else:
            logger.error(f"Analysis failed: {result.get('error', 'Unknown error')}")
            
        return result
        
    except Exception as e:
        logger.error(f"Debug failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    asyncio.run(debug_professional_ui())