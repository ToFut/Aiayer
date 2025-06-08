#\!/usr/bin/env python3
"""
Fixed WebSocket Echo Server
This server properly handles the websockets library signature
"""
import asyncio
import websockets
import json
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('echo_server')

async def echo(websocket):
    """Simple echo handler that logs and echoes messages"""
    client_id = id(websocket)
    client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
    logger.info(f"Client connected: {client_info} (ID: {client_id})")
    
    # Send welcome message
    welcome = {
        "type": "welcome",
        "message": "Connected to Echo WebSocket Server",
        "client_id": client_id,
        "client_address": client_info
    }
    await websocket.send(json.dumps(welcome))
    logger.info(f"Sent welcome message to client {client_id}")
    
    try:
        async for message in websocket:
            logger.info(f"Received from {client_id}: {message}")
            
            # Try to parse as JSON
            try:
                data = json.loads(message)
                # Add echo field to the data
                data["echo"] = True
                data["server_timestamp"] = asyncio.get_event_loop().time()
                # Send it back
                await websocket.send(json.dumps(data))
                logger.info(f"Echoed JSON to {client_id}")
            except json.JSONDecodeError:
                # Not JSON, just echo as text
                await websocket.send(f"ECHO: {message}")
                logger.info(f"Echoed text to {client_id}")
                
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Client {client_id} disconnected: code={e.code}, reason='{e.reason}'")
    except Exception as e:
        logger.error(f"Error with client {client_id}: {str(e)}")
    finally:
        logger.info(f"Connection with client {client_id} closed")

async def main():
    # Start server on port 8766
    server = await websockets.serve(echo, "0.0.0.0", 8766)
    logger.info("WebSocket Echo Server running on ws://0.0.0.0:8766")
    
    # Print all ways to connect locally
    logger.info("Connect locally using:")
    logger.info("- ws://localhost:8766")
    logger.info("- ws://127.0.0.1:8766")
    
    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
