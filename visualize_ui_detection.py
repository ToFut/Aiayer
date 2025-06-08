#!/usr/bin/env python3
"""
Visualize UI Detection Results
Create a visualization of the UI detection on the test webpage
"""
import asyncio
import sys
import os
import json
import time
import logging
import webbrowser
import pyautogui
from datetime import datetime

# Import our unified UI detection API
from unified_ui_detection_api import UnifiedUIDetectionAPI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('visualize_ui_detection')

async def visualize_detection():
    """Create a visualization of UI detection results"""
    output_dir = "results/ui_detection_visualizations"
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize the API
    ui_detection = UnifiedUIDetectionAPI()
    
    # Load the latest detection results
    latest_result = ui_detection.get_latest_result()
    
    if not latest_result:
        logger.error("No detection results found. Please run the test_unified_ui_detection.py script first.")
        return 1
    
    # Create visualization 
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"{output_dir}/ui_detection_visualization_{timestamp}.png"
    
    # Take a fresh screenshot
    logger.info("Taking a fresh screenshot for visualization...")
    screenshot_path = f"{output_dir}/screenshot_{timestamp}.png"
    pyautogui.screenshot().save(screenshot_path)
    
    # Create visualization using the screenshot
    logger.info(f"Creating visualization with {len(latest_result.elements)} detected elements...")
    if ui_detection.visualize_detection(latest_result, output_path):
        logger.info(f"Visualization saved to {output_path}")
        
        # Create a summary of detected elements
        summary_path = f"{output_dir}/detection_summary_{timestamp}.json"
        summary = {
            "timestamp": latest_result.timestamp,
            "element_count": len(latest_result.elements),
            "detection_methods": latest_result.detection_methods,
            "element_types": latest_result.count_by_type(),
            "detection_time": latest_result.detection_time,
            "top_elements": [
                {
                    "id": elem.element_id,
                    "type": elem.element_type,
                    "text": elem.text[:50] + "..." if len(elem.text) > 50 else elem.text,
                    "confidence": elem.confidence,
                    "can_click": elem.can_click,
                    "can_type": elem.can_type,
                }
                for elem in sorted(latest_result.elements, key=lambda e: e.confidence, reverse=True)[:5]
            ]
        }
        
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Detection summary saved to {summary_path}")
        return 0
    else:
        logger.error("Failed to create visualization")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(visualize_detection()))