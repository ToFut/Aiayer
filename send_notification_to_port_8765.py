#!/usr/bin/env python3
"""
Send notification to port 8765 - The main port that overlay UI uses for doButton
"""

import asyncio
import websockets
import json
import sys
from datetime import datetime
import os
import logging

# Add parent directory to path for importing utility modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import standardized notification formatter
from utils.notification_formatter import format_notification, to_json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("send_notification_8765")

async def send_notification(message, importance="high", play_sound=True, buttons=None):
    """Send a notification to port 8765"""
    try:
        # Connect to port 8765
        async with websockets.connect("ws://localhost:8765", ping_interval=None) as websocket:
            # Wait for welcome message
            welcome = await websocket.recv()
            logger.info(f"Connected to WebSocket server. Welcome: {welcome}")
            
            # Create notification using standardized formatter
            notification = format_notification(
                message=message,
                buttons=buttons,
                importance=importance,
                play_sound=play_sound
            )
            
            # Send notification
            logger.info(f"Sending notification: {message}")
            await websocket.send(to_json(notification))
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                logger.info(f"Response: {response}")
                return True
            except asyncio.TimeoutError:
                logger.warning("No response received within timeout")
                return False
                
    except Exception as e:
        logger.error(f"Error: {e}")
        return False

async def main():
    """Main function"""
    # Get message from command line
    if len(sys.argv) > 1:
        message = sys.argv[1]
    else:
        message = "🔔 IMPORTANT TEST: This notification should appear in the overlay!"
    
    # Get importance from command line
    importance = "high"
    if len(sys.argv) > 2:
        importance = sys.argv[2]
    
    # Get play_sound flag from command line
    play_sound = True
    if len(sys.argv) > 3:
        play_sound = sys.argv[3].lower() in ["true", "yes", "1"]
    
    # Define standard buttons
    buttons = [
        {"text": "✅ Got it", "value": "understood", "style": "success"},
        {"text": "❌ Dismiss", "value": "dismiss", "style": "danger"}
    ]
    
    logger.info(f"Sending notification to port 8765:")
    logger.info(f"  Message: {message}")
    logger.info(f"  Importance: {importance}")
    logger.info(f"  Play sound: {play_sound}")
    
    success = await send_notification(message, importance, play_sound, buttons)
    
    if success:
        print("✅ Notification sent successfully!")
    else:
        print("❌ Failed to send notification!")

if __name__ == "__main__":
    asyncio.run(main())