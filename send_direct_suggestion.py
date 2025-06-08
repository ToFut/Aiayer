#!/usr/bin/env python3
"""
Send Direct Suggestion to Chat Overlay

This script sends a properly formatted suggestion message directly to the chat overlay.
"""

import asyncio
import json
import logging
import sys
import time
import uuid
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
logger = logging.getLogger("send_suggestion")

# WebSocket connection info
WS_URI = "ws://localhost:8765"

async def send_action_message():
    """Send a direct action suggestion to the chat interface"""
    try:
        logger.info(f"Connecting to WebSocket server at {WS_URI}")
        
        async with websockets.connect(WS_URI, ping_interval=5, ping_timeout=20) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            logger.info(f"Received welcome: {welcome[:100]}")
            
            # Create suggestion message (DO button format)
            message = {
                "type": "do_button",
                "action": "display",
                "content": {
                    "title": "Shopping Suggestion",
                    "message": "I noticed you're looking at a smartphone. Would you like me to help you compare prices?",
                    "buttons": [
                        {
                            "id": "do_it",
                            "text": "Yes, help me",
                            "type": "primary"
                        },
                        {
                            "id": "dismiss",
                            "text": "No thanks",
                            "type": "secondary"
                        }
                    ]
                }
            }
            
            # Alternate format - direct chat message (try both formats)
            chat_message = {
                "type": "chat_message",
                "mode": "SUGGEST",
                "message": "💡 Shopping Suggestion: I noticed you're looking at a smartphone. Would you like me to help you compare prices?",
                "user_id": "system",
                "session_id": f"suggestion_{int(time.time())}",
                "timestamp": datetime.now().isoformat(),
                "suggest_buttons": [
                    {
                        "id": "do_it",
                        "text": "Yes, help me",
                        "type": "primary"
                    },
                    {
                        "id": "dismiss",
                        "text": "No thanks",
                        "type": "secondary"
                    }
                ]
            }
            
            # First send the DO button message
            await websocket.send(json.dumps(message))
            logger.info(f"Sent DO button message")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                logger.info(f"Received response: {response[:100]}")
            except asyncio.TimeoutError:
                logger.warning("No response received within timeout for DO button message")
            
            # Wait a moment
            await asyncio.sleep(1)
            
            # Then try the chat message format
            await websocket.send(json.dumps(chat_message))
            logger.info(f"Sent direct chat message with suggestion")
            
            # Wait for response to chat message
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                logger.info(f"Received response to chat message: {response[:100]}")
                return True
            except asyncio.TimeoutError:
                logger.warning("No response received within timeout for chat message")
                return True
                
    except Exception as e:
        logger.error(f"Error sending action message: {e}")
        return False

async def main():
    """Main function"""
    logger.info("🚀 Sending direct suggestion to chat overlay")
    
    # Send action message
    success = await send_action_message()
    
    if success:
        logger.info("✅ Suggestion sent successfully")
        logger.info("Check the chat overlay for the suggestion")
    else:
        logger.error("❌ Failed to send suggestion")
        
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