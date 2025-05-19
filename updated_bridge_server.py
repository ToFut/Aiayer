#!/usr/bin/env python3
"""
Updated Bridge Server

Fixed bridge server implementation with websockets compatibility.
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime

# Setup directories and logging
os.makedirs('logs', exist_ok=True)
os.makedirs('pids', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bridge_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('bridge_server')

# Save PID for management
with open('pids/bridge_server.pid', 'w') as f:
    f.write(str(os.getpid()))

# State tracking
connected_clients = set()
sensor_data = {
    "processes": [],
    "screen": {},
    "files": [],
    "last_update": datetime.now().isoformat()
}

# Import websockets with version check
try:
    import websockets
    import websockets.version
    logger.info(f"Using websockets version: {websockets.version.__version__}")
except ImportError:
    logger.error("Websockets package not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
    import websockets
    import websockets.version
    logger.info(f"Installed websockets version: {websockets.version.__version__}")

# Determine if we're using websockets >= 10.0 (new API style)
NEW_API = websockets.version.__version__.startswith(("10.", "11."))
logger.info(f"Using {'new' if NEW_API else 'old'} websockets API")

# Handler for websocket connections - supports both API styles
if NEW_API:
    # New API style (websockets >= 10.0) doesn't use path parameter
    async def handler(websocket):
        client_id = f"client_{id(websocket)}"
        connected_clients.add(websocket)
        logger.info(f"Client {client_id} connected")
        
        try:
            # Send welcome message
            await websocket.send(json.dumps({
                "type": "welcome",
                "message": "Connected to bridge server",
                "timestamp": datetime.now().isoformat()
            }))
            
            # Send initial data if available
            if any([sensor_data["processes"], sensor_data["screen"], sensor_data["files"]]):
                await websocket.send(json.dumps({
                    "type": "sensor_data",
                    "payload": sensor_data,
                    "timestamp": datetime.now().isoformat()
                }))
            
            # Handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    msg_type = data.get('type', 'unknown')
                    logger.info(f"Received message type: {msg_type}")
                    
                    # Echo back all messages for now
                    await websocket.send(json.dumps({
                        "type": "response",
                        "original_type": msg_type,
                        "message": f"Processed {msg_type} request",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from client {client_id}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format"
                    }))
                    
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            connected_clients.remove(websocket)
            logger.info(f"Client {client_id} disconnected")
else:
    # Old API style (websockets < 10.0) requires path parameter
    async def handler(websocket, path):
        client_id = f"client_{id(websocket)}"
        connected_clients.add(websocket)
        logger.info(f"Client {client_id} connected at path: {path}")
        
        try:
            # Send welcome message
            await websocket.send(json.dumps({
                "type": "welcome",
                "message": f"Connected to bridge server. Path: {path}",
                "timestamp": datetime.now().isoformat()
            }))
            
            # Send initial data if available
            if any([sensor_data["processes"], sensor_data["screen"], sensor_data["files"]]):
                await websocket.send(json.dumps({
                    "type": "sensor_data",
                    "payload": sensor_data,
                    "timestamp": datetime.now().isoformat()
                }))
            
            # Handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    msg_type = data.get('type', 'unknown')
                    logger.info(f"Received message type: {msg_type}")
                    
                    # Echo back all messages for now
                    await websocket.send(json.dumps({
                        "type": "response",
                        "original_type": msg_type,
                        "message": f"Processed {msg_type} request",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from client {client_id}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format"
                    }))
                    
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            connected_clients.remove(websocket)
            logger.info(f"Client {client_id} disconnected")

# Broadcast helper
async def broadcast_message(message):
    if not connected_clients:
        return
        
    for client in list(connected_clients):  # Use list to avoid modification during iteration
        try:
            await client.send(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending message to client: {e}")

# Heartbeat task
async def heartbeat_task():
    while True:
        try:
            # Send heartbeat to all clients
            await broadcast_message({
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat(),
                "clients_connected": len(connected_clients)
            })
        except Exception as e:
            logger.error(f"Error in heartbeat: {e}")
            
        # Wait before next heartbeat
        await asyncio.sleep(30)

async def main():
    # Configuration
    host = "localhost" 
    port = 8765  # Bridge server port
    
    logger.info(f"Starting bridge server on {host}:{port}...")
    
    # Start the WebSocket server with the appropriate API
    if NEW_API:
        # New API style
        async with websockets.serve(handler, host, port):
            logger.info(f"Bridge server started on ws://{host}:{port}")
            
            # Start heartbeat task
            heartbeat = asyncio.create_task(heartbeat_task())
            
            # Run forever
            await asyncio.Future()
    else:
        # Old API style
        server = await websockets.serve(handler, host, port)
        logger.info(f"Bridge server started on ws://{host}:{port}")
        
        # Start heartbeat task
        heartbeat = asyncio.create_task(heartbeat_task())
        
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