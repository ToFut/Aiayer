#!/usr/bin/env python3
"""
Simple Bridge Server (Fixed)

A minimal bridge server that works with any websockets version.
"""
import asyncio
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
        logging.FileHandler('logs/bridge_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('bridge_server')

# Create directories
os.makedirs('pids', exist_ok=True)
os.makedirs('logs', exist_ok=True)

# Save PID
with open('pids/bridge_server.pid', 'w') as f:
    f.write(str(os.getpid()))

# Import websockets
try:
    import websockets
except ImportError:
    logger.error("Websockets package not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
    import websockets

# Track connected clients
connected_clients = set()
llm_service = None

# Very simple handler that works with any websockets version
async def handler(websocket, path=None):
    """WebSocket connection handler that works with any API version"""
    global llm_service
    client_id = id(websocket)
    connected_clients.add(websocket)
    client_type = "unknown"
    logger.info(f"Client {client_id} connected")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "connection_established",
            "payload": {
                "client_id": client_id,
                "timestamp": datetime.now().isoformat(), 
                "status": "connected"
            }
        }))
        
        # Handle incoming messages
        async for message in websocket:
            try:
                # Try to parse as JSON
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                logger.info(f"Received message type: {msg_type}")
                
                # Handle different message types
                if msg_type == 'connection_established':
                    client_info = data.get('payload', {})
                    client_type = client_info.get('client', 'unknown')
                    logger.info(f"Client identified as: {client_type}")
                    
                    # Register LLM service if applicable
                    if client_type == 'ollama_llm_service':
                        llm_service = websocket
                        logger.info("LLM service registered")
                
                elif msg_type == 'llm_request':
                    # Handle LLM request
                    query = data.get('payload', {}).get('query', '')
                    logger.info(f"LLM request received: {query[:50]}...")
                    
                    if llm_service and llm_service in connected_clients:
                        # Forward to LLM service
                        logger.info("Forwarding request to LLM service")
                        await llm_service.send(json.dumps(data))
                    else:
                        # No LLM service available
                        logger.warning("No LLM service available, sending simulated response")
                        await websocket.send(json.dumps({
                            "type": "llm_response",
                            "payload": {
                                "response": "This is a simulated response. The LLM service is not connected.",
                                "model": "simulated",
                                "timestamp": datetime.now().isoformat()
                            }
                        }))
                
                elif msg_type == 'llm_response':
                    # Forward LLM response to original requester
                    logger.info("Received LLM response, forwarding to clients")
                    
                    # Forward to all non-LLM clients
                    for client in connected_clients:
                        if client != llm_service:
                            try:
                                await client.send(json.dumps(data))
                            except:
                                logger.warning(f"Failed to forward response to a client")
                
                else:
                    # Unknown message type - echo back
                    logger.info(f"Unhandled message type: {msg_type}")
                    await websocket.send(json.dumps({
                        "type": "echo",
                        "payload": data
                    }))
                
            except json.JSONDecodeError:
                # Handle plain text
                logger.info(f"Received plain text: {message}")
                await websocket.send(f"Echo: {message}")
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Connection closed for client {client_id}")
    except Exception as e:
        logger.error(f"Error handling client {client_id}: {e}")
    finally:
        connected_clients.remove(websocket)
        if websocket == llm_service:
            llm_service = None
            logger.info("LLM service disconnected")
        logger.info(f"Client {client_id} ({client_type}) disconnected")

async def main():
    port = 8765
    host = "localhost"
    
    logger.info(f"Starting bridge server on {host}:{port}...")
    
    # Start server
    server = await websockets.serve(handler, host, port)
    
    logger.info(f"Bridge server running on ws://{host}:{port}")
    
    # Run forever
    await asyncio.Future()

if __name__ == "__main__":
    try:
        # Run the server
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bridge server stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)