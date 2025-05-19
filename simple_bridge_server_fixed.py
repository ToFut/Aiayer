#!/usr/bin/env python3
"""
Simple Bridge Server (Fixed)

A minimal bridge server that works with any websockets version.
"""
import asyncio
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
        logging.FileHandler('logs/bridge_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('bridge_server')

# Create directories
os.makedirs('pids', exist_ok=True)
os.makedirs('logs', exist_ok=True)

# Save PID
with open('pids/bridge_server.pid', 'w') as f:
    f.write(str(os.getpid()))

# Import websockets
try:
    import websockets
except ImportError:
    logger.error("Websockets package not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
    import websockets

# Track connected clients
connected_clients = set()

# Very simple handler that works with any websockets version
async def handler(websocket, path=None):
    """WebSocket connection handler that works with any API version"""
    client_id = id(websocket)
    connected_clients.add(websocket)
    logger.info(f"Client {client_id} connected")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": "Connected to bridge server",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Handle incoming messages
        async for message in websocket:
            try:
                # Try to parse as JSON
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                logger.info(f"Received message type: {msg_type}")
                
                # Echo back the message
                await websocket.send(json.dumps({
                    "type": "response",
                    "original_type": msg_type,
                    "message": f"Received {msg_type} message",
                    "timestamp": datetime.now().isoformat()
                }))
                
            except json.JSONDecodeError:
                # Handle plain text
                logger.info(f"Received plain text: {message}")
                await websocket.send(f"Echo: {message}")
                
    except Exception as e:
        logger.error(f"Error handling client {client_id}: {e}")
    finally:
        connected_clients.remove(websocket)
        logger.info(f"Client {client_id} disconnected")

async def main():
    port = 8765
    host = "localhost"
    
    logger.info(f"Starting bridge server on {host}:{port}...")
    
    # Start server
    server = await websockets.serve(handler, host, port)
    
    logger.info(f"Bridge server running on ws://{host}:{port}")
    
    # Run forever
    await asyncio.Future()

if __name__ == "__main__":
    try:
        # Run the server
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bridge server stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)