#!/usr/bin/env python3
"""
Debug notification display in overlay
This script tests sending notifications directly to the overlay chat widget
"""

import asyncio
import json
import logging
import websockets
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/debug_notification.log')
    ]
)
logger = logging.getLogger("debug_notification")

async def send_direct_notification():
    """Send a direct notification to the overlay"""
    # WebSocket URI
    ws_uri = "ws://localhost:8765"
    
    try:
        logger.info(f"Connecting to overlay WebSocket server at {ws_uri}")
        
        async with websockets.connect(ws_uri) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            logger.info(f"Received welcome: {welcome}")
            
            # Create direct message
            test_message = {
                "success": True,
                "response": "🔴 URGENT TEST NOTIFICATION: This is a test message. Can you see this in the overlay?",
                "mode": "SUGGEST",
                "processing_time": 0.5,
                "enterprise_validated": True,
                "buttons": [
                    {
                        "id": "yes_visible",
                        "text": "Yes, I can see it!",
                        "action": "accept",
                        "style": "success"
                    },
                    {
                        "id": "not_visible",
                        "text": "No, not visible",
                        "action": "dismiss",
                        "style": "danger"
                    }
                ],
                "interactive": True
            }
            
            # Send message
            await websocket.send(json.dumps(test_message))
            logger.info("✅ Sent direct test notification")
            
            # Wait for response
            try:
                logger.info("Waiting for response...")
                response = await asyncio.wait_for(websocket.recv(), timeout=30)
                logger.info(f"Received response: {response}")
                return True
            except asyncio.TimeoutError:
                logger.warning("No response received after 30 seconds")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    """Main function"""
    logger.info("🚀 Starting overlay notification debug test")
    
    success = await send_direct_notification()
    
    if success:
        logger.info("✅ Test completed successfully")
    else:
        logger.error("❌ Test failed")
        
if __name__ == "__main__":
    asyncio.run(main())