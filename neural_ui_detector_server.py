#!/usr/bin/env python3
"""
Neural UI Detector WebSocket Server

This server provides WebSocket access to the Neural UI Detector
for use with the overlay chat interface.
"""

import asyncio
import websockets
import json
import os
import sys
import time
import logging
import base64
from io import BytesIO
from typing import Dict, Any, List, Optional
from neural_ui_detector import ui_detector

# Configure logging
os.makedirs('logs/neural_ui_detector', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/neural_ui_detector/server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("neural_ui_detector_server")
logger.setLevel(logging.DEBUG)

# Track connected clients
connected_clients = set()

# Store latest detection result
latest_detection = None
last_detection_time = 0

async def handle_client(websocket, path):
    """Handle WebSocket client connection"""
    client_id = id(websocket)
    logger.info(f"Client {client_id} connected")
    connected_clients.add(websocket)
    
    # Send welcome message
    welcome_msg = {
        "type": "welcome",
        "message": "Connected to Neural UI Detector WebSocket Server",
        "version": "1.0.0",
        "capabilities": ["detect", "find", "click", "type", "key", "hotkey", "visualize"]
    }
    await websocket.send(json.dumps(welcome_msg))
    
    try:
        async for message in websocket:
            try:
                logger.debug(f"Raw message from client {client_id}: {message}")
                data = json.loads(message)
                logger.info(f"Received message from client {client_id}: {data['action'] if 'action' in data else 'unknown'}")
                
                # Process command
                response = await process_command(data)
                logger.debug(f"Response to client {client_id}: {response}")
                
                # Send response
                await websocket.send(json.dumps(response))
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from client {client_id}: {message}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": "Invalid JSON"
                }))
                
            except Exception as e:
                logger.error(f"Error processing message from client {client_id}: {str(e)}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": str(e)
                }))
    
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} disconnected")
    
    finally:
        connected_clients.remove(websocket)

