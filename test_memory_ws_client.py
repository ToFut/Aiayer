#!/usr/bin/env python3
"""
Test WebSocket client for memory test system
"""
import asyncio
import websockets
import json
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('test_memory_ws_client')

# WebSocket connection info
WS_URI = "ws://localhost:8769"

async def test_connection():
    """Test WebSocket connection to memory server"""
    try:
        logger.info(f"Connecting to {WS_URI}...")
        
        async with websockets.connect(WS_URI) as websocket:
            logger.info("Connected successfully!")
            
            # Receive welcome message
            response = await websocket.recv()
            logger.info(f"Received: {response}")
            
            # Send ping message
            logger.info("Sending ping message...")
            await websocket.send(json.dumps({
                "type": "ping"
            }))
            
            # Receive pong response
            response = await websocket.recv()
            logger.info(f"Received: {response}")
            
            # Add a test memory
            logger.info("Adding test memory...")
            await websocket.send(json.dumps({
                "type": "add_memory",
                "content": "This is a test memory from the WebSocket client",
                "source": "test",
                "tags": ["test", "websocket"]
            }))
            
            # Receive memory added response
            response = await websocket.recv()
            logger.info(f"Received: {response}")
            
            # Search for memories
            logger.info("Searching memories...")
            await websocket.send(json.dumps({
                "type": "search_memory",
                "query": "test memory websocket",
                "top_k": 5
            }))
            
            # Receive search results
            response = await websocket.recv()
            data = json.loads(response)
            logger.info(f"Received {len(data.get('results', []))} search results")
            
            logger.info("Test completed successfully!")
            return True
            
    except Exception as e:
        logger.error(f"Error: {e}")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(test_connection())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)