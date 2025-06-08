#!/usr/bin/env python3
import asyncio
import websockets
import json
import uuid
from datetime import datetime

async def send_notification():
    """Send a notification directly to the backend server on port 8767"""
    try:
        print("Connecting to backend server on port 8767...")
        async with websockets.connect("ws://localhost:8767/ws") as ws:
            # First message is usually a welcome message
            welcome = await ws.recv()
            print(f"Received welcome: {welcome}")
            
            # Register as a client
            register_msg = {
                "type": "register",
                "client_type": "notification_test",
                "client_id": f"notification_test_{uuid.uuid4()}"
            }
            await ws.send(json.dumps(register_msg))
            register_response = await ws.recv()
            print(f"Register response: {register_response}")
            
            # Create a notification message for the backend
            notification = {
                "type": "notification",
                "message_type": "suggestion",
                "content": "⚠️ BACKEND TEST NOTIFICATION ⚠️\n\nThis is a direct backend notification test.",
                "buttons": [
                    {
                        "text": "Works",
                        "value": "works",
                        "style": "success"
                    },
                    {
                        "text": "Fails",
                        "value": "fails",
                        "style": "danger"
                    }
                ],
                "importance": "high",
                "play_sound": True,
                "timestamp": datetime.now().isoformat()
            }
            
            # Send the notification
            print(f"Sending backend notification: {notification}")
            await ws.send(json.dumps(notification))
            print("Backend notification sent!")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                print(f"Received response: {response}")
            except asyncio.TimeoutError:
                print("No response received within timeout")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    print("=== BACKEND NOTIFICATION TEST ===")
    print("Sending a notification directly to the backend server (port 8767)")
    asyncio.run(send_notification())
    print("Test complete. Check if the notification appeared in the overlay.")
    print("If not, try clicking on the overlay window to give it focus.")