async def process_command(data):
    """Process command from client"""
    global latest_detection, last_detection_time
    
    action = data.get("action", "")
    logger.debug(f"Processing action: {action}")
    
    try:
        if action == "detect":
            # Check if we have a recent detection (less than 5 seconds old)
            if latest_detection and time.time() - last_detection_time < 5:
                logger.info("Using recent detection result")
                result = latest_detection
            else:
                # Perform new detection
                result = await ui_detector.detect_elements()
                latest_detection = result
                last_detection_time = time.time()
            
            # Create visualization
            vis_path = ui_detector.visualize_detection(result)
            
            # Convert elements to serializable format
            elements = []
            for elem in result.elements:
                elem_data = {
                    "id": elem.id,
                    "element_type": elem.element_type,
                    "confidence": elem.confidence,
                    "bounding_box": elem.bounding_box,
                    "center": elem.center,
                    "text": elem.text,
                    "detection_method": elem.detection_method
                }
                elements.append(elem_data)
            
            # Read visualization image if available
            vis_image = None
            if vis_path and os.path.exists(vis_path):
                try:
                    with open(vis_path, "rb") as f:
                        vis_data = f.read()
                        vis_image = base64.b64encode(vis_data).decode('utf-8')
                except Exception as e:
                    logger.error(f"Error reading visualization image: {e}")
            
            return {
                "type": "detection_result",
                "timestamp": result.timestamp,
                "count": len(result.elements),
                "methods": result.detection_methods,
                "execution_time": result.execution_time,
                "elements": elements,
                "visualization": vis_image
            }
        
        elif action == "find":
            description = data.get("description", "")
            element_type = data.get("element_type")
            refresh = data.get("refresh", True)  # Default to refresh for more reliable results
            
            if not description:
                return {
                    "type": "error",
                    "error": "Missing description"
                }
            
            try:
                # Force detection of new elements first
                if refresh:
                    logger.info(f"Performing fresh detection for find operation: {description}")
                    result = await ui_detector.detect_elements()
                    
                    # Return UI detection result with all elements for the client to display
                    elements_data = []
                    for elem in result.elements:
                        elements_data.append({
                            "id": elem.id,
                            "element_type": elem.element_type,
                            "confidence": elem.confidence,
                            "bounding_box": elem.bounding_box,
                            "center": elem.center,
                            "text": elem.text or "",
                            "detection_method": elem.detection_method
                        })
                    
                    # Now find the specific element after fresh detection
                    element = await ui_detector.find_element(description, element_type, refresh=False)
                
                else:
                    # Use existing detection results
                    element = await ui_detector.find_element(description, element_type, refresh=False)
                    elements_data = []
                
                # Create response with both the find result and detection results
                response = {
                    "type": "ui_detection_result",
                    "element_type": element_type or description,
                    "timestamp": time.time(),
                    "results": elements_data
                }
                
                # Add find result information
                if element:
                    response["found"] = True
                    response["element"] = {
                        "id": element.id,
                        "element_type": element.element_type,
                        "confidence": element.confidence,
                        "bounding_box": element.bounding_box,
                        "center": element.center,
                        "text": element.text or ""
                    }
                else:
                    response["found"] = False
                    response["message"] = f"Element '{description}' not found"
                
                return response
                
            except Exception as e:
                logger.error(f"Error processing find command: {e}")
                return {
                    "type": "error",
                    "error": f"Find operation failed: {str(e)}"
                }
        
        elif action == "click":
            description = data.get("description", "")
            element_type = data.get("element_type")
            
            if not description:
                return {
                    "type": "error",
                    "error": "Missing description"
                }
            
            # Click element
            success = await ui_detector.click_element(description, element_type)
            
            return {
                "type": "click_result",
                "success": success,
                "message": f"Clicked element '{description}'" if success else f"Failed to click element '{description}'"
            }
        
        elif action == "type":
            description = data.get("description", "")
            text = data.get("text", "")
            element_type = data.get("element_type")
            
            if not description or not text:
                return {
                    "type": "error",
                    "error": "Missing description or text"
                }
            
            # Type text
            success = await ui_detector.type_text(description, text, element_type)
            
            return {
                "type": "type_result",
                "success": success,
                "message": f"Typed text into element '{description}'" if success else f"Failed to type text into element '{description}'"
            }
        
        elif action == "key":
            key = data.get("key", "")
            
            if not key:
                return {
                    "type": "error",
                    "error": "Missing key"
                }
            
            # Press key
            success = await ui_detector.press_key(key)
            
            return {
                "type": "key_result",
                "success": success,
                "message": f"Pressed key '{key}'" if success else f"Failed to press key '{key}'"
            }
        
        elif action == "hotkey":
            keys = data.get("keys", [])
            
            if not keys:
                return {
                    "type": "error",
                    "error": "Missing keys"
                }
            
            # Press hotkey
            success = await ui_detector.press_hotkey(*keys)
            
            return {
                "type": "hotkey_result",
                "success": success,
                "message": f"Pressed hotkey '{'+'.join(keys)}'" if success else f"Failed to press hotkey '{'+'.join(keys)}'"
            }
        
        elif action == "execute":
            # This action executes a sequence of steps
            steps = data.get("steps", [])
            
            if not steps:
                return {
                    "type": "error",
                    "error": "Missing steps"
                }
            
            # Execute steps
            results = []
            success_count = 0
            
            for i, step in enumerate(steps):
                step_action = step.get("action", "")
                step_result = None
                
                if step_action == "detect":
                    result = await ui_detector.detect_elements()
                    step_result = {
                        "success": True,
                        "count": len(result.elements),
                        "execution_time": result.execution_time
                    }
                    success_count += 1
                
                elif step_action == "find":
                    description = step.get("description", "")
                    element_type = step.get("element_type")
                    element = await ui_detector.find_element(description, element_type)
                    step_result = {
                        "success": element is not None,
                        "message": f"Found element '{description}'" if element else f"Failed to find element '{description}'"
                    }
                    if element:
                        success_count += 1
                
                elif step_action == "click":
                    description = step.get("description", "")
                    element_type = step.get("element_type")
                    success = await ui_detector.click_element(description, element_type)
                    step_result = {
                        "success": success,
                        "message": f"Clicked element '{description}'" if success else f"Failed to click element '{description}'"
                    }
                    if success:
                        success_count += 1
                
                elif step_action == "type":
                    description = step.get("description", "")
                    text = step.get("text", "")
                    element_type = step.get("element_type")
                    success = await ui_detector.type_text(description, text, element_type)
                    step_result = {
                        "success": success,
                        "message": f"Typed text into element '{description}'" if success else f"Failed to type text into element '{description}'"
                    }
                    if success:
                        success_count += 1
                
                elif step_action == "key":
                    key = step.get("key", "")
                    success = await ui_detector.press_key(key)
                    step_result = {
                        "success": success,
                        "message": f"Pressed key '{key}'" if success else f"Failed to press key '{key}'"
                    }
                    if success:
                        success_count += 1
                
                elif step_action == "hotkey":
                    keys = step.get("keys", [])
                    success = await ui_detector.press_hotkey(*keys)
                    step_result = {
                        "success": success,
                        "message": f"Pressed hotkey '{'+'.join(keys)}'" if success else f"Failed to press hotkey '{'+'.join(keys)}'"
                    }
                    if success:
                        success_count += 1
                
                elif step_action == "wait":
                    duration = step.get("duration", 1.0)
                    await asyncio.sleep(duration)
                    step_result = {
                        "success": True,
                        "message": f"Waited for {duration} seconds"
                    }
                    success_count += 1
                
                else:
                    step_result = {
                        "success": False,
                        "message": f"Unknown action: {step_action}"
                    }
                
                results.append({
                    "step": i + 1,
                    "action": step_action,
                    "result": step_result
                })
                
                # Stop execution if step failed and abort_on_failure is true
                if not step_result.get("success", False) and data.get("abort_on_failure", False):
                    break
            
            return {
                "type": "execute_result",
                "total_steps": len(steps),
                "success_count": success_count,
                "success": success_count == len(steps),
                "results": results
            }
        
        else:
            return {
                "type": "error",
                "error": f"Unknown action: {action}"
            }
    
    except Exception as e:
        logger.error(f"Error processing action '{action}': {str(e)}")
        return {
            "type": "error",
            "error": str(e)
        }

