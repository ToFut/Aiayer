#!/usr/bin/env python3
"""
Test Script to verify the notification message formats in the overlay.
This script sends different notification formats to check which ones are properly displayed.
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
logger = logging.getLogger("notification_format_test")

# WebSocket connection info
WS_URI = "ws://localhost:8765"  # Primary WebSocket server

async def test_notification_formats():
    """Test different notification message formats"""
    try:
        # Step 1: Connect to WebSocket server
        logger.info(f"Connecting to WebSocket server at {WS_URI}")
        async with websockets.connect(WS_URI, ping_interval=5, ping_timeout=20) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            logger.info(f"Received welcome: {welcome[:100]}")
            
            # Step 2: Send a series of test notifications with different formats
            
            # Generate a plan ID to use consistently
            plan_id = f"test_plan_{int(time.time())}"
            
            # Test Format 1: Simple suggestion with type: suggestion
            logger.info("Sending Format 1: Simple suggestion with type: suggestion")
            message1 = {
                "type": "suggestion",
                "response": "This is a test suggestion (Format 1)",
                "buttons": [
                    {
                        "id": "do_it",
                        "text": "Yes, do it",
                        "type": "primary"
                    },
                    {
                        "id": "dismiss",
                        "text": "No thanks",
                        "type": "secondary"
                    }
                ],
                "importance": "high",
                "play_sound": True
            }
            
            await websocket.send(json.dumps(message1))
            logger.info("Format 1 sent, waiting 5 seconds...")
            await asyncio.sleep(5)
            
            # Test Format 2: SUGGEST mode with notification flag
            logger.info("Sending Format 2: SUGGEST mode with notification flag")
            message2 = {
                "mode": "SUGGEST",
                "notification": True,
                "data": {
                    "response": "This is a test suggestion (Format 2)",
                    "buttons": [
                        {
                            "id": "do_it",
                            "text": "Yes, do it",
                            "type": "primary"
                        },
                        {
                            "id": "dismiss",
                            "text": "No thanks",
                            "type": "secondary"
                        }
                    ],
                    "importance": "high"
                },
                "play_sound": True
            }
            
            await websocket.send(json.dumps(message2))
            logger.info("Format 2 sent, waiting 5 seconds...")
            await asyncio.sleep(5)
            
            # Test Format 3: do_button with action:display
            logger.info("Sending Format 3: do_button with action:display")
            message3 = {
                "type": "do_button",
                "action": "display",
                "plan_id": plan_id,
                "content": {
                    "title": "Test DO Button",
                    "message": "This is a test suggestion (Format 3)",
                    "buttons": [
                        {
                            "id": "do_it",
                            "text": "Yes, do it",
                            "type": "primary"
                        },
                        {
                            "id": "dismiss",
                            "text": "No thanks",
                            "type": "secondary"
                        }
                    ]
                },
                "notification": True,
                "play_sound": True,
                "importance": "high"
            }
            
            await websocket.send(json.dumps(message3))
            logger.info("Format 3 sent, waiting 5 seconds...")
            await asyncio.sleep(5)
            
            # Test Format 4: Combined format with both suggestion and notification keys
            logger.info("Sending Format 4: Combined format")
            message4 = {
                "type": "suggestion",
                "mode": "SUGGEST",
                "notification": True,
                "response": "This is a test suggestion (Format 4)",
                "buttons": [
                    {
                        "id": "do_it",
                        "text": "Yes, do it",
                        "type": "primary"
                    },
                    {
                        "id": "dismiss",
                        "text": "No thanks",
                        "type": "secondary"
                    }
                ],
                "importance": "high",
                "play_sound": True
            }
            
            await websocket.send(json.dumps(message4))
            logger.info("Format 4 sent, waiting 5 seconds...")
            await asyncio.sleep(5)
            
            # Test Format 5: Using the agent_confirmation format directly
            logger.info("Sending Format 5: agent_confirmation format")
            message5 = {
                "type": "agent_confirmation",
                "action": "CONFIRM",
                "plan_id": plan_id,
                "content": "This is a test suggestion (Format 5)",
                "buttons": [
                    {
                        "id": "execute",
                        "text": "Yes, execute",
                        "type": "primary"
                    },
                    {
                        "id": "dismiss",
                        "text": "No thanks",
                        "type": "secondary"
                    }
                ],
                "notification": True,
                "play_sound": True,
                "importance": "high"
            }
            
            await websocket.send(json.dumps(message5))
            logger.info("Format 5 sent, waiting 5 seconds...")
            await asyncio.sleep(5)
            
            logger.info("All test formats sent. Check the overlay to see which ones displayed correctly.")
            logger.info("Test completed. You can now close this script.")
            
    except Exception as e:
        logger.error(f"Error in test_notification_formats: {e}")
        return False

async def main():
    """Run the test"""
    await test_notification_formats()
    
    logger.info("\n===== TEST COMPLETED =====")
    logger.info("Verify which notification formats were properly displayed in the overlay")
    logger.info("This information will help determine the correct format to use")

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