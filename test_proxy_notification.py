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

# WebSocket server details
PROXY_PORT = 8766  # Proxy bridge server port

async def send_via_proxy():
    """Send a notification through the proxy bridge server"""
    try:
        # Connect to proxy bridge
        logger.info(f"Connecting to proxy bridge on port {PROXY_PORT}...")
        async with websockets.connect(f"ws://localhost:{PROXY_PORT}") as ws:
            # Wait for welcome message
            welcome = await ws.recv()
            logger.info(f"Received welcome: {welcome}")
            
            # Create a suggestion notification with bright styling
            notification = {
                "type": "suggestion",
                "response": "⚠️ URGENT TEST NOTIFICATION ⚠️\n\nThis is a high-visibility test of the overlay notification system.",
                "buttons": [
                    {
                        "text": "✅ I can see this",
                        "value": "visible",
                        "style": "success"
                    },
                    {
                        "text": "❌ Not visible",
                        "value": "not_visible",
                        "style": "danger"
                    }
                ],
                "importance": "high",
                "play_sound": True,
                "plan_id": f"proxy_test_{uuid.uuid4()}",
                "timestamp": datetime.now().isoformat()
            }
            
            # Send the notification
            await ws.send(json.dumps(notification))
            logger.info(f"Sent notification via proxy: {notification['response'][:50]}...")
            
            # Wait for confirmation
            response = await ws.recv()
            logger.info(f"Received response: {response}")
            
            return True
    except Exception as e:
        logger.error(f"Error sending notification via proxy: {str(e)}")
        logger.error(f"Exception details:", exc_info=True)
        return False

async def main():
    logger.info("=== PROXY NOTIFICATION TEST ===")
    success = await send_via_proxy()
    logger.info(f"Notification sent via proxy: {success}")
    
    if success:
        logger.info("""
CHECK THE OVERLAY APP NOW!
- Make sure the overlay window is visible and in focus
- Look for a notification box with buttons
- If you don't see it, try clicking on the overlay window to bring it to focus
- The notification should have a yellow warning icon and buttons
""")
    else:
        logger.info("Failed to send notification. Check the logs for details.")

if __name__ == "__main__":
    asyncio.run(main())