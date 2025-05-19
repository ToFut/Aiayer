#!/usr/bin/env python3
import asyncio
import websockets
import json

async def test_connection():
    try:
        print("Connecting to WebSocket server...")
        async with websockets.connect('ws://localhost:8765') as websocket:
            print("Connection established!")
            
            # Send a test message
            message = json.dumps({
                "type": "user_interaction",
                "payload": {
                    "type": "query",
                    "query": "Hello, are you working?"
                }
            })
            
            print(f"Sending message: {message}")
            await websocket.send(message)
            
            # Wait for response
            print("Waiting for response...")
            response = await websocket.recv()
            print(f"Received response: {response}")
            
            return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())