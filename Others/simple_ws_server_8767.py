#!/usr/bin/env python
"""
Simple WebSocket Server on Port 8767

Minimal WebSocket server implementation for testing.
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
        logging.FileHandler('logs/ws_server_8767.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Track connected clients
connected_clients = set()

async def handler(websocket, path):
    """Handle WebSocket connections with proper signature including path parameter."""
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
        # Try different ports if the default one is in use
        ports_to_try = [8767, 8769, 8770, 8771]
        server = None
        
        for port in ports_to_try:
            try:
                server = await websockets.serve(
                    handler,
                    "127.0.0.1",
                    port,
                    ping_interval=10,
                    ping_timeout=5,
                    max_size=10 * 1024 * 1024,  # 10MB max message size
                    max_queue=64,               # Queue size
                    close_timeout=2             # Close timeout
                )
                logger.info(f"WebSocket server started on ws://127.0.0.1:{port}")
                # Save the port we're actually using
                with open("ws_port.txt", "w") as f:
                    f.write(str(port))
                break
            except OSError as e:
                logger.warning(f"Port {port} is in use, trying another port: {e}")
                continue
                
        if server is None:
            raise OSError("All ports are in use. Cannot start WebSocket server.")
        
        # Start broadcast task
        broadcast_task = asyncio.create_task(broadcast_status())
        
        # Keep the server running
        await asyncio.Future()
        
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)
