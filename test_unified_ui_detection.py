#!/usr/bin/env python3
"""
Test Unified UI Element Detection
Run the unified UI detection system on a web page to verify accuracy and API accessibility
"""
import asyncio
import sys
import os
import json
import time
import logging
from datetime import datetime
import http.server
import socketserver
import threading
import webbrowser
import pyautogui
import argparse
from typing import Dict, List, Optional, Tuple, Any, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('unified_ui_detection_test')

# Import our unified UI detection API
from unified_ui_detection_api import UnifiedUIDetectionAPI, UIElement, DetectionResult

# Web server to serve test page
def start_web_server(port=8082):
    """Start a simple HTTP server to serve test pages"""
    logger.info(f"Starting web server on port {port}")
    
    # Set up handler
    handler = http.server.SimpleHTTPRequestHandler
    
    # Create and start server in a separate thread
    server = socketserver.TCPServer(("", port), handler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True  # Allow thread to exit when main thread exits
    server_thread.start()
    
    logger.info(f"Web server running at http://localhost:{port}")
    return server

async def test_ui_detection(use_visualization=True, output_dir="results/ui_detection_tests", fast_mode=True):
    """Test the unified UI detection system on a test web page"""
    try:
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info("🔍 Testing unified UI element detection on web page")
        logger.info("=" * 60)
        
        # Start web server
        server = start_web_server(port=8082)
        
        # Open test page in browser
        test_url = "http://localhost:8082/test_webpage.html"
        logger.info(f"Opening test page: {test_url}")
        webbrowser.open(test_url)
        
        # Give browser time to load
        logger.info("Waiting for page to load...")
        await asyncio.sleep(3)
        
        # Initialize unified UI detection API
        logger.info("Initializing unified UI detection system...")
        ui_detection = UnifiedUIDetectionAPI()
        
        # For faster testing, disable some methods
        if fast_mode:
            ui_detection.enable_detection_method("ocr", False)
            ui_detection.enable_detection_method("cv", False)
            logger.info("Fast mode enabled: OCR and CV detection disabled")
        
        # Take screenshot for analysis
        screenshot_path = f"{output_dir}/test_screenshot_{int(time.time())}.png"
        pyautogui.screenshot().save(screenshot_path)
        
        # Run UI detection with appropriate methods based on mode
        logger.info("📸 Running unified UI detection...")
        if fast_mode:
            # In fast mode, only use browser detection
            result = await ui_detection.detect_ui_elements(
                url=test_url,
                context={"test_name": "web_page_test", "browser": "Safari", "mode": "fast"}
            )
        else:
            # Full detection with all methods
            result = await ui_detection.detect_ui_elements(
                image_path=screenshot_path,
                url=test_url,
                context={"test_name": "web_page_test", "browser": "Safari", "mode": "full"}
            )
        
        # Save raw result
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{output_dir}/unified_ui_detection_test_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        
        logger.info(f"💾 Full analysis saved to: {output_file}")
        
        # Create visualization if requested
        if use_visualization:
            vis_file = f"{output_dir}/unified_ui_detection_vis_{timestamp}.png"
            ui_detection.visualize_detection(result, vis_file)
            logger.info(f"🖼️ Visualization saved to: {vis_file}")
        
        # Process and analyze results
        analyze_results(result, expected_elements={
            "button": 5,
            "textfield": 3,
            "form": 1,
            "link": 3
        })
        
        # Demonstrate API accessibility with examples
        demonstrate_api_usage(ui_detection, result)
        
        # Stop server
        server.shutdown()
        logger.info("Web server stopped")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error during unified UI detection test: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

def analyze_results(result: DetectionResult, expected_elements: Dict[str, int] = None):
    """Process and print UI detection results"""
    logger.info("\n🔍 UNIFIED UI DETECTION RESULTS")
    logger.info("=" * 40)
    
    # Summary
    logger.info(f"Total elements detected: {len(result.elements)}")
    logger.info(f"Detection methods used: {', '.join(result.detection_methods)}")
    logger.info(f"Detection time: {result.detection_time:.2f}s")
    
    # Element counts by type
    type_counts = result.count_by_type()
    logger.info("\nElement counts by type:")
    for element_type, count in sorted(type_counts.items()):
        logger.info(f"  - {element_type}: {count}")
    
    # Top elements by confidence
    elements_by_confidence = sorted(result.elements, key=lambda e: e.confidence, reverse=True)
    logger.info("\nTop 5 elements by confidence:")
    for i, elem in enumerate(elements_by_confidence[:5], 1):
        logger.info(f"  {i}. {elem.element_type.upper()}: {elem.text[:30]}")
        logger.info(f"     Confidence: {elem.confidence:.2f}")
        if elem.bounding_box:
            x1, y1, x2, y2 = elem.bounding_box
            width, height = x2 - x1, y2 - y1
            logger.info(f"     Position: ({x1}, {y1}) - {width}x{height}")
        logger.info(f"     Detection: {elem.detection_method}")
    
    # Check if expected elements were found
    if expected_elements:
        logger.info("\n📈 ACCURACY ASSESSMENT:")
        logger.info("=" * 30)
        
        for element_type, expected_count in expected_elements.items():
            actual_count = type_counts.get(element_type, 0)
            
            if actual_count >= expected_count:
                logger.info(f"✅ {element_type.upper()}: Found {actual_count} (expected {expected_count})")
            else:
                logger.info(f"❌ {element_type.upper()}: Found only {actual_count} (expected {expected_count})")
        
        # Overall assessment
        total_expected = sum(expected_elements.values())
        total_found = sum(count for element_type, count in type_counts.items() 
                         if element_type in expected_elements)
        
        accuracy = total_found / total_expected if total_expected > 0 else 0
        
        logger.info(f"\nOverall accuracy: {accuracy:.1%}")
        
        if accuracy >= 0.8:
            logger.info("🎉 SUCCESS: UI detection is working with high accuracy!")
        elif accuracy >= 0.5:
            logger.info("⚠️ PARTIAL SUCCESS: UI detection is working but missed some elements.")
        else:
            logger.info("❌ LOW ACCURACY: UI detection needs improvement.")

def demonstrate_api_usage(api: UnifiedUIDetectionAPI, result: DetectionResult):
    """Demonstrate the API accessibility with examples"""
    logger.info("\n🧪 API USAGE EXAMPLES")
    logger.info("=" * 40)
    
    # Example 1: Find element by text
    logger.info("\n📝 Example 1: Find element by text")
    search_text = "Search"
    search_element = api.find_element_by_text(search_text, result)
    
    if search_element:
        logger.info(f"✅ Found element with text '{search_text}':")
        logger.info(f"  - Type: {search_element.element_type}")
        logger.info(f"  - Text: {search_element.text}")
        logger.info(f"  - Confidence: {search_element.confidence:.2f}")
    else:
        logger.info(f"❌ No element found with text '{search_text}'")
    
    # Example 2: Find elements by type
    logger.info("\n📝 Example 2: Find elements by type")
    buttons = result.get_elements_by_type("button")
    
    logger.info(f"✅ Found {len(buttons)} button elements:")
    for i, button in enumerate(buttons[:3], 1):  # Show first 3
        logger.info(f"  {i}. Text: {button.text}")
        logger.info(f"     Confidence: {button.confidence:.2f}")
    
    # Example 3: Find elements containing text
    logger.info("\n📝 Example 3: Find elements containing specific text")
    form_elements = result.get_elements_containing_text("form", case_sensitive=False)
    
    logger.info(f"✅ Found {len(form_elements)} elements containing 'form':")
    for i, elem in enumerate(form_elements[:3], 1):  # Show first 3
        logger.info(f"  {i}. Type: {elem.element_type}")
        logger.info(f"     Text: {elem.text}")
    
    # Example 4: Count elements by type
    logger.info("\n📝 Example 4: Count elements by type")
    type_counts = result.count_by_type()
    
    logger.info("Element counts:")
    for element_type, count in sorted(type_counts.items()):
        logger.info(f"  - {element_type}: {count}")
    
    # Example 5: Accessing the latest result
    logger.info("\n📝 Example 5: Access latest result")
    latest = api.get_latest_result()
    
    if latest:
        logger.info(f"✅ Retrieved latest result with {len(latest.elements)} elements")
        logger.info(f"  - Timestamp: {datetime.fromtimestamp(latest.timestamp)}")
        logger.info(f"  - Detection methods: {', '.join(latest.detection_methods)}")
    else:
        logger.info("❌ No latest result available")

async def main():
    parser = argparse.ArgumentParser(description="Test the Unified UI Detection API")
    parser.add_argument("--no-visualization", action="store_true", help="Disable visualization generation")
    parser.add_argument("--output-dir", default="results/ui_detection_tests", help="Output directory for results")
    parser.add_argument("--full", action="store_true", help="Run full detection (slower but more comprehensive)")
    
    args = parser.parse_args()
    
    return await test_ui_detection(
        use_visualization=not args.no_visualization,
        output_dir=args.output_dir,
        fast_mode=not args.full
    )

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))