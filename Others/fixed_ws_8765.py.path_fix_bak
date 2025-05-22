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
from typing import Dict, Any, Optional, Set
import websockets
from websockets.server import WebSocketServerProtocol

# Configure logging
os.makedirs('logs/websocket', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/websocket/ws_server_8765.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Track connected clients
connected_clients: Set[WebSocketServerProtocol] = set()
llm_service = None
chat_overlay = None  # Track chat overlay client
client_types = {}  # Map client websockets to their types

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
                
                if msg_type in ['register', 'connection_established']:
                    # Handle client registration
                    if msg_type == 'register':
                        client_type = data.get('client_type', data.get('payload', {}).get('client_type', 'unknown'))
                    else:  # connection_established
                        client_type = data.get('payload', {}).get('client', 'unknown')
                    
                    logger.info(f"Client {client_id} registered as {client_type}")
                    
                    # Store client type
                    client_types[websocket] = client_type
                    
                    # Send registration confirmation
                    await websocket.send(json.dumps({
                        "type": "registration_confirmed",
                        "payload": {
                            "client_id": client_id,
                            "client_type": client_type,
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                    
                    # Store special clients
                    if client_type in ['llm', 'ollama_llm_service']:
                        global llm_service
                        llm_service = websocket
                        logger.info("LLM service connected")
                        # Notify all clients about LLM service status
                        await broadcast_to_clients({
                            "type": "llm_service_status",
                            "payload": {
                                "status": "connected",
                                "timestamp": datetime.now().isoformat()
                            }
                        }, exclude={websocket})
                    elif client_type in ['chat_overlay', 'ui']:
                        global chat_overlay
                        chat_overlay = websocket
                        logger.info("Chat overlay connected")
                        # Send current LLM service status to the new client
                        if llm_service:
                            try:
                                await websocket.send(json.dumps({
                                    "type": "llm_service_status",
                                    "payload": {
                                        "status": "connected",
                                        "timestamp": datetime.now().isoformat()
                                    }
                                }))
                            except Exception as e:
                                logger.error(f"Error sending LLM status to new client: {e}")
                
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
                    await broadcast_to_clients(data, exclude={llm_service})
                
                elif msg_type == 'chat_message':
                    # Handle chat messages by forwarding to backend server
                    logger.info("Received chat message, forwarding to backend server")
                    try:
                        response = await forward_to_backend(data)
                        if response:
                            # Send response back to the originating client
                            await websocket.send(json.dumps(response))
                            logger.info(f"Sent backend response to client {client_id}")
                        else:
                            # Send error if no response
                            await websocket.send(json.dumps({
                                "type": "error",
                                "payload": {
                                    "message": "No response from backend server",
                                    "timestamp": datetime.now().isoformat()
                                }
                            }))
                    except Exception as e:
                        logger.error(f"Error handling chat message: {e}")
                        await websocket.send(json.dumps({
                            "type": "error",
                            "payload": {
                                "message": f"Error processing message: {str(e)}",
                                "timestamp": datetime.now().isoformat()
                            }
                        }))
                
                elif msg_type == 'user_interaction':
                    # Forward user interactions to LLM service
                    logger.info("Received user interaction, forwarding to LLM service")
                    if llm_service:
                        try:
                            # Convert to LLM request format
                            llm_request = {
                                "type": "llm_request",
                                "payload": {
                                    "query": data.get('payload', {}).get('message', ''),
                                    "context": data.get('payload', {}).get('context', {}),
                                    "timestamp": datetime.now().isoformat()
                                }
                            }
                            await llm_service.send(json.dumps(llm_request))
                            logger.info("Forwarded user interaction to LLM service")
                        except Exception as e:
                            logger.error(f"Error forwarding to LLM service: {e}")
                            await websocket.send(json.dumps({
                                "type": "error",
                                "payload": {
                                    "message": f"Error forwarding to LLM service: {str(e)}",
                                    "timestamp": datetime.now().isoformat()
                                }
                            }))
                    else:
                        logger.warning("No LLM service available")
                        await websocket.send(json.dumps({
                            "type": "error",
                            "payload": {
                                "message": "No LLM service available",
                                "timestamp": datetime.now().isoformat()
                            }
                        }))
                
                else:
                    # Forward all other messages to all clients
                    logger.info(f"Forwarding {msg_type} message to all clients")
                    await broadcast_to_clients(data, exclude={websocket})
                
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
        if websocket in client_types:
            del client_types[websocket]
        if websocket == llm_service:
            llm_service = None
            logger.info("LLM service disconnected")
            # Notify all clients about LLM service disconnection
            await broadcast_to_clients({
                "type": "llm_service_status",
                "payload": {
                    "status": "disconnected",
                    "timestamp": datetime.now().isoformat()
                }
            })
        if websocket == chat_overlay:
            chat_overlay = None
            logger.info("Chat overlay disconnected")
        logger.info(f"Client {client_id} ({client_type}) disconnected")

async def broadcast_to_clients(message: Dict[str, Any], exclude: Set[WebSocketServerProtocol] = None) -> None:
    """Broadcast message to all connected clients except those in exclude set."""
    exclude = exclude or set()
    for client in connected_clients:
        if client not in exclude:
            try:
                await client.send(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")

async def main():
    """Main function to start the WebSocket server."""
    try:
        # Use port 8765 to match the sensors' configuration
        port = 8765
        
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

async def forward_to_backend(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Forward message to backend server and return response."""
    try:
        # Connect to backend server on port 8767
        uri = "ws://localhost:8767"
        async with websockets.connect(uri) as backend_ws:
            # Convert chat_message to user_message format expected by backend
            backend_message = {
                "type": "user_message",
                "payload": {
                    "query": data.get('message', data.get('query', '')),
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # Send message to backend
            await backend_ws.send(json.dumps(backend_message))
            logger.info("Sent message to backend server")
            
            # Wait for response
            response_str = await asyncio.wait_for(backend_ws.recv(), timeout=30.0)
            response = json.loads(response_str)
            logger.info("Received response from backend server")
            
            return response
            
    except asyncio.TimeoutError:
        logger.error("Timeout waiting for backend response")
        return None
    except Exception as e:
        logger.error(f"Error communicating with backend: {e}")
        return None

def is_port_in_use(port: int) -> bool:
    """Check if a port is in use."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

if __name__ == "__main__":
    asyncio.run(main())