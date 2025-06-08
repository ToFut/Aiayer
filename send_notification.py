#!/usr/bin/env python3
"""
Send Notification - Simple command line tool to send notifications to the overlay
Usage: python send_notification.py "Your message here" [--port PORT] [--format FORMAT] [--importance IMPORTANCE] [--sound]
"""

import asyncio
import json
import websockets
import uuid
import sys
import argparse
from datetime import datetime

# Notification formats
FORMATS = {
    "suggestion": {
        "type": "suggestion",
        "response": "{message}",
        "buttons": [],
        "importance": "{importance}",
        "play_sound": "{play_sound}",
        "notification": True,
        "plan_id": "{notification_id}",
        "timestamp": "{timestamp}"
    },
    "message": {
        "type": "message",
        "message": "{message}",
        "mode": "SUGGEST",
        "buttons": [],
        "importance": "{importance}",
        "play_sound": "{play_sound}",
        "notification": True,
        "timestamp": "{timestamp}"
    },
    "legacy": {
        "success": True,
        "response": "{message}",
        "mode": "SUGGEST",
        "notification": True,
        "play_sound": "{play_sound}",
        "importance": "{importance}",
        "buttons": [],
        "interactive": True,
        "timestamp": "{timestamp}"
    }
}

# Default buttons
DEFAULT_BUTTONS = [
    {"text": "✅ Got it", "value": "understood", "style": "success"},
    {"text": "❌ Dismiss", "value": "dismiss", "style": "danger"}
]

async def send_notification(message, port=8765, format_name="suggestion", importance="high", play_sound=True):
    """Send a notification to the overlay"""
    # Create a notification ID and timestamp
    notification_id = f"notification_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}"
    timestamp = datetime.now().isoformat()
    
    # Get the format template
    if format_name not in FORMATS:
        print(f"Unknown format: {format_name}")
        print(f"Available formats: {', '.join(FORMATS.keys())}")
        return False
    
    # Create a deep copy of the template
    notification = json.loads(json.dumps(FORMATS[format_name]))
    
    # Replace placeholders in the template
    if "response" in notification:
        notification["response"] = notification["response"].format(
            message=message,
            notification_id=notification_id,
            timestamp=timestamp,
            importance=importance,
            play_sound=play_sound
        )
    if "message" in notification:
        notification["message"] = notification["message"].format(
            message=message,
            notification_id=notification_id,
            timestamp=timestamp,
            importance=importance,
            play_sound=play_sound
        )
    if "plan_id" in notification:
        notification["plan_id"] = notification["plan_id"].format(
            message=message,
            notification_id=notification_id,
            timestamp=timestamp,
            importance=importance,
            play_sound=play_sound
        )
    if "timestamp" in notification:
        notification["timestamp"] = notification["timestamp"].format(
            message=message,
            notification_id=notification_id,
            timestamp=timestamp,
            importance=importance,
            play_sound=play_sound
        )
    if "importance" in notification and isinstance(notification["importance"], str):
        notification["importance"] = notification["importance"].format(
            message=message,
            notification_id=notification_id,
            timestamp=timestamp,
            importance=importance,
            play_sound=play_sound
        )
    if "play_sound" in notification and isinstance(notification["play_sound"], str):
        notification["play_sound"] = notification["play_sound"].format(
            message=message,
            notification_id=notification_id,
            timestamp=timestamp,
            importance=importance,
            play_sound=play_sound
        ) == "True"
    
    # Add buttons
    if "buttons" in notification:
        notification["buttons"] = DEFAULT_BUTTONS
    
    # Connect to the WebSocket
    ws_url = f"ws://localhost:{port}"
    if port == 8767:
        ws_url += "/ws"  # Backend requires /ws path
    
    try:
        print(f"Connecting to {ws_url}...")
        async with websockets.connect(ws_url, ping_timeout=10) as ws:
            # Wait for welcome message
            welcome = await ws.recv()
            print(f"Connected! Welcome message received.")
            
            # Register with backend if needed
            if port == 8767:
                register_msg = {
                    "type": "register",
                    "client_type": "notification_sender",
                    "client_id": f"send_notification_{uuid.uuid4()}"
                }
                await ws.send(json.dumps(register_msg))
                await ws.recv()
                print("Registered with backend")
            
            # Send notification
            notification_json = json.dumps(notification)
            print(f"Sending notification using format '{format_name}'...")
            await ws.send(notification_json)
            
            # Wait for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                print(f"Response received")
                return True
            except asyncio.TimeoutError:
                print("No response received within timeout")
                return False
                
    except Exception as e:
        print(f"Error sending notification: {e}")
        return False

def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(description="Send a notification to the overlay")
    parser.add_argument("message", help="The message to send")
    parser.add_argument("--port", type=int, default=8765, help="WebSocket port (default: 8765)")
    parser.add_argument("--format", choices=FORMATS.keys(), default="suggestion", help="Notification format (default: suggestion)")
    parser.add_argument("--importance", choices=["low", "medium", "high"], default="high", help="Notification importance (default: high)")
    parser.add_argument("--sound", action="store_true", help="Play a sound with the notification")
    
    args = parser.parse_args()
    
    print(f"\n=== SENDING NOTIFICATION ===")
    print(f"Message: {args.message}")
    print(f"Port: {args.port}")
    print(f"Format: {args.format}")
    print(f"Importance: {args.importance}")
    print(f"Sound: {'Yes' if args.sound else 'No'}")
    print()
    
    # Send notification
    success = asyncio.run(send_notification(
        message=args.message,
        port=args.port,
        format_name=args.format,
        importance=args.importance,
        play_sound=args.sound
    ))
    
    if success:
        print("\n✅ Notification sent successfully")
        print("Check the overlay UI for the notification")
    else:
        print("\n❌ Failed to send notification")
        print("Make sure the overlay and servers are running")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())