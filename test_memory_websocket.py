#!/usr/bin/env python3
"""
Test WebSocket Client for Memory Test Server
"""

import asyncio
import json
import logging
import websockets
import time
import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_memory_websocket.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("test_client")

async def test_memory_websocket():
    """Test connection to memory websocket server"""
    uri = "ws://localhost:8769"
    logger.info(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Wait for welcome message
            response = await websocket.recv()
            logger.info(f"Received welcome: {response}")
            
            # Send ping message
            logger.info("Sending ping message...")
            await websocket.send(json.dumps({
                "type": "ping"
            }))
            
            # Wait for pong response
            response = await websocket.recv()
            logger.info(f"Received pong: {response}")
            
            # Send get_system_stats message
            logger.info("Sending get_system_stats message...")
            await websocket.send(json.dumps({
                "type": "get_system_stats"
            }))
            
            # Wait for stats response
            response = await websocket.recv()
            logger.info(f"Received stats: {response}")
            
            # Test adding a memory
            logger.info("Sending add_memory message...")
            await websocket.send(json.dumps({
                "type": "add_memory",
                "content": f"Test memory from test client at {datetime.datetime.now().isoformat()}",
                "source": "test_client",
                "tags": ["test", "websocket", "debug"]
            }))
            
            # Wait for add memory response
            response = await websocket.recv()
            logger.info(f"Received add memory response: {response}")
            
            # Test searching memory
            logger.info("Sending search_memory message...")
            await websocket.send(json.dumps({
                "type": "search_memory",
                "query": "test client websocket",
                "top_k": 5,
                "min_similarity": 0.1
            }))
            
            # Wait for search response
            response = await websocket.recv()
            logger.info(f"Received search response: {response[:200]}...")
            
            logger.info("Test completed successfully")
            
    except Exception as e:
        logger.error(f"Error connecting to WebSocket server: {e}")

if __name__ == "__main__":
    asyncio.run(test_memory_websocket())