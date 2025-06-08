#!/usr/bin/env python3
"""
Direct UI Test - Simplified script that directly connects to Neural UI Detector
and tests UI elements on the test page.

This script handles the entire process:
1. Opens the UI test elements page
2. Connects to the Neural UI Detector
3. Detects UI elements on the page
4. Executes interactions (clicks, typing) on specific elements
"""

import asyncio
import websockets
import json
import sys
import time
import webbrowser
import os
import subprocess
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("direct_ui_test")

# Test elements - these should match elements in ui_test_elements.html
TEST_ELEMENTS = [
    # Buttons
    {"id": "btnPrimary", "type": "button", "name": "Primary Button", "action": "click"},
    {"id": "btnSuccess", "type": "button", "name": "Success Button", "action": "click"},
    
    # Form Elements
    {"id": "textInput", "type": "text_input", "name": "Text Input", "action": "type", "value": "Test input from UI detector"},
    {"id": "emailInput", "type": "text_input", "name": "Email Input", "action": "type", "value": "test@example.com"}
]

async def connect_to_detector(port=8768):
    """Connect to the Neural UI Detector WebSocket server"""
    try:
        logger.info(f"Connecting to Neural UI Detector WebSocket server on port {port}...")
        websocket = await websockets.connect(f"ws://localhost:{port}")
        logger.info("Connected!")
        
        # Wait for welcome message
        welcome = await websocket.recv()
        welcome_data = json.loads(welcome)
        logger.info(f"Received welcome message: {welcome_data}")
        
        return websocket
    except Exception as e:
        logger.error(f"Failed to connect to WebSocket server: {e}")
        return None

async def open_test_page():
    """Open the UI test elements page in default browser"""
    try:
        # Use absolute path for file URL
        test_page_path = os.path.abspath("ui_test_elements.html")
        test_page_url = f"file://{test_page_path}"
        logger.info(f"Opening test page: {test_page_url}")
        webbrowser.open(test_page_url)
        
        # Wait for page to load
        logger.info("Waiting for page to load (5 seconds)...")
        await asyncio.sleep(5)
        return True
    except Exception as e:
        logger.error(f"Failed to open test page: {e}")
        return False

async def detect_ui_elements(websocket):
    """Detect UI elements on the current screen"""
    try:
        logger.info("Detecting UI elements...")
        detect_request = {"action": "detect"}
        await websocket.send(json.dumps(detect_request))
        
        # Wait for response
        response = await websocket.recv()
        data = json.loads(response)
        
        if data.get("type") == "detection_result":
            logger.info(f"Successfully detected {data.get('count', 0)} UI elements")
            return data.get("elements", [])
        else:
            logger.error(f"Failed to detect UI elements: {data}")
            return []
    except Exception as e:
        logger.error(f"Error during element detection: {e}")
        return []

async def find_element(websocket, element_description, element_type=None):
    """Find a specific UI element"""
    try:
        logger.info(f"Finding element: {element_description} (type: {element_type})")
        find_request = {
            "action": "find",
            "description": element_description,
            "element_type": element_type
        }
        await websocket.send(json.dumps(find_request))
        
        # Wait for response
        response = await websocket.recv()
        data = json.loads(response)
        
        if data.get("type") == "ui_detection_result":
            if data.get("found"):
                logger.info(f"Successfully found element: {element_description}")
                return data.get("element")
            else:
                logger.warning(f"Element not found: {element_description}")
                return None
        else:
            logger.error(f"Failed to find element: {data}")
            return None
    except Exception as e:
        logger.error(f"Error finding element: {e}")
        return None

async def click_element(websocket, element_description, element_type=None):
    """Click on a UI element"""
    try:
        logger.info(f"Clicking element: {element_description} (type: {element_type})")
        click_request = {
            "action": "click",
            "description": element_description,
            "element_type": element_type
        }
        await websocket.send(json.dumps(click_request))
        
        # Wait for response
        response = await websocket.recv()
        data = json.loads(response)
        
        if data.get("type") == "click_result":
            if data.get("success"):
                logger.info(f"Successfully clicked element: {element_description}")
                return True
            else:
                logger.warning(f"Failed to click element: {element_description}")
                return False
        else:
            logger.error(f"Unexpected response for click: {data}")
            return False
    except Exception as e:
        logger.error(f"Error clicking element: {e}")
        return False

async def type_text(websocket, element_description, text, element_type=None):
    """Type text into a UI element"""
    try:
        logger.info(f"Typing '{text}' into element: {element_description}")
        type_request = {
            "action": "type",
            "description": element_description,
            "text": text,
            "element_type": element_type
        }
        await websocket.send(json.dumps(type_request))
        
        # Wait for response
        response = await websocket.recv()
        data = json.loads(response)
        
        if data.get("type") == "type_result":
            if data.get("success"):
                logger.info(f"Successfully typed text into element: {element_description}")
                return True
            else:
                logger.warning(f"Failed to type text into element: {element_description}")
                return False
        else:
            logger.error(f"Unexpected response for type: {data}")
            return False
    except Exception as e:
        logger.error(f"Error typing text: {e}")
        return False