async def start_server(port=8769, retry=True, max_retries=5):
    """Start WebSocket server with improved port conflict handling
    
    Args:
        port: Initial port to try
        retry: Whether to retry with alternative ports
        max_retries: Maximum number of retry attempts
    """
    logger.info(f"Starting Neural UI Detector WebSocket Server on port {port}")
    
    # Make sure we don't conflict with other known services
    known_service_ports = {
        8765: "DO Button Server",
        8766: "DO Button Connection Bridge"
    }
    
    if port in known_service_ports:
        logger.warning(f"Port {port} is used by {known_service_ports[port]}, trying alternative port 8769")
        port = 8769
    
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Create server
            server = await websockets.serve(handle_client, "localhost", port)
            
            # Print status with prominent visual separator
            print("\n" + "=" * 70)
            print(f"🚀 Neural UI Detector WebSocket Server running on ws://localhost:{port}")
            print(f"🧠 Server capabilities: detect, find, click, type, key, hotkey, visualize")
            print("=" * 70 + "\n")
            
            # Write port to multiple discoverable locations
            os.makedirs('logs/neural_ui_detector', exist_ok=True)
            
            # Standard port file
            with open('logs/neural_ui_detector/server_port.txt', 'w') as f:
                f.write(str(port))
                
            # Root directory port file for easier discovery
            with open('neural_ui_detector_port.txt', 'w') as f:
                f.write(str(port))
                
            # Update the test_neural_ui_detector_fixed.html file with the correct port if it exists
            try:
                html_path = os.path.join(os.path.dirname(__file__), 'test_neural_ui_detector_fixed.html')
                if os.path.exists(html_path):
                    with open(html_path, 'r') as f:
                        content = f.read()
                    
                    # Update WebSocket URL in the HTML file
                    updated_content = content.replace('ws://localhost:8765', f'ws://localhost:{port}')
                    if content != updated_content:
                        with open(html_path, 'w') as f:
                            f.write(updated_content)
                        logger.info(f"Updated WebSocket URL in test_neural_ui_detector_fixed.html to port {port}")
            except Exception as e:
                logger.warning(f"Failed to update HTML test file: {e}")
            
            # Keep server running
            await asyncio.Future()
            
        except OSError as e:
            if "address already in use" in str(e).lower() and retry:
                # Try the next port
                retry_count += 1
                port += 1
                
                # Skip any known service ports
                while port in known_service_ports:
                    port += 1
                
                logger.warning(f"Port {port-1} is already in use, trying port {port}... (attempt {retry_count}/{max_retries})")
            else:
                logger.error(f"Failed to start server: {e}")
                raise
        except Exception as e:
            logger.error(f"Error starting server: {e}")
            raise

