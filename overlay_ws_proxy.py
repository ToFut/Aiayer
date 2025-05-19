#!/usr/bin/env python
"""
WebSocket Proxy Server

This server acts as a proxy between the Tauri application and the backend server.
It handles message forwarding and connection management.
"""

import asyncio
import json
import logging
import websockets
import argparse
from typing import Dict, Set, Optional
from websockets.server import WebSocketServerProtocol

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ws_proxy")

# Store connected clients
connected_clients: Set[WebSocketServerProtocol] = set()

async def handle_client(websocket: WebSocketServerProtocol, path: str):
    """Handle a client connection."""
    try:
        # Add client to set
        connected_clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(connected_clients)}")
        
        # Keep connection alive and handle messages
        async for message in websocket:
            try:
                # Try to parse as JSON
                data = json.loads(message)
                logger.info(f"Received message: {data}")
                
                # Process the message
                response = {
                    "type": "response",
                    "status": "success",
                    "data": data
                }
                
                # Send response
                await websocket.send(json.dumps(response))
                
            except json.JSONDecodeError:
                logger.warning(f"Received non-JSON message: {message}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
                
    except websockets.exceptions.ConnectionClosed:
        logger.info("Client connection closed")
    except Exception as e:
        logger.error(f"Error handling client: {e}")
    finally:
        # Remove client from set
        connected_clients.remove(websocket)
        logger.info(f"Client disconnected. Total clients: {len(connected_clients)}")

async def forward_messages(source: WebSocketServerProtocol,
                         destination: WebSocketServerProtocol,
                         direction: str):
    """Forward messages between two WebSocket connections."""
    try:
        async for message in source:
            try:
                # Log the message
                logger.info(f"Forwarding {direction} message: {message}")
                
                # Forward the message
                await destination.send(message)
                
            except websockets.exceptions.ConnectionClosed:
                logger.info(f"{direction} connection closed")
                break
            except Exception as e:
                logger.error(f"Error forwarding {direction} message: {e}")
                break
                
    except Exception as e:
        logger.error(f"Error in {direction} forward loop: {e}")

async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='WebSocket Proxy Server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8765, help='Port to bind to')
    args = parser.parse_args()
    
    try:
        # Start the server
        server = await websockets.serve(
            handle_client,
            args.host,
            args.port,
            ping_interval=20,
            ping_timeout=60,
            close_timeout=10
        )
        
        logger.info(f"WebSocket proxy server started on ws://{args.host}:{args.port}")
        logger.info("Waiting for connections...")
        
        # Keep the server running until cancelled
        await asyncio.Future()
        
    except asyncio.CancelledError:
        logger.info("Server shutdown requested")
        # Clean up any remaining connections
        for client in connected_clients:
            try:
                await client.close(1000, "Server shutdown")
            except Exception as e:
                logger.error(f"Error closing client connection: {e}")
        logger.info("Server shutdown complete")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}") 