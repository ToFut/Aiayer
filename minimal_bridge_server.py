#!/usr/bin/env python3
"""
Minimal WebSocket bridge server for connecting to Ollama LLM
Designed to work with various websockets library versions
"""
import asyncio
import websockets
import json
import logging
import os
import sys
from datetime import datetime
import inspect

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/minimal_bridge.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('minimal_bridge')

# Connected clients
connected_clients = set()
sensor_data = {
    "processes": [],
    "screen": {},
    "files": [],
    "last_update": datetime.now().isoformat()
}

# Check websockets version for proper handler signature
# In newer versions, handler only needs websocket parameter
# In older versions, handler needs both websocket and path parameters
websockets_version = tuple(map(int, websockets.__version__.split('.')[:2]))
logger.info(f"Websockets version: {websockets.__version__}")

# Use the appropriate handler signature based on version detection
if websockets_version >= (10, 0):
    logger.info("Using new-style handler (websocket only)")
    
    async def handler(websocket):
        """Handler function for newer websockets versions"""
        client_id = f"client_{id(websocket)}"
        connected_clients.add(websocket)
        logger.info(f"Client {client_id} connected")
        
        try:
            # Send welcome message
            await websocket.send(json.dumps({
                "type": "welcome",
                "message": "Connected to minimal WebSocket bridge",
                "timestamp": datetime.now().isoformat()
            }))
            
            # Send initial sensor data (if we have any)
            if any([sensor_data["processes"], sensor_data["screen"], sensor_data["files"]]):
                await websocket.send(json.dumps({
                    "type": "sensor_data",
                    "payload": sensor_data,
                    "timestamp": datetime.now().isoformat()
                }))
            
            # Handle incoming messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    msg_type = data.get('type', 'unknown')
                    logger.info(f"Received from {client_id}: {msg_type}")
                    
                    # Handle specific message types
                    if msg_type == 'connection_established':
                        client_info = data.get('payload', {})
                        client_type = client_info.get('client', 'unknown')
                        logger.info(f"Client {client_id} identified as: {client_type}")
                        
                        # Send ready confirmation
                        await websocket.send(json.dumps({
                            "type": "server_ready",
                            "payload": {
                                "status": "connected",
                                "server_version": "1.0.0",
                                "server_time": datetime.now().isoformat(),
                                "capabilities": ["context_tracking", "llm"]
                            }
                        }))
                    
                    # Handle status or context requests
                    elif msg_type == 'status_request' or msg_type == 'context_request':
                        # Send dummy context info
                        await websocket.send(json.dumps({
                            "type": "context_update",
                            "payload": {
                                "context": {
                                    "active_window": "LocalLLM Chat",
                                    "active_app": "Overlay"
                                },
                                "timestamp": datetime.now().isoformat()
                            }
                        }))
                    
                    # Handle chat messages - forward to other clients
                    elif msg_type == 'llm_request' or msg_type == 'user_message' or msg_type == 'chat_message':
                        # Forward to other clients (esp. LLM service)
                        await broadcast_except(data, websocket)
                        
                    elif msg_type == 'llm_response':
                        # Forward LLM responses to all clients except the LLM service
                        await broadcast_except(data, websocket)
                    
                    elif msg_type == 'ping':
                        # Respond to ping with pong
                        await websocket.send(json.dumps({
                            "type": "pong",
                            "timestamp": datetime.now().isoformat()
                        }))
                    
                    else:
                        # Echo back for other message types
                        await websocket.send(json.dumps({
                            "type": "echo",
                            "original_type": msg_type,
                            "message": f"Received your {msg_type} message",
                            "timestamp": datetime.now().isoformat()
                        }))
                    
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from {client_id}: {message[:100]}...")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format"
                    }))
                    
        except websockets.exceptions.ConnectionClosed as e:
            logger.info(f"Connection closed with {client_id}: {e}")
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            connected_clients.remove(websocket)
            logger.info(f"Client {client_id} disconnected")
