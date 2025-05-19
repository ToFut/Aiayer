#!/usr/bin/env python3
"""
Ultra-minimal standalone WebSocket server that doesn't rely on any project modules
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
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('minimal_ws.log')
    ]
)
logger = logging.getLogger('minimal_ws')

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
                
                # Send response back
                response = {
                    "type": "response",
                    "payload": {
                        "message": f"Received your message",
                        "original": data,
                        "server_time": datetime.now().isoformat()
                    }
                }
                await websocket.send(json.dumps(response))
                
                # Periodically send sample data
                if "connection_established" in str(data):
                    asyncio.create_task(send_periodic_data(websocket, client_id))
                
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

async def send_periodic_data(websocket, client_id):
    """Send periodic data to the client"""
    try:
        for i in range(100):  # Send 100 updates then stop
            # Create sample data
            sensor_data = {
                "processes": [
                    {"name": "Chrome", "pid": 12345, "cpu": 15.3, "memory": 234.5},
                    {"name": "VSCode", "pid": 12346, "cpu": 8.7, "memory": 412.8}
                ],
                "screen": {
                    "active_app": "Terminal",
                    "window_title": "bash - minimal_ws"
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Send to client
            await websocket.send(json.dumps({
                "type": "sensor_data",
                "payload": sensor_data
            }))
            
            # Wait before next update
            await asyncio.sleep(5)
            
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Connection closed during periodic updates for {client_id}")
    except Exception as e:
        logger.error(f"Error sending periodic data to {client_id}: {e}")

async def main():
    """Main function to run the WebSocket server"""
    port = 8765
    host = "localhost"
    
    logger.info(f"Starting minimal WebSocket server on {host}:{port}")
    
    # Start the server
    async with websockets.serve(handler, host, port):
        logger.info(f"Server started successfully")
        
        # Save PID
        with open('minimal_ws.pid', 'w') as f:
            f.write(str(os.getpid()))
        
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