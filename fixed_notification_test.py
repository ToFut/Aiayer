#!/usr/bin/env python3
"""
Fixed Notification Test - Sends notifications directly to the overlay UI
using the correct format expected by NextGenAppleChatWidget.svelte
"""

import asyncio
import json
import logging
import websockets
from datetime import datetime
import argparse
import os
import sys

# Add parent directory to path for importing utility modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import standardized notification formatter
from utils.notification_formatter import format_notification, to_json

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/fixed_notification_test.log')
    ]
)

logger = logging.getLogger(__name__)

async def send_notification(message, buttons=None, importance="high", play_sound=True):
    """Send a notification using the format that the NextGenAppleChatWidget expects"""
    
    if buttons is None:
        buttons = [
            {"text": "✅ Got it", "value": "understood", "style": "success"},
            {"text": "❌ Dismiss", "value": "dismiss", "style": "danger"}
        ]
    
    # Create notification using standardized formatter
    notification = format_notification(
        message=message,
        buttons=buttons,
        importance=importance,
        play_sound=play_sound
    )
    
    # Try multiple ports used in the system
    for port in [8765, 8766, 8767, 8768]:
        # Connect to each port and attempt notification
        # Try port 8765 first as it's the main port the overlay uses (from config.js)
        ws_url = f"ws://localhost:{port}"
        logger.info(f"Trying to connect to {ws_url}...")
        
        try:
            async with websockets.connect(ws_url, ping_interval=None, close_timeout=2.0) as ws:
                # Wait for welcome message
                try:
                    welcome = await asyncio.wait_for(ws.recv(), timeout=2.0)
                    logger.info(f"Connected! Welcome: {welcome}")
                    
                    # Send notification with standardized format
                    logger.info(f"Sending notification: {message}")
                    await ws.send(to_json(notification))
                    
                    # Wait for response
                    try:
                        response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                        logger.info(f"Response: {response}")
                        return True
                    except asyncio.TimeoutError:
                        logger.warning("No response received")
                except asyncio.TimeoutError:
                    logger.warning(f"No welcome message received from {ws_url}")
        except Exception as e:
            logger.error(f"Error connecting to {ws_url}: {e}")
    
    return False

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Send a notification to the overlay UI')
    parser.add_argument('message', nargs='?', help='The notification message')
    parser.add_argument('--sound', action='store_true', help='Play a sound with the notification')
    parser.add_argument('--importance', choices=['low', 'medium', 'high'], default='high', help='Notification importance')
    args = parser.parse_args()
    
    print("\n=== FIXED NOTIFICATION TEST ===\n")
    print("This script sends notifications directly to the overlay UI")
    print("using the standardized message format for the NextGenAppleChatWidget\n")
    
    message = args.message
    if not message:
        try:
            message = input("Enter notification message: ")
        except (EOFError, KeyboardInterrupt):
            message = "🔔 FIXED TEST: This notification should appear in the overlay!"
    
    if not message:
        message = "🔔 FIXED TEST: This notification should appear in the overlay!"
    
    print(f"\nSending notification: {message}")
    print(f"Importance: {args.importance}")
    print(f"Sound: {'Yes' if args.sound else 'No'}")
    
    # Define custom buttons
    buttons = [
        {"text": "✅ Show me", "value": "show", "style": "success"},
        {"text": "❓ More info", "value": "info", "style": "primary"},
        {"text": "❌ Dismiss", "value": "dismiss", "style": "danger"}
    ]
    
    success = await send_notification(
        message=message,
        buttons=buttons,
        importance=args.importance,
        play_sound=args.sound
    )
    
    if success:
        print("\n✅ Notification sent successfully!")
        print("Check the overlay UI for the notification.")
    else:
        print("\n❌ Failed to send notification.")
        print("Make sure the overlay UI is running and connected to port 8766.")

if __name__ == "__main__":
    asyncio.run(main())