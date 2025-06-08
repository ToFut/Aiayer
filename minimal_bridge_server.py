#!/usr/bin/env python3
"""
Minimal Bridge Server - Connects port 8768 to backend on port 8767
"""
import asyncio
import websockets
import json
import logging
import os
from datetime import datetime

# Configure logging
os.makedirs('logs/websocket', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/websocket/minimal_bridge.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('minimal_bridge')

# Track connected clients
connected_clients = set()

async def handle_client(websocket, path):
    """Handle client connection"""
    client_id = f"client_{id(websocket)}"
    connected_clients.add(websocket)
    logger.info(f"Client {client_id} connected")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "connection_established",
            "client_id": client_id,
            "server_version": "1.0.0",
            "capabilities": ["chat", "memory", "automation"],
            "timestamp": datetime.now().isoformat()
        }))
        
        # Handle messages
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received from {client_id}: {data.get('type', 'unknown')}")
                
                # If we receive a chat_request, forward it to the backend
                if data.get('type') == 'chat_request':
                    try:
                        # Forward to backend
                        async with websockets.connect('ws://localhost:8767') as backend_ws:
                            # First message will be welcome
                            await backend_ws.recv()
                            
                            # Forward the request
                            await backend_ws.send(message)
                            logger.info(f"Forwarded chat request to backend")
                            
                            # Wait for response
                            response = await backend_ws.recv()
                            await websocket.send(response)
                            logger.info(f"Forwarded backend response to client")
                    except Exception as e:
                        logger.error(f"Error forwarding to backend: {e}")
                        # Send error response
                        await websocket.send(json.dumps({
                            "type": "chat_response",
                            "success": False,
                            "response": f"Error connecting to backend: {str(e)}",
                            "timestamp": datetime.now().isoformat()
                        }))
                else:
                    # Echo other message types
                    await websocket.send(json.dumps({
                        "type": "response",
                        "original_type": data.get('type', 'unknown'),
                        "message": "Message received",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {client_id}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": "Invalid JSON format",
                    "timestamp": datetime.now().isoformat()
                }))
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} disconnected")
    finally:
        connected_clients.remove(websocket)

async def main():
    """Start the WebSocket server"""
    host = "localhost"
    port = 8768
    
    logger.info(f"Starting Minimal Bridge Server on {host}:{port}")
    async with websockets.serve(handle_client, host, port):
        logger.info(f"Minimal Bridge Server running on ws://{host}:{port}")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")