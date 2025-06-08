#!/usr/bin/env python3
import asyncio
import websockets
import json
import sys
from datetime import datetime
import uuid

async def send_chat_request(message, port=8767, mode="Suggest"):
    """
    Send a chat_request to the server, which should trigger a response
    that will appear in the overlay
    """
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
            
            # Create a chat_request (this is what the overlay sends normally)
            session_id = f"session_{uuid.uuid4().hex[:8]}"
            request = {
                "type": "chat_request",
                "mode": mode,
                "message": message,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # Send request
            print(f"Sending chat request: {json.dumps(request)}")
            await ws.send(json.dumps(request))
            print("Chat request sent!")
            
            # Wait for response - this should be the notification that appears in the overlay
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                print(f"Response received: {response[:200]}...")
                return True
            except asyncio.TimeoutError:
                print("No response received within timeout")
                return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    # Get message from command line
    if len(sys.argv) < 2:
        print("Usage: python send_chat_request.py \"Your message\" [port] [mode]")
        print("Example: python send_chat_request.py \"Hello there!\" 8767 Ask")
        sys.exit(1)
    
    message = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8767  # Default to port 8767
    mode = sys.argv[3] if len(sys.argv) > 3 else "Suggest"  # Default mode
    
    print(f"Sending chat request to port {port}, mode {mode}:")
    print(f"Message: {message}")
    
    asyncio.run(send_chat_request(message, port, mode))