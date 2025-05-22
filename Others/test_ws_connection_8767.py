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
    """Test WebSocket connection to the bridge server on port 8767."""
    uri = "ws://localhost:8767"
    logger.info(f"Attempting to connect to {uri}...")
    
    try:
        async with websockets.connect(uri, ping_interval=None, close_timeout=2) as websocket:
            logger.info(f"Successfully connected to {uri}")
            
            # Send a test message
            test_message = {
                "type": "chat_message",
                "payload": {
                    "user_id": "test_user",
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
                    if response_json.get("type") == "chat_response":
                        logger.info("✅ Response type is 'chat_response'")
                        if "content" in response_json.get("payload", {}):
                            content = response_json["payload"]["content"]
                            logger.info(f"✅ Response content: {content[:200]}...")
                        else:
                            logger.warning("❌ Response does not contain content field")
                    else:
                        logger.warning(f"❌ Response type is not 'chat_response', got: {response_json.get('type')}")
                else:
                    logger.warning("❌ Response does not contain required fields")
            except asyncio.TimeoutError:
                logger.error("❌ Timeout waiting for response")
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())