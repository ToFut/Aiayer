#!/usr/bin/env python3
import asyncio
import websockets
import json
import time

async def test_query_handler():
    try:
        print("Connecting to WebSocket server...")
        async with websockets.connect('ws://localhost:8765') as websocket:
            print("Connection established!")
            
            # Send a properly formatted user query
            query_message = {
                "type": "user_interaction",
                "payload": {
                    "type": "query",
                    "query": "Hello, can you respond to this message?"
                }
            }
            
            print(f"Sending query: {query_message}")
            await websocket.send(json.dumps(query_message))
            
            # Listen for all responses for 10 seconds
            print("Listening for all responses for 10 seconds...")
            response_count = 0
            
            # Set a timeout for the entire operation
            start_time = time.time()
            while time.time() - start_time < 10:
                try:
                    # Set a timeout for each receive operation
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    response_count += 1
                    print(f"Response {response_count}: {response}")
                    
                    # Parse the response to see if it's our answer
                    try:
                        parsed = json.loads(response)
                        if parsed.get("type") == "query_response":
                            print("\n✓ SUCCESS: Received a proper query response!")
                            return True
                    except json.JSONDecodeError:
                        print("Failed to parse response as JSON")
                        
                except asyncio.TimeoutError:
                    # This is expected after all responses are received
                    print(".", end="", flush=True)
                    continue
            
            print("\n✗ FAILURE: No query_response received within 10 seconds")
            return False
                
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_query_handler())