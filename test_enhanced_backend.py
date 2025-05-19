#!/usr/bin/env python3
"""
Direct test for the enhanced backend server (port 8765)
This script directly sends an LLM request message formatted exactly as expected.
"""
import asyncio
import websockets
import json
import logging
import sys
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

async def test_backend_llm():
    """Test the enhanced backend server by directly sending an LLM request."""
    uri = "ws://localhost:8765"
    logger.info(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri, ping_interval=None, close_timeout=5) as websocket:
            logger.info(f"Connected to {uri}")
            
            # Wait for initial connection message
            response = await websocket.recv()
            logger.info(f"Initial response: {response}")
            
            # Send LLM request directly, no registration needed
            request = {
                "type": "llm_request", 
                "payload": {
                    "query": "Show me some examples of what you can do",
                    "timestamp": time.time()
                }
            }
            
            logger.info(f"Sending direct LLM request: {request}")
            await websocket.send(json.dumps(request))
            
            # Keep receiving messages until we get an LLM-related response
            start_time = time.time()
            timeout = 60
            
            while True:
                remaining = timeout - (time.time() - start_time)
                if remaining <= 0:
                    logger.error("Timeout waiting for response")
                    break
                    
                try:
                    logger.info(f"Waiting for response (remaining: {remaining:.1f}s)...")
                    response = await asyncio.wait_for(websocket.recv(), timeout=remaining)
                    
                    # Parse response
                    data = json.loads(response)
                    msg_type = data.get("type", "unknown")
                    
                    logger.info(f"Received message type: {msg_type}")
                    
                    # Check if we received the expected response
                    if msg_type in ["query_response", "llm_response"]:
                        logger.info(f"✅ Found LLM response: {response}")
                        
                        # Extract the response content
                        payload = data.get("payload", {})
                        if "response" in payload:
                            content = payload["response"]
                            logger.info(f"✅ Response content: {content[:200]}...")
                            break
                        else:
                            logger.warning("Response doesn't contain expected content field")
                    else:
                        logger.info(f"Received other message type: {msg_type}. Continuing to wait...")
                        
                except asyncio.TimeoutError:
                    logger.error("Timeout waiting for response")
                    break
                except Exception as e:
                    logger.error(f"Error processing response: {e}")
                    break
            
    except Exception as e:
        logger.error(f"Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(test_backend_llm())