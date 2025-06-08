#!/usr/bin/env python3
"""
Simple test to check WebSocket connection and agent mode
"""

import asyncio
import json
import websockets
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_websocket():
    """Test WebSocket connection to backend"""
    
    uri = "ws://localhost:8767"
    
    try:
        logger.info(f"Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            logger.info("Connected successfully!")
            
            # Receive welcome message
            welcome = await websocket.recv()
            logger.info(f"Welcome message: {welcome}")
            
            # Register client
            register_msg = {
                "type": "register",
                "client_type": "test_script"
            }
            await websocket.send(json.dumps(register_msg))
            
            # Receive registration response
            reg_response = await websocket.recv()
            logger.info(f"Registration response: {reg_response}")
            
            # Send a simple request
            request = {
                "type": "request",
                "mode": "Agent",
                "query": "search for cats on google",
                "session_id": "test_session"
            }
            
            logger.info(f"Sending request: {json.dumps(request)}")
            await websocket.send(json.dumps(request))
            
            # Wait for response
            logger.info("Waiting for response...")
            response = await asyncio.wait_for(websocket.recv(), timeout=30)
            logger.info(f"Response received: {response}")
            
            return True
            
    except Exception as e:
        logger.error(f"Error during WebSocket test: {e}")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_websocket())
        if result:
            print("\n✅ WebSocket test successful!")
        else:
            print("\n❌ WebSocket test failed!")
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")