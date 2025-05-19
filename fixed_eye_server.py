#!/usr/bin/env python3
"""
Fixed Eye Server

A minimal eye server implementation that works with the current WebSocket API.
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime

# Try to import websockets
try:
    import websockets
except ImportError:
    print("Installing websockets package...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
    import websockets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/eye_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("eye_server")

# Create directories
os.makedirs("pids", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# Save PID
with open("pids/eye_server.pid", "w") as f:
    f.write(str(os.getpid()))

# Compatible handler that doesn't need the path parameter
async def handler(websocket):
    client_id = id(websocket)
    logger.info(f"Client {client_id} connected to eye server")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": "Connected to fixed eye server",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Handle messages
        async for message in websocket:
            try:
                # Try to parse as JSON
                data = json.loads(message)
                msg_type = data.get("type", "unknown")
                
                logger.info(f"Received {msg_type} message from client {client_id}")
                
                # Handle different message types
                if msg_type == "get_eye_state":
                    # Send eye state
                    await websocket.send(json.dumps({
                        "type": "eye_state",
                        "state": {
                            "active": True,
                            "mode": "normal",
                            "tracking": True
                        },
                        "timestamp": datetime.now().isoformat()
                    }))
                else:
                    # Echo back the message with a response
                    await websocket.send(json.dumps({
                        "type": "response",
                        "original_type": msg_type,
                        "message": f"Processed your {msg_type} request",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
            except json.JSONDecodeError:
                # Handle non-JSON messages
                logger.warning(f"Received non-JSON message from client {client_id}")
                await websocket.send(f"Echo: {message}")
                
    except Exception as e:
        logger.error(f"Error handling client {client_id}: {e}")

async def main():
    port = 8766  # Use port 8766 for eye server
    host = "localhost"
    
    logger.info(f"Starting eye server on {host}:{port}...")
    
    # Start the server using the compatible API
    async with websockets.serve(handler, host, port):
        logger.info(f"Eye server running at ws://{host}:{port}")
        
        # Keep running forever
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Eye server stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)