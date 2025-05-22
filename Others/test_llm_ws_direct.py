#!/usr/bin/env python3
"""
Direct test script for LLM WebSocket server
This will try to connect directly to the LLM service and send a request
"""
import asyncio
import websockets
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_direct_llm')

# LLM WebSocket URL
LLM_URL = "ws://localhost:8770"

async def test_llm_connection():
    """Test direct connection to LLM service"""
    try:
        logger.info(f"Connecting to LLM service at {LLM_URL}...")
        async with websockets.connect(LLM_URL, ping_interval=None) as ws:
            logger.info("Connected to LLM service!")
            
            # Wait for welcome message
            welcome = await ws.recv()
            logger.info(f"Received welcome message: {welcome}")
            
            # Send LLM request
            request = {
                "type": "llm_request",
                "payload": {
                    "query": "Hello, can you give me a quick response to test if you're working?"
                }
            }
            
            logger.info(f"Sending request: {request}")
            await ws.send(json.dumps(request))
            
            # Wait for response
            logger.info("Waiting for response...")
            response = await asyncio.wait_for(ws.recv(), timeout=30.0)
            
            # Parse and display response
            logger.info(f"Received response: {response}")
            response_data = json.loads(response)
            
            if 'content' in response_data:
                logger.info(f"LLM response: {response_data['content']}")
                return True
            else:
                logger.error(f"Unexpected response format: {response_data}")
                return False
            
    except Exception as e:
        logger.error(f"Error testing LLM connection: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_llm_connection())