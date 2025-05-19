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
        logging.FileHandler('logs/bridge_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('bridge_server')

# Track connected clients
connected_clients = set()
sensor_data = {
    "processes": [],
    "screen": {},
    "files": []
}

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
        
        # Send initial sensor data (if we have any)
        if any(sensor_data.values()):
            await websocket.send(json.dumps({
                "type": "sensor_data",
                "payload": sensor_data
            }))
        
        # Handle incoming messages
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                logger.info(f"Received from {client_id}: {msg_type}")
                
                # Handle specific message types
                if msg_type == 'connection_established':
                    logger.info(f"Overlay client initialized: {data.get('payload', {})}")
                    await websocket.send(json.dumps({
                        "type": "server_ready",
                        "payload": {
                            "status": "connected",
                            "server_version": "1.0.0",
                            "capabilities": ["context_tracking", "suggestions", "screen_capture"]
                        }
                    }))
                elif msg_type == 'process_data':
                    # Store process data from sensor
                    sensor_data["processes"] = data.get('payload', [])
                    # Broadcast to all clients
                    await broadcast({
                        "type": "sensor_data",
                        "payload": sensor_data
                    })
                elif msg_type == 'screen_data':
                    # Store screen data from sensor
                    sensor_data["screen"] = data.get('payload', {})
                    # Broadcast to all clients
                    await broadcast({
                        "type": "sensor_data",
                        "payload": sensor_data
                    })
                elif msg_type == 'file_data':
                    # Store file data from sensor
                    sensor_data["files"] = data.get('payload', [])
                    # Broadcast to all clients
                    await broadcast({
                        "type": "sensor_data",
                        "payload": sensor_data
                    })
                else:
                    # Default echo response
                    response = {
                        "type": "response",
                        "payload": {
                            "message": f"Received {msg_type} message",
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
                
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Connection closed with {client_id}: {e}")
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

async def main():
    # Bind to localhost on port 8765 (for overlay connections)
    port = 8765
    host = "localhost"
    
    # Start server
    logger.info(f"Starting WebSocket bridge server on {host}:{port}")
    server = await websockets.serve(handler, host, port)
    
    # Save PID
    with open('pids/bridge_server.pid', 'w') as f:
        f.write(str(os.getpid()))
        
    logger.info(f"WebSocket bridge server started on ws://{host}:{port}")
    
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
