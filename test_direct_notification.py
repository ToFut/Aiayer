#!/usr/bin/env python3
import asyncio
import websockets
import json
import uuid
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# WebSocket server details - connect directly to the overlay app
OVERLAY_PORT = 8765  # DO button server port that overlay connects to

async def send_direct_notification():
    """Send a notification directly to the overlay"""
    try:
        # Connect to DO button server that overlay uses
        logger.info(f"Connecting to overlay via DO button server on port {OVERLAY_PORT}...")
        async with websockets.connect(f"ws://localhost:{OVERLAY_PORT}") as ws:
            # Create a simple notification with buttons
            notification = {
                "type": "suggestion",
                "response": "🔔 DIRECT TEST NOTIFICATION\n\nThis is a direct test of the overlay notification system.",
                "buttons": [
                    {
                        "text": "👍 Visible",
                        "value": "visible",
                        "style": "success"
                    },
                    {
                        "text": "👎 Not Visible",
                        "value": "not_visible",
                        "style": "danger"
                    }
                ],
                "importance": "high",
                "play_sound": True,
                "plan_id": f"direct_test_{uuid.uuid4()}",
                "timestamp": datetime.now().isoformat()
            }
            
            # Send the notification
            await ws.send(json.dumps(notification))
            logger.info(f"Sent direct notification: {notification['response'][:50]}...")
            
            # Wait for response
            response = await ws.recv()
            logger.info(f"Received response: {response}")
            
            return True
    except Exception as e:
        logger.error(f"Error sending direct notification: {str(e)}")
        logger.error(f"Exception details:", exc_info=True)
        return False

async def main():
    logger.info("=== DIRECT NOTIFICATION TEST ===")
    success = await send_direct_notification()
    logger.info(f"Direct notification sent: {success}")
    
    if success:
        logger.info("Check the overlay app to see if the notification appears!")
    else:
        logger.info("Failed to send notification. Check the logs for details.")

if __name__ == "__main__":
    asyncio.run(main())