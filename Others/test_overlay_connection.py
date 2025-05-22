#!/usr/bin/env python3
"""
Test script to debug overlay connection issues with the LLM service

This script will:
1. Register as a client to the WebSocket server
2. Send periodic context updates
3. Print all received messages
"""
import asyncio
import json
import logging
import websockets
import uuid
from datetime import datetime
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("overlay_connection_test")

# WebSocket endpoint - same one used by the overlay
WS_URL = "ws://localhost:8765"

# Construct a client ID
CLIENT_ID = str(uuid.uuid4())

async def heartbeat(websocket):
    """Send periodic pings to keep the connection alive."""
    try:
        while True:
            # Send a ping message every 20 seconds
            ping_message = {
                "type": "ping",
                "payload": {
                    "timestamp": time.time()
                }
            }
            await websocket.send(json.dumps(ping_message))
            logger.info("Sent ping")
            await asyncio.sleep(20)
    except Exception as e:
        logger.error(f"Heartbeat error: {e}")

async def send_context_update(websocket):
    """Simulate sending context updates like the LLM context connector."""
    try:
        while True:
            # Send a context update every 10 seconds
            context_message = {
                "type": "context_update",
                "payload": {
                    "context": f"Test context update from {CLIENT_ID}",
                    "timestamp": datetime.now().isoformat()
                }
            }
            await websocket.send(json.dumps(context_message))
            logger.info("Sent context update")
            await asyncio.sleep(10)
    except Exception as e:
        logger.error(f"Context update error: {e}")

async def main():
    """Main function to run the test."""
    try:
        logger.info(f"Connecting to {WS_URL}...")
        
        # Connect to the WebSocket server
        async with websockets.connect(WS_URL) as websocket:
            logger.info(f"Connected to {WS_URL}")
            
            # Register as a LLM service (this is what the overlay expects)
            register_message = {
                "type": "register",
                "client_type": "llm",
                "version": "1.0.0",
                "capabilities": ["context", "chat"]
            }
            await websocket.send(json.dumps(register_message))
            logger.info(f"Sent registration message as LLM service")
            
            # Start background tasks
            heartbeat_task = asyncio.create_task(heartbeat(websocket))
            context_task = asyncio.create_task(send_context_update(websocket))
            
            # Main loop to process incoming messages
            try:
                while True:
                    message = await websocket.recv()
                    try:
                        data = json.loads(message)
                        logger.info(f"Received: {data['type']}")
                        
                        # If we get a ping, respond with a pong
                        if data['type'] == 'ping':
                            pong_message = {
                                "type": "pong",
                                "payload": {
                                    "timestamp": time.time()
                                }
                            }
                            await websocket.send(json.dumps(pong_message))
                            logger.info("Sent pong response")
                            
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON received: {message[:100]}...")
                        
            except websockets.exceptions.ConnectionClosed as e:
                logger.info(f"Connection closed: {e}")
            finally:
                # Cancel background tasks
                heartbeat_task.cancel()
                context_task.cancel()
                
    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    logger.info("Starting LLM service connection test")
    asyncio.run(main())