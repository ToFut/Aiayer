#!/usr/bin/env python3
"""
Test script to verify LLM registration with the WebSocket server.
"""
import asyncio
import json
import logging
import sys
import websockets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def register_as_llm():
    """Register as an LLM service with the WebSocket server."""
    uri = "ws://localhost:8765"
    
    try:
        logger.info(f"Connecting to WebSocket server at {uri}")
        async with websockets.connect(uri) as websocket:
            # Receive welcome message
            welcome = await websocket.recv()
            logger.info(f"Received welcome message: {welcome}")
            
            # Register as LLM service
            registration = {
                "type": "register",
                "client_type": "llm",
                "version": "1.0",
                "capabilities": ["context_aware_responses"]
            }
            
            logger.info(f"Sending registration: {registration}")
            await websocket.send(json.dumps(registration))
            
            # Wait for registration confirmation
            confirmation = await websocket.recv()
            logger.info(f"Received response: {confirmation}")
            
            # Keep the connection alive for a bit
            logger.info("Registered as LLM service. Keeping connection alive for 30 seconds...")
            await asyncio.sleep(30)
            
            logger.info("Test completed successfully")
    
    except Exception as e:
        logger.error(f"Error during test: {e}")
        return False
        
    return True

if __name__ == "__main__":
    logger.info("Starting LLM registration test")
    success = asyncio.run(register_as_llm())
    if success:
        logger.info("Test completed successfully")
        sys.exit(0)
    else:
        logger.error("Test failed")
        sys.exit(1)