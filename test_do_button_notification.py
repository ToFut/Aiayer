#!/usr/bin/env python3
"""
Test DO button notification system through the proxy.
This script simulates the actual DO button notification format that would come from the backend.
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
logger = logging.getLogger("test_do_button")

# Connection settings
PROXY_PORT = 8766

async def send_do_button_notification():
    """Send a DO button notification through the proxy"""
    try:
        print(f"Connecting to proxy on port {PROXY_PORT}...")
        async with websockets.connect(f"ws://localhost:{PROXY_PORT}") as ws:
            print("Connected to proxy!")
            
            # Wait for welcome message
            welcome = await ws.recv()
            print(f"Received welcome: {welcome[:100]}...")
            
            # Create a unique plan ID for this test
            plan_id = f"do_button_test_{int(datetime.now().timestamp())}"
            
            # Create a DO button notification in the original format (before proxy translation)
            notification = {
                "type": "do_button_notification",
                "content": {
                    "message": "🚀 DO BUTTON TEST: This is a simulated DO button notification. Can you see this?",
                    "buttons": [
                        {"text": "✅ Yes, I can see it!", "value": "do_it"},
                        {"text": "❌ No, not visible", "value": "cancel"}
                    ]
                },
                "importance": "high",
                "plan_id": plan_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # Send the notification
            print("\nSending DO button notification through proxy...")
            await ws.send(json.dumps(notification))
            print("DO button notification sent!")
            
            # The proxy should convert this to a suggestion format for the overlay
            print("\n================================================================")
            print("🔔 CHECK THE OVERLAY NOW - YOU SHOULD SEE A DO BUTTON NOTIFICATION!")
            print("================================================================\n")
            
            # Wait for a response (button click)
            print("Waiting for button click response (will timeout after 30 seconds)...")
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=30)
                print(f"\n✅ RECEIVED RESPONSE: {response[:100]}...")
                print("\nGreat! This confirms the DO button notification system is working.")
                return True
            except asyncio.TimeoutError:
                print("\n⚠️  No button click received within 30 seconds.")
                print("If you can see the notification but didn't click a button, the display part is working.")
                print("If you can't see the notification in the overlay, there's an issue with the proxy or overlay.")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("\n=== DO BUTTON NOTIFICATION TEST ===\n")
    print("This test will send a DO button notification through the proxy.")
    print("The proxy should convert it to a suggestion format that the overlay can display.\n")
    
    asyncio.run(send_do_button_notification())
    
    print("\n=== TEST COMPLETE ===")
    print("If you saw the notification in the overlay, the proxy is working correctly!")
    print("This means notifications from DO button actions will now be displayed properly.")