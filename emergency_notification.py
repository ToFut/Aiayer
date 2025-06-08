#\!/usr/bin/env python3
"""
Emergency Notification Sender

This script attempts multiple notification formats and ports to ensure the overlay
receives and displays a notification. It also includes a test for the emergency DOM
injection method if available.
"""

import asyncio
import websockets
import json
import uuid
from datetime import datetime
import random
import argparse

# Define message types to try
MESSAGE_TYPES = [
    "suggestion",
    "notification", 
    "do_button", 
    "chat_notification",
    "system_notification"
]

# Define ports to try
PORTS = [8765, 8766, 8767, 8768]

async def try_notification_format(websocket, message_type, message_text, importance="high"):
    """Try a specific notification format"""
    
    # Generate a unique ID
    msg_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    # Create buttons
    buttons = [
        {"text": "OK", "value": "ok", "style": "success"},
        {"text": "Dismiss", "value": "dismiss", "style": "danger"}
    ]
    
    # Basic format for most types
    notification = {
        "type": message_type,
        "response": message_text,
        "message": message_text,  # Include both for maximum compatibility
        "content": message_text,
        "importance": importance,
        "play_sound": True,
        "buttons": buttons,
        "plan_id": msg_id,
        "session_id": msg_id,
        "timestamp": timestamp
    }
    
    # Special handling for do_button format
    if message_type == "do_button":
        notification = {
            "type": "do_button",
            "action": "display",
            "content": {
                "title": "URGENT NOTIFICATION",
                "message": message_text,
                "buttons": [
                    {"id": "do_it", "text": "OK", "type": "primary"},
                    {"id": "dismiss", "text": "Dismiss", "type": "secondary"}
                ]
            },
            "session_id": msg_id,
            "timestamp": timestamp
        }
    
    # Send and wait for response
    try:
        await websocket.send(json.dumps(notification))
        print(f"Sent {message_type} notification")
        
        # Wait for response with timeout
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
            print(f"Received response: {response}")
            return True
        except asyncio.TimeoutError:
            print(f"No response received for {message_type}")
            return False
    except Exception as e:
        print(f"Error sending {message_type} notification: {e}")
        return False

async def try_port(port, message, importance):
    """Try all message types on a specific port"""
    ws_url = f"ws://localhost:{port}"
    
    try:
        print(f"\nTrying port {port}...")
        async with websockets.connect(ws_url, ping_interval=None) as ws:
            try:
                welcome = await asyncio.wait_for(ws.recv(), timeout=2.0)
                print(f"Received welcome from port {port}: {welcome[:100]}...")
            except asyncio.TimeoutError:
                print(f"No welcome message received from port {port}, continuing anyway...")
            
            # Try all message types
            for msg_type in MESSAGE_TYPES:
                success = await try_notification_format(ws, msg_type, message, importance)
                if success:
                    print(f"✅ Successfully sent {msg_type} notification via port {port}")
                
                # Wait a bit between attempts
                await asyncio.sleep(0.5)
                
            return True
    except Exception as e:
        print(f"Error connecting to port {port}: {e}")
        return False

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Emergency Notification Sender')
    parser.add_argument('--message', type=str, default="URGENT: This is an emergency notification test", 
                        help='Notification message')
    parser.add_argument('--importance', type=str, default='high', choices=['high', 'medium', 'low'], 
                        help='Importance level')
    
    args = parser.parse_args()
    
    # Add some attention-grabbing symbols
    symbols = ["⚠️", "🔔", "🚨", "🛑", "⚡", "💡", "📣"]
    random_symbol = random.choice(symbols)
    message = f"{random_symbol} {args.message} {random_symbol}"
    
    # Try all ports
    results = []
    for port in PORTS:
        result = await try_port(port, message, args.importance)
        results.append((port, result))
    
    # Summary
    print("\n--- NOTIFICATION ATTEMPT SUMMARY ---")
    for port, result in results:
        status = "✅ Connected" if result else "❌ Failed"
        print(f"Port {port}: {status}")
    
    successful_ports = [port for port, result in results if result]
    if successful_ports:
        print(f"\n✅ Successfully connected to ports: {successful_ports}")
        print("If notifications still don't appear in the overlay:")
        print("1. Check the overlay UI components for visibility issues")
        print("2. Verify overlay has focus and is not minimized")
        print("3. Check browser console for JavaScript errors")
    else:
        print("\n❌ Failed to connect to any ports")
        print("Make sure the overlay WebSocket servers are running")

if __name__ == "__main__":
    asyncio.run(main())
