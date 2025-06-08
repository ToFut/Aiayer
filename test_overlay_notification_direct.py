#!/usr/bin/env python3
"""
Test if notifications are displayed properly in the overlay
by sending directly to the proxy at port 8766.

This test connects to port 8766 and sends a test notification.
"""

import asyncio
import json
import logging
import sys
import websockets
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/websocket/overlay_notification_direct.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("overlay_notification_direct")

# Connection settings
PROXY_PORT = 8766

async def send_direct_notification():
    """Send a test notification directly to the proxy"""
    try:
        logger.info(f"Connecting to proxy at ws://localhost:{PROXY_PORT}")
        async with websockets.connect(f"ws://localhost:{PROXY_PORT}") as ws:
            logger.info("Connected to proxy")
            
            # Wait for welcome message
            welcome = await ws.recv()
            logger.info(f"Received welcome: {welcome}")
            
            # Create a test notification in the suggestion format that overlay expects
            notification = {
                "type": "suggestion",
                "response": "🔔 DIRECT TEST: This notification should appear in the overlay. Please click a button if you see this message.",
                "buttons": [
                    {"text": "✅ I see it!", "value": "success"},
                    {"text": "❌ Not working", "value": "failure"}
                ],
                "importance": "high",
                "play_sound": True,
                "plan_id": f"direct_test_{datetime.now().timestamp()}"
            }
            
            # Send the notification
            await ws.send(json.dumps(notification))
            logger.info(f"Sent direct notification: {notification}")
            
            # Wait for any response (button click)
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=30)
                logger.info(f"Received response: {response}")
                logger.info("✅ SUCCESS: Overlay received and responded to notification!")
                return True
            except asyncio.TimeoutError:
                logger.warning("No response received within timeout (normal if no button was clicked)")
            
            logger.info("Direct notification test completed")
            
    except Exception as e:
        logger.error(f"Error in send_direct_notification: {e}")
        return False
    
    return True

if __name__ == "__main__":
    logger.info("Starting direct overlay notification test")
    success = asyncio.run(send_direct_notification())
    if success:
        logger.info("✅ Test completed - Check if notification appeared in overlay")
        print("\n✅ Test completed - Please check if notification appeared in overlay!")
        sys.exit(0)
    else:
        logger.error("❌ Test failed")
        print("\n❌ Test failed - Please check logs for details")
        sys.exit(1)