#!/usr/bin/env python3
"""
Simple WebSocket Server on Port 8790
"""
import asyncio
import json
import logging
import websockets
import sys
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ws_server_8790.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Track connected clients
connected_clients = set()

async def handler(websocket, path):
    """Handle WebSocket connections."""
    try:
        # Add client to set
        connected_clients.add(websocket)
        client_id = id(websocket)
        logger.info(f"Client {client_id} connected at path: {path}")
        
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "connection_established",
            "data": {
                "message": f"Connected to WebSocket server at path: {path}",
                "timestamp": datetime.now().isoformat()
            }
        }))
        
        # Handle messages
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received message from client {client_id}: {data}")
                
                # Echo back the message
                await websocket.send(json.dumps({
                    "type": "echo",
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                }))
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from client {client_id}")
            except Exception as e:
                logger.error(f"Error processing message from client {client_id}: {e}")
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error with client {client_id}: {e}")
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)

async def broadcast_status():
    """Periodically broadcast status updates to all clients."""
    while True:
        if connected_clients:
            message = json.dumps({
                "type": "status_update",
                "data": {
                    "client_count": len(connected_clients),
                    "timestamp": datetime.now().isoformat()
                }
            })
            
            # Broadcast to all clients
            await asyncio.gather(
                *[client.send(message) for client in connected_clients],
                return_exceptions=True
            )
        
        await asyncio.sleep(5)

async def main():
    """Main function to start the WebSocket server."""
    try:
        # Create the server
        server = await websockets.serve(
            handler,
            "127.0.0.1",
            8790,
            ping_interval=10,
            ping_timeout=5
        )
        
        logger.info("WebSocket server started on ws://127.0.0.1:8790")
        
        # Save PID to file
        with open('pids/ws_server_8790.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        # Start broadcast task
        broadcast_task = asyncio.create_task(broadcast_status())
        
        # Keep the server running
        await asyncio.Future()
        
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs("logs", exist_ok=True)
    os.makedirs("pids", exist_ok=True)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)