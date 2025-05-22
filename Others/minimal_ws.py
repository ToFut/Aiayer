#!/usr/bin/env python3
import asyncio
import websockets
import json
import logging
import os
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/minimal_ws.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('minimal_ws')

# Track connected clients
connected_clients = set()

# Handle WebSocket connections (with both websocket and path parameters)
async def handler(websocket, path):
    """Handler with proper signature including path parameter"""
    client_id = f"client_{id(websocket)}"
    connected_clients.add(websocket)
    logger.info(f"Client {client_id} connected at path: {path}")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": f"Hello client {client_id}! You are connected on path: {path}",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Handle incoming messages
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received from {client_id}: {data.get('type', 'unknown')}")
                
                # Echo back
                response = {
                    "type": "echo",
                    "original": data,
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send(json.dumps(response))
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {client_id}: {message[:100]}...")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Connection closed with {client_id}: {e}")
    finally:
        connected_clients.remove(websocket)
        logger.info(f"Client {client_id} disconnected")

async def main():
    # Bind to localhost on port 8767
    port = 8767
    host = "localhost"
    
    # Start server
    logger.info(f"Starting WebSocket server on {host}:{port}")
    server = await websockets.serve(handler, host, port)
    
    # Save PID
    with open('pids/minimal_ws.pid', 'w') as f:
        f.write(str(os.getpid()))
        
    logger.info(f"WebSocket server started on ws://{host}:{port}")
    
    # Keep running forever
    await asyncio.Future()

if __name__ == "__main__":
    # Ensure pids directory exists
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