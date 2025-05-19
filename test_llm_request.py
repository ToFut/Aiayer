#!/usr/bin/env python3
import asyncio
import websockets
import json
import time

async def test_llm_query():
    """Send a test query to the LLM via the WebSocket."""
    uri = "ws://localhost:8765"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to {uri}")
            
            # First receive the connection establishment message
            print("Waiting for initial connection message...")
            init_response = await websocket.recv()
            init_data = json.loads(init_response)
            print(f"Received connection message: {init_data}")
            
            # Wait a moment for connection to stabilize
            print("Waiting for connection to stabilize...")
            await asyncio.sleep(2)
            
            # Send a test query
            test_query = "Hello, what's your name?"
            message = {
                "type": "llm_request",
                "payload": {
                    "query": test_query,
                    "timestamp": time.time()
                }
            }
            
            print(f"Sending query: {test_query}")
            await websocket.send(json.dumps(message))
            
            # Wait for response
            print("Waiting for response...")
            response = await websocket.recv()
            data = json.loads(response)
            
            if data.get("type") == "llm_response":
                llm_response = data.get("payload", {}).get("response", "No response")
                model = data.get("payload", {}).get("model", "unknown")
                print(f"\nResponse from {model}:\n{llm_response}\n")
            else:
                print(f"Received non-LLM response: {data}")
                
            # Try to receive another message in case first one wasn't the response
            print("Checking for additional messages...")
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                data = json.loads(response)
                if data.get("type") == "llm_response":
                    llm_response = data.get("payload", {}).get("response", "No response")
                    model = data.get("payload", {}).get("model", "unknown")
                    print(f"\nResponse from {model}:\n{llm_response}\n")
                else:
                    print(f"Received additional non-LLM response: {data}")
            except asyncio.TimeoutError:
                print("No additional messages received within timeout")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_llm_query())