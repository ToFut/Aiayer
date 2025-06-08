#!/usr/bin/env python3
"""
Send a direct notification to the DO button server
This script will send a notification to the overlay chat in the exact format
expected by the DO button server
"""

import asyncio
import json
import logging
import websockets
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/do_button_notification.log')
    ]
)
logger = logging.getLogger("do_button_notification")

# Message content from command line arguments
title = "Memory Trigger"
message = "This is a memory trigger notification. Did you see this in the overlay?"
if len(sys.argv) > 1:
    title = sys.argv[1]
if len(sys.argv) > 2:
    message = sys.argv[2]

async def send_direct_notification():
    """Send a direct notification to the overlay"""
    # WebSocket URI
    ws_uri = "ws://localhost:8765"
    
    try:
        logger.info(f"Connecting to DO button server at {ws_uri}")
        
        async with websockets.connect(ws_uri) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            logger.info(f"Received welcome: {welcome}")
            
            # Create DO button message in the format expected by the server
            session_id = f"memory_trigger_{int(datetime.now().timestamp())}"
            test_message = {
                "type": "do_button",
                "action": "display",
                "content": {
                    "title": title,
                    "message": message,
                    "buttons": [
                        {
                            "id": "do_it",
                            "text": "Yes, I See It!",
                            "type": "primary"
                        },
                        {
                            "id": "dismiss",
                            "text": "No, Not Visible",
                            "type": "secondary"
                        }
                    ]
                },
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # Send message
            await websocket.send(json.dumps(test_message))
            logger.info("✅ Sent DO button notification")
            
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
    logger.info("🚀 Starting DO button notification test")
    
    success = await send_direct_notification()
    
    if success:
        logger.info("✅ Test completed successfully")
    else:
        logger.error("❌ Test failed")
        
if __name__ == "__main__":
    asyncio.run(main())