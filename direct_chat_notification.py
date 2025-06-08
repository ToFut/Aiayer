#!/usr/bin/env python3
"""
Direct Chat Notification Test

This script bypasses the memory system and directly sends a notification 
to the chat interface via WebSocket to test if notifications are working.
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
logger = logging.getLogger("direct_notification")

# WebSocket connection info
WS_URI = "ws://localhost:8765"

async def send_direct_notification():
    """Send a direct notification to the chat interface"""
    try:
        logger.info(f"Connecting to WebSocket server at {WS_URI}")
        
        async with websockets.connect(WS_URI, ping_interval=5, ping_timeout=20) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Create a unique notification ID
            notification_id = str(uuid.uuid4())
            
            # Create a direct notification message
            notification = {
                "type": "notification",
                "id": notification_id,
                "timestamp": time.time(),
                "content": {
                    "title": "Direct Test Notification",
                    "message": "This is a direct test notification from the memory trigger system.",
                    "priority": "high",
                    "actions": [
                        {
                            "id": "do",
                            "text": "Do It",
                            "action": "execute"
                        },
                        {
                            "id": "dismiss",
                            "text": "Dismiss",
                            "action": "dismiss"
                        }
                    ],
                    "context": {
                        "notification_type": "test",
                        "source": "direct_test",
                        "timestamp": datetime.now().isoformat()
                    }
                }
            }
            
            # Send the notification
            await websocket.send(json.dumps(notification))
            logger.info(f"Sent direct notification with ID: {notification_id}")
            
            # Wait for response or confirmation
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                logger.info(f"Received response: {response[:100]}")
                return True
            except asyncio.TimeoutError:
                logger.warning("No response received within timeout")
                # This might still be OK if the server doesn't send responses
                return True
                
    except Exception as e:
        logger.error(f"Error sending direct notification: {e}")
        return False

async def send_suggest_message():
    """Send a direct suggestion message to the chat interface"""
    try:
        logger.info(f"Connecting to WebSocket server at {WS_URI}")
        
        async with websockets.connect(WS_URI, ping_interval=5, ping_timeout=20) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Create a unique message ID
            message_id = str(uuid.uuid4())
            
            # Create a suggest mode message
            suggest_message = {
                "type": "chat_message",
                "id": message_id,
                "mode": "suggest",
                "timestamp": time.time(),
                "message": "I notice you're browsing shopping content. Would you like help finding the best deals?",
                "user_id": "system",
                "session_id": f"test_session_{int(time.time())}",
                "actions": [
                    {
                        "id": "accept",
                        "text": "Yes, help me",
                        "action": "accept"
                    },
                    {
                        "id": "decline",
                        "text": "No thanks",
                        "action": "decline"
                    }
                ],
                "context": {
                    "source": "direct_test",
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # Send the message
            await websocket.send(json.dumps(suggest_message))
            logger.info(f"Sent suggest message with ID: {message_id}")
            
            # Wait for response or confirmation
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                logger.info(f"Received response: {response[:100]}")
                return True
            except asyncio.TimeoutError:
                logger.warning("No response received within timeout")
                # This might still be OK if the server doesn't send responses
                return True
                
    except Exception as e:
        logger.error(f"Error sending suggest message: {e}")
        return False

async def main():
    """Main function"""
    logger.info("🚀 Starting direct notification test")
    
    # Send a direct notification
    notification_sent = await send_direct_notification()
    if not notification_sent:
        logger.error("Failed to send direct notification")
    else:
        logger.info("Direct notification sent successfully")
    
    # Send a suggest message
    suggest_sent = await send_suggest_message()
    if not suggest_sent:
        logger.error("Failed to send suggest message")
    else:
        logger.info("Suggest message sent successfully")
    
    # Return overall success
    return notification_sent or suggest_sent

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        result = asyncio.run(main())
        if result:
            logger.info("✅ Direct notification test completed successfully")
            sys.exit(0)
        else:
            logger.error("❌ Direct notification test failed")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)