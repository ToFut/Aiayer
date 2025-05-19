#!/usr/bin/env python3
"""
Simple WebSocket server for the eye widget overlay
"""
import asyncio
import websockets
import json
import logging
import os
import sys
import time
from datetime import datetime

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/eye_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('eye_server')

# Track connected clients
connected_clients = set()

# Simple handler function with both websocket and path parameters
async def handler(websocket, path):
    """WebSocket connection handler that works with the eye widget overlay"""
    logger.info(f"Client connected on path: {path}")
    client_id = f"client_{id(websocket)}"
    connected_clients.add(websocket)
    logger.info(f"Client {client_id} connected")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": f"Connected to Eye Widget Server",
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
                            "server_time": datetime.now().isoformat()
                        }
                    }))
                    
                elif msg_type == 'user_interaction':
                    # Handle user interaction (like chat message)
                    payload = data.get('payload', {})
                    if payload.get('type') == 'query':
                        query = payload.get('query', '')
                        logger.info(f"Query from {client_id}: {query}")
                        
                        # Send response back to the client
                        response = f"You asked: '{query}'. This is a test response from the eye widget server."
                        await websocket.send(json.dumps({
                            "type": "query_response",
                            "response": response,
                            "timestamp": datetime.now().isoformat()
                        }))
                    
                else:
                    # Default echo response
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

async def broadcast_status():
    """Send periodic status updates to all clients"""
    while True:
        if connected_clients:
            try:
                message = json.dumps({
                    "type": "status_update",
                    "payload": {
                        "server_time": datetime.now().isoformat(),
                        "connected_clients": len(connected_clients)
                    }
                })
                
                await asyncio.gather(
                    *[client.send(message) for client in connected_clients],
                    return_exceptions=True
                )
                logger.debug(f"Status update sent to {len(connected_clients)} clients")
            except Exception as e:
                logger.error(f"Error sending status update: {e}")
                
        await asyncio.sleep(30)  # Send status every 30 seconds

async def main():
    # Create directories
    os.makedirs("pids", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Kill any existing server on port 8765
    if sys.platform == "win32":
        os.system(f"taskkill /F /FI \"PID ne {os.getpid()}\" /FI \"LOCALPORT eq 8765\" 2>nul")
    else:
        os.system(f"lsof -ti:8765 | grep -v {os.getpid()} | xargs kill -9 2>/dev/null || true")
    
    # Bind to localhost on port 8765
    port = 8765
    host = "localhost"
    
    try:
        # Use the correct handler with websocket and path parameters
        server = await websockets.serve(handler, host, port)
        
        # Save PID file
        with open('pids/eye_server.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        # Start status broadcasting task
        status_task = asyncio.create_task(broadcast_status())
        
        logger.info(f"Eye Widget WebSocket server started on ws://{host}:{port}")
        print(f"\n=== Eye Widget Server ===")
        print(f"WebSocket server running on ws://{host}:{port}")
        print(f"Ready to connect with eye widget overlay")
        print(f"Press Ctrl+C to exit\n")
        
        # Keep running until terminated
        await asyncio.Future()
        
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        print("\nEye Widget Server stopped by user")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)