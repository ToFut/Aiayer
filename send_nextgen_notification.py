#!/usr/bin/env python3
import asyncio
import websockets
import json
import sys
from datetime import datetime

async def send_notification(message, port=8767, mode="Suggest"):
    """Send a notification to the NextGenAppleChatWidget"""
    # The app.svelte is connecting to ws://localhost:8767 as seen in line 125
    ws_url = f"ws://localhost:{port}"
    
    # Port 8767 requires /ws path
    if port == 8767:
        ws_url += "/ws"
    
    print(f"Connecting to {ws_url}...")
    
    try:
        async with websockets.connect(ws_url) as ws:
            print(f"Connected to {ws_url}")
            
            # Wait for welcome message
            try:
                welcome = await asyncio.wait_for(ws.recv(), timeout=2.0)
                print(f"Welcome message: {welcome[:100]}...")
            except asyncio.TimeoutError:
                print("No welcome message received (continuing anyway)")
            
            # Create notification in the expected format
            # Try without the type field - just use the brain router format
            notification = {
                "success": True,
                "response": message,
                "mode": mode,
                "timestamp": datetime.now().isoformat()
            }
            
            # Send notification
            print(f"Sending notification: {json.dumps(notification)}")
            await ws.send(json.dumps(notification))
            print("Notification sent!")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                print(f"Response received: {response[:100]}...")
            except asyncio.TimeoutError:
                print("No response received (this may be normal)")
            
            print("✅ Notification sent successfully")
            return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    # Get message from command line
    if len(sys.argv) < 2:
        print("Usage: python send_nextgen_notification.py \"Your message\" [port] [mode]")
        print("Example: python send_nextgen_notification.py \"Hello there!\" 8767 Ask")
        sys.exit(1)
    
    message = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8767  # Default to port 8767
    mode = sys.argv[3] if len(sys.argv) > 3 else "Suggest"  # Default mode
    
    print(f"Sending notification to port {port}, mode {mode}:")
    print(f"Message: {message}")
    
    asyncio.run(send_notification(message, port, mode))