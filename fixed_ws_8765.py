#!/usr/bin/env python3
"""
WebSocket Server
Handles WebSocket connections and message routing.
"""
import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import websockets
from websockets.server import WebSocketServerProtocol

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ws_server_8768.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Track connected clients
connected_clients = set()
llm_service = None
chat_overlay = None  # Track chat overlay client

async def handler(websocket: WebSocketServerProtocol):
    """Handle WebSocket connections."""
    client_id = str(uuid.uuid4())
    client_type = "unknown"
    logger.info(f"Client {client_id} connected")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "payload": {
                "client_id": client_id,
                "message": "Connected to WebSocket server",
                "timestamp": datetime.now().isoformat()
            }
        }))
        
        # Add to connected clients
        connected_clients.add(websocket)
        
        # Process messages
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type')
                logger.info(f"Received message type {msg_type} from {client_id}")
                
                if msg_type == 'connection_established':
                    # Update client type
                    client_type = data.get('payload', {}).get('client_type', 'unknown')
                    logger.info(f"Client {client_id} identified as {client_type}")
                    
                    # Store special clients
                    if client_type == 'llm':
                        global llm_service
                        llm_service = websocket
                        logger.info("LLM service connected")
                    elif client_type == 'chat_overlay':
                        global chat_overlay
                        chat_overlay = websocket
                        logger.info("Chat overlay connected")
                
                elif msg_type == 'llm_request':
                    # Forward to LLM service if available
                    if llm_service:
                        await llm_service.send(json.dumps(data))
                        logger.info(f"Forwarded LLM request to service")
                    else:
                        await websocket.send(json.dumps({
                            "type": "error",
                            "payload": {
                                "message": "No LLM service available",
                                "timestamp": datetime.now().isoformat()
                            }
                        }))
                
                elif msg_type == 'llm_response':
                    # Forward LLM response to all clients except the LLM service
                    logger.info("Received LLM response, forwarding to clients")
                    for client in connected_clients:
                        if client != llm_service:
                            try:
                                await client.send(json.dumps(data))
                                logger.info(f"Forwarded LLM response to client {client_id}")
                            except Exception as e:
                                logger.error(f"Error forwarding to client {client_id}: {e}")
                
                elif msg_type == 'chat_message':
                    # Forward chat messages to all clients
                    logger.info("Received chat message, forwarding to all clients")
                    for client in connected_clients:
                        try:
                            await client.send(json.dumps(data))
                            logger.info(f"Forwarded chat message to client {client_id}")
                        except Exception as e:
                            logger.error(f"Error forwarding chat message to client {client_id}: {e}")
                
                else:
                    # Forward all other messages to all clients
                    logger.info(f"Forwarding {msg_type} message to all clients")
                    for client in connected_clients:
                        if client != websocket:  # Don't echo back to sender
                            try:
                                await client.send(json.dumps(data))
                                logger.info(f"Forwarded {msg_type} message to client {client_id}")
                            except Exception as e:
                                logger.error(f"Error forwarding message to client {client_id}: {e}")
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {client_id}: {message[:100]}...")
                await websocket.send(json.dumps({
                    "type": "error",
                    "payload": {"message": "Invalid JSON format"}
                }))
                
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Connection closed with {client_id}: {e}")
    except Exception as e:
        logger.error(f"Error handling client {client_id}: {e}")
    finally:
        connected_clients.remove(websocket)
        if websocket == llm_service:
            llm_service = None
            logger.info("LLM service disconnected")
        if websocket == chat_overlay:
            chat_overlay = None
            logger.info("Chat overlay disconnected")
        logger.info(f"Client {client_id} ({client_type}) disconnected")

async def main():
    """Main function to start the WebSocket server."""
    try:
        # Use port 8768 to match the system's standard
        port = 8768
        
        # Check if port is in use
        if is_port_in_use(port):
            logger.error(f"Port {port} is already in use")
            
            # Try to forcefully release the port by killing any process using it
            os.system(f"lsof -ti :{port} | xargs kill -9 2>/dev/null || true")
            os.system(f"pkill -f 'port {port}' 2>/dev/null || true")
            
            # Wait a moment for the port to be released
            await asyncio.sleep(1)
            
            # Check again
            if is_port_in_use(port):
                logger.error("Failed to release port")
                sys.exit(1)
        
        # Create the server
        server = await websockets.serve(
            handler,
            "0.0.0.0",  # Bind to all interfaces
            port,
            ping_interval=10,
            ping_timeout=5
        )
        
        logger.info(f"WebSocket server started on ws://0.0.0.0:{port}")
        
        # Keep the server running
        await asyncio.Future()
        
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)

def is_port_in_use(port: int) -> bool:
    """Check if a port is in use."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

if __name__ == "__main__":
    asyncio.run(main())