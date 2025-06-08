#!/usr/bin/env python3
"""
Simple test script to check the WebSocket connection to the memory test server
"""

import asyncio
import websockets
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ws_test")

async def test_connection():
    """Test the WebSocket connection to the memory test server"""
    uri = "ws://localhost:8769"
    
    try:
        logger.info(f"Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            logger.info("Connected!")
            
            # Wait for welcome message
            response = await websocket.recv()
            logger.info(f"Received: {response}")
            
            # Send a ping
            await websocket.send(json.dumps({
                "type": "ping"
            }))
            logger.info("Sent ping")
            
            # Receive pong
            response = await websocket.recv()
            logger.info(f"Received: {response}")
            
            # Get system stats
            await websocket.send(json.dumps({
                "type": "get_system_stats"
            }))
            logger.info("Sent get_system_stats")
            
            # Receive stats
            response = await websocket.recv()
            logger.info(f"Received: {response}")
            
            return True
    
    except Exception as e:
        logger.error(f"Connection error: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_connection())
    if result:
        print("\n✅ Connection test successful!")
    else:
        print("\n❌ Connection test failed!")