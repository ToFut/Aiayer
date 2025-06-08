#!/usr/bin/env python3
"""
Simple WebSocket Test Client
===========================

Tests basic connectivity to the enhanced backend WebSocket server.
"""

import asyncio
import json
import websockets
import time
import sys

async def test_connection():
    """Test connection to the WebSocket server and send a simple request."""
    uri = "ws://localhost:8767"
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected! Sending test message...")
            
            # Test general mode first (simplest)
            request = {
                "type": "request",
                "mode": "general",
                "message": "hello, are you working?",
                "session_id": f"test_{int(time.time())}"
            }
            
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
                    print(f"❌ Unexpected response format: {data}")
                    return False
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response: {response[:50]}...")
                return False
                
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Simple WebSocket Test")
    print("=" * 50)
    
    try:
        result = asyncio.run(test_connection())
        if result:
            print("\n✅ Test PASSED - Server is responding correctly")
            sys.exit(0)
        else:
            print("\n❌ Test FAILED - Server did not respond as expected")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(130)