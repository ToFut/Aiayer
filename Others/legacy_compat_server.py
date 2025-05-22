#!/usr/bin/env python3
"""
Legacy Compatible WebSocket Server that works with older websockets library.
This is specifically designed to be compatible with the version of the
websockets library that expects a two-parameter handler function.
"""
import asyncio
import json
import logging
import os
import sys
import subprocess
from datetime import datetime
import signal

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/legacy_compat_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Track connected clients
connected_clients = set()

# Simple handler for websockets
async def handler(websocket, path):
    """Handler function with both websocket and path parameters to work with older websockets library."""
    connected_clients.add(websocket)
    client_id = f"client_{id(websocket)}"
    logger.info(f"Client {client_id} connected at path: {path}")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": f"Connected to WebSocket Server",
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
                    logger.info(f"Overlay client initialized: {data.get('payload', {})}")
                    await websocket.send(json.dumps({
                        "type": "server_ready",
                        "payload": {
                            "status": "connected",
                            "server_version": "1.0.0",
                            "capabilities": ["context_tracking", "suggestions", "screen_capture"]
                        }
                    }))
                    
                elif msg_type == 'user_interaction':
                    # Handle user interaction (like chat message)
                    payload = data.get('payload', {})
                    if payload.get('type') == 'query':
                        query = payload.get('query', '')
                        logger.info(f"Query from {client_id}: {query}")
                        
                        # Send a mock response
                        response = f"You asked: '{query}'. This is a test response from the WebSocket server."
                        await websocket.send(json.dumps({
                            "type": "query_response",
                            "payload": {
                                "response": response,
                                "timestamp": datetime.now().isoformat()
                            }
                        }))
                
                else:
                    # Default echo response
                    await websocket.send(json.dumps({
                        "type": "echo",
                        "original_type": msg_type,
                        "message": f"Received your {msg_type} message",
                        "timestamp": datetime.now().isoformat()
                    }))
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {client_id}: {message[:100]}...")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
                
    except Exception as e:
        logger.error(f"Error handling client {client_id}: {e}")
    finally:
        connected_clients.remove(websocket)
        logger.info(f"Client {client_id} disconnected")

async def send_periodic_updates():
    """Send periodic status updates to all clients"""
    while True:
        if connected_clients:
            try:
                # Create data
                status_data = {
                    "type": "status_update",
                    "payload": {
                        "timestamp": datetime.now().isoformat(),
                        "client_count": len(connected_clients),
                        "system_status": "operational"
                    }
                }
                
                # Send to all clients
                for client in connected_clients:
                    try:
                        await client.send(json.dumps(status_data))
                    except Exception as e:
                        logger.error(f"Error sending status to client: {e}")
                        
            except Exception as e:
                logger.error(f"Error in status update: {e}")
                
        await asyncio.sleep(30)  # Update every 30 seconds

def shutdown_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {sig}, shutting down...")
    sys.exit(0)

async def main():
    global server
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    
    try:
        # Create dirs
        os.makedirs("pids", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        
        # Kill any existing server on port 8765
        if sys.platform == "win32":
            subprocess.run("taskkill /F /FI \"LOCALPORT eq 8765\" 2>nul", shell=True)
        else:
            subprocess.run("lsof -ti:8765 | xargs kill -9 2>/dev/null || true", shell=True)
        
        # Import websockets here
        import websockets
        
        port = 8765
        host = "localhost"
        
        # Start the server
        server = await websockets.serve(handler, host, port)
        
        # Create PID file
        with open('pids/legacy_compat_server.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        # Start status update task
        asyncio.create_task(send_periodic_updates())
        
        # Log information
        logger.info(f"WebSocket server started on ws://{host}:{port}")
        print(f"WebSocket server running at ws://{host}:{port}")
        print(f"Press Ctrl+C to stop the server")
        
        # Keep running forever
        await asyncio.Future()
        
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        print("\nServer stopped by user")
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        sys.exit(1)