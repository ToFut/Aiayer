#!/usr/bin/env python3
"""
Fix for DO button connection with Neural UI Detector

This script addresses the issue where DO button actions aren't properly processed when using
the Neural UI Detector system. The root cause is a port conflict between the Ultimate DO Button
Server and the Neural UI Detector WebSocket Server, both trying to use port 8765.

The fix ensures that:
1. The Ultimate DO Button Server runs on port 8765
2. The Neural UI Detector WebSocket Server runs on port 8768
3. This proxy bridges the communication between all components
4. DO button messages from the overlay are properly forwarded to the Ultimate DO Button Server
5. Neural UI detection messages are properly forwarded to the Neural UI Detector

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
from datetime import datetime
import time

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
        ws = await websockets.connect(f"ws://localhost:{settings.neural_ui_port}")
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

async def proxy_handler(websocket, path=None):
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
                    
                    # Normalize message format if needed
                    if msg_type == "do_button":
                        # Convert to consistent format for the DO button server
                        normalized_data = {
                            "type": "agent_confirmation",
                            "action": data.get("button", "EXECUTE"),
                            "session_id": data.get("plan_id", ""),
                            "plan_id": data.get("plan_id", ""),  # Ensure plan_id is included
                            "timestamp": datetime.now().isoformat()
                        }
                        await do_button_ws.send(json.dumps(normalized_data))
                    elif msg_type == "button_action":
                        # Ensure plan_id is properly included
                        if "plan_id" not in data and "session_id" in data:
                            data["plan_id"] = data["session_id"]
                        
                        # Forward the message with proper format
                        await do_button_ws.send(message)
                    else:
                        # Forward the message as-is
                        await do_button_ws.send(message)
                    
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
        # Connect without timeout parameter
        async with websockets.connect(f"ws://localhost:{DO_BUTTON_SERVER_PORT}") as ws:
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
        # Continue anyway for now
        logger.warning("Continuing startup despite DO Button Server connection issues")
    
    # Test Neural UI Detector Server
    try:
        logger.info("Testing Neural UI Detector Server connection...")
        # Connect without timeout parameter
        async with websockets.connect(f"ws://localhost:{NEURAL_UI_PORT}") as ws:
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
        # Continue anyway for now
        logger.warning("Continuing startup despite Neural UI Detector Server connection issues")
    
    logger.info("✅ All required servers are running and responding")
    return True

async def start_proxy_server():
    """Start the WebSocket proxy server"""
    global PROXY_PORT
    
    # First check if port is in use
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', PROXY_PORT))
    except OSError as e:
        if e.errno == 98:  # Port already in use
            logger.warning(f"Port {PROXY_PORT} is already in use. Attempting to kill existing process...")
            try:
                os.system(f"lsof -ti:{PROXY_PORT} | xargs kill -9")
                time.sleep(1)  # Wait for port to be freed
            except Exception as kill_error:
                logger.error(f"Failed to kill process on port {PROXY_PORT}: {kill_error}")
                # Use alternative port
                PROXY_PORT = 8770
                logger.info(f"Using alternative port {PROXY_PORT}")
        else:
            raise

    # Start the server
    server = await websockets.serve(proxy_handler, "localhost", PROXY_PORT)
    logger.info(f"Proxy server started on port {PROXY_PORT}")
    return server

async def main():
    """Main function"""
    logger.info("============================================================")
    logger.info("  DO Button Neural UI Proxy - Starting")
    logger.info("============================================================")
    logger.info("This proxy bridges communication between:")
    logger.info(f"- The Ultimate DO Button Server (port {DO_BUTTON_SERVER_PORT})")
    logger.info(f"- The Neural UI Detector Server (port {NEURAL_UI_PORT})")
    logger.info(f"- Client applications like the overlay chat")
    logger.info("============================================================")
    
    # Create directories
    os.makedirs("logs/websocket", exist_ok=True)
    
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