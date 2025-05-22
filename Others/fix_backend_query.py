#!/usr/bin/env python3
import asyncio
import websockets
import json
import time

async def test_with_fixed_query():
    try:
        print("Connecting to WebSocket server...")
        async with websockets.connect('ws://localhost:8765') as websocket:
            print("Connection established!")
            
            # This key difference is using the correctly formatted user_interaction message
            # The issue is likely that the client is sending the wrong format
            message = {
                "type": "user_interaction",
                "payload": {
                    "type": "query",
                    "query": "Hello, can you fix this issue and respond to my message?"
                }
            }
            
            print(f"Sending properly formatted message: {json.dumps(message)}")
            await websocket.send(json.dumps(message))
            
            # Wait for all possible responses
            print("\nWaiting for responses (up to 20 seconds)...")
            start_time = time.time()
            
            while time.time() - start_time < 20:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    parsed = json.loads(response)
                    print(f"\nReceived: {json.dumps(parsed, indent=2)}")
                    
                    # Check if this is our query response
                    if parsed.get("type") == "query_response":
                        print("\n✅ SUCCESS: Received query response!")
                        return True
                except asyncio.TimeoutError:
                    print(".", end="", flush=True)
                    continue
                except Exception as e:
                    print(f"\nError processing response: {e}")
            
            print("\n❌ FAILED: Did not receive a proper query response")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_with_fixed_query())