#!/usr/bin/env python3
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

async def test_llm_request():
    """Test sending an LLM request to the backend server and getting a response."""
    uri = "ws://localhost:8765"
    logger.info(f"Attempting to connect to {uri}...")
    
    try:
        async with websockets.connect(uri, ping_interval=None, close_timeout=5) as websocket:
            logger.info(f"Successfully connected to {uri}")
            
            # Step 1: Register as overlay_chat client
            register_message = {
                "type": "register",
                "payload": {
                    "client_type": "overlay_chat",
                    "client_id": "test_overlay",
                    "version": "1.0.0"
                }
            }
            
            logger.info(f"Sending registration message: {register_message}")
            await websocket.send(json.dumps(register_message))
            logger.info("Registration message sent")
            
            # Wait for registration response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                logger.info(f"Registration response: {response}")
            except asyncio.TimeoutError:
                logger.warning("No registration response received, continuing anyway")
            
            # Step 2: Send status request to verify connection
            status_request = {
                "type": "status_request",
                "payload": {
                    "timestamp": time.time()
                }
            }
            
            logger.info(f"Sending status request: {status_request}")
            await websocket.send(json.dumps(status_request))
            
            # Wait for status response
            try:
                status_response = await asyncio.wait_for(websocket.recv(), timeout=5)
                logger.info(f"Status response: {status_response}")
            except asyncio.TimeoutError:
                logger.warning("No status response received, continuing anyway")
            
            # Step 3: Send LLM request
            llm_request = {
                "type": "llm_request",
                "payload": {
                    "query": "Show me some examples",
                    "timestamp": time.time()
                }
            }
            
            logger.info(f"Sending LLM request: {llm_request}")
            await websocket.send(json.dumps(llm_request))
            logger.info("LLM request sent")
            
            # Step 4: Wait for responses with a longer timeout (LLM might be slow)
            # Continue receiving responses until we get an LLM response or timeout
            try:
                logger.info("Waiting for LLM response (this may take up to 60 seconds)...")
                
                # Keep track of if we found a valid LLM response
                found_llm_response = False
                start_time = time.time()
                timeout = 60  # Total timeout for the whole process
                
                # Try to receive multiple responses until we find an LLM response or timeout
                while time.time() - start_time < timeout and not found_llm_response:
                    try:
                        # Calculate remaining time
                        remaining_time = timeout - (time.time() - start_time)
                        if remaining_time <= 0:
                            break
                            
                        # Wait for next response with the remaining timeout
                        response = await asyncio.wait_for(websocket.recv(), timeout=remaining_time)
                        logger.info(f"Received response: {response[:200]}...")
                        
                        # Parse and validate response
                        response_data = json.loads(response)
                        response_type = response_data.get("type", "unknown")
                        
                        # Check if we have an LLM-related response
                        if response_type in ["query_response", "llm_response"]:
                            logger.info(f"✅ Found LLM response type: {response_type}")
                            
                            # Extract and display the actual content
                            payload = response_data.get("payload", {})
                            if "response" in payload:
                                content = payload["response"]
                                logger.info(f"✅ Response content found: {content[:150]}...")
                                found_llm_response = True
                            elif "content" in payload:
                                content = payload["content"]
                                logger.info(f"✅ Response content found: {content[:150]}...")
                                found_llm_response = True
                            else:
                                logger.warning("❌ No content found in response payload")
                                logger.info(f"Full payload: {payload}")
                        else:
                            logger.info(f"Received non-LLM response type: {response_type}")
                            logger.info(f"Continuing to wait for LLM response... (remaining time: {remaining_time:.1f}s)")
                    
                    except asyncio.TimeoutError:
                        logger.warning("Timeout waiting for response")
                        break
                    except Exception as e:
                        logger.error(f"Error processing response: {e}")
                        # Continue to next response
                
                if found_llm_response:
                    logger.info("✅ Successfully completed LLM request test!")
                else:
                    logger.error("❌ Did not receive a valid LLM response after multiple attempts")
                    
            except asyncio.TimeoutError:
                logger.error("❌ Timeout waiting for any response")
            except Exception as e:
                logger.error(f"❌ Error in response processing loop: {e}")
                
    except Exception as e:
        logger.error(f"❌ Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(test_llm_request())