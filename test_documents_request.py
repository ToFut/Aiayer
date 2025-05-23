#!/usr/bin/env python3
import asyncio
import websockets
import json
import time

async def test_documents_request():
    """Test the exact Documents Folder request"""
    try:
        uri = "ws://localhost:8767"
        print(f"🔌 Testing Documents Folder request...")
        
        async with websockets.connect(uri) as websocket:
            # Wait for welcome
            welcome = await websocket.recv()
            print("✅ Connected")
            
            # Send the exact request
            request = {
                "type": "chat_request",
                "query": "click on Documents Folder",
                "mode": "agent",
                "timestamp": str(int(time.time()))
            }
            
            print(f"🚀 Sending: {request['query']}")
            await websocket.send(json.dumps(request))
            
            # Wait for response
            response = await websocket.recv()
            response_data = json.loads(response)
            
            print(f"📨 Response type: {response_data.get('type')}")
            payload = response_data.get('payload', {})
            print(f"💬 Response: {payload.get('response', 'No response')[:200]}...")
            print(f"✅ Success: {payload.get('success', False)}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_documents_request())