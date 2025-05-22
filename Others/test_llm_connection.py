#!/usr/bin/env python3
import asyncio
import websockets
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('llm_connection_test')

async def test_connection():
    """Test WebSocket connection to LLM service"""
    uri = "ws://localhost:8765"
    logger.info(f"Attempting to connect to LLM service at {uri}")
    
    try:
        async with websockets.connect(uri, ping_interval=None) as websocket:
            logger.info(f"Successfully connected to {uri}")
            
            # Send registration message
            message = {
                "type": "register",
                "payload": {
                    "client_type": "ui",
                    "version": "1.0.0",
                    "capabilities": ["chat", "context"]
                }
            }
            
            await websocket.send(json.dumps(message))
            logger.info(f"Sent registration message: {message}")
            
            # Wait for response
            response = await websocket.recv()
            logger.info(f"Received response: {response}")
            
            # Send a ping message
            ping_message = {
                "type": "ping",
                "payload": {
                    "timestamp": 0
                }
            }
            
            await websocket.send(json.dumps(ping_message))
            logger.info("Sent ping message")
            
            # Wait for response
            response = await websocket.recv()
            logger.info(f"Received response: {response}")
            
            logger.info("Connection test successful!")
            return True
    except Exception as e:
        logger.error(f"Connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting LLM connection test")
    asyncio.run(test_connection())