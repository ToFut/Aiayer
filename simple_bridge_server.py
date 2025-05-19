#!/usr/bin/env python3
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

# Simple handler that works with the required path parameter
async def handler(websocket, path):
    """WebSocket connection handler with the correct signature including path parameter"""
    client_id = f"client_{id(websocket)}"
    connected_clients.add(websocket)
    logger.info(f"Client {client_id} connected at path: {path}")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": f"Connected to Eye Widget Bridge",
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
                            "server_time": datetime.now().isoformat()
                        }
                    }))
                    
                elif msg_type == 'user_interaction':
                    # Handle user interaction (like chat message)
                    payload = data.get('payload', {})
                    if payload.get('type') == 'query':
                        query = payload.get('query', '')
                        logger.info(f"Query from {client_id}: {query}")
                        
                        # Send response
                        await websocket.send(json.dumps({
                            "type": "query_response",
                            "response": f"I received your message: '{query}'. This is a simple echo response.",
                            "timestamp": datetime.now().isoformat()
                        }))
                    
                else:
                    # Default echo response
                    await websocket.send(json.dumps({
                        "type": "echo",
                        "original_type": msg_type,
                        "message": f"Echoing your {msg_type} message",
                        "timestamp": datetime.now().isoformat()
                    }))
                
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

async def heartbeat():
    """Send periodic heartbeat to all clients"""
    while True:
        if connected_clients:
            try:
                await broadcast({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat(),
                    "clients_connected": len(connected_clients)
                })
                logger.debug(f"Heartbeat sent to {len(connected_clients)} clients")
            except Exception as e:
                logger.error(f"Error sending heartbeat: {e}")
        await asyncio.sleep(30)  # Heartbeat every 30 seconds

async def main():
    # Bind to localhost on port 8765 (for overlay connections)
    port = 8765
    host = "localhost"
    
    # Create directories
    os.makedirs("pids", exist_ok=True)
    
    # Kill any existing server on this port
    if sys.platform == "win32":
        os.system(f"taskkill /F /FI \"PID ne {os.getpid()}\" /FI \"LOCALPORT eq {port}\" 2>nul")
    else:
        os.system(f"lsof -ti:{port} | grep -v {os.getpid()} | xargs kill -9 2>/dev/null || true")
    
    # Start server with explicit handler function that includes path parameter
    try:
        server = await websockets.serve(handler, host, port)
        
        # Save PID
        with open('pids/bridge_server.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        # Start heartbeat task
        heartbeat_task = asyncio.create_task(heartbeat())
        
        logger.info(f"WebSocket bridge server started on ws://{host}:{port}")
        logger.info(f"Heartbeat system active")
        
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