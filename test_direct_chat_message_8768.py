#!/usr/bin/env python3
"""
Test script to send direct chat messages to the fixed_bridge_server.py on port 8768.
This verifies we can send notifications to the correct WebSocket server that EnterpriseChatWidget connects to.
"""

import asyncio
import json
import logging
import sys
import websockets
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("test_direct_message")

# WebSocket connection info - USING CORRECT PORT 8768
WS_URI = "ws://localhost:8768"  # This matches EnterpriseChatWidget.svelte

async def send_test_message():
    """Connect to WebSocket server and send a test message"""
    try:
        # Connect to WebSocket server
        logger.info(f"Connecting to WebSocket server at {WS_URI}...")
        websocket = await websockets.connect(
            WS_URI,
            ping_interval=None,  # Disable ping to avoid compatibility issues
            max_size=10 * 1024 * 1024,  # 10MB max message size
        )
        
        logger.info("Connected to WebSocket server")
        
        # Receive welcome message
        welcome = await websocket.recv()
        logger.info(f"Received welcome: {welcome[:100]}...")
        
        # Generate a unique session ID
        session_id = str(uuid.uuid4())
        title = "Test Notification"
        message = "This is a test notification. Can you see this message in the chat widget?"
        
        # Create DO button message in the format expected by the server
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
                        "type": "primary",
                        "style": "success"
                    },
                    {
                        "id": "dismiss",
                        "text": "No, Not Visible",
                        "type": "secondary", 
                        "style": "danger"
                    }
                ]
            },
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send the message
        logger.info(f"Sending test message: {json.dumps(test_message)[:100]}...")
        await websocket.send(json.dumps(test_message))
        logger.info(f"✅ Sent test notification to chat overlay")
        
        # Wait for a response (optional)
        logger.info("Waiting for response...")
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=10)
            logger.info(f"Received response: {response[:100]}...")
        except asyncio.TimeoutError:
            logger.warning("No response received in 10 seconds")
        
        # Close the connection
        await websocket.close()
        logger.info("Connection closed")
        
        return True
    except Exception as e:
        logger.error(f"Error sending test message: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    """Main function"""
    logger.info("🚀 Starting test direct message to port 8768")
    
    success = await send_test_message()
    
    if success:
        logger.info("✅ Test completed successfully")
    else:
        logger.error("❌ Test failed")
        
    return success

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Test stopped by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        import traceback
        logger.error(traceback.format_exc())