#!/usr/bin/env python3
"""
Fixed Test Direct Chat Message to Overlay

This script sends a properly formatted chat message directly to the chat overlay,
using the exact format expected by EnterpriseChatWidget.svelte.
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
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("fixed_direct_chat_test")

# WebSocket connection info
WS_URI = "ws://localhost:8765"

async def send_direct_chat_message():
    """Send a direct chat message to the overlay in the exact format expected by EnterpriseChatWidget"""
    try:
        logger.info(f"Connecting to WebSocket server at {WS_URI}")
        
        async with websockets.connect(WS_URI, ping_interval=5, ping_timeout=20) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            logger.info(f"Received welcome: {welcome[:100]}")
            
            # Create direct chat message in the EXACT format expected by EnterpriseChatWidget handleBackendMessage function
            # After analyzing EnterpriseChatWidget.svelte, we found this is the correct format that should work
            message = {
                "success": True,
                "response": "💡 This is a direct notification message from the memory trigger service. Would you like some help with this task?",
                "mode": "SUGGEST",
                "processing_time": 0.5,
                "enterprise_validated": True,
                "buttons": [
                    {
                        "id": "accept_suggestion",
                        "text": "Yes, help me",
                        "action": "accept",
                        "style": "success"
                    },
                    {
                        "id": "dismiss_suggestion",
                        "text": "No thanks",
                        "action": "dismiss",
                        "style": "danger"
                    }
                ],
                "interactive": True
            }
            
            # Send the message
            await websocket.send(json.dumps(message))
            logger.info(f"Sent direct chat message to overlay using the exact format expected by EnterpriseChatWidget")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                logger.info(f"Received response: {response[:100]}")
                return True
            except asyncio.TimeoutError:
                logger.warning("No response received within timeout")
                return True
                
    except Exception as e:
        logger.error(f"Error sending chat message: {e}")
        return False

async def main():
    """Main function"""
    logger.info("🚀 Sending direct chat message to overlay with exact expected format")
    
    # Send direct chat message
    success = await send_direct_chat_message()
    
    if success:
        logger.info("✅ Direct chat message sent successfully")
        logger.info("Check the chat overlay for the message")
    else:
        logger.error("❌ Failed to send direct chat message")
        
    return success

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)