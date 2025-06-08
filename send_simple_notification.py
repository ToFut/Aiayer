#!/usr/bin/env python3
import asyncio
import websockets
import json
import sys
from datetime import datetime

async def send_direct_notification(message, port=8768, mode="Suggest"):
    """
    Send a notification in the exact format expected by EnterpriseChatWidget.svelte
    This is a simplified version with minimal dependencies
    """
    ws_url = f"ws://localhost:{port}"
    
    print(f"Connecting to {ws_url}...")
    
    try:
        async with websockets.connect(ws_url) as ws:
            # Wait for welcome message
            welcome = await ws.recv()
            print(f"Connected: {welcome[:100]}...")
            
            # Create notification in exact format expected by handleBackendMessage function
            # Based on line 233 in EnterpriseChatWidget.svelte:
            # if (data.success !== undefined && data.response) {
            notification = {
                "success": True,
                "response": message,
                "mode": mode
            }
            
            # Send notification
            await ws.send(json.dumps(notification))
            print(f"Notification sent: {json.dumps(notification)}")
            
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                print(f"Response received: {response[:100]}...")
            except asyncio.TimeoutError:
                print("No response received (this may be normal)")
            
            print("✅ Done - check the overlay to see if the notification appears")
            return True
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    # Get message from command line arguments
    if len(sys.argv) < 2:
        print("Usage: python3 send_simple_notification.py \"Your message\" [port] [mode]")
        print("Example: python3 send_simple_notification.py \"Hello there!\" 8768 Ask")
        sys.exit(1)
    
    message = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8768
    mode = sys.argv[3] if len(sys.argv) > 3 else "Suggest"
    
    print(f"Sending notification: \"{message}\"")
    print(f"Port: {port}, Mode: {mode}")
    
    asyncio.run(send_direct_notification(message, port, mode))