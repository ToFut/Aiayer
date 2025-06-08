#!/usr/bin/env python3
"""
Brain Router Connector for Overlay
This script creates a WebSocket server on port 8766 that forwards messages to the brain router
backend on port 8767 and properly formats responses for the overlay.
"""
import asyncio
import websockets
import json
import logging
import sys
import time
import traceback
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/brain_router_connector.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Settings
BACKEND_URI = "ws://localhost:8767"
CONNECTOR_PORT = 8766

# Connected clients
connected_clients = {}
backend_connections = {}

async def forward_to_backend(client_ws, message_data):
    """Forward message to brain router backend and handle response"""
    try:
        client_id = connected_clients.get(client_ws)
        if not client_id:
            logger.error("No client ID for websocket")
            return False
            
        logger.info(f"Forwarding to brain router: {message_data[:100]}...")
        
        # Create backend connection if needed
        if client_ws not in backend_connections:
            logger.info(f"Creating new backend connection for client {client_id}")
            backend_ws = await websockets.connect(
                BACKEND_URI, 
                ping_interval=30,
                ping_timeout=300
            )
            backend_connections[client_ws] = backend_ws
            
            # Start listener for backend messages
            asyncio.create_task(listen_to_backend(client_ws, backend_ws))
        else:
            backend_ws = backend_connections[client_ws]
            
        # Send to backend
        await backend_ws.send(message_data)
        return True
        
    except Exception as e:
        logger.error(f"Error forwarding to backend: {e}")
        logger.error(traceback.format_exc())
        
        # Send error to client
        try:
            error_message = {
                "type": "error",
                "payload": {
                    "message": f"Error connecting to backend: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
            }
            await client_ws.send(json.dumps(error_message))
        except:
            pass
            
        return False

async def listen_to_backend(client_ws, backend_ws):
    """Listen for responses from the backend and forward to client"""
    try:
        while True:
            # Wait for message from backend
            response = await backend_ws.recv()
            
            # Process response if needed
            try:
                response_data = json.loads(response)
                logger.info(f"Received from backend: {response_data.get('type', 'unknown')} message")
                
                # If this is a query response, ensure it's in the right format for the overlay
                if response_data.get('type') in ['chat_response', 'llm_response', 'final_response']:
                    # Reformat to query_response if needed for better overlay compatibility
                    if 'response' in response_data and 'payload' not in response_data:
                        response_data = {
                            "type": "query_response",
                            "payload": {
                                "response": response_data['response'],
                                "mode": response_data.get('mode', 'Ask'),
                                "timestamp": datetime.now().isoformat()
                            }
                        }
                        response = json.dumps(response_data)
            except:
                # Just forward as-is if we can't parse
                pass
                
            # Forward to client
            await client_ws.send(response)
            
    except websockets.exceptions.ConnectionClosed:
        logger.info("Backend connection closed")
    except Exception as e:
        logger.error(f"Error in backend listener: {e}")
        logger.error(traceback.format_exc())
    finally:
        # Clean up this backend connection
        if client_ws in backend_connections:
            if backend_connections[client_ws] == backend_ws:
                del backend_connections[client_ws]

async def handle_client(websocket, path=None):
    """Handle WebSocket client connections"""
    client_id = f"client_{int(time.time() * 1000)}"
    connected_clients[websocket] = client_id
    
    try:
        logger.info(f"Client {client_id} connected")
        
        # Send immediate connection message
        await websocket.send(json.dumps({
            "type": "connection_established",
            "message": "Brain Router Connector for Overlay",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        }))
        
        # Handle messages
        async for message in websocket:
            try:
                # Parse message
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                logger.info(f"Received message type: {msg_type} from client {client_id}")
                
                # Check if it's a query
                if msg_type in ['llm_request', 'chat_request']:
                    # Format for brain router if needed
                    if msg_type == 'llm_request' and 'payload' in data:
                        # Convert to chat_request format that brain router expects
                        chat_request = {
                            "type": "chat_request",
                            "message": data['payload'].get('query', ''),
                            "mode": data['payload'].get('mode', 'ask'),
                            "session_id": data['payload'].get('session_id', client_id),
                            "client_id": client_id,
                            "timestamp": datetime.now().isoformat()
                        }
                        await forward_to_backend(websocket, json.dumps(chat_request))
                    else:
                        # Forward as-is
                        await forward_to_backend(websocket, message)
                    
                    # Send typing indicator for better UX
                    await websocket.send(json.dumps({
                        "type": "typing_start",
                        "message": "AI is thinking...",
                        "timestamp": datetime.now().isoformat()
                    }))
                else:
                    # Forward all other messages
                    await forward_to_backend(websocket, message)
                    
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from client {client_id}")
            except Exception as e:
                logger.error(f"Error processing message from {client_id}: {e}")
                logger.error(traceback.format_exc())
    
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error with client {client_id}: {e}")
        logger.error(traceback.format_exc())
    finally:
        # Clean up
        if websocket in connected_clients:
            del connected_clients[websocket]
        
        # Close backend connection if exists
        if websocket in backend_connections:
            try:
                await backend_connections[websocket].close()
            except:
                pass
            del backend_connections[websocket]

async def main():
    """Start the brain router connector"""
    # Start WebSocket server
    logger.info(f"Starting Brain Router Connector on port {CONNECTOR_PORT}")
    async with websockets.serve(handle_client, "0.0.0.0", CONNECTOR_PORT):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        logger.error(traceback.format_exc())
