#!/usr/bin/env python3
"""
WebSocket test script for button action messages.
Sends a button action directly to the WebSocket server.
"""

import asyncio
import json
import logging
import sys
import time
import websockets
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def send_button_action():
    try:
        # Connect to the WebSocket server
        uri = "ws://localhost:8767"
        logger.info(f"Connecting to WebSocket server at {uri}...")
        
        async with websockets.connect(uri) as websocket:
            # Generate a unique client ID
            client_id = f"test_client_{int(time.time())}"
            
            # First register with the server
            register_message = {
                "type": "register",
                "client_type": "test_client",
                "version": "1.0",
                "capabilities": ["button_actions"],
                "client_id": client_id
            }
            
            logger.info(f"Sending registration message: {register_message}")
            await websocket.send(json.dumps(register_message))
            
            # Wait for registration response
            response = await websocket.recv()
            logger.info(f"Received registration response: {response}")
            
            # Create a test plan ID
            plan_id = f"universal_test_plan_{int(time.time())}"
            
            # Send a button action message
            button_action = {
                "type": "button_action",
                "action": "DO",
                "plan_id": plan_id,
                "client_id": client_id,
                "timestamp": time.time() * 1000
            }
            
            logger.info(f"Sending button action: {button_action}")
            await websocket.send(json.dumps(button_action))
            
            # Wait for response(s)
            logger.info("Waiting for responses...")
            try:
                for _ in range(5):  # Try to get up to 5 messages
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    logger.info(f"Received response: {response}")
                    
                    # Check if this is a final response
                    try:
                        data = json.loads(response)
                        if data.get("type") in ["agent_execution_success", "agent_execution_error", "button_action_error"]:
                            break
                    except:
                        pass
            except asyncio.TimeoutError:
                logger.warning("Timed out waiting for more responses")
            
            # Done
            logger.info("WebSocket test completed")
            return True
            
    except Exception as e:
        logger.error(f"Error in WebSocket test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n🔍 Testing WebSocket button action message...\n")
    
    # Run test
    success = asyncio.run(send_button_action())
    
    print(f"\n{'✅' if success else '❌'} WebSocket test: {'PASSED' if success else 'FAILED'}\n")
    
    if success:
        print("🎉 WebSocket test completed!")
        print("Check the logs above to see if the button action was processed correctly.")
        print("If you see 'agent_execution_success', the execution path is working.")
    else:
        print("⚠️ WebSocket test failed. Check the error message above.")
    
    sys.exit(0 if success else 1)
