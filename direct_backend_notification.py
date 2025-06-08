#!/usr/bin/env python3
"""
Direct Backend Notification - Sends notifications directly to the backend server on port 8767
"""

import asyncio
import json
import websockets
import uuid
from datetime import datetime

async def send_notification():
    """Send a direct notification to the backend server"""
    ws_url = "ws://localhost:8767/ws"
    client_id = f"direct_test_{uuid.uuid4()}"
    
    try:
        print(f"Connecting to {ws_url}...")
        async with websockets.connect(ws_url, ping_timeout=10) as ws:
            # Wait for welcome message
            welcome = await ws.recv()
            print(f"Connected! Welcome message: {welcome[:100]}...")
            
            # Register with backend
            register_msg = {
                "type": "register",
                "client_type": "direct_test",
                "client_id": client_id
            }
            await ws.send(json.dumps(register_msg))
            response = await ws.recv()
            print(f"Registration response: {response[:100]}...")
            
            # Define message and buttons
            message = "🚨 URGENT NOTIFICATION: This is a direct test to the backend server on port 8767"
            buttons = [
                {"text": "✅ Got it", "value": "understood", "style": "success"},
                {"text": "❓ Tell me more", "value": "more", "style": "primary"},
                {"text": "❌ Dismiss", "value": "dismiss", "style": "danger"}
            ]
            
            # Try all notification formats
            formats = [
                # Format 1: Standard message format
                {
                    "type": "message",
                    "message": f"[FORMAT 1] {message}",
                    "mode": "SUGGEST",
                    "buttons": buttons,
                    "importance": "high",
                    "play_sound": True,
                    "notification": True,
                    "timestamp": datetime.now().isoformat()
                },
                
                # Format 2: Suggestion format
                {
                    "type": "suggestion",
                    "response": f"[FORMAT 2] {message}",
                    "buttons": buttons,
                    "importance": "high",
                    "play_sound": True,
                    "notification": True,
                    "plan_id": f"plan_{uuid.uuid4()}",
                    "timestamp": datetime.now().isoformat()
                },
                
                # Format 3: Chat response format
                {
                    "type": "chat_response",
                    "response": f"[FORMAT 3] {message}",
                    "mode": "SUGGEST",
                    "buttons": buttons,
                    "importance": "high",
                    "play_sound": True,
                    "notification": True,
                    "timestamp": datetime.now().isoformat()
                },
                
                # Format 4: Direct client response
                {
                    "type": "client_response",
                    "message": f"[FORMAT 4] {message}",
                    "success": True,
                    "notification": True,
                    "buttons": buttons,
                    "play_sound": True,
                    "importance": "high",
                    "timestamp": datetime.now().isoformat()
                },
                
                # Format 5: Legacy format
                {
                    "success": True,
                    "response": f"[FORMAT 5] {message}",
                    "mode": "SUGGEST",
                    "notification": True,
                    "play_sound": True,
                    "importance": "high",
                    "buttons": buttons,
                    "interactive": True,
                    "timestamp": datetime.now().isoformat()
                }
            ]
            
            # Send each format
            for i, format in enumerate(formats):
                print(f"Sending format {i+1}...")
                await ws.send(json.dumps(format))
                
                # Wait for response
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    print(f"Response received for format {i+1}")
                except asyncio.TimeoutError:
                    print(f"No response for format {i+1}")
                
                # Wait briefly before sending next format
                await asyncio.sleep(1)
            
            print("All notification formats sent!")
            return True
            
    except Exception as e:
        print(f"Error sending notification: {e}")
        return False

async def main():
    """Main function"""
    print("\n=== DIRECT BACKEND NOTIFICATION TEST ===\n")
    print("This script sends notifications directly to the backend server\n")
    
    success = await send_notification()
    
    if success:
        print("\n✅ Test completed successfully")
        print("Check the overlay UI for notifications")
    else:
        print("\n❌ Test failed")
        print("Could not connect to backend server or send notifications")

if __name__ == "__main__":
    asyncio.run(main())