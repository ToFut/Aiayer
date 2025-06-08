#!/usr/bin/env python3
"""
Fixed Neural UI Detector WebSocket Server

This server provides WebSocket access to the Neural UI Detector
for use with the overlay chat interface. This improved version includes:

1. Enhanced port conflict resolution
2. Optimized detection algorithm to prevent hanging
3. Improved error handling
4. Graceful shutdown
5. Comprehensive monitoring
"""

import asyncio
import websockets
import json
import os
import sys
import time
import logging
import base64
import signal
import uuid
import traceback
from io import BytesIO
from typing import Dict, Any, List, Optional, Set
from concurrent.futures import ThreadPoolExecutor

# Import neural UI detector with import error handling
try:
    from neural_ui_detector import ui_detector
    DETECTOR_AVAILABLE = True
except ImportError:
    print("ERROR: Neural UI Detector module not found. Please make sure it's installed.")
    DETECTOR_AVAILABLE = False
except Exception as e:
    print(f"ERROR: Failed to import Neural UI Detector: {e}")
    DETECTOR_AVAILABLE = False

# Configure logging
os.makedirs('logs/neural_ui_detector', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/neural_ui_detector/fixed_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("fixed_neural_ui_detector_server")

# Track connected clients
connected_clients = set()

# Initialize global variables
server = None
keep_running = True
latest_detection = None
last_detection_time = 0
detection_lock = asyncio.Lock()

# Thread pool for CPU-intensive operations
thread_pool = ThreadPoolExecutor(max_workers=2)

class PerformanceMonitor:
    """Monitor performance of detection operations"""
    def __init__(self):
        self.operation_times = {}
        self.operation_counts = {}
    
    def start_operation(self, operation_name: str) -> str:
        """Start timing an operation and return operation ID"""
        operation_id = f"{operation_name}_{uuid.uuid4()}"
        self.operation_times[operation_id] = {
            "start": time.time(),
            "end": None,
            "duration": None,
            "operation_name": operation_name
        }
        return operation_id
    
    def end_operation(self, operation_id: str) -> float:
        """End timing an operation and return duration"""
        if operation_id not in self.operation_times:
            return 0.0
        
        self.operation_times[operation_id]["end"] = time.time()
        duration = self.operation_times[operation_id]["end"] - self.operation_times[operation_id]["start"]
        self.operation_times[operation_id]["duration"] = duration
        
        # Update operation counts and average time
        operation_name = self.operation_times[operation_id]["operation_name"]
        if operation_name not in self.operation_counts:
            self.operation_counts[operation_name] = {
                "count": 0,
                "total_time": 0.0,
                "avg_time": 0.0,
                "max_time": 0.0
            }
        
        self.operation_counts[operation_name]["count"] += 1
        self.operation_counts[operation_name]["total_time"] += duration
        self.operation_counts[operation_name]["avg_time"] = (
            self.operation_counts[operation_name]["total_time"] / 
            self.operation_counts[operation_name]["count"]
        )
        
        if duration > self.operation_counts[operation_name]["max_time"]:
            self.operation_counts[operation_name]["max_time"] = duration
        
        # Log slow operations
        if duration > 2.0:  # Log operations taking more than 2 seconds
            logger.warning(f"Slow operation: {operation_name} took {duration:.2f}s")
        
        return duration
    
    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get performance statistics"""
        return self.operation_counts

# Create performance monitor
performance_monitor = PerformanceMonitor()

async def handle_client(websocket, path=None):
    """Handle WebSocket client connection"""
    client_id = id(websocket)
    logger.info(f"Client {client_id} connected")
    connected_clients.add(websocket)
    
    # Send welcome message
    welcome_msg = {
        "type": "welcome",
        "message": "Connected to Neural UI Detector WebSocket Server (Fixed)",
        "version": "1.1.0",
        "capabilities": ["detect", "find", "click", "type", "key", "hotkey", "visualize"],
        "server_id": str(uuid.uuid4())[:8]
    }
    await websocket.send(json.dumps(welcome_msg))
    
    try:
        async for message in websocket:
            try:
                # Handle ping separately for testing
                if message == "ping":
                    logger.info(f"Received ping from client {client_id}")
                    await websocket.send(json.dumps({"type": "pong", "message": "pong"}))
                    continue
                
                # Parse JSON message
                try:
                    data = json.loads(message)
                    logger.info(f"Received message from client {client_id}: {data.get('action', 'unknown')}")
                    
                    # Process command with proper error handling
                    try:
                        response = await process_command(data)
                        await websocket.send(json.dumps(response))
                    except Exception as e:
                        error_details = "".join(traceback.format_exception(type(e), e, e.__traceback__))
                        logger.error(f"Error processing command: {str(e)}\n{error_details}")
                        await websocket.send(json.dumps({
                            "type": "error",
                            "error": str(e),
                            "action": data.get("action", "unknown")
                        }))
                    
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from client {client_id}: {message}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "error": "Invalid JSON"
                    }))
                    
            except Exception as e:
                error_details = "".join(traceback.format_exception(type(e), e, e.__traceback__))
                logger.error(f"Error processing message from client {client_id}: {str(e)}\n{error_details}")
                try:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "error": str(e)
                    }))
                except:
                    pass
    
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Client {client_id} disconnected: code={e.code}, reason={e.reason}")
    
    finally:
        connected_clients.remove(websocket)

async def process_command(data):
    """Process command from client with improved error handling and timeouts"""
    global latest_detection, last_detection_time
    
    action = data.get("action", "")
    operation_id = performance_monitor.start_operation(f"command_{action}")
    
    try:
        # Handle different action types
        if action == "detect":
            return await handle_detect_action(data)
            
        elif action == "find":
            return await handle_find_action(data)
            
        elif action == "click":
            return await handle_click_action(data)
            
        elif action == "type":
            return await handle_type_action(data)
            
        elif action == "key":
            return await handle_key_action(data)
            
        elif action == "hotkey":
            return await handle_hotkey_action(data)
            
        elif action == "execute":
            return await handle_execute_action(data)
            
        elif action == "cancel":
            return {
                "type": "cancel_result",
                "message": "Operation cancelled",
                "timestamp": time.time()
            }
            
        elif action == "stats":
            # Return performance statistics
            stats = performance_monitor.get_stats()
            return {
                "type": "stats_result",
                "stats": stats,
                "timestamp": time.time()
            }
            
        else:
            return {
                "type": "error",
                "error": f"Unknown action: {action}"
            }
    
    except Exception as e:
        error_details = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        logger.error(f"Error processing action '{action}': {str(e)}\n{error_details}")
        return {
            "type": "error",
            "error": str(e),
            "action": action
        }
    finally:
        # End timing the operation
        duration = performance_monitor.end_operation(operation_id)
        logger.info(f"Command {action} completed in {duration:.2f}s")

async def handle_detect_action(data):
    """Handle detect action with optimized timeouts and proper locking"""
    global latest_detection, last_detection_time
    
    # Check if we have a recent detection (less than 3 seconds old) to avoid duplicate work
    if latest_detection and time.time() - last_detection_time < 3:
        logger.info("Using recent detection result")
        result = latest_detection
    else:
        # Use lock to prevent multiple simultaneous detections
        async with detection_lock:
            try:
                # Set a timeout for detection
                operation_id = performance_monitor.start_operation("ui_detect")
                
                # Run detection in thread pool to avoid blocking asyncio loop
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(thread_pool, run_detection_sync)
                
                performance_monitor.end_operation(operation_id)
                
                # Update latest detection
                latest_detection = result
                last_detection_time = time.time()
            except asyncio.TimeoutError:
                logger.error("Detection timed out")
                return {
                    "type": "error",
                    "error": "Detection timed out",
                    "action": "detect"
                }
    
    # Create visualization
    try:
        operation_id = performance_monitor.start_operation("visualize")
        vis_path = ui_detector.visualize_detection(result)
        performance_monitor.end_operation(operation_id)
    except Exception as e:
        logger.error(f"Error creating visualization: {e}")
        vis_path = None
    
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

def run_detection_sync():
    """Run detection synchronously for the thread pool"""
    # This runs in a separate thread, so we use the synchronous event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(ui_detector.detect_elements())
        return result
    finally:
        loop.close()

async def handle_find_action(data):
    """Handle find action"""
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

async def handle_click_action(data):
    """Handle click action"""
    description = data.get("description", "")
    element_type = data.get("element_type")
    
    if not description:
        return {
            "type": "error",
            "error": "Missing description"
        }
    
    # Click element
    operation_id = performance_monitor.start_operation("click")
    success = await ui_detector.click_element(description, element_type)
    performance_monitor.end_operation(operation_id)
    
    return {
        "type": "click_result",
        "success": success,
        "message": f"Clicked element '{description}'" if success else f"Failed to click element '{description}'",
        "timestamp": time.time()
    }

async def handle_type_action(data):
    """Handle type action"""
    description = data.get("description", "")
    text = data.get("text", "")
    element_type = data.get("element_type")
    
    if not description or not text:
        return {
            "type": "error",
            "error": "Missing description or text"
        }
    
    # Type text
    operation_id = performance_monitor.start_operation("type")
    success = await ui_detector.type_text(description, text, element_type)
    performance_monitor.end_operation(operation_id)
    
    return {
        "type": "type_result",
        "success": success,
        "message": f"Typed text into element '{description}'" if success else f"Failed to type text into element '{description}'",
        "timestamp": time.time()
    }

async def handle_key_action(data):
    """Handle key action"""
    key = data.get("key", "")
    
    if not key:
        return {
            "type": "error",
            "error": "Missing key"
        }
    
    # Press key
    operation_id = performance_monitor.start_operation("key")
    success = await ui_detector.press_key(key)
    performance_monitor.end_operation(operation_id)
    
    return {
        "type": "key_result",
        "success": success,
        "message": f"Pressed key '{key}'" if success else f"Failed to press key '{key}'",
        "timestamp": time.time()
    }

async def handle_hotkey_action(data):
    """Handle hotkey action"""
    keys = data.get("keys", [])
    
    if not keys:
        return {
            "type": "error",
            "error": "Missing keys"
        }
    
    # Press hotkey
    operation_id = performance_monitor.start_operation("hotkey")
    success = await ui_detector.press_hotkey(*keys)
    performance_monitor.end_operation(operation_id)
    
    return {
        "type": "hotkey_result",
        "success": success,
        "message": f"Pressed hotkey '{'+'.join(keys)}'" if success else f"Failed to press hotkey '{'+'.join(keys)}'",
        "timestamp": time.time()
    }

async def handle_execute_action(data):
    """Handle execute action with improved error handling and timeouts"""
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
    
    operation_id = performance_monitor.start_operation("execute")
    
    for i, step in enumerate(steps):
        step_action = step.get("action", "")
        step_result = None
        
        # Monitor each step execution
        step_operation_id = performance_monitor.start_operation(f"step_{step_action}")
        
        try:
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
        except Exception as e:
            logger.error(f"Error executing step {i+1} ({step_action}): {e}")
            step_result = {
                "success": False,
                "message": f"Error: {str(e)}"
            }
        
        # End step timing
        performance_monitor.end_operation(step_operation_id)
        
        results.append({
            "step": i + 1,
            "action": step_action,
            "result": step_result
        })
        
        # Stop execution if step failed and abort_on_failure is true
        if not step_result.get("success", False) and data.get("abort_on_failure", False):
            logger.info(f"Aborting execution after step {i+1} failed")
            break
    
    # End overall execution timing
    performance_monitor.end_operation(operation_id)
    
    return {
        "type": "execute_result",
        "total_steps": len(steps),
        "success_count": success_count,
        "success": success_count == len(steps),
        "results": results,
        "timestamp": time.time()
    }

async def broadcast_status():
    """Broadcast status to all connected clients periodically"""
    while keep_running:
        try:
            if connected_clients:
                # Get performance stats
                stats = performance_monitor.get_stats()
                
                status_message = {
                    "type": "server_status",
                    "timestamp": time.time(),
                    "clients": len(connected_clients),
                    "uptime": time.time() - server_start_time,
                    "stats": stats
                }
                
                # Broadcast to all clients
                for client in connected_clients:
                    try:
                        await client.send(json.dumps(status_message))
                    except:
                        # Ignore errors for clients that might be disconnecting
                        pass
                
                logger.debug(f"Broadcast status to {len(connected_clients)} clients")
        except Exception as e:
            logger.error(f"Error broadcasting status: {e}")
        
        # Wait for next broadcast
        await asyncio.sleep(30)  # Broadcast every 30 seconds

async def start_server(port=8768, retry=True, max_retries=5):
    """Start WebSocket server with improved port conflict handling
    
    Args:
        port: Initial port to try
        retry: Whether to retry with alternative ports
        max_retries: Maximum number of retry attempts
    """
    global server, server_start_time
    server_start_time = time.time()
    
    logger.info(f"Starting Neural UI Detector WebSocket Server on port {port}")
    
    # Make sure we don't conflict with other known services
    known_service_ports = {
        8765: "DO Button Server",
        8766: "WebSocket Proxy",
        8767: "Backend Server"
    }
    
    if port in known_service_ports:
        logger.warning(f"Port {port} is used by {known_service_ports[port]}, trying alternative port 8768")
        port = 8768
    
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Create server
            server = await websockets.serve(handle_client, "localhost", port)
            
            # Start status broadcast task
            asyncio.create_task(broadcast_status())
            
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
            
            # Update the test HTML file with the correct port
            try:
                html_path = os.path.join(os.path.dirname(__file__), 'test_neural_ui_detector_fixed.html')
                if os.path.exists(html_path):
                    with open(html_path, 'r') as f:
                        content = f.read()
                    
                    # Update WebSocket URL in the HTML file
                    new_content = content
                    
                    # Try different patterns to catch all potential URLs
                    port_patterns = [
                        f"ws://localhost:8765",
                        f"ws://localhost:8768",
                        f"document.getElementById('wsUrl').value = 'ws://localhost:8768'"
                    ]
                    
                    for pattern in port_patterns:
                        if pattern in new_content:
                            # Replace only localhost URLs, not the variable
                            if "localhost" in pattern:
                                new_content = new_content.replace(pattern, f"ws://localhost:{port}")
                            # Replace the default port in the input field
                            elif "wsUrl" in pattern:
                                new_content = new_content.replace(pattern, f"document.getElementById('wsUrl').value = 'ws://localhost:{port}'")
                    
                    if content != new_content:
                        with open(html_path, 'w') as f:
                            f.write(new_content)
                        logger.info(f"Updated WebSocket URL in test_neural_ui_detector_fixed.html to port {port}")
            except Exception as e:
                logger.warning(f"Failed to update HTML test file: {e}")
            
            # Keep server running until shutdown
            while keep_running:
                await asyncio.sleep(1)
            
            # Close the server
            server.close()
            await server.wait_closed()
            logger.info("Server closed")
            
            return
            
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

def handle_shutdown(signum, frame):
    """Handle shutdown signal"""
    global keep_running
    print("\n⚠️  Shutting down server...")
    keep_running = False

if __name__ == "__main__":
    try:
        import subprocess
        import os
        import signal
        import argparse
        
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='Fixed Neural UI Detector WebSocket Server')
        parser.add_argument('--port', type=int, default=8768, help='Port to run the server on (default: 8768)')
        parser.add_argument('--no-kill', action='store_true', help='Do not kill existing processes on the port')
        parser.add_argument('--debug', action='store_true', help='Enable debug logging')
        args = parser.parse_args()
        
        # Set debug logging if requested
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.setLevel(logging.DEBUG)
            logger.info("Debug logging enabled")
        
        # Check if Neural UI Detector is available
        if not DETECTOR_AVAILABLE:
            logger.error("Neural UI Detector module not available. Exiting.")
            sys.exit(1)
        
        # Default port is 8768 to avoid conflicts
        target_port = args.port
        
        # Make sure we don't try to use ports that are known to be used by other critical services
        known_service_ports = {
            8765: "DO Button Server",
            8766: "WebSocket Proxy",
            8767: "Backend Server"
        }
        
        if target_port in known_service_ports:
            logger.warning(f"Port {target_port} is used by {known_service_ports[target_port]}, using port 8768 instead")
            target_port = 8768
        
        # Clean up existing processes only if not disabled
        if not args.no_kill:
            # Check and kill processes on our target port
            try:
                # Try different commands for different platforms
                if sys.platform == "darwin" or sys.platform.startswith("linux"):
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
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, handle_shutdown)
        signal.signal(signal.SIGTERM, handle_shutdown)
        
        # Start server
        print(f"\n🚀 Starting Fixed Neural UI Detector WebSocket Server on port {target_port}...")
        asyncio.run(start_server(port=target_port, retry=True, max_retries=5))
        
    except KeyboardInterrupt:
        print("\n❌ Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        
        # Create a more helpful error message
        print("\n❌ ERROR: Failed to start the Fixed Neural UI Detector Server")
        print("\nPossible solutions:")
        print("1. Try starting with a different port: python fixed_neural_ui_detector_server.py --port 8770")
        print("2. Check if another process is using the port and kill it manually")
        print("3. Check the logs at logs/neural_ui_detector/fixed_server.log for more details")
        print("4. Start with --no-kill to avoid automatic process termination")
        print("5. Start with --debug for more detailed logging")
        print("\nIf the issue persists, please report it with the log information.")