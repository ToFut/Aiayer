#!/usr/bin/env python3
"""
Simple WebSocket client to test backend
"""
import asyncio
import websockets
import json
import sys

async def test():
    try:
        # Connect to the backend WebSocket server
        print("Connecting to backend...")
        uri = "ws://localhost:8767"
        async with websockets.connect(uri) as websocket:
            print("Connected!")
            
            # Receive initial connection message
            response = await websocket.recv()
            print(f"Received: {response[:100]}...")
            
            # Send test chat request
            test_message = {
                "type": "chat_request",
                "mode": "General",
                "message": "Hello, can you respond to this message?",
                "session_id": "test_session",
                "client_id": "test_client"
            }
            
            print(f"Sending message: {test_message}")
            await websocket.send(json.dumps(test_message))
            
            # Wait for response with timeout
            print("Waiting for response...")
            response = await asyncio.wait_for(websocket.recv(), timeout=15)
            print(f"Received response: {response[:200]}...")
            
            # Parse response
            try:
                response_data = json.loads(response)
                response_type = response_data.get("type", "unknown")
                
                if "response" in response_data:
                    print(f"Response content: {response_data['response'][:200]}...")
                else:
                    print(f"Response data: {response_data}")
                
                # Success!
                print("TEST PASSED: Received valid response from backend")
                return True
                
            except json.JSONDecodeError:
                print(f"ERROR: Invalid JSON response: {response[:50]}...")
                return False
                
    except asyncio.TimeoutError:
        print("ERROR: Timeout waiting for response")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    print("Simple WebSocket Backend Test")
    result = asyncio.run(test())
    sys.exit(0 if result else 1)