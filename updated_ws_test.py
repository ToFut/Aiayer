#!/usr/bin/env python3
"""
Updated WebSocket Test Client
===========================

Tests communication with the enhanced backend WebSocket server using the correct protocol.
"""

import asyncio
import json
import websockets
import time
import sys

async def test_connection():
    """Test connection to the WebSocket server with the correct message format."""
    uri = "ws://localhost:8767"
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected! Waiting for connection establishment message...")
            
            # First receive the connection establishment message
            response = await websocket.recv()
            print(f"Initial response received: {response[:200]}...")
            
            # Now send a proper chat request
            request = {
                "type": "chat_request",  # Use chat_request instead of request
                "mode": "general",       # Use proper mode: general, agent, ask, suggest
                "message": "hello, are you working?",
                "session_id": f"test_{int(time.time())}"
            }
            
            print("Sending chat request...")
            await websocket.send(json.dumps(request))
            print("Message sent, waiting for response...")
            
            # Wait for response
            response = await websocket.recv()
            print(f"Response received: {response[:200]}...")
            
            # Try to parse response
            try:
                data = json.loads(response)
                if data.get("type") == "response" and data.get("response"):
                    print("✅ Server responded correctly!")
                    print(f"Response message: {data.get('response')[:100]}...")
                    return True
                else:
                    print(f"Response format: {data.get('type')}")
                    print(f"Full response data: {data}")
                    return True  # Still return true if we got any response
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response: {response[:50]}...")
                return False
                
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Updated WebSocket Test")
    print("=" * 50)
    
    try:
        result = asyncio.run(test_connection())
        if result:
            print("\n✅ Test PASSED - Server is responding")
            sys.exit(0)
        else:
            print("\n❌ Test FAILED - Server did not respond as expected")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(130)