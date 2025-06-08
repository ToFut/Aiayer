#!/usr/bin/env python3
"""
Test Direct Notification - Tests notifications directly to the DO button server on port 8765
"""

import asyncio
import json
import websockets
import uuid
from datetime import datetime
import argparse

async def send_notification(message="🔔 DIRECT TEST NOTIFICATION", port=8765):
    """Send a direct notification to the DO button server"""
    
    # Define buttons
    buttons = [
        {"text": "✅ Got it", "value": "understood", "style": "success"},
        {"text": "❓ More info", "value": "info", "style": "primary"},
        {"text": "❌ Dismiss", "value": "dismiss", "style": "danger"}
    ]
    
    # Create a notification ID
    notification_id = f"notification_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}"
    
    # Try to connect to the server
    try:
        print(f"Connecting to ws://localhost:{port}...")
        async with websockets.connect(f"ws://localhost:{port}", ping_timeout=10) as ws:
            # Wait for welcome message
            welcome = await ws.recv()
            print(f"Connected! Welcome message received: {welcome[:100]}...")
            
            # Try multiple notification formats for maximum compatibility
            
            # Format 1: Modern suggestion format
            notification1 = {
                "type": "suggestion",
                "response": f"[PORT {port}] {message}",
                "buttons": buttons,
                "importance": "high",
                "play_sound": True,
                "notification": True,
                "plan_id": notification_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # Send notification
            print(f"Sending suggestion format notification to port {port}...")
            await ws.send(json.dumps(notification1))
            print("Sent!")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                print(f"Response received: {response[:100]}...")
            except asyncio.TimeoutError:
                print("No response received within timeout.")
            
            # Wait a moment before sending the next format
            await asyncio.sleep(1)
            
            # Format 2: Legacy format
            notification2 = {
                "success": True,
                "response": f"[LEGACY FORMAT] {message}",
                "mode": "SUGGEST",
                "notification": True,
                "play_sound": True,
                "importance": "high",
                "buttons": buttons,
                "interactive": True,
                "timestamp": datetime.now().isoformat()
            }
            
            # Send notification
            print(f"Sending legacy format notification to port {port}...")
            await ws.send(json.dumps(notification2))
            print("Sent!")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                print(f"Response received: {response[:100]}...")
            except asyncio.TimeoutError:
                print("No response received within timeout.")
            
            # Wait a moment before sending the next format
            await asyncio.sleep(1)
            
            # Format 3: Direct message format
            notification3 = {
                "type": "message",
                "message": f"[MESSAGE FORMAT] {message}",
                "mode": "SUGGEST",
                "buttons": buttons,
                "importance": "high",
                "play_sound": True,
                "notification": True,
                "timestamp": datetime.now().isoformat()
            }
            
            # Send notification
            print(f"Sending message format notification to port {port}...")
            await ws.send(json.dumps(notification3))
            print("Sent!")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                print(f"Response received: {response[:100]}...")
            except asyncio.TimeoutError:
                print("No response received within timeout.")
            
            # Format 4: Direct do_button_action format
            notification4 = {
                "type": "do_button_action",
                "do_button_action": {
                    "plan_id": notification_id,
                    "message": f"[DO_BUTTON_ACTION FORMAT] {message}",
                    "buttons": buttons,
                    "importance": "high",
                    "play_sound": True,
                    "notification": True
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Send notification
            print(f"Sending do_button_action format notification to port {port}...")
            await ws.send(json.dumps(notification4))
            print("Sent!")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                print(f"Response received: {response[:100]}...")
            except asyncio.TimeoutError:
                print("No response received within timeout.")
            
            print("\nAll notification formats sent successfully!")
            return True
            
    except Exception as e:
        print(f"Error sending notification: {e}")
        return False

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test direct notifications to the overlay")
    parser.add_argument("--port", type=int, default=8765, help="WebSocket port to connect to")
    parser.add_argument("--message", type=str, default="🔔 TEST NOTIFICATION: Direct test of the overlay notification system", help="Message to send")
    args = parser.parse_args()
    
    print("=== DIRECT NOTIFICATION TEST ===")
    print(f"Testing direct notification to port {args.port}")
    print(f"Message: {args.message}")
    
    success = await send_notification(message=args.message, port=args.port)
    
    if success:
        print("\n✅ Test completed!")
        print("Check the overlay UI for notifications.")
    else:
        print("\n❌ Test failed.")
        print(f"Could not connect to port {args.port} or send notifications.")
    
    print("\nIf you don't see notifications in the overlay UI, try the other ports:")
    print("  python test_direct_overlay_notification.py --port 8766")
    print("  python test_direct_overlay_notification.py --port 8767")
    print("  python test_direct_overlay_notification.py --port 8768")

if __name__ == "__main__":
    asyncio.run(main())