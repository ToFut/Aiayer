#!/usr/bin/env python3
"""
Port 8767 WebSocket Server

A simple WebSocket server that specifically runs on port 8767.
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
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("port_8767_server")

# Simple WebSocket handler
async def handler(websocket):
    client_id = id(websocket)
    logger.info(f"Client {client_id} connected")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": "Connected to Port 8767 Server",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Process incoming messages
        async for message in websocket:
            try:
                logger.info(f"Received: {message}")
                
                # Try to parse as JSON
                try:
                    data = json.loads(message)
                    # Echo back as JSON
                    await websocket.send(json.dumps({
                        "type": "echo",
                        "data": data,
                        "timestamp": datetime.now().isoformat()
                    }))
                except json.JSONDecodeError:
                    # Echo back as plain text
                    await websocket.send(f"Echo: {message}")
                    
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Connection closed for client {client_id}")
    except Exception as e:
        logger.error(f"Error with client {client_id}: {e}")

async def main():
    # Create pids directory
    os.makedirs("pids", exist_ok=True)
    
    # Save PID 
    with open("pids/port_8767_server.pid", "w") as f:
        f.write(str(os.getpid()))
    
    port = 8767
    host = "localhost"
    
    logger.info(f"Starting WebSocket server on {host}:{port}...")
    
    # Start the server using the newer API style
    async with websockets.serve(handler, host, port):
        logger.info(f"Server running at ws://{host}:{port}")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)