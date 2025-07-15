#!/usr/bin/env python3
"""
Debug Agent Mode Response
See exactly what the agent mode is returning
"""

import asyncio
import json
import websockets
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_agent_mode():
    """Debug what agent mode is actually returning"""
    
    backend_uri = "ws://localhost:8767"
    max_retries = 10
    for attempt in range(max_retries):
        try:
            async with websockets.connect(backend_uri) as websocket:
                logger.info(f"Connected to backend on attempt {attempt+1}")
                # Register client
                register_msg = {
                    "type": "register",
                    "client_id": "debug_client",
                    "client_type": "test"
                }
                logger.info(f"Sending: {register_msg}")
                await websocket.send(json.dumps(register_msg))
                response = await websocket.recv()
                logger.info(f"Received: {response}")
                
                # Send agent mode request
                agent_request = {
                    "type": "chat_request",
                    "mode": "Agent",
                    "message": "Open SEGEV in Google",
                    "session_id": "debug_session"
                }
                logger.info(f"Sending agent request: {json.dumps(agent_request, indent=2)}")
                await websocket.send(json.dumps(agent_request))
                
                # Wait for the actual plan response (not registration confirmation)
                response = await websocket.recv()
                logger.info(f"Received: {response}")
                result = json.loads(response)
                
                # If we got registration confirmation, wait for the actual plan response
                if result.get('type') == 'registration_confirmed':
                    logger.info("Received registration confirmation, waiting for plan response...")
                    response = await websocket.recv()
                    logger.info(f"Received plan response: {response}")
                    result = json.loads(response)
                
                logger.info("=" * 60)
                logger.info("AGENT MODE RESPONSE DEBUG")
                logger.info("=" * 60)
                logger.info(f"Full response: {json.dumps(result, indent=2)}")
                logger.info("=" * 60)
                
                # Check specific fields
                logger.info(f"Type: {result.get('type')}")
                logger.info(f"Mode: {result.get('mode')}")
                logger.info(f"Success: {result.get('success')}")
                logger.info(f"Response length: {len(result.get('response', ''))}")
                logger.info(f"Response preview: {result.get('response', '')[:200]}...")
                
                # Check if it contains automation plan indicators
                response_text = result.get('response', '')
                has_plan = "AUTOMATION EXECUTION PLAN" in response_text
                has_execute = "🟢 EXECUTE" in response_text or "EXECUTE" in response_text
                has_steps = "Automation Steps" in response_text or "🚀" in response_text
                
                logger.info(f"Contains 'AUTOMATION EXECUTION PLAN': {has_plan}")
                logger.info(f"Contains 'EXECUTE' button: {has_execute}")
                logger.info(f"Contains automation steps: {has_steps}")
                
                if has_plan and has_execute and has_steps:
                    logger.info("✅ SUCCESS: Agent mode generated proper automation plan")
                else:
                    logger.info("❌ FAILURE: Agent mode did not generate proper automation plan")
                return
        except Exception as e:
            logger.error(f"Connection attempt {attempt+1} failed: {e}")
            time.sleep(2)
    logger.error(f"Failed to connect to backend after {max_retries} attempts.")

if __name__ == "__main__":
    asyncio.run(debug_agent_mode())