if __name__ == "__main__":
    try:
        import subprocess
        import os
        import signal
        import argparse
        import time
        
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='Neural UI Detector WebSocket Server')
        parser.add_argument('--port', type=int, default=8769, help='Port to run the server on (default: 8769)')
        parser.add_argument('--no-kill', action='store_true', help='Do not kill existing processes on the port')
        args = parser.parse_args()
        
        # Default port is 8769 to avoid conflicts with the DO Button Server (8765)
        # and DO Button Connection Bridge (8766)
        target_port = args.port
        
        # Make sure we don't try to use ports that are known to be used by other critical services
        known_service_ports = {
            8765: "DO Button Server",
            8766: "DO Button Connection Bridge"
        }
        
        if target_port in known_service_ports:
            logger.warning(f"Port {target_port} is used by {known_service_ports[target_port]}, using port 8769 instead")
            target_port = 8769
        
        # Clean up existing processes only if not disabled
        if not args.no_kill:
            # Check and kill processes on our target port
            try:
                # Try different commands for different platforms
                if sys.platform == "darwin" or sys.platform == "linux":
                    # For macOS and Linux, use lsof
                    result = subprocess.run(['lsof', f'-ti:{target_port}'], capture_output=True, text=True)
                    pids = result.stdout.strip().split('\n')
                elif sys.platform == "win32":
                    # For Windows, use netstat
                    result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
                    lines = result.stdout.strip().split('\n')
                    pids = []
                    for line in lines:
                        if f":{target_port}" in line:
                            parts = line.split()
                            if len(parts) >= 5:
                                pids.append(parts[4])
                else:
                    pids = []
                    logger.warning(f"Unsupported platform for process checking: {sys.platform}")
                
                # Kill processes if found
                for pid in pids:
                    if pid and pid.strip():
                        logger.info(f"Killing existing process on port {target_port}: PID {pid}")
                        try:
                            if sys.platform == "win32":
                                subprocess.run(['taskkill', '/F', '/PID', pid])
                            else:
                                os.kill(int(pid), signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                        except Exception as e:
                            logger.warning(f"Error killing process {pid}: {e}")
                
                # Wait a moment for ports to be released
                time.sleep(1)
                
            except Exception as e:
                logger.warning(f"Error checking for existing processes: {e}")
        
        # Start server
        print(f"\n🚀 Starting Neural UI Detector WebSocket Server on port {target_port}...")
        asyncio.run(start_server(port=target_port, retry=True, max_retries=5))
        
    except KeyboardInterrupt:
        print("\n❌ Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        
        # Create a more helpful error message
        print("\n❌ ERROR: Failed to start the Neural UI Detector Server")
        print("\nPossible solutions:")
        print("1. Try starting with a different port: python neural_ui_detector_server.py --port 8770")
        print("2. Check if another process is using the port and kill it manually")
        print("3. Check the logs at logs/neural_ui_detector/server.log for more details")
        print("4. Start with --no-kill to avoid automatic process termination")
        print("\nIf the issue persists, please report it with the log information.")
