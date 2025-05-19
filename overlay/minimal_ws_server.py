#!/usr/bin/env python3
"""
Minimal WebSocket server with proper handler signature.
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
        logging.FileHandler('logs/minimal_ws.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('minimal_ws')

# Connected clients
connected_clients = set()

# IMPORTANT: Handler must include the path parameter
async def handler(websocket, path):
    """WebSocket handler with both websocket and path parameters"""
    client_id = f"client_{id(websocket)}"
    connected_clients.add(websocket)
    logger.info(f"Client {client_id} connected at path: {path}")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": f"Connected to minimal WebSocket server",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Start data sending task
        data_task = asyncio.create_task(send_periodic_data(websocket))
        
        # Process messages
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received from {client_id}: {data}")
                
                # Send response
                await websocket.send(json.dumps({
                    "type": "response",
                    "payload": {
                        "message": "Received your message",
                        "timestamp": datetime.now().isoformat()
                    }
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
        data_task.cancel()
        logger.info(f"Client {client_id} disconnected")

async def send_periodic_data(websocket):
    """Send periodic data to client"""
    try:
        import random
        counter = 0
        
        while True:
            # Create simulated data
            processes = [
                {"name": "Chrome", "pid": 12345, "cpu": random.uniform(5, 20), "memory": 234.5},
                {"name": "VS Code", "pid": 12346, "cpu": random.uniform(2, 10), "memory": 412.8},
                {"name": "Terminal", "pid": 12347, "cpu": random.uniform(0.5, 5), "memory": 78.3}
            ]
            
            # Rotate active app
            apps = ["Chrome", "VS Code", "Terminal", "Finder"]
            active_app = apps[counter % len(apps)]
            
            screen_data = {
                "active_app": active_app,
                "window_title": f"{active_app} - Working on project",
                "timestamp": datetime.now().isoformat()
            }
            
            # Send sensor data
            sensor_data = {
                "type": "sensor_data",
                "payload": {
                    "processes": processes,
                    "screen": screen_data,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            await websocket.send(json.dumps(sensor_data))
            
            counter += 1
            await asyncio.sleep(5)
            
    except asyncio.CancelledError:
        logger.debug("Data sending task canceled")
    except Exception as e:
        logger.error(f"Error sending data: {e}")

async def main():
    """Main function"""
    host = "localhost"
    port = 8765
    
    logger.info(f"Starting WebSocket server on {host}:{port}")
    
    server = await websockets.serve(handler, host, port)
    
    with open('pids/ws_server.pid', 'w') as f:
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
