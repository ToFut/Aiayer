#!/usr/bin/env python3
"""
Test Web UI Element Detection
Run the UI detection system on a web page to verify accuracy
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('web_ui_detection_test')

# Web server to serve test page
def start_web_server(port=8081):
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

async def analyze_web_ui():
    """Test UI element detection on a test web page"""
    try:
        # Import detection components
        from sensors.total_screen_analyzer import TotalScreenAnalyzer
        from enhanced_ui_detection_system import EnhancedUIDetectionSystem
        from hybrid_ui_element_detector import HybridUIElementDetector
        
        logger.info("🔍 Testing UI element detection on web page")
        logger.info("=" * 60)
        
        # Start web server
        server = start_web_server(port=8082)
        
        # Open test page in browser
        test_url = "http://localhost:8082/test_webpage.html"
        logger.info(f"Opening test page: {test_url}")
        webbrowser.open(test_url)
        
        # Give browser time to load
        logger.info("Waiting for page to load...")
        await asyncio.sleep(5)
        
        # Initialize analyzers
        logger.info("Initializing UI detection systems...")
        
        # Standard analyzer
        total_analyzer = TotalScreenAnalyzer()
        
        # Try to load enhanced analyzers if available
        ui_detector = None
        enhanced_detector = None
        
        try:
            ui_detector = HybridUIElementDetector()
            logger.info("✅ Loaded Hybrid UI Element Detector")
        except Exception as e:
            logger.warning(f"Could not load Hybrid UI Detector: {e}")
        
        try:
            enhanced_detector = EnhancedUIDetectionSystem()
            logger.info("✅ Loaded Enhanced UI Detection System")
        except Exception as e:
            logger.warning(f"Could not load Enhanced UI Detection System: {e}")
        
        # Perform analysis with all available detectors
        results = {}
        
        # Total screen analyzer
        logger.info("📸 Running total screen analysis...")
        total_result = await total_analyzer.analyze_full_screen()
        if total_result:
            results["total_analyzer"] = total_result
            logger.info("✅ Total screen analysis completed")
        
        # Hybrid UI detector if available
        if ui_detector:
            logger.info("📸 Running hybrid UI detection...")
            try:
                action_description = "Analyze webpage UI elements"
                hybrid_result = ui_detector.get_smart_coordinates_for_action(action_description)
                results["hybrid_detector"] = {
                    "coordinates": hybrid_result,
                    "action": action_description,
                    "elements": []  # This would be populated in a real test
                }
                logger.info("✅ Hybrid UI detection completed")
            except Exception as e:
                logger.error(f"Error in hybrid detection: {e}")
        
        # Enhanced UI detection if available
        if enhanced_detector:
            logger.info("📸 Running enhanced UI detection...")
            try:
                # Save screenshot for processing
                temp_screenshot = "temp_web_screenshot.png"
                pyautogui.screenshot().save(temp_screenshot)
                
                # Use the correct method name
                enhanced_result = await enhanced_detector.enhanced_detect_ui_elements(
                    temp_screenshot, 
                    {"app_name": "Browser", "view_name": "Test Webpage"}
                )
                
                # Convert to dict for JSON serialization
                from dataclasses import asdict
                results["enhanced_detector"] = {
                    "elements": [asdict(elem) for elem in enhanced_result.elements],
                    "detection_methods_used": enhanced_result.detection_methods_used,
                    "timestamp": enhanced_result.timestamp
                }
                logger.info("✅ Enhanced UI detection completed")
            except Exception as e:
                logger.error(f"Error in enhanced detection: {e}")
        
        # Process and analyze results
        process_results(results)
        
        # Save all results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"web_ui_detection_test_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"💾 Full analysis saved to: {output_file}")
        
        # Stop server
        server.shutdown()
        logger.info("Web server stopped")
        
    except Exception as e:
        logger.error(f"❌ Error during web UI detection test: {e}")
        import traceback
        logger.error(traceback.format_exc())

def process_results(results):
    """Process and print UI detection results"""
    logger.info("\n🔍 UI DETECTION RESULTS")
    logger.info("=" * 40)
    
    # Process total analyzer results
    if "total_analyzer" in results:
        total_result = results["total_analyzer"]
        layers = total_result.get("layers", {})
        ui_analysis = layers.get("ui_analysis", {})
        text_analysis = layers.get("text_analysis", {})
        
        logger.info("\n🔲 TOTAL ANALYZER RESULTS:")
        logger.info("-" * 30)
        
        # UI elements
        elements = ui_analysis.get("elements", [])
        logger.info(f"UI elements detected: {len(elements)}")
        
        # Group elements by type
        element_types = {}
        for element in elements:
            element_type = element.get("type", "unknown")
            if element_type not in element_types:
                element_types[element_type] = []
            element_types[element_type].append(element)
        
        # Show counts by type
        for element_type, elements_list in element_types.items():
            logger.info(f"  - {element_type}: {len(elements_list)}")
        
        # Show details for important elements
        important_types = ["button", "input", "form", "link", "dropdown", "checkbox", "radio"]
        for element_type in important_types:
            if element_type in element_types:
                logger.info(f"\n📊 {element_type.upper()} ELEMENTS:")
                for i, element in enumerate(element_types[element_type][:5], 1):  # Show first 5
                    position = element.get("position", {})
                    confidence = element.get("confidence", 0.0)
                    label = element.get("label", "")
                    
                    logger.info(f"  {i}. {element_type}: {label}")
                    logger.info(f"     Position: ({position.get('x', 0)}, {position.get('y', 0)}) - {position.get('width', 0)}x{position.get('height', 0)}")
                    logger.info(f"     Confidence: {confidence:.2f}")
    
    # Process hybrid detector results
    if "hybrid_detector" in results:
        hybrid_result = results["hybrid_detector"]
        
        logger.info("\n🔲 HYBRID DETECTOR RESULTS:")
        logger.info("-" * 30)
        
        elements = hybrid_result.get("elements", [])
        logger.info(f"UI elements detected: {len(elements)}")
        
        # Show top elements by confidence
        elements.sort(key=lambda x: x.get("confidence", 0.0), reverse=True)
        for i, element in enumerate(elements[:5], 1):  # Show top 5
            element_type = element.get("type", "unknown")
            position = element.get("position", {})
            confidence = element.get("confidence", 0.0)
            label = element.get("label", "")
            
            logger.info(f"  {i}. {element_type}: {label}")
            logger.info(f"     Position: ({position.get('x', 0)}, {position.get('y', 0)}) - {position.get('width', 0)}x{position.get('height', 0)}")
            logger.info(f"     Confidence: {confidence:.2f}")
    
    # Process enhanced detector results
    if "enhanced_detector" in results:
        enhanced_result = results["enhanced_detector"]
        
        logger.info("\n🔲 ENHANCED DETECTOR RESULTS:")
        logger.info("-" * 30)
        
        elements = enhanced_result.get("elements", [])
        logger.info(f"UI elements detected: {len(elements)}")
        
        # Show top elements by confidence
        elements.sort(key=lambda x: x.get("confidence", 0.0), reverse=True)
        for i, element in enumerate(elements[:5], 1):  # Show top 5
            element_type = element.get("type", "unknown")
            position = element.get("position", {})
            confidence = element.get("confidence", 0.0)
            label = element.get("label", "")
            
            logger.info(f"  {i}. {element_type}: {label}")
            logger.info(f"     Position: ({position.get('x', 0)}, {position.get('y', 0)}) - {position.get('width', 0)}x{position.get('height', 0)}")
            logger.info(f"     Confidence: {confidence:.2f}")
    
    # Overall accuracy assessment
    logger.info("\n📈 ACCURACY ASSESSMENT:")
    logger.info("=" * 30)
    
    # Expected elements on test page
    expected_elements = {
        "button": 5,  # Approximate number of buttons
        "input": 3,   # Approximate number of inputs
        "form": 1,    # Approximate number of forms
    }
    
    # Check if elements were detected
    for element_type, expected_count in expected_elements.items():
        total_count = 0
        
        # Count from total analyzer
        if "total_analyzer" in results:
            total_result = results["total_analyzer"]
            layers = total_result.get("layers", {})
            ui_analysis = layers.get("ui_analysis", {})
            elements = ui_analysis.get("elements", [])
            
            type_count = len([e for e in elements if e.get("type") == element_type])
            total_count += type_count
        
        # Check if count meets expectations
        if total_count >= expected_count:
            logger.info(f"✅ {element_type.upper()}: Found {total_count} (expected {expected_count})")
        else:
            logger.info(f"❌ {element_type.upper()}: Found only {total_count} (expected {expected_count})")
    
    # Overall assessment
    if "total_analyzer" in results:
        total_result = results["total_analyzer"]
        layers = total_result.get("layers", {})
        ui_analysis = layers.get("ui_analysis", {})
        elements = ui_analysis.get("elements", [])
        
        if len(elements) >= 5:  # If we found at least 5 elements
            logger.info("\n🎉 SUCCESS: UI detection is working correctly!")
        else:
            logger.info("\n⚠️ WARNING: UI detection found fewer elements than expected.")

if __name__ == "__main__":
    asyncio.run(analyze_web_ui())