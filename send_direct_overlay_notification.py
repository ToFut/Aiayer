#!/usr/bin/env python3
"""
Direct Overlay Notification - Sends notifications directly to port 8765
which is the main port the overlay uses for doButton in config.js
"""

import asyncio
import json
import logging
import websockets
from datetime import datetime
import argparse
import os

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/direct_overlay_notification.log')
    ]
)

logger = logging.getLogger(__name__)

async def send_notification(message, buttons=None, importance="high", play_sound=True):
    """Send a notification directly to port 8765 which the overlay uses for doButton"""
    
    if buttons is None:
        buttons = [
            {"text": "✅ Got it", "value": "understood", "style": "success"},
            {"text": "❌ Dismiss", "value": "dismiss", "style": "danger"}
        ]
    
    # Connect specifically to port 8765 (doButton in config.js)
    ws_url = "ws://localhost:8765"
    logger.info(f"Connecting directly to overlay UI at {ws_url}...")
    
    try:
        async with websockets.connect(ws_url, ping_interval=None, close_timeout=2.0) as ws:
            # Format the notification exactly as expected by NextGenAppleChatWidget.svelte
            notification = {
                "type": "suggestion",
                "response": message,
                "mode": "SUGGEST",
                "buttons": buttons,
                "importance": importance,
                "play_sound": play_sound,
                "notification": True,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Sending direct notification: {message}")
            await ws.send(json.dumps(notification))
            
            # Wait for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                logger.info(f"Response: {response}")
                return True
            except asyncio.TimeoutError:
                logger.warning("No response received")
                return True  # Still consider it a success even without response
    except Exception as e:
        logger.error(f"Error connecting to {ws_url}: {e}")
        return False

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Send a direct notification to the overlay UI on port 8765')
    parser.add_argument('message', nargs='?', help='The notification message')
    parser.add_argument('--sound', action='store_true', help='Play a sound with the notification')
    parser.add_argument('--importance', choices=['low', 'medium', 'high'], default='high', help='Notification importance')
    args = parser.parse_args()
    
    print("\n=== DIRECT OVERLAY NOTIFICATION ===\n")
    print("This script sends notifications directly to port 8765")
    print("which is the main port the overlay uses for doButton\n")
    
    message = args.message
    if not message:
        try:
            message = input("Enter notification message: ")
        except (EOFError, KeyboardInterrupt):
            message = "🔔 DIRECT TEST: This notification should appear in the overlay!"
    
    if not message:
        message = "🔔 DIRECT TEST: This notification should appear in the overlay!"
    
    print(f"\nSending direct notification: {message}")
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
        print("\n✅ Direct notification sent successfully!")
        print("Check the overlay UI for the notification.")
    else:
        print("\n❌ Failed to send notification.")
        print("Make sure the overlay UI is running and connected to port 8765.")

if __name__ == "__main__":
    asyncio.run(main())