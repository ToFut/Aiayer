#!/usr/bin/env python
"""
Fixed WebSocket Server on Port 8767

Fixed implementation with correct handler signature.
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

# Make sure the handler has the correct signature
async def handler(websocket):
    """Handle WebSocket connections."""
    try:
        # Add client to set
        connected_clients.add(websocket)
        client_id = id(websocket)
        logger.info(f"Client {client_id} connected")
        
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "connection_established",
            "data": {
                "message": "Connected to WebSocket server",
                "timestamp": datetime.now().isoformat()
            }
        }))
        
        # Handle messages
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received message from client {client_id}: {data}")
                
                # Echo back the message with some additional info
                response = {
                    "type": "response",
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                }
                
                # If it's a user interaction, add a special response
                if data.get('type') == 'user_interaction':
                    payload = data.get('payload', {})
                    if payload.get('type') == 'query':
                        response = {
                            "type": "query_response",
                            "payload": {
                                "query": payload.get('query', ''),
                                "response": f"Processed your query: {payload.get('query', '')}",
                                "timestamp": datetime.now().isoformat()
                            }
                        }
                
                # Send the response
                await websocket.send(json.dumps(response))
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from client {client_id}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": "Invalid JSON format"
                }))
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
        port = 8767
        host = "0.0.0.0"  # Bind to all interfaces
        
        # Create server
        server = await websockets.serve(
            handler,
            host,
            port,
            ping_interval=10,
            ping_timeout=5,
            max_size=10 * 1024 * 1024,  # 10MB max message size
            max_queue=64,               # Queue size
            close_timeout=2             # Close timeout
        )
        
        logger.info(f"server listening on {host}:{port}")
        logger.info(f"WebSocket server started on ws://{host}:{port}")
        
        # Save the port we're using
        with open("ws_port.txt", "w") as f:
            f.write(str(port))
            
        # Save PID
        with open("pids/ws_server_8767.pid", "w") as f:
            f.write(str(os.getpid()))
        
        # Start broadcast task
        broadcast_task = asyncio.create_task(broadcast_status())
        
        # Keep the server running
        await asyncio.Future()
        
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Create directories if needed
    os.makedirs("logs", exist_ok=True)
    os.makedirs("pids", exist_ok=True)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)