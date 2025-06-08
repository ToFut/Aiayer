#!/usr/bin/env python3
import asyncio
import websockets
import json
import uuid
from datetime import datetime

async def send_notification():
    """Send a simple notification directly to port 8765"""
    try:
        print("Connecting to DO button server on port 8765...")
        async with websockets.connect("ws://localhost:8765") as ws:
            # First message is usually a welcome message
            welcome = await ws.recv()
            print(f"Received welcome: {welcome}")
            
            # Create a very basic notification
            notification = {
                "type": "suggestion",
                "response": "🚨 EMERGENCY TEST NOTIFICATION 🚨\n\nThis is a critical test notification. If you can see this, please click 'YES'.",
                "buttons": [
                    {
                        "text": "YES",
                        "value": "yes",
                        "style": "success"
                    },
                    {
                        "text": "NO",
                        "value": "no",
                        "style": "danger"
                    }
                ],
                "importance": "high",
                "play_sound": True,
                "plan_id": f"critical_test_{uuid.uuid4()}",
                "timestamp": datetime.now().isoformat()
            }
            
            # Send the notification
            print(f"Sending notification: {notification}")
            await ws.send(json.dumps(notification))
            print("Notification sent!")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                print(f"Received response: {response}")
            except asyncio.TimeoutError:
                print("No response received within timeout")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    print("=== SIMPLE NOTIFICATION TEST ===")
    print("Sending a direct notification to the overlay via port 8765")
    asyncio.run(send_notification())
    print("Test complete. Check if the notification appeared in the overlay.")
    print("If not, try clicking on the overlay window to give it focus.")