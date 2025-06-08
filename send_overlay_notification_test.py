#!/usr/bin/env python3
"""
Simple test script to send notifications to the overlay via the DO button proxy.
This script sends direct notifications in the correct format to ensure they display properly.

Usage:
  python3 send_overlay_notification_test.py
  
The script will:
1. Connect to the DO button proxy (port 8766)
2. Send a notification in the exact format that the overlay expects
3. Verify if the notification was sent successfully
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
logger = logging.getLogger("notification_test")

# WebSocket connection info
PROXY_WS_URI = "ws://localhost:8766"  # Connect to proxy on port 8766

async def send_notification():
    """Send notification directly to the overlay via proxy"""
    try:
        logger.info(f"Connecting to proxy at {PROXY_WS_URI}")
        async with websockets.connect(PROXY_WS_URI, ping_interval=5, ping_timeout=20) as websocket:
            logger.info("Connected to proxy WebSocket")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            logger.info("Received welcome message from proxy")
            
            # Generate a unique notification ID
            notification_id = f"notification_{int(time.time())}"
            
            # Create notification message in EXACT format expected by the overlay
            notification = {
                "type": "suggestion",  # MUST be "suggestion" type
                "response": "This is a direct notification test. Please click a button to verify notifications are displaying correctly.",
                "buttons": [
                    {
                        "id": "confirm",
                        "text": "Yes, I See It",
                        "type": "primary"
                    },
                    {
                        "id": "dismiss",
                        "text": "Not Visible",
                        "type": "secondary"
                    }
                ],
                "importance": "high",
                "play_sound": True,
                "plan_id": notification_id
            }
            
            # Send the notification
            logger.info("Sending notification to overlay...")
            await websocket.send(json.dumps(notification))
            logger.info("Notification sent")
            
            # Wait for response (if any)
            logger.info("Waiting for response...")
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                logger.info(f"Received response: {response[:100]}...")
            except asyncio.TimeoutError:
                logger.info("No response received within timeout")
            
            # Send a second notification with extra fields to see if it displays
            logger.info("Sending second notification with different format...")
            notification2 = {
                "type": "suggestion",
                "mode": "SUGGEST",
                "notification": True,
                "response": "This is a second test notification with extra fields.",
                "data": {
                    "importance": "high",
                    "buttons": [
                        {
                            "id": "confirm",
                            "text": "Confirm Format 2",
                            "type": "primary"
                        }
                    ]
                },
                "play_sound": True
            }
            
            await websocket.send(json.dumps(notification2))
            logger.info("Second notification sent")
            
            # Wait again for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                logger.info(f"Received response: {response[:100]}...")
            except asyncio.TimeoutError:
                logger.info("No response received within timeout")
            
            logger.info("Test complete - Please check if the notifications appeared in the overlay")
            logger.info("If you can see the notifications, the fix is working correctly!")
            
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        return False
    
    return True

async def main():
    """Run the notification test"""
    logger.info("======= OVERLAY NOTIFICATION TEST =======")
    
    success = await send_notification()
    
    if success:
        logger.info("✅ Notifications sent successfully")
        logger.info("👀 Please check if they are visible in the overlay")
        logger.info("💡 Tip: Make sure the overlay is connected to ws://localhost:8766")
    else:
        logger.error("❌ Failed to send notifications")
        logger.error("Please check if the proxy is running")
    
    logger.info("========================================")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)