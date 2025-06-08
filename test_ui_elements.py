#!/usr/bin/env python3
"""
Test script for interacting with UI test elements page through Neural UI Detector
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_ui_elements")

# UI element test data - matches with ui_test_elements.html
TEST_ELEMENTS = [
    # Buttons
    {"id": "btnPrimary", "type": "button", "name": "Primary Button"},
    {"id": "btnOutline", "type": "button", "name": "Outline Button"},
    {"id": "btnSuccess", "type": "button", "name": "Success Button"},
    {"id": "btnWarning", "type": "button", "name": "Warning Button"},
    {"id": "btnError", "type": "button", "name": "Error Button"},
    
    # Form Elements
    {"id": "textInput", "type": "text_input", "name": "Text Input", "value": "Sample text"},
    {"id": "emailInput", "type": "text_input", "name": "Email Input", "value": "test@example.com"},
]

async def test_ui_elements(port=8768):
    """Test interacting with UI elements through the Neural UI Detector server"""
    try:
        # Connect to the Neural UI Detector WebSocket server
        logger.info(f"Connecting to Neural UI Detector WebSocket server on port {port}...")
        async with websockets.connect(f"ws://localhost:{port}") as websocket:
            logger.info("Connected!")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            logger.info(f"Received welcome message: {welcome_data}")
            
            # Open the UI test elements page in a browser
            test_page_path = os.path.abspath("ui_test_elements.html")
            test_page_url = f"file://{test_page_path}"
            logger.info(f"Opening test page: {test_page_url}")
            webbrowser.open(test_page_url)
            
            # Wait for the page to load
            logger.info("Waiting for page to load (5 seconds)...")
            await asyncio.sleep(5)
            
            # First, detect all UI elements
            logger.info("Detecting UI elements...")
            detect_request = {"action": "detect"}
            await websocket.send(json.dumps(detect_request))
            
            # Wait for response
            detect_response = await websocket.recv()
            detect_data = json.loads(detect_response)
            
            if detect_data.get("type") == "detection_result":
                logger.info(f"Detected {detect_data.get('count', 0)} UI elements")
                elements = detect_data.get("elements", [])
                
                # Process each test element
                for test_elem in TEST_ELEMENTS:
                    logger.info(f"Testing element: {test_elem['name']} (ID: {test_elem['id']})")
                    
                    # Find the element by its text or ID
                    found_element = None
                    for elem in elements:
                        if (elem.get("text") and test_elem["id"] in elem.get("text")) or \
                           (elem.get("text") and test_elem["name"] in elem.get("text")):
                            found_element = elem
                            break
                    
                    if not found_element:
                        logger.warning(f"Element not found: {test_elem['name']}")
                        continue
                    
                    logger.info(f"Found element: {found_element}")
                    
                    # Test different actions based on element type
                    if test_elem["type"] == "button":
                        # Click the button
                        logger.info(f"Clicking button: {test_elem['name']}")
                        click_request = {
                            "action": "click",
                            "description": test_elem["name"],
                            "element_type": "button"
                        }
                        await websocket.send(json.dumps(click_request))
                        click_response = await websocket.recv()
                        click_data = json.loads(click_response)
                        
                        if click_data.get("type") == "click_result" and click_data.get("success"):
                            logger.info(f"Successfully clicked: {test_elem['name']}")
                        else:
                            logger.error(f"Failed to click: {test_elem['name']}")
                            logger.error(f"Response: {click_data}")
                    
                    elif test_elem["type"] == "text_input":
                        # Type into the input field
                        logger.info(f"Typing into: {test_elem['name']}")
                        type_request = {
                            "action": "type",
                            "description": test_elem["name"],
                            "text": test_elem.get("value", "Test input"),
                            "element_type": "text_input"
                        }
                        await websocket.send(json.dumps(type_request))
                        type_response = await websocket.recv()
                        type_data = json.loads(type_response)
                        
                        if type_data.get("type") == "type_result" and type_data.get("success"):
                            logger.info(f"Successfully typed into: {test_elem['name']}")
                        else:
                            logger.error(f"Failed to type into: {test_elem['name']}")
                            logger.error(f"Response: {type_data}")
                    
                    # Wait between actions
                    await asyncio.sleep(2)
                
                logger.info("Test complete!")
                
            else:
                logger.error(f"Error during detection: {detect_data}")
    
    except ConnectionRefusedError:
        logger.error(f"Connection refused. Make sure the server is running on port {port}.")
    except Exception as e:
        logger.error(f"Error: {str(e)}")

async def run_with_server():
    """Run the test with a fresh Neural UI Detector server"""
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
        except Exception:
            pass
        
        # Start server if not running
        server_process = None
        if not is_running:
            logger.info("Starting Neural UI Detector server...")
            server_process = subprocess.Popen(
                [sys.executable, "neural_ui_detector_server.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            # Give it time to start
            logger.info("Waiting for server to initialize...")
            await asyncio.sleep(5)
        
        # Run the test
        await test_ui_elements()
        
        # Clean up server if we started it
        if server_process:
            logger.info("Stopping server...")
            server_process.terminate()
    
    except Exception as e:
        logger.error(f"Error in test run: {str(e)}")

if __name__ == "__main__":
    # Use port from command line argument if provided
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8768
    asyncio.run(test_ui_elements(port))