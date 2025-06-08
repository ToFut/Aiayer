#!/usr/bin/env python3
"""
Send a test message to the overlay on port 8766
"""
import asyncio
import websockets
import json
import sys

async def send_test_message():
    """Send a test message to the overlay"""
    try:
        uri = "ws://localhost:8766"
        async with websockets.connect(uri) as websocket:
            # Wait for welcome message
            response = await websocket.recv()
            print(f"Received welcome message: {response[:100]}...")
            
            # Register
            register_msg = {
                "type": "register",
                "payload": {
                    "client_type": "test_client",
                    "version": "1.0",
                    "capabilities": ["text"]
                }
            }
            
            print("Registering with server...")
            await websocket.send(json.dumps(register_msg))
            
            # Wait for registration confirmation
            response = await websocket.recv()
            print(f"Registration response: {response[:100]}...")
            
            # Send test message
            query = "This is a direct test message to verify the overlay is working"
            if len(sys.argv) > 1:
                query = " ".join(sys.argv[1:])
                
            test_msg = {
                "type": "query_response",
                "payload": {
                    "response": f"TEST RESPONSE: {query}",
                    "query": query,
                    "mode": "ask",
                    "source": "test_script"
                }
            }
            
            print(f"Sending test message: {query}")
            await websocket.send(json.dumps(test_msg))
            print("Test message sent!")
            
            # Wait for confirmation
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2)
                print(f"Response: {response[:100]}...")
            except asyncio.TimeoutError:
                print("No response received (this is normal)")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Sending test message to overlay...")
    asyncio.run(send_test_message())
    print("Done! Check the overlay for the test message.")