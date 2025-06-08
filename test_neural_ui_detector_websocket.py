#!/usr/bin/env python3
import asyncio
import websockets
import json
import sys

async def test_connection():
    """Test connection to Neural UI Detector WebSocket server"""
    uri = "ws://localhost:8768"
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri, ping_interval=None) as websocket:
            print("Connected to server!")
            
            # Send a simple ping message
            message = {
                "type": "ping",
                "message": "Hello from test client"
            }
            
            print(f"Sending message: {message}")
            await websocket.send(json.dumps(message))
            
            # Wait for response with timeout
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"Received response: {response}")
                return True
            except asyncio.TimeoutError:
                print("Timeout waiting for response")
                return False
                
    except ConnectionRefusedError:
        print("Connection refused - server not running or wrong port")
        return False
    except Exception as e:
        print(f"Error connecting to server: {e}")
        return False

if __name__ == "__main__":
    print("Neural UI Detector WebSocket Test")
    print("================================")
    
    try:
        result = asyncio.run(test_connection())
        if result:
            print("\nTest SUCCESSFUL - Connection and communication working!")
            sys.exit(0)
        else:
            print("\nTest FAILED - Could not communicate with server")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nTest interrupted")
        sys.exit(130)