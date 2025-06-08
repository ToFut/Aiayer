#!/usr/bin/env python3
"""
Test WebSocket client for memory trigger system
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
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('test_ws_client')

# WebSocket connection info
WS_URI = "ws://localhost:8765"

async def send_test_notification():
    """Send a test notification to WebSocket server"""
    try:
        logger.info(f"Connecting to WebSocket server at {WS_URI}")
        
        async with websockets.connect(WS_URI) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            logger.info(f"Received welcome: {welcome}")
            
            # Create test notification
            message = {
                "success": True,
                "response": "💡 Test Notification: This is a test notification from the memory trigger system.",
                "mode": "SUGGEST",
                "processing_time": 0.5,
                "enterprise_validated": True,
                "buttons": [
                    {
                        "id": "test_accept",
                        "text": "This Works!",
                        "action": "accept",
                        "style": "success"
                    },
                    {
                        "id": "test_dismiss",
                        "text": "Dismiss Test",
                        "action": "dismiss",
                        "style": "danger"
                    }
                ],
                "interactive": True
            }
            
            # Send the message
            await websocket.send(json.dumps(message))
            logger.info(f"✅ Sent test notification to server")
            
            # Wait for response
            response = await websocket.recv()
            logger.info(f"Received response: {response}")
            
            # Wait for user input
            logger.info("Check if the notification appears in the overlay. Press Enter to continue...")
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False

async def main():
    """Main function"""
    logger.info("🚀 Testing WebSocket notification")
    await send_test_notification()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)