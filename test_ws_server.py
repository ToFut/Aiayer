#!/usr/bin/env python3
"""
Test WebSocket server for memory trigger system
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
        logging.FileHandler('logs/test_ws_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('test_ws_server')

# Connected clients
connected_clients = set()

async def handler(websocket):
    """WebSocket handler with websocket parameter"""
    client_id = f"client_{id(websocket)}"
    connected_clients.add(websocket)
    logger.info(f"Client {client_id} connected")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": f"Connected to test WebSocket server",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Process messages
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received from {client_id}: {data}")
                
                # Echo back any message received
                await websocket.send(json.dumps({
                    "type": "echo",
                    "original": data,
                    "message": "Message received",
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
    except Exception as e:
        logger.error(f"Error with {client_id}: {e}")
    finally:
        connected_clients.remove(websocket)
        logger.info(f"Client {client_id} disconnected")

async def main():
    """Main function"""
    host = "localhost"
    port = 8765
    
    logger.info(f"Starting WebSocket server on {host}:{port}")
    
    # Make sure directories exist
    os.makedirs("logs", exist_ok=True)
    os.makedirs("pids", exist_ok=True)
    
    server = await websockets.serve(handler, host, port)
    
    # Write PID file
    with open('pids/test_ws_server.pid', 'w') as f:
        f.write(str(os.getpid()))
        
    logger.info(f"Server started on ws://{host}:{port}")
    
    await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)