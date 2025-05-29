#!/usr/bin/env python3
"""
Test the improved detection through the backend integration
"""

import asyncio
import websockets
import json
import time

async def test_agent_mode():
    """Test AGENT mode with improved detection"""
    
    print("🔍 TESTING BACKEND INTEGRATION WITH IMPROVED DETECTION")
    print("=" * 60)
    
    uri = "ws://localhost:8767"
    
    try:
        async with websockets.connect(uri) as websocket:
            # Register client
            register_msg = {
                "type": "register",
                "data": {"name": "TestClient"}
            }
            await websocket.send(json.dumps(register_msg))
            
            # Wait for registration response
            response = await websocket.recv()
            print(f"📝 Registration response: {json.loads(response)}")
            
            # Send AGENT mode request
            agent_request = {
                "type": "chat_request",
                "data": {
                    "mode": "AGENT",
                    "message": "Search for 'OpenAI GPT' on Google"
                }
            }
            
            print(f"📤 Sending AGENT request: {agent_request['data']['message']}")
            await websocket.send(json.dumps(agent_request))
            
            # Wait for response
            print("⏳ Waiting for automation response...")
            response = await websocket.recv()
            result = json.loads(response)
            
            print(f"📥 Response received:")
            print(f"   Type: {result.get('type')}")
            print(f"   Success: {result.get('success')}")
            print(f"   Message: {result.get('message', 'No message')}")
            
            if result.get('data'):
                print(f"   Data: {result['data']}")
            
            print("\n✅ Backend integration test complete")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")

if __name__ == "__main__":
    asyncio.run(test_agent_mode())