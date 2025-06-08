#!/usr/bin/env python3
"""
Test if notifications are displayed properly in the overlay
after using the WebSocket proxy to format them correctly.

This test connects to the proxy at port 8766 and sends a notification
message that should be displayed in the overlay.
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
        logging.FileHandler('logs/websocket/overlay_notification_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("overlay_notification_test")

# Proxy connection settings
PROXY_PORT = 8766

async def send_notification():
    """Send a test notification through the proxy"""
    try:
        logger.info(f"Connecting to proxy at ws://localhost:{PROXY_PORT}")
        async with websockets.connect(f"ws://localhost:{PROXY_PORT}") as ws:
            logger.info("Connected to proxy")
            
            # Wait for welcome message
            welcome = await ws.recv()
            logger.info(f"Received welcome: {welcome}")
            
            # Create a test notification in the original format
            notification = {
                "type": "do_button_notification",
                "content": {
                    "message": "🔔 This is a test notification from the fixed proxy! Click a button to confirm it's working.",
                    "buttons": [
                        {"text": "It works! 👍", "value": "success"},
                        {"text": "Not working 👎", "value": "failure"}
                    ]
                },
                "importance": "high",
                "plan_id": f"test_notification_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat()
            }
            
            # Send the notification
            await ws.send(json.dumps(notification))
            logger.info(f"Sent notification: {notification}")
            
            # Wait for acknowledgment
            for _ in range(3):
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=5)
                    logger.info(f"Received response: {response}")
                except asyncio.TimeoutError:
                    logger.warning("No response received within timeout")
                    break
            
            logger.info("Notification test completed")
            
    except Exception as e:
        logger.error(f"Error in send_notification: {e}")
        return False
    
    return True

if __name__ == "__main__":
    logger.info("Starting overlay notification test")
    success = asyncio.run(send_notification())
    if success:
        logger.info("✅ Test completed - Check if notification appeared in overlay")
        print("\n✅ Test completed - Please check if notification appeared in overlay!")
        sys.exit(0)
    else:
        logger.error("❌ Test failed")
        print("\n❌ Test failed - Please check logs for details")
        sys.exit(1)