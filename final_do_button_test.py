#!/usr/bin/env python3
"""
Final DO Button Test

This script sends a simple plan to the DO button server to verify it's working correctly.
"""

import asyncio
import websockets
import json
import logging
import time
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/final_do_button_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FinalDoButtonTest")

async def test_do_button():
    """Test the DO button with a simple plan"""
    try:
        # Connect to DO button server - using port 8766 for the proxy
        uri = "ws://localhost:8766"
        async with websockets.connect(uri) as websocket:
            logger.info(f"✅ Connected to DO button server at {uri}")
            
            # Receive welcome message
            welcome = await websocket.recv()
            logger.info(f"✅ Received welcome message: {welcome[:100]}...")
            
            # Create a simple plan with proper format
            test_plan_id = f"test_plan_{int(time.time())}"
            test_plan = {
                "id": test_plan_id,
                "title": "Test Plan",
                "description": "This is a test plan for DO button verification",
                "steps": [
                    {
                        "id": f"{test_plan_id}_step_1",
                        "type": "notification",
                        "action": "notify",
                        "content": "DO button system is working correctly!",
                        "position": {"x": 500, "y": 300}
                    }
                ],
                "metadata": {
                    "created_at": time.time(),
                    "test_plan": True,
                    "session_id": f"test_session_{int(time.time())}"
                }
            }
            
            # Create DO button message
            message = {
                "type": "do_button",
                "plan_id": test_plan_id,
                "plan": test_plan,
                "session_id": test_plan["metadata"]["session_id"]
            }
            
            # Send the message
            await websocket.send(json.dumps(message))
            logger.info(f"✅ Sent DO button message with plan ID: {test_plan_id}")
            
            # Wait for responses
            responses = []
            try:
                # Collect responses for up to 5 seconds
                start_time = time.time()
                while time.time() - start_time < 5.0:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                        response_data = json.loads(response)
                        responses.append(response_data)
                        logger.info(f"✅ Received response: {response_data}")
                        
                        # If we get an error, log it and stop
                        if response_data.get("type") == "error":
                            logger.error(f"❌ Error response: {response_data}")
                            return False
                            
                        # If we got an agent_progress message, we're good
                        if response_data.get("type") == "agent_progress":
                            logger.info(f"✅ Received agent_progress message")
                            return True
                    except asyncio.TimeoutError:
                        # This is expected when we've waited long enough
                        continue
            except Exception as e:
                logger.error(f"❌ Error receiving responses: {e}")
                return False
                
            # Check for success
            progress_messages = [r for r in responses if r.get("type") == "agent_progress"]
            
            if progress_messages:
                logger.info(f"✅ Test passed! Received {len(progress_messages)} progress messages.")
                return True
            else:
                logger.error("❌ Test failed! No progress messages received.")
                return False
    except Exception as e:
        logger.error(f"❌ Error testing DO button: {e}")
        return False

async def main():
    """Main function"""
    logger.info("🚀 Starting Final DO Button Test")
    
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    result = await test_do_button()
    
    if result:
        logger.info("✅ Final DO Button Test PASSED!")
        logger.info("🎉 The DO button system is fully operational")
    else:
        logger.error("❌ Final DO Button Test FAILED!")
        
    logger.info("Test completed.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Test stopped by user")
    except Exception as e:
        logger.error(f"Error in test: {e}")
        import traceback
        logger.error(traceback.format_exc())