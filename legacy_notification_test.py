#!/usr/bin/env python3
import asyncio
import websockets
import json
import uuid
from datetime import datetime

async def send_notification():
    """Send a notification in legacy format directly to proxy on port 8766"""
    try:
        print("Connecting to proxy server on port 8766...")
        async with websockets.connect("ws://localhost:8766") as ws:
            # First message is usually a welcome message
            welcome = await ws.recv()
            print(f"Received welcome: {welcome}")
            
            # Create a legacy notification format
            notification = {
                "mode": "SUGGEST",
                "notification": True,
                "response": "🔥 LEGACY TEST NOTIFICATION 🔥\n\nThis is a test of the legacy notification format.",
                "buttons": [
                    {
                        "text": "I see it",
                        "value": "seen",
                        "style": "success"
                    },
                    {
                        "text": "Not visible",
                        "value": "not_seen",
                        "style": "danger"
                    }
                ],
                "importance": "high",
                "play_sound": True,
                "plan_id": f"legacy_test_{uuid.uuid4()}",
                "timestamp": datetime.now().isoformat()
            }
            
            # Send the notification
            print(f"Sending legacy notification: {notification}")
            await ws.send(json.dumps(notification))
            print("Legacy notification sent!")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                print(f"Received response: {response}")
            except asyncio.TimeoutError:
                print("No response received within timeout")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    print("=== LEGACY NOTIFICATION TEST ===")
    print("Sending a legacy format notification to the overlay via proxy (port 8766)")
    asyncio.run(send_notification())
    print("Test complete. Check if the notification appeared in the overlay.")
    print("If not, try clicking on the overlay window to give it focus.")