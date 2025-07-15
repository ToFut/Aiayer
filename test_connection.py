#!/usr/bin/env python3
import asyncio
import websockets
import json

async def test_connection():
    try:
        async with websockets.connect('ws://localhost:8767') as websocket:
            print("✅ Connected to backend")
            
            # Send registration
            register_message = {
                "type": "register",
                "client_id": "test_client"
            }
            await websocket.send(json.dumps(register_message))
            
            # Wait for response
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"✅ Registration response: {response_data.get('type')}")
            
            # Send chat request
            chat_message = {
                "type": "chat_request",
                "message": "Open Safari and search for SEGEV",
                "mode": "Agent",
                "client_id": "test_client"
            }
            await websocket.send(json.dumps(chat_message))
            
            # Wait for response
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"✅ Chat response: {response_data.get('type')}")
            print(f"✅ Full response: {response_data}")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection()) 