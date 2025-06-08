#!/usr/bin/env python3
"""
Direct Overlay Notification - Sends notifications directly to the Tauri overlay UI
Bypasses all intermediary servers to ensure notifications display correctly
"""

import asyncio
import json
import uuid
import logging
import websockets
from datetime import datetime
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/direct_overlay_notification.log')
    ]
)

logger = logging.getLogger(__name__)

# WebSocket ports to try
# The Tauri overlay might be using a direct WebSocket server that's different from the bridge
PORTS_TO_TRY = [8765, 8766, 8767, 8768]

async def send_notification(message, buttons=None, importance="high", play_sound=True):
    """Send a notification to all possible overlay ports"""
    
    if buttons is None:
        buttons = [
            {"text": "✅ Got it", "value": "understood", "style": "success"},
            {"text": "❌ Dismiss", "value": "dismiss", "style": "danger"}
        ]
    
    notification_id = f"notification_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}"
    success = False
    
    # Try all notification formats on all ports
    for port in PORTS_TO_TRY:
        try:
            # Skip if port is not active
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                result = s.connect_ex(('localhost', port))
                if result != 0:
                    logger.warning(f"Port {port} not active, skipping")
                    continue
                    
            # Connect to the port
            ws_url = f"ws://localhost:{port}"
            if port == 8767:
                ws_url += "/ws"  # Backend requires /ws path
                
            logger.info(f"Trying to connect to {ws_url}...")
            async with websockets.connect(ws_url, ping_timeout=10) as ws:
                # Wait for welcome message
                try:
                    welcome = await asyncio.wait_for(ws.recv(), timeout=2.0)
                    logger.info(f"Connected to {ws_url}! Welcome message received.")
                    
                    # Register with backend if needed
                    if port == 8767:
                        register_msg = {
                            "type": "register",
                            "client_type": "direct_notification",
                            "client_id": f"direct_notification_{uuid.uuid4()}"
                        }
                        await ws.send(json.dumps(register_msg))
                        await asyncio.wait_for(ws.recv(), timeout=2.0)
                    
                    # Try the modern format
                    notification = {
                        "type": "suggestion",
                        "response": message,
                        "buttons": buttons,
                        "importance": importance,
                        "play_sound": play_sound,
                        "notification": True,
                        "plan_id": notification_id,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    logger.info(f"Sending notification to port {port}: {message}")
                    await ws.send(json.dumps(notification))
                    logger.info(f"Modern format sent to port {port}")
                    
                    # Wait briefly
                    await asyncio.sleep(0.5)
                    
                    # Also try the legacy format
                    legacy_notification = {
                        "success": True,
                        "response": message,
                        "mode": "SUGGEST",
                        "notification": True,
                        "play_sound": play_sound,
                        "importance": importance,
                        "buttons": buttons,
                        "interactive": True,
                        "timestamp": datetime.now().isoformat()
                    }
                    await ws.send(json.dumps(legacy_notification))
                    logger.info(f"Legacy format sent to port {port}")
                    
                    # Also try the NextGen format
                    nextgen_notification = {
                        "type": "message",
                        "message": message,
                        "mode": "SUGGEST",
                        "buttons": buttons,
                        "importance": importance,
                        "play_sound": play_sound,
                        "notification": True,
                        "timestamp": datetime.now().isoformat()
                    }
                    await ws.send(json.dumps(nextgen_notification))
                    logger.info(f"NextGen format sent to port {port}")
                    
                    # Wait for response with timeout
                    try:
                        response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                        logger.info(f"Response received from port {port}")
                        success = True
                    except asyncio.TimeoutError:
                        logger.warning(f"No response received from port {port}")
                
                except asyncio.TimeoutError:
                    logger.warning(f"No welcome message from {ws_url}, skipping")
        
        except Exception as e:
            logger.error(f"Error with port {port}: {e}")
    
    return success

async def main():
    """Main function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Send a direct notification to the overlay')
    parser.add_argument('message', nargs='?', help='The notification message')
    parser.add_argument('--sound', action='store_true', help='Play a sound with the notification')
    parser.add_argument('--importance', choices=['low', 'medium', 'high'], default='high', help='Notification importance')
    args = parser.parse_args()
    
    print("\n=== DIRECT OVERLAY NOTIFICATION ===\n")
    print("This script bypasses all intermediary servers to send notifications")
    print("directly to the Tauri overlay UI\n")
    
    # Get message from command line or ask for it
    message = args.message
    if not message:
        try:
            message = input("Enter notification message: ")
        except (EOFError, KeyboardInterrupt):
            message = "🔔 NOTIFICATION TEST: This is a direct overlay notification test."
    
    if not message:
        message = "🔔 NOTIFICATION TEST: This is a direct overlay notification test."
    
    print(f"\nSending notification: {message}")
    print(f"Importance: {args.importance}")
    print(f"Sound: {'Yes' if args.sound else 'No'}")
    
    # Define custom buttons
    buttons = [
        {"text": "✅ Show me", "value": "show", "style": "success"},
        {"text": "❓ More info", "value": "info", "style": "primary"},
        {"text": "❌ Dismiss", "value": "dismiss", "style": "danger"}
    ]
    
    # Send the notification to all ports
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
        print("\n❌ Failed to send notification to any port.")
        print("Make sure the overlay UI is running.")
    
    print("\nThis script tries to connect directly to the Tauri overlay UI")
    print("by bypassing all intermediary servers and bridges.")

if __name__ == "__main__":
    asyncio.run(main())