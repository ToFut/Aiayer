#!/usr/bin/env python3
"""
Test Script to verify the fixed DO button notification display.
This script sends notification messages through our fixed proxy to test
if they properly appear in the overlay.
"""

import asyncio
import json
import logging
import sys
import time
import websockets
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("do_button_notification_test")

# WebSocket connection info
PROXY_WS_URI = "ws://localhost:8766"  # Connect to our proxy server

async def test_fixed_notification():
    """Test the notification display with our fixed proxy"""
    try:
        # Step 1: Connect to proxy WebSocket server
        logger.info(f"Connecting to proxy WebSocket server at {PROXY_WS_URI}")
        async with websockets.connect(PROXY_WS_URI, ping_interval=5, ping_timeout=20) as websocket:
            logger.info("Connected to proxy WebSocket server")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            logger.info(f"Received welcome: {welcome[:100]}")
            
            # Step 2: Send a do_button notification that should be properly converted
            logger.info("Sending DO button notification through proxy...")
            
            # Generate a unique plan ID
            plan_id = f"test_plan_{int(time.time())}"
            
            notification = {
                "type": "do_button_notification",
                "plan_id": plan_id,
                "content": {
                    "message": "This is a test notification through the fixed proxy. If you can see this, the fix works!",
                    "buttons": [
                        {
                            "id": "execute",
                            "text": "Yes, Execute",
                            "type": "primary"
                        },
                        {
                            "id": "dismiss",
                            "text": "No, Thanks",
                            "type": "secondary"
                        }
                    ]
                },
                "importance": "high"
            }
            
            await websocket.send(json.dumps(notification))
            logger.info("DO button notification sent through proxy")
            
            # Step 3: Wait to see if we get a response
            try:
                logger.info("Waiting for response...")
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                logger.info(f"Received response: {response[:100]}")
            except asyncio.TimeoutError:
                logger.info("No response received within timeout period")
            
            # Step 4: Wait a bit to observe if the notification appears
            logger.info("Waiting 5 seconds for notification to be displayed...")
            await asyncio.sleep(5)
            
            # Step 5: Send a second notification in standard suggestion format as a comparison
            logger.info("Sending standard suggestion format for comparison...")
            
            suggestion = {
                "type": "suggestion",
                "response": "This is a standard suggestion message for comparison. Both should display!",
                "buttons": [
                    {
                        "id": "confirm",
                        "text": "Confirm",
                        "type": "primary"
                    },
                    {
                        "id": "cancel",
                        "text": "Cancel",
                        "type": "secondary"
                    }
                ],
                "importance": "high",
                "play_sound": True
            }
            
            await websocket.send(json.dumps(suggestion))
            logger.info("Standard suggestion sent")
            
            # Step 6: Wait again to see if we get a response
            try:
                logger.info("Waiting for response...")
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                logger.info(f"Received response: {response[:100]}")
            except asyncio.TimeoutError:
                logger.info("No response received within timeout period")
            
            # Step 7: Final wait to observe
            logger.info("Waiting 10 more seconds to observe both notifications...")
            await asyncio.sleep(10)
            
            logger.info("Test completed. Check the overlay to see if both notifications were displayed correctly.")
            
    except Exception as e:
        logger.error(f"Error in test_fixed_notification: {e}")
        return False

async def main():
    """Run the test"""
    await test_fixed_notification()
    
    logger.info("\n===== TEST COMPLETED =====")
    logger.info("Verify if the DO button notification and standard suggestion were properly displayed")
    logger.info("If both appeared, the fix is working correctly!")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)