#!/usr/bin/env python3
"""
Ultra-simple bridge server for WebSocket communication with overlay
This version uses the simplest possible websockets configuration to avoid compatibility issues.
"""
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/simple_bridge.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('simple_bridge')

# Track connected clients
connected_clients = set()

# For newer websockets versions, we don't need the path parameter
async def handler(websocket):
    """WebSocket connection handler for newer websockets versions"""
    client_id = f"client_{id(websocket)}"
    connected_clients.add(websocket)
    logger.info(f"Client {client_id} connected")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": "Connected to Simple Bridge Server",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Handle incoming messages
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                logger.info(f"Received from {client_id}: {msg_type}")
                
                # Handle specific message types
                if msg_type == 'connection_established':
                    client_info = data.get('payload', {})
                    client_type = client_info.get('client', 'unknown')
                    logger.info(f"Client {client_id} identified as: {client_type}")
                    
                    # Send ready confirmation
                    await websocket.send(json.dumps({
                        "type": "server_ready",
                        "payload": {
                            "status": "connected",
                            "server_version": "1.0.0",
                            "server_time": datetime.now().isoformat(),
                            "capabilities": ["llm", "chat"]
                        }
                    }))
                    
                elif msg_type == 'llm_request':
                    # Forward to LLM system
                    logger.info(f"LLM request received: {data.get('payload', {}).get('query', 'empty')}")
                    
                    # Forward to other connected clients (especially the LLM service)
                    for client in connected_clients:
                        if client != websocket:  # Don't send back to sender
                            try:
                                await client.send(json.dumps(data))
                            except Exception as e:
                                logger.error(f"Error forwarding to client: {e}")
                    
                else:
                    # Default echo response
                    response = {
                        "type": "echo",
                        "original_type": msg_type,
                        "message": f"Echoing your {msg_type} message",
                        "timestamp": datetime.now().isoformat()
                    }
                    await websocket.send(json.dumps(response))
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {client_id}: {message[:100]}...")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
                
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Connection closed with {client_id}: {e}")
    except Exception as e:
        logger.error(f"Error handling client {client_id}: {e}")
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
    
    # Create pid directory
    os.makedirs("pids", exist_ok=True)
    
    try:
        # Start server
        async with websockets.serve(handler, host, port):
            # Save PID
            with open('pids/bridge_server.pid', 'w') as f:
                f.write(str(os.getpid()))
            
            logger.info(f"WebSocket bridge server started on ws://{host}:{port}")
            
            # Keep running forever
            await asyncio.Future()
            
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)