all #!/usr/bin/env python3
import asyncio
import websockets
import json
import sys

async def test_connection():
    uri = "ws://localhost:8765"
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket server")
            
            # Wait for welcome message
            response = await websocket.recv()
            print(f"Received: {response}")
            
            # Send a test LLM request
            test_message = {
                "type": "llm_request",
                "payload": {
                    "query": "Hello, can you help me with something?"
                }
            }
            
            print("\nSending test message...")
            await websocket.send(json.dumps(test_message))
            
            # Wait for response
            response = await websocket.recv()
            print(f"\nReceived response: {response}")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_connection()) 