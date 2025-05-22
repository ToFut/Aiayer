#!/usr/bin/env python3
"""
Ultra-minimal WebSocket server with proper handler signature.
This server focuses solely on the correct implementation of the WebSocket handler signature.
"""
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('ultra_minimal_ws')

# Connected clients
connected_clients = set()

# Explicitly define the handler function with the correct signature
async def handler(websocket, path):
    """Handler function with the correct signature: It MUST have websocket and path parameters"""
    client_id = f"client_{id(websocket)}"
    logger.info(f"Client {client_id} connected at path: {path}")
    connected_clients.add(websocket)
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": f"Connected to minimal WebSocket server. Path: {path}",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Process messages
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received from {client_id}: {data}")
                
                # Echo the message back
                await websocket.send(json.dumps({
                    "type": "echo",
                    "original": data,
                    "timestamp": datetime.now().isoformat()
                }))
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {client_id}")
                await websocket.send(json.dumps({
                    "type": "error", 
                    "message": "Invalid JSON"
                }))
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Connection closed with {client_id}")
    finally:
        connected_clients.remove(websocket)
        logger.info(f"Client {client_id} disconnected")

async def main():
    # Start server on localhost:8765
    host = "localhost"
    port = 8765
    
    # IMPORTANT: The handler is passed directly here, with correct signature
    server = await websockets.serve(handler, host, port)
    
    logger.info(f"WebSocket server running at ws://{host}:{port}")
    
    # Keep running forever
    await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)