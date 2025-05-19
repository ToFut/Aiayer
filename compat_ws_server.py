#!/usr/bin/env python3
"""
Compatible WebSocket Server for Tauri overlay
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/compat_ws_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Track connected clients
connected = set()

# Define path handler function
def get_handler():
    # Simple handler function as closure to avoid issues with websockets library
    async def handler(websocket):
        """Handle WebSocket connections"""
        # Add to client set
        connected.add(websocket)
        client_id = id(websocket)
        logger.info(f"Client {client_id} connected")
        
        try:
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
                    msg_type = data.get('type', 'unknown')
                    logger.info(f"Received {msg_type} message from client {client_id}")
                    
                    # Handle connection established
                    if msg_type == 'connection_established':
                        await websocket.send(json.dumps({
                            "type": "server_ready",
                            "payload": {
                                "status": "connected",
                                "server_version": "1.0.0",
                                "features": ["sensor_data", "context_tracking"],
                                "timestamp": datetime.now().isoformat()
                            }
                        }))
                    
                    # Handle user queries (chat messages)
                    elif msg_type == 'user_interaction':
                        payload = data.get('payload', {})
                        
                        if payload.get('type') == 'query':
                            query = payload.get('query', '')
                            logger.info(f"User query: {query}")
                            
                            # Send a mock response
                            await websocket.send(json.dumps({
                                "type": "query_response",
                                "payload": {
                                    "response": f"You asked: '{query}'. This is a test response from the WebSocket server.",
                                    "source": "mock_data",
                                    "timestamp": datetime.now().isoformat()
                                }
                            }))
                    
                    # Echo back other messages
                    else:
                        await websocket.send(json.dumps({
                            "type": "echo",
                            "data": data,
                            "timestamp": datetime.now().isoformat()
                        }))
                
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from client {client_id}")
                except Exception as e:
                    logger.error(f"Error processing message from {client_id}: {e}")
        
        except Exception as e:
            logger.error(f"Error with client {client_id}: {e}")
        finally:
            connected.remove(websocket)
            logger.info(f"Client {client_id} disconnected")
    
    return handler

async def broadcast_status():
    """Send periodic status updates to all clients"""
    while True:
        if connected:
            try:
                status = {
                    "type": "status_update",
                    "payload": {
                        "client_count": len(connected),
                        "server_time": datetime.now().isoformat(),
                        "sensors": ["process", "screen", "file"],
                        "active": True
                    }
                }
                
                msg = json.dumps(status)
                await asyncio.gather(
                    *[client.send(msg) for client in connected],
                    return_exceptions=True
                )
            except Exception as e:
                logger.error(f"Error sending status: {e}")
        
        await asyncio.sleep(10)

async def main():
    """Main entry point"""
    try:
        os.makedirs("pids", exist_ok=True)
        
        # Kill any existing server on port 8765
        if sys.platform == "win32":
            os.system(f"taskkill /F /FI \"PID ne {os.getpid()}\" /FI \"LOCALPORT eq 8765\" 2>nul")
        else:
            os.system(f"lsof -ti:8765 | grep -v {os.getpid()} | xargs kill -9 2>/dev/null || true")
        
        host = "localhost"
        port = 8765
        
        # Import websockets here to avoid any module-level issues
        import websockets
        
        # Log websockets version for debugging
        import websockets as ws_module
        logger.info(f"Using websockets version: {ws_module.__version__}")
        
        # Use legacy serve API if needed or the current one
        logger.info(f"Starting WebSocket server on {host}:{port}")
        try:
            # Try the new API
            async with websockets.serve(get_handler(), host, port):
                # Save PID file
                with open('pids/compat_ws_server.pid', 'w') as f:
                    f.write(str(os.getpid()))
                
                logger.info(f"WebSocket server started on ws://{host}:{port}")
                print(f"WebSocket server running at ws://{host}:{port}")
                
                # Start status broadcast in background
                status_task = asyncio.create_task(broadcast_status())
                
                # Keep running
                await asyncio.Future()
        except Exception as e:
            logger.error(f"Error with new API: {e}, trying alternate method")
            # Fall back to older API
            server = await websockets.serve(get_handler(), host, port)
            
            # Save PID file
            with open('pids/compat_ws_server.pid', 'w') as f:
                f.write(str(os.getpid()))
            
            logger.info(f"WebSocket server started with alternate API on ws://{host}:{port}")
            print(f"WebSocket server running at ws://{host}:{port}")
            
            # Start status broadcast in background
            status_task = asyncio.create_task(broadcast_status())
            
            # Keep running
            await asyncio.Future()
    
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        return 1

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        print("Server stopped by user")
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        sys.exit(1)