#!/usr/bin/env python3
"""
Test sending a notification to the overlay through the proxy on port 8766.
This sends a notification that is formatted to be clearly visible in the overlay.
"""

import asyncio
import json
import logging
import sys
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
logger = logging.getLogger("test_notification")

# Connection settings
PROXY_PORT = 8766

async def send_visible_notification():
    """Send a very visible notification that should appear in the overlay"""
    try:
        print(f"Connecting to proxy on port {PROXY_PORT}...")
        async with websockets.connect(f"ws://localhost:{PROXY_PORT}") as ws:
            print("Connected to proxy!")
            
            # Wait for welcome message
            welcome = await ws.recv()
            print(f"Received welcome: {welcome}")
            
            # Create a highly visible notification
            timestamp = datetime.now().timestamp()
            notification = {
                "type": "suggestion",
                "response": f"🔴 IMPORTANT NOTIFICATION TEST [{timestamp}]\n\n" +
                           f"This is a test notification sent directly to the overlay.\n\n" +
                           f"If you can see this message, it means the notification system is working correctly!\n\n" +
                           f"Please click one of the buttons below to confirm:",
                "buttons": [
                    {"text": "✅ I can see this notification", "value": "success"},
                    {"text": "❌ Still not working", "value": "failure"}
                ],
                "importance": "high",
                "play_sound": True,
                "plan_id": f"overlay_test_{timestamp}"
            }
            
            # Send the notification
            print("\nSending notification to overlay...")
            await ws.send(json.dumps(notification))
            print("Notification sent!")
            print("\n================================================================")
            print("🔔 CHECK THE OVERLAY NOW - YOU SHOULD SEE A RED NOTIFICATION!")
            print("================================================================\n")
            
            # Wait for a response (button click)
            print("Waiting for button click response (will timeout after 30 seconds)...")
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=30)
                print(f"\n✅ RECEIVED RESPONSE: {response}")
                print("\nGreat! This means the overlay received the notification and you clicked a button.")
                return True
            except asyncio.TimeoutError:
                print("\n⚠️  No button click received within 30 seconds.")
                print("If you can see the notification but didn't click a button, that's still a success!")
                print("If you can't see the notification in the overlay, the proxy connection isn't working.")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("\n=== OVERLAY NOTIFICATION TEST ===\n")
    print("This test will send a notification that should appear in the overlay.")
    print("If successful, you will see a red notification with buttons in the overlay.\n")
    
    asyncio.run(send_visible_notification())
    
    print("\n=== TEST COMPLETE ===")
    print("If you saw the notification in the overlay, the notification system is working!")
    print("If not, we need to check the overlay's WebSocket connection settings.")