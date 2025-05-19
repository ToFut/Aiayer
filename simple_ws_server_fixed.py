import asyncio
import websockets
import json
import logging
import os
import time
from datetime import datetime

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/fixed_ws.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('fixed_websocket')

# Connected clients
connected_clients = set()

# IMPORTANT: Handler must accept websocket AND path parameters
async def handler(websocket, path):
    """WebSocket connection handler with proper signature"""
    client_id = id(websocket)
    connected_clients.add(websocket)
    logger.info(f"Client {client_id} connected. Path: {path}")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome", 
            "message": "Welcome to the Aiayer system!",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Handle messages
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received message from client {client_id}: {data.get('type', 'unknown')}")
                
                # Echo back with confirmation
                response = {
                    "type": "response",
                    "originalType": data.get("type", "unknown"),
                    "message": f"Server received: {data.get('message', 'No message')}",
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send(json.dumps(response))
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {message[:100]}...")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
    
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Connection with client {client_id} closed: {e}")
    finally:
        connected_clients.remove(websocket)
        logger.info(f"Client {client_id} disconnected")

async def broadcast(message):
    """Broadcast a message to all connected clients"""
    if connected_clients:
        await asyncio.gather(
            *[client.send(json.dumps(message)) for client in connected_clients]
        )

async def heartbeat():
    """Send periodic heartbeat to clients"""
    while True:
        if connected_clients:
            heartbeat_msg = {
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat(),
                "active_connections": len(connected_clients)
            }
            await broadcast(heartbeat_msg)
            logger.debug(f"Heartbeat sent to {len(connected_clients)} clients")
        await asyncio.sleep(30)  # Send heartbeat every 30 seconds

async def main():
    """Main server function"""
    # Start heartbeat task
    heartbeat_task = asyncio.create_task(heartbeat())
    
    # Start server
    port = 8767
    server = await websockets.serve(handler, "localhost", port)
    logger.info(f"WebSocket server started on ws://localhost:{port}")
    
    # Save PID to file
    with open('pids/ws_server_8767.pid', 'w') as f:
        f.write(str(os.getpid()))
    
    # Keep server running
    await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
