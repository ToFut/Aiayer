#!/usr/bin/env python3
import asyncio
import websockets
import json
import time
from datetime import datetime

async def send_notification():
    """Send notification directly to port 8768 (where EnterpriseChatWidget.svelte is listening)"""
    ws_url = 'ws://localhost:8768'
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    print(f"Connecting to {ws_url}...")
    
    try:
        async with websockets.connect(ws_url) as ws:
            print("Connected! Waiting for welcome message...")
            welcome = await ws.recv()
            print(f"Welcome message: {welcome[:100]}...")
            
            # The EXACT format that EnterpriseChatWidget.svelte expects
            notification = {
                "success": True,
                "response": f"Test notification at {timestamp}. This notification is sent directly to port 8768, which is the default port that EnterpriseChatWidget.svelte connects to.",
                "mode": "Suggest"
            }
            
            print(f"Sending notification: {json.dumps(notification)}")
            await ws.send(json.dumps(notification))
            print("Notification sent!")
            
            # Wait for response (optional)
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                print(f"Response: {response[:100]}...")
            except asyncio.TimeoutError:
                print("No response received (this is normal)")
            
            print("Done!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(send_notification())