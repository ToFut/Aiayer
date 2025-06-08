#\!/usr/bin/env python3
"""
Ultra Simple WebSocket Echo Server

This is a bare-bones WebSocket server for testing connectivity.
It echoes back any message it receives.
"""

import asyncio
import websockets
import json
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

async def echo(websocket, path):
    """Simple echo handler that logs and echoes messages"""
    client_id = id(websocket)
    client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
    logging.info(f"Client connected: {client_info} (ID: {client_id})")
    
    # Send welcome message
    welcome = {
        "type": "welcome",
        "message": "Connected to Echo WebSocket Server",
        "client_id": client_id,
        "client_address": client_info
    }
    await websocket.send(json.dumps(welcome))
    logging.info(f"Sent welcome message to client {client_id}")
    
    try:
        async for message in websocket:
            logging.info(f"Received from {client_id}: {message}")
            
            # Try to parse as JSON
            try:
                data = json.loads(message)
                # Add echo field to the data
                data["echo"] = True
                data["server_timestamp"] = asyncio.get_event_loop().time()
                # Send it back
                await websocket.send(json.dumps(data))
                logging.info(f"Echoed JSON to {client_id}")
            except json.JSONDecodeError:
                # Not JSON, just echo as text
                await websocket.send(f"ECHO: {message}")
                logging.info(f"Echoed text to {client_id}")
                
    except websockets.exceptions.ConnectionClosed as e:
        logging.info(f"Client {client_id} disconnected: code={e.code}, reason='{e.reason}'")
    except Exception as e:
        logging.error(f"Error with client {client_id}: {str(e)}")
    finally:
        logging.info(f"Connection with client {client_id} closed")

async def main():
    # Start server on all interfaces (0.0.0.0) to make it accessible from other devices
    server = await websockets.serve(echo, "0.0.0.0", 8766)
    logging.info("WebSocket Echo Server running on ws://0.0.0.0:8766")
    
    # Print all ways to connect locally
    logging.info("Connect locally using:")
    logging.info("- ws://localhost:8766")
    logging.info("- ws://127.0.0.1:8766")
    
    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
    except Exception as e:
        logging.error(f"Server error: {str(e)}")
