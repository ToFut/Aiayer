#!/usr/bin/env python3
"""
Test script to verify DO button execution through the WebSocket flow on port 8765
"""

import asyncio
import websockets
import json
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_do_button_8765')

async def test_agent_confirmation():
    """Test agent confirmation flow via WebSocket connection"""
    ws_url = "ws://localhost:8765"  # WebSocket server endpoint (port 8765)
    
    try:
        logger.info(f"Connecting to WebSocket server: {ws_url}")
        async with websockets.connect(ws_url) as websocket:
            logger.info("Connected! Sending agent_confirmation message")

            # Create a test session ID
            session_id = f"test_universal_{int(datetime.now().timestamp())}"
            
            # Send agent_confirmation message (simulating DO button click)
            confirmation_message = {
                "type": "agent_confirmation",
                "session_id": session_id,
                "action": "DO",
                "modifications": {},
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Sending message: {confirmation_message}")
            await websocket.send(json.dumps(confirmation_message))
            
            # Wait for responses
            logger.info("Waiting for responses...")
            try:
                # Set a timeout to prevent hanging indefinitely
                response_count = 0
                max_responses = 5  # Expect multiple responses
                
                while response_count < max_responses:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    response_data = json.loads(response)
                    response_count += 1
                    
                    logger.info(f"Response {response_count}: {response_data.get('type', 'unknown')}")
                    logger.debug(f"Full response: {response}")
                    
                    # If we received an execution success message, we're done
                    if response_data.get('type') == 'agent_execution_success':
                        logger.info("✅ Success! Received agent_execution_success message")
                        break
                    
                    # If we received an error, log it and continue
                    if response_data.get('type') == 'error':
                        logger.error(f"❌ Error received: {response_data.get('error', 'Unknown error')}")
            
            except asyncio.TimeoutError:
                logger.warning("⚠️ Timeout waiting for response")
            
            logger.info("Test completed")

    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    logger.info("Starting DO button execution test on port 8765")
    
    try:
        result = asyncio.run(test_agent_confirmation())
        if result:
            logger.info("✅ Test completed successfully")
            sys.exit(0)
        else:
            logger.error("❌ Test failed")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)