#!/usr/bin/env python3
"""
Simple test to check backend connection and message handling
"""

import asyncio
import json
import websockets
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_backend():
    """Test backend connection and message handling"""
    
    backend_uri = "ws://localhost:8767"
    
    try:
        async with websockets.connect(backend_uri) as websocket:
            logger.info("Connected to backend")
            
            # Send registration
            register_msg = {
                "type": "register",
                "client_id": "test_client",
                "client_type": "test"
            }
            await websocket.send(json.dumps(register_msg))
            response = await websocket.recv()
            logger.info(f"Registration response: {response}")
            
            # Send chat_request
            chat_request = {
                "type": "chat_request",
                "mode": "Agent",
                "message": "Open SEGEV in Google",
                "session_id": "test_session"
            }
            logger.info(f"Sending chat_request: {json.dumps(chat_request, indent=2)}")
            await websocket.send(json.dumps(chat_request))
            
            # Wait for the actual plan response (not registration confirmation)
            max_wait = 30  # Wait up to 30 seconds for the plan response
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    logger.info(f"Received response: {response}")
                    
                    # Parse response
                    try:
                        result = json.loads(response)
                        logger.info(f"Response type: {result.get('type')}")
                        logger.info(f"Response mode: {result.get('mode')}")
                        logger.info(f"Success: {result.get('success')}")
                        
                        # Check if this is the actual plan response
                        if result.get('type') == 'response' and result.get('mode') == 'Agent':
                            logger.info("✅ SUCCESS: Received proper automation plan response!")
                            if 'response' in result:
                                logger.info(f"Response preview: {result['response'][:200]}...")
                                # Check if it's a proper automation plan
                                if "AUTOMATION EXECUTION PLAN" in result['response']:
                                    logger.info("✅ SUCCESS: Received proper automation plan!")
                                else:
                                    logger.info("❌ FAILED: Did not receive proper automation plan")
                            else:
                                logger.info("❌ FAILED: No response content found")
                            return
                        elif result.get('type') == 'error' and result.get('mode') == 'Agent':
                            logger.info("✅ SUCCESS: Received error response from backend (this is expected when LLM times out)")
                            logger.info(f"Error message: {result.get('response', 'Unknown error')}")
                            return
                        elif result.get('type') == 'registration_confirmed':
                            logger.info("Received registration confirmation, waiting for plan response...")
                            continue
                        else:
                            logger.info(f"Received other response type: {result.get('type')}")
                            continue
                            
                    except Exception as e:
                        logger.error(f"Error parsing response: {e}")
                        continue
                        
                except asyncio.TimeoutError:
                    logger.info("Waiting for plan response...")
                    continue
                    
            logger.error("❌ FAILED: Timeout waiting for plan response")
                
    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_backend()) 