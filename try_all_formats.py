#!/usr/bin/env python3
import asyncio
import websockets
import json
import sys
from datetime import datetime
import uuid

async def try_all_notification_formats(message, port=8767):
    """Try all possible notification formats to see which one works"""
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
            
            # Try different notification formats
            formats = [
                # Format 1: Simple brain router format
                {
                    "success": True,
                    "response": f"{message} (Format 1: Simple brain router)",
                    "mode": "Suggest"
                },
                
                # Format 2: With notification type
                {
                    "type": "notification",
                    "message": f"{message} (Format 2: With notification type)",
                    "importance": "high"
                },
                
                # Format 3: With suggestion type
                {
                    "type": "suggestion",
                    "message": f"{message} (Format 3: With suggestion type)",
                    "importance": "high"
                },
                
                # Format 4: Chat request format
                {
                    "type": "chat_request",
                    "mode": "Suggest",
                    "message": f"{message} (Format 4: Chat request)",
                    "session_id": f"session_{uuid.uuid4().hex[:8]}"
                },
                
                # Format 5: System message
                {
                    "type": "system_message",
                    "message": f"{message} (Format 5: System message)"
                }
            ]
            
            # Try each format
            for i, format_data in enumerate(formats):
                try:
                    # Add timestamp to all formats
                    format_data["timestamp"] = datetime.now().isoformat()
                    
                    print(f"\nTrying Format #{i+1}: {format_data}")
                    await ws.send(json.dumps(format_data))
                    print(f"Format #{i+1} sent")
                    
                    # Wait for response
                    try:
                        response = await asyncio.wait_for(ws.recv(), timeout=3.0)
                        print(f"Response for Format #{i+1}: {response[:200]}...")
                    except asyncio.TimeoutError:
                        print(f"No response for Format #{i+1}")
                    
                    # Wait a bit before trying the next format
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    print(f"Error with Format #{i+1}: {e}")
            
            print("\nAll formats have been tried!")
            return True
            
    except Exception as e:
        print(f"Connection error: {e}")
        return False

if __name__ == "__main__":
    # Get message from command line
    message = sys.argv[1] if len(sys.argv) > 1 else "Test message"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8767  # Default to port 8767
    
    print(f"Testing all notification formats with base message: {message}")
    asyncio.run(try_all_notification_formats(message, port))