async def execute_element_action(websocket, element, all_elements):
    """Execute the specified action on an element"""
    try:
        # Try to find the element in detected elements
        found = False
        element_id = element["id"]
        element_name = element["name"]
        element_type = element["type"]
        
        for detected in all_elements:
            # Match based on text containing either the ID or name
            if (detected.get("text") and (element_id in detected.get("text") or element_name in detected.get("text"))):
                found = True
                logger.info(f"Found matching element: {detected}")
                
                # Execute the action
                action = element.get("action", "click")
                if action == "click":
                    success = await click_element(websocket, element_name, element_type)
                elif action == "type":
                    value = element.get("value", "Test input")
                    success = await type_text(websocket, element_name, value, element_type)
                else:
                    logger.warning(f"Unsupported action: {action}")
                    success = False
                
                return success
        
        if not found:
            logger.warning(f"Element not found in detection results: {element_name}")
            
            # Try direct find+action as fallback
            if element.get("action") == "click":
                # Try direct click without finding first
                return await click_element(websocket, element_name, element_type)
            elif element.get("action") == "type":
                # Find then type
                found_element = await find_element(websocket, element_name, element_type)
                if found_element:
                    value = element.get("value", "Test input")
                    return await type_text(websocket, element_name, value, element_type)
            
            return False
    except Exception as e:
        logger.error(f"Error executing action on element: {e}")
        return False

async def run_ui_tests(port=8768, open_page=True, include_elements=None):
    """Run UI tests on the test elements page"""
    try:
        # Connect to detector
        websocket = await connect_to_detector(port)
        if not websocket:
            logger.error("Could not connect to Neural UI Detector")
            return False
        
        # Open test page if requested
        if open_page:
            success = await open_test_page()
            if not success:
                logger.error("Failed to open test page")
                await websocket.close()
                return False
        
        # Wait a bit for the page to be fully loaded and visible
        await asyncio.sleep(2)
        
        # Detect UI elements
        elements = await detect_ui_elements(websocket)
        if not elements:
            logger.error("No UI elements detected")
            await websocket.close()
            return False
        
        logger.info(f"Detected {len(elements)} UI elements")
        
        # Filter test elements if specified
        test_elements = TEST_ELEMENTS
        if include_elements:
            test_elements = [elem for elem in TEST_ELEMENTS if elem["id"] in include_elements]
        
        # Execute actions on each test element
        success_count = 0
        total_count = len(test_elements)
        
        for element in test_elements:
            logger.info(f"Testing element: {element['name']} ({element['id']})")
            success = await execute_element_action(websocket, element, elements)
            
            if success:
                success_count += 1
            
            # Wait between actions
            await asyncio.sleep(1)
        
        # Print summary
        logger.info(f"Test completed: {success_count}/{total_count} elements successfully tested")
        
        # Close WebSocket connection
        await websocket.close()
        
        return success_count == total_count
    except Exception as e:
        logger.error(f"Error during UI testing: {e}")
        return False

async def ensure_server_running(port=8768):
    """Check if the Neural UI Detector server is running and start it if not"""
    try:
        # Check if server is already running
        is_running = False
        try:
            if sys.platform == "darwin" or sys.platform.startswith("linux"):
                result = subprocess.run(['lsof', '-ti:8768'], capture_output=True, text=True)
                is_running = bool(result.stdout.strip())
            elif sys.platform == "win32":
                result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
                is_running = "8768" in result.stdout
        except Exception as e:
            logger.warning(f"Could not check if server is running: {e}")
        
        if is_running:
            logger.info("Neural UI Detector server is already running")
            return True
        
        # Start the server
        logger.info("Starting Neural UI Detector server...")
        server_process = subprocess.Popen(
            [sys.executable, "neural_ui_detector_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a bit for the server to start
        logger.info("Waiting for server to initialize...")
        await asyncio.sleep(5)
        
        # Check if the process is still running
        if server_process.poll() is None:
            logger.info("Neural UI Detector server started successfully")
            return True
        else:
            logger.error("Failed to start Neural UI Detector server")
            return False
    except Exception as e:
        logger.error(f"Error ensuring server is running: {e}")
        return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Test UI elements with Neural UI Detector')
    parser.add_argument('--port', type=int, default=8768, help='WebSocket port for Neural UI Detector (default: 8768)')
    parser.add_argument('--no-open', action='store_true', help='Do not open the test page (use if already open)')
    parser.add_argument('--start-server', action='store_true', help='Start the Neural UI Detector server if not running')
    parser.add_argument('--elements', type=str, help='Comma-separated list of element IDs to test')
    args = parser.parse_args()
    
    # Extract element IDs if provided
    include_elements = None
    if args.elements:
        include_elements = [elem.strip() for elem in args.elements.split(',')]
    
    # Ensure server is running if requested
    if args.start_server:
        asyncio.run(ensure_server_running(args.port))
    
    # Run the tests
    success = asyncio.run(run_ui_tests(
        port=args.port,
        open_page=not args.no_open,
        include_elements=include_elements
    ))
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()