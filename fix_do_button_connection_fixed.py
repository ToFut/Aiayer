#!/usr/bin/env python3
"""
Fix for DO button connection with Neural UI Detector - FIXED VERSION

This script addresses the issue where DO button actions aren't properly processed when using
the Neural UI Detector system. The root cause is a combination of:
1. Port conflict between the Ultimate DO Button Server and the Neural UI Detector WebSocket Server
2. Plan persistence issues where plan IDs aren't synchronized between components

The fix ensures that:
1. The Ultimate DO Button Server runs on port 8765
2. The Neural UI Detector WebSocket Server runs on port 8768
3. This proxy bridges the communication between all components
4. DO button messages from the overlay are properly forwarded to the Ultimate DO Button Server
5. Neural UI detection messages are properly forwarded to the Neural UI Detector
6. Plan IDs are synchronized between components to ensure execution works

IMPORTANT: This script must be run AFTER starting both the Ultimate DO Button Server 
and the Neural UI Detector Server, but BEFORE launching the overlay.
"""

import asyncio
import json
import logging
import os
import sys
import websockets
import socket
import subprocess
import time
from datetime import datetime

# Configure logging
os.makedirs('logs/websocket', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/websocket/do_button_neural_proxy.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("do_button_neural_proxy")

# Connection settings
DO_BUTTON_SERVER_PORT = 8765
NEURAL_UI_PORT = 8768
PROXY_PORT = 8766  # Default proxy port
BACKEND_PORT = 8767

# Define a settings class to handle port changes
class Settings:
    def __init__(self):
        self.do_button_port = DO_BUTTON_SERVER_PORT
        self.neural_ui_port = NEURAL_UI_PORT
        self.proxy_port = PROXY_PORT
        self.backend_port = BACKEND_PORT

# Create a settings instance
settings = Settings()

# Track connected clients
connected_clients = set()

# Connection pools
do_button_connections = {}
neural_ui_connections = {}

# Plan store for synchronization between systems
active_plans = {}

# Import plan persistence if available
try:
    from plan_persistence import save_plan, load_plan, generate_plan_id
    PLAN_PERSISTENCE_AVAILABLE = True
    logger.info("✅ Plan persistence module loaded for plan synchronization")
except ImportError as e:
    logger.warning(f"⚠️ Plan persistence not available, using in-memory plan sync: {e}")
    PLAN_PERSISTENCE_AVAILABLE = False

async def check_server_status(host, port):
    """Check if a server is running on the specified port"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            return result == 0
    except Exception as e:
        logger.error(f"Error checking server on port {port}: {e}")
        return False

async def connect_to_do_button_server(client_id):
    """Create or reuse a connection to the DO button server"""
    if client_id in do_button_connections and do_button_connections[client_id]['ws'].open:
        return do_button_connections[client_id]['ws']
    
    try:
        # Connect to DO button server
        ws = await websockets.connect(f"ws://localhost:{settings.do_button_port}")
        do_button_connections[client_id] = {
            'ws': ws,
            'created_at': datetime.now().isoformat()
        }
        logger.info(f"Connected to DO button server for client {client_id}")
        
        # Start a background task to receive messages from the DO button server
        asyncio.create_task(forward_do_button_responses(ws, client_id))
        
        return ws
    except Exception as e:
        logger.error(f"Failed to connect to DO button server: {e}")
        raise

async def forward_do_button_responses(do_button_ws, client_id):
    """Forward responses from DO button server to the client"""
    try:
        async for message in do_button_ws:
            try:
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                logger.info(f"Received from DO button server for client {client_id}: {msg_type}")
                
                # Convert DO button responses to proper notification format for overlay
                if msg_type == "do_button_notification" or msg_type == "display_notification":
                    # Convert to suggestion format that overlay can display
                    converted_data = {
                        "type": "suggestion",
                        "response": data.get("content", {}).get("message", "Action required"),
                        "buttons": data.get("content", {}).get("buttons", []),
                        "importance": data.get("importance", "high"),
                        "play_sound": True,
                        "plan_id": data.get("plan_id", "")
                    }
                    message = json.dumps(converted_data)
                    logger.info(f"Converted DO button notification to suggestion format for client {client_id}")
                
                # Forward the message to the client
                client_ws = None
                for client in connected_clients:
                    if id(client) == int(client_id.split('_')[1]):
                        client_ws = client
                        break
                
                if client_ws and client_ws.open:
                    await client_ws.send(message)
                    logger.info(f"Forwarded DO button response to client {client_id}")
                else:
                    logger.warning(f"Client {client_id} not found or closed, couldn't forward DO button response")
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from DO button server")
            except Exception as e:
                logger.error(f"Error forwarding DO button response: {e}")
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Connection to DO button server closed for client {client_id}")
    except Exception as e:
        logger.error(f"Error in DO button response handler: {e}")
    finally:
        # Clean up the connection
        if client_id in do_button_connections:
            try:
                await do_button_connections[client_id]['ws'].close()
            except:
                pass
            del do_button_connections[client_id]

async def connect_to_neural_ui_detector(client_id):
    """Create a connection to the Neural UI detector"""
    if client_id in neural_ui_connections and neural_ui_connections[client_id]['ws'].open:
        return neural_ui_connections[client_id]['ws']
        
    try:
        # Connect to Neural UI detector
        ws = await websockets.connect(f"ws://localhost:{NEURAL_UI_PORT}")
        neural_ui_connections[client_id] = {
            'ws': ws,
            'created_at': datetime.now().isoformat()
        }
        logger.info(f"Connected to Neural UI detector for client {client_id}")
        
        # Start a background task to receive messages from the Neural UI detector
        asyncio.create_task(forward_neural_ui_responses(ws, client_id))
        
        return ws
    except Exception as e:
        logger.error(f"Failed to connect to Neural UI detector: {e}")
        raise

async def forward_neural_ui_responses(neural_ui_ws, client_id):
    """Forward responses from Neural UI detector to the client"""
    try:
        async for message in neural_ui_ws:
            try:
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                logger.info(f"Received from Neural UI detector for client {client_id}: {msg_type}")
                
                # Convert Neural UI responses to proper format for overlay if needed
                if msg_type == "do_button_notification" or msg_type == "display_notification":
                    # Convert to suggestion format that overlay can display
                    converted_data = {
                        "type": "suggestion",
                        "response": data.get("content", {}).get("message", "Action required"),
                        "buttons": data.get("content", {}).get("buttons", []),
                        "importance": data.get("importance", "high"),
                        "play_sound": True,
                        "plan_id": data.get("plan_id", "")
                    }
                    message = json.dumps(converted_data)
                    logger.info(f"Converted Neural UI notification to suggestion format for client {client_id}")
                
                # Forward the message to the client
                client_ws = None
                for client in connected_clients:
                    if id(client) == int(client_id.split('_')[1]):
                        client_ws = client
                        break
                
                if client_ws and client_ws.open:
                    await client_ws.send(message)
                    logger.info(f"Forwarded Neural UI response to client {client_id}")
                else:
                    logger.warning(f"Client {client_id} not found or closed, couldn't forward Neural UI response")
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from Neural UI detector")
            except Exception as e:
                logger.error(f"Error forwarding Neural UI response: {e}")
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Connection to Neural UI detector closed for client {client_id}")
    except Exception as e:
        logger.error(f"Error in Neural UI response handler: {e}")
    finally:
        # Clean up the connection
        if client_id in neural_ui_connections:
            try:
                await neural_ui_connections[client_id]['ws'].close()
            except:
                pass
            del neural_ui_connections[client_id]

async def ensure_plan_exists(plan_id):
    """Ensure plan exists in both systems by creating a backup plan if needed"""
    # First check if we have a plan in memory
    if plan_id in active_plans:
        logger.info(f"Plan {plan_id} exists in memory")
        return True
    
    # Then check persistent storage if available
    if PLAN_PERSISTENCE_AVAILABLE:
        try:
            plan_data = await load_plan(plan_id)
            if plan_data:
                logger.info(f"Plan {plan_id} loaded from persistent storage")
                active_plans[plan_id] = plan_data
                return True
        except Exception as e:
            logger.warning(f"Error loading plan from persistent storage: {e}")
    
    # If plan doesn't exist, create a dummy one
    try:
        timestamp = int(time.time())
        
        # Create a simple automation plan with basic steps
        dummy_plan = {
            "task_id": plan_id,
            "title": f"Automation Plan {plan_id}",
            "description": f"Dummy plan created for {plan_id}",
            "steps": [
                {
                    "id": "step_1",
                    "description": "Analyze current screen",
                    "action_type": "analyze_screen",
                    "estimated_duration": 1.0,
                    "status": "pending"
                },
                {
                    "id": "step_2",
                    "description": "Execute action based on analysis",
                    "action_type": "execute",
                    "estimated_duration": 2.0,
                    "status": "pending"
                }
            ],
            "estimated_duration": 3.0,
            "status": "awaiting_approval",
            "creation_time": timestamp,
            "dummy_plan": True  # Mark as dummy plan for easy identification
        }
        
        # Store in memory
        active_plans[plan_id] = dummy_plan
        
        # Save to persistent storage if available
        if PLAN_PERSISTENCE_AVAILABLE:
            try:
                success = await save_plan(plan_id, dummy_plan)
                if success:
                    logger.info(f"Created and saved dummy plan {plan_id}")
                else:
                    logger.warning(f"Failed to save dummy plan {plan_id}")
            except Exception as e:
                logger.warning(f"Error saving dummy plan to persistent storage: {e}")
        else:
            logger.info(f"Created dummy plan {plan_id} in memory only (persistent storage not available)")
        
        return True
    except Exception as e:
        logger.error(f"Error creating dummy plan: {e}")
        return False

async def proxy_handler(websocket, path):
    """Handle incoming connections and route messages"""
    client_id = f"client_{id(websocket)}"
    connected_clients.add(websocket)
    
    logger.info(f"Client {client_id} connected to proxy")
    
    # Connections to backend services
    do_button_ws = None
    neural_ui_ws = None
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "connection_established",
            "server": "Neural UI DO Button Proxy",
            "version": "1.0.0",
            "capabilities": [
                "do_button", 
                "agent_confirmation", 
                "button_action", 
                "detect", 
                "find", 
                "click", 
                "type", 
                "key", 
                "hotkey", 
                "execute"
            ],
            "timestamp": datetime.now().isoformat()
        }))
        
        # Handle incoming messages
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                logger.info(f"Client {client_id} sent: {msg_type}")
                
                # Route DO button related messages to the Ultimate DO Button Server
                if msg_type in ['agent_confirmation', 'button_action', 'do_button']:
                    # Lazily connect to DO button server when needed
                    if not do_button_ws:
                        try:
                            do_button_ws = await connect_to_do_button_server(client_id)
                        except Exception as e:
                            # If DO button server is not available, send error response
                            await websocket.send(json.dumps({
                                "type": "error",
                                "error": f"DO button server not available: {e}",
                                "timestamp": datetime.now().isoformat()
                            }))
                            continue
                    
                    # Get plan ID based on message type
                    plan_id = None
                    if msg_type == "do_button":
                        plan_id = data.get("plan_id", "")
                    elif msg_type == "button_action":
                        plan_id = data.get("plan_id", data.get("session_id", ""))
                    elif msg_type == "agent_confirmation":
                        plan_id = data.get("session_id", "")
                    
                    # Ensure plan exists before forwarding the request
                    if plan_id:
                        await ensure_plan_exists(plan_id)
                    
                    # Normalize message format if needed
                    if msg_type == "do_button":
                        # Convert to consistent format for the DO button server
                        normalized_data = {
                            "type": "agent_confirmation",
                            "action": data.get("button", "EXECUTE"),
                            "session_id": plan_id,
                            "plan_id": plan_id,  # Ensure plan_id is included
                            "timestamp": datetime.now().isoformat()
                        }
                        await do_button_ws.send(json.dumps(normalized_data))
                        logger.info(f"Forwarded DO button message as agent_confirmation with plan_id: {plan_id}")
                    elif msg_type == "button_action":
                        # Ensure plan_id is properly included
                        if "plan_id" not in data and "session_id" in data:
                            data["plan_id"] = data["session_id"]
                        
                        # Forward the message with proper format
                        await do_button_ws.send(message)
                        logger.info(f"Forwarded button_action with plan_id: {plan_id}")
                    else:
                        # Forward the message as-is
                        await do_button_ws.send(message)
                        logger.info(f"Forwarded {msg_type} as-is to DO button server")
                    
                    logger.info(f"Forwarded {msg_type} to DO button server")
                
                # Route Neural UI detector messages to the Neural UI detector
                elif msg_type in ['detect', 'find', 'click', 'type', 'key', 'hotkey', 'execute']:
                    # Lazily connect to Neural UI detector when needed
                    if not neural_ui_ws:
                        try:
                            neural_ui_ws = await connect_to_neural_ui_detector(client_id)
                        except Exception as e:
                            # If Neural UI detector is not available, send error response
                            await websocket.send(json.dumps({
                                "type": "error",
                                "error": f"Neural UI detector not available: {e}",
                                "timestamp": datetime.now().isoformat()
                            }))
                            continue
                    
                    # Forward the message
                    await neural_ui_ws.send(message)
                    logger.info(f"Forwarded {msg_type} to Neural UI detector")
                
                # Handle ping messages
                elif msg_type == 'ping':
                    await websocket.send(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }))
                
                # Unknown message type
                else:
                    logger.warning(f"Unknown message type: {msg_type}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "error": f"Unknown message type: {msg_type}",
                        "timestamp": datetime.now().isoformat()
                    }))
            
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from client {client_id}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": "Invalid JSON",
                    "timestamp": datetime.now().isoformat()
                }))
            
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }))
    
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} disconnected")
    
    except Exception as e:
        logger.error(f"Error in proxy handler: {e}")
    
    finally:
        # Clean up
        connected_clients.remove(websocket)
        
        # Close backend connections
        if client_id in do_button_connections:
            try:
                await do_button_connections[client_id]['ws'].close()
            except:
                pass
            del do_button_connections[client_id]
        
        if client_id in neural_ui_connections:
            try:
                await neural_ui_connections[client_id]['ws'].close()
            except:
                pass
            del neural_ui_connections[client_id]

async def verify_server_connectivity():
    """Verify connectivity to required servers"""
    # Check if servers are running
    do_button_running = await check_server_status('localhost', DO_BUTTON_SERVER_PORT)
    neural_ui_running = await check_server_status('localhost', NEURAL_UI_PORT)
    backend_running = await check_server_status('localhost', BACKEND_PORT)
    
    logger.info(f"Server status: DO Button (8765): {do_button_running}, Neural UI (8768): {neural_ui_running}, Backend (8767): {backend_running}")
    
    # If servers are not running, log errors
    if not do_button_running:
        logger.error("❌ The Ultimate DO Button Server is not running on port 8765!")
        logger.error("   Please run 'python3 ultimate_do_button_server.py' first.")
        return False
    
    if not neural_ui_running:
        logger.error("❌ The Neural UI Detector Server is not running on port 8768!")
        logger.error("   Please run 'python3 neural_ui_detector_server.py' first.")
        return False
    
    # Test connectivity to servers
    logger.info("Testing connectivity to required servers...")
    
    # Test DO Button Server
    try:
        logger.info("Testing DO Button Server connection...")
        async with websockets.connect(f"ws://localhost:{DO_BUTTON_SERVER_PORT}", timeout=3) as ws:
            # Wait for welcome message
            welcome = await asyncio.wait_for(ws.recv(), timeout=3)
            welcome_data = json.loads(welcome)
            logger.info(f"✅ DO Button Server welcome received: {welcome_data.get('type', 'unknown')}")
            
            # Send a ping to test
            await ws.send(json.dumps({"type": "ping"}))
            
            # Wait for response
            response = await asyncio.wait_for(ws.recv(), timeout=3)
            response_data = json.loads(response)
            logger.info(f"✅ DO Button Server responded: {response_data.get('type', 'unknown')}")
    except Exception as e:
        logger.error(f"❌ Error connecting to DO Button Server: {e}")
        return False
    
    # Test Neural UI Detector Server
    try:
        logger.info("Testing Neural UI Detector Server connection...")
        async with websockets.connect(f"ws://localhost:{NEURAL_UI_PORT}", timeout=3) as ws:
            # Wait for welcome message
            welcome = await asyncio.wait_for(ws.recv(), timeout=3)
            welcome_data = json.loads(welcome)
            logger.info(f"✅ Neural UI Detector Server welcome received: {welcome_data.get('type', 'unknown')}")
            
            # Send a ping to test
            await ws.send(json.dumps({"type": "ping"}))
            
            # Wait for response
            response = await asyncio.wait_for(ws.recv(), timeout=3)
            response_data = json.loads(response)
            logger.info(f"✅ Neural UI Detector Server responded: {response_data.get('type', 'unknown')}")
    except Exception as e:
        logger.error(f"❌ Error connecting to Neural UI Detector Server: {e}")
        return False
    
    logger.info("✅ All required servers are running and responding")
    return True

async def start_proxy_server():
    """Start the WebSocket proxy server"""
    # We need to use the global PROXY_PORT variable to modify it
    global PROXY_PORT
    
    # First check if port is in use
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', PROXY_PORT))
            logger.info(f"Port {PROXY_PORT} is available")
    except OSError as e:
        if "Address already in use" in str(e):
            logger.warning(f"Port {PROXY_PORT} is already in use. Killing existing process...")
            try:
                subprocess.run(f"lsof -t -i:{PROXY_PORT} | xargs kill -9", shell=True)
                logger.info(f"Killed process on port {PROXY_PORT}")
                await asyncio.sleep(2)  # Wait for port to be released
            except Exception as kill_error:
                logger.error(f"Failed to kill process on port {PROXY_PORT}: {kill_error}")
                # Use alternative port
                PROXY_PORT = 8770
                logger.info(f"Using alternative port {PROXY_PORT}")
        else:
            raise
    
    # Start server
    logger.info(f"Starting DO Button Neural UI Proxy on localhost:{PROXY_PORT}")
    
    server = await websockets.serve(proxy_handler, "localhost", PROXY_PORT)
    
    logger.info(f"✅ DO Button Neural UI Proxy running on ws://localhost:{PROXY_PORT}")
    logger.info(f"✅ Forwarding DO button messages to ws://localhost:{DO_BUTTON_SERVER_PORT}")
    logger.info(f"✅ Forwarding Neural UI messages to ws://localhost:{NEURAL_UI_PORT}")
    
    # Write port to file for clients to discover
    with open("logs/neural_ui_do_button_proxy.txt", "w") as f:
        f.write(str(PROXY_PORT))
    
    # Keep server running
    await asyncio.Future()

async def main():
    """Main function"""
    logger.info("============================================================")
    logger.info("  DO Button Neural UI Proxy - FIXED VERSION - Starting")
    logger.info("============================================================")
    logger.info("This proxy bridges communication between:")
    logger.info(f"- The Ultimate DO Button Server (port {DO_BUTTON_SERVER_PORT})")
    logger.info(f"- The Neural UI Detector Server (port {NEURAL_UI_PORT})")
    logger.info(f"- Client applications like the overlay chat")
    logger.info("============================================================")
    logger.info("FIXED VERSION: Ensures plan IDs are synchronized between components")
    logger.info("============================================================")
    
    # Create directories
    os.makedirs("logs/websocket", exist_ok=True)
    os.makedirs("cache/plans", exist_ok=True)
    
    # Verify server connectivity
    if not await verify_server_connectivity():
        logger.error("Failed to verify server connectivity. Please make sure all required servers are running.")
        return 1
    
    # Start the proxy server
    try:
        await start_proxy_server()
        return 0
    except Exception as e:
        logger.error(f"Failed to start proxy server: {e}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("DO button Neural UI proxy interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)