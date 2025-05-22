#!/usr/bin/env python3
import asyncio
import websockets
import json
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

async def test_connection():
    """Test WebSocket connection to the enhanced backend server on port 8765."""
    uri = "ws://localhost:8765"
    logger.info(f"Attempting to connect to {uri}...")
    
    try:
        async with websockets.connect(uri, ping_interval=None, close_timeout=2) as websocket:
            logger.info(f"Successfully connected to {uri}")
            
            # Register as a client
            register_message = {
                "type": "register",
                "payload": {
                    "client_type": "overlay_chat",
                    "client_id": "test_client"
                }
            }
            
            logger.info(f"Sending registration message: {register_message}")
            await websocket.send(json.dumps(register_message))
            logger.info("Registration message sent")
            
            # Wait briefly for registration response
            try:
                reg_response = await asyncio.wait_for(websocket.recv(), timeout=5)
                logger.info(f"Registration response: {reg_response}")
            except asyncio.TimeoutError:
                logger.warning("No explicit registration response - continuing")
            
            # Send a test message
            test_message = {
                "type": "llm_request",
                "payload": {
                    "query": "Show me some examples",
                    "timestamp": "2025-05-19T08:45:00.000Z"
                }
            }
            
            logger.info(f"Sending test message: {test_message}")
            await websocket.send(json.dumps(test_message))
            logger.info("Test message sent")
            
            # Wait for the response with a timeout
            logger.info("Waiting for response...")
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=30)
                logger.info(f"Received response: {response[:200]}...")
                response_json = json.loads(response)
                
                # Check if we got a valid response
                if "type" in response_json and "payload" in response_json:
                    logger.info("✅ Received valid JSON response with type and payload")
                    if response_json.get("type") == "llm_response":
                        logger.info("✅ Response type is 'llm_response'")
                        if "content" in response_json.get("payload", {}):
                            content = response_json["payload"]["content"]
                            logger.info(f"✅ Response content: {content[:200]}...")
                        else:
                            logger.warning("❌ Response does not contain content field")
                    else:
                        logger.warning(f"❌ Response type is not 'llm_response', got: {response_json.get('type')}")
                else:
                    logger.warning("❌ Response does not contain required fields")
            except asyncio.TimeoutError:
                logger.error("❌ Timeout waiting for response")
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())