else:
    logger.info("Using old-style handler (websocket, path)")
    
    async def handler(websocket, path):
        """Handler function with the old-style signature including path parameter"""
        client_id = f"client_{id(websocket)}"
        connected_clients.add(websocket)
        logger.info(f"Client {client_id} connected at path: {path}")
        
        try:
            # Send welcome message
            await websocket.send(json.dumps({
                "type": "welcome",
                "message": f"Connected to minimal WebSocket bridge. Path: {path}",
                "timestamp": datetime.now().isoformat()
            }))
            
            # Send initial sensor data (if we have any)
            if any([sensor_data["processes"], sensor_data["screen"], sensor_data["files"]]):
                await websocket.send(json.dumps({
                    "type": "sensor_data",
                    "payload": sensor_data,
                    "timestamp": datetime.now().isoformat()
                }))
            
            # Handle incoming messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    msg_type = data.get('type', 'unknown')
                    logger.info(f"Received from {client_id}: {msg_type}")
                    
                    # Handle specific message types
                    if msg_type == 'connection_established':
                        client_info = data.get('payload', {})
                        client_type = client_info.get('client', 'unknown')
                        logger.info(f"Client {client_id} identified as: {client_type}")
                        
                        # Send ready confirmation
                        await websocket.send(json.dumps({
                            "type": "server_ready",
                            "payload": {
                                "status": "connected",
                                "server_version": "1.0.0",
                                "server_time": datetime.now().isoformat(),
                                "capabilities": ["context_tracking", "llm"]
                            }
                        }))
                    
                    # Handle status or context requests
                    elif msg_type == 'status_request' or msg_type == 'context_request':
                        # Send dummy context info
                        await websocket.send(json.dumps({
                            "type": "context_update",
                            "payload": {
                                "context": {
                                    "active_window": "LocalLLM Chat",
                                    "active_app": "Overlay"
                                },
                                "timestamp": datetime.now().isoformat()
                            }
                        }))
                    
                    # Handle chat messages - forward to other clients
                    elif msg_type == 'llm_request' or msg_type == 'user_message' or msg_type == 'chat_message':
                        # Forward to other clients (esp. LLM service)
                        await broadcast_except(data, websocket)
                        
                    elif msg_type == 'llm_response':
                        # Forward LLM responses to all clients except the LLM service
                        await broadcast_except(data, websocket)
                    
                    elif msg_type == 'ping':
                        # Respond to ping with pong
                        await websocket.send(json.dumps({
                            "type": "pong",
                            "timestamp": datetime.now().isoformat()
                        }))
                    
                    else:
                        # Echo back for other message types
                        await websocket.send(json.dumps({
                            "type": "echo",
                            "original_type": msg_type,
                            "message": f"Received your {msg_type} message",
                            "timestamp": datetime.now().isoformat()
                        }))
                    
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from {client_id}: {message[:100]}...")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format"
                    }))
                    
        except websockets.exceptions.ConnectionClosed as e:
            logger.info(f"Connection closed with {client_id}: {e}")
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            connected_clients.remove(websocket)
            logger.info(f"Client {client_id} disconnected")

async def broadcast(message):
    """Broadcast a message to all connected clients"""
    if connected_clients:
        await asyncio.gather(
            *[client.send(json.dumps(message)) for client in connected_clients],
            return_exceptions=True
        )
        logger.debug(f"Broadcast sent to {len(connected_clients)} clients")

async def broadcast_except(message, exclude_websocket):
    """Broadcast a message to all connected clients except the excluded one"""
    targets = [client for client in connected_clients if client != exclude_websocket]
    if targets:
        await asyncio.gather(
            *[client.send(json.dumps(message)) for client in targets],
            return_exceptions=True
        )
        logger.debug(f"Broadcast sent to {len(targets)} clients (excluded 1)")

async def heartbeat():
    """Send periodic heartbeat to all clients"""
    while True:
        if connected_clients:
            try:
                await broadcast({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat(),
                    "clients_connected": len(connected_clients)
                })
                logger.debug(f"Heartbeat sent to {len(connected_clients)} clients")
            except Exception as e:
                logger.error(f"Error sending heartbeat: {e}")
        await asyncio.sleep(30)  # Heartbeat every 30 seconds

async def start_server():
    """Start the WebSocket server with appropriate parameters"""
    port = 8765
    host = "localhost"
    
    logger.info(f"Starting WebSocket bridge server on {host}:{port}")
    
    # Determine if serve function accepts the handler directly or needs a function
    serve_params = inspect.signature(websockets.serve).parameters
    
    if websockets_version >= (10, 0):
        # For newer versions
        server = await websockets.serve(handler, host, port)
    else:
        # For older versions
        server = await websockets.serve(handler, host, port)
    
    # Start heartbeat
    heartbeat_task = asyncio.create_task(heartbeat())
    
    logger.info(f"WebSocket bridge server started on ws://{host}:{port}")
    logger.info("Heartbeat system active")
    
    return server

async def main():
    """Main async function"""
    # Create directories
    os.makedirs("pids", exist_ok=True)
    
    # Start server
    server = await start_server()
    
    # Save PID
    with open('pids/bridge_server.pid', 'w') as f:
        f.write(str(os.getpid()))
    
    # Keep running
    await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)