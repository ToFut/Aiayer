#!/usr/bin/env python3
import asyncio
import websockets
import json
import logging
import os
import sys
from datetime import datetime

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ws_server_8765.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ws_server_8765')

# Track connected clients
connected_clients = set()

# Handle WebSocket connections (with both websocket and path parameters)
async def handler(websocket, path=None):
    """Handler with optional path parameter for compatibility"""
    client_id = f"client_{id(websocket)}"
    connected_clients.add(websocket)
    logger.info(f"Client {client_id} connected" + (f" at path: {path}" if path else ""))
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": f"Hello client {client_id}! You are connected" + (f" on path: {path}" if path else ""),
            "timestamp": datetime.now().isoformat()
        }))
        
        # Send fake system context periodically
        context_task = asyncio.create_task(send_context_updates(websocket, client_id))
        
        # Handle incoming messages
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received from {client_id}: {data.get('type', 'unknown')}")
                
                # Handle specific message types
                if data.get('type') == 'connection_established':
                    logger.info(f"Overlay client initialized: {data.get('payload', {})}")
                    await websocket.send(json.dumps({
                        "type": "server_ready",
                        "payload": {
                            "status": "connected",
                            "server_version": "1.0.0",
                            "capabilities": ["context_tracking", "suggestions", "screen_capture"]
                        }
                    }))
                else:
                    # Default echo response
                    response = {
                        "type": "response",
                        "payload": {
                            "message": f"Received {data.get('type', 'unknown')} message",
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                    await websocket.send(json.dumps(response))
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {client_id}: {message[:100]}...")
                await websocket.send(json.dumps({
                    "type": "error",
                    "payload": {"message": "Invalid JSON format"}
                }))
                
        # Cancel context task when the loop breaks
        context_task.cancel()
                
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Connection closed with {client_id}: {e}")
    except asyncio.CancelledError:
        logger.info(f"Tasks for {client_id} cancelled")
    finally:
        connected_clients.remove(websocket)
        logger.info(f"Client {client_id} disconnected")

async def send_context_updates(websocket, client_id):
    """Send periodic context updates to simulate sensor data"""
    try:
        while True:
            # Create fake system context data
            context_data = {
                "type": "sensor_data",
                "payload": {
                    "timestamp": datetime.now().isoformat(),
                    "active_app": "Visual Studio Code",
                    "window_title": "project.py - Aiayer - VS Code",
                    "cpu_usage": 23.5,
                    "memory_usage": 42.8,
                    "processes": [
                        {"name": "Code", "id": 12345, "cpu": 12.3, "memory": 234.5},
                        {"name": "Chrome", "id": 12346, "cpu": 8.7, "memory": 412.8},
                        {"name": "Terminal", "id": 12347, "cpu": 1.2, "memory": 78.3}
                    ]
                }
            }
            
            try:
                await websocket.send(json.dumps(context_data))
                logger.debug(f"Sent context update to {client_id}")
            except Exception as e:
                logger.error(f"Error sending context to {client_id}: {e}")
                raise
                
            # Send every 10 seconds
            await asyncio.sleep(10)
            
    except asyncio.CancelledError:
        logger.debug(f"Context updates for {client_id} stopped")
        raise

async def main():
    # Bind to localhost on port 8765
    port = 8765
    host = "localhost"
    
    # Start server
    logger.info(f"Starting WebSocket server on {host}:{port}")
    server = await websockets.serve(handler, host, port)
    
    # Save PID
    with open('pids/ws_server_8765.pid', 'w') as f:
        f.write(str(os.getpid()))
        
    logger.info(f"WebSocket server started on ws://{host}:{port}")
    
    # Keep running forever
    await asyncio.Future()

if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs("pids", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)
