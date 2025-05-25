#!/usr/bin/env python3
"""
Test the new real LLM backend
"""

import asyncio
import websockets
import json

async def test_real_backend():
    """Test the real LLM backend"""
    print("🧪 Testing Real LLM Backend...")
    
    try:
        # Connect to the backend
        uri = "ws://localhost:8767"
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to backend")
            
            # Send a chat request
            test_message = {
                "type": "chat_request",
                "mode": "Ask",
                "message": "What is machine learning?",
                "session_id": "test_session"
            }
            
            print("📤 Sending test message...")
            await websocket.send(json.dumps(test_message))
            
            # Wait for response
            print("⏳ Waiting for response...")
            response = await asyncio.wait_for(websocket.recv(), timeout=30)
            
            # Parse and display response
            response_data = json.loads(response)
            print("✅ Received response!")
            print(f"Type: {response_data.get('type')}")
            print(f"Mode: {response_data.get('mode')}")
            print(f"AI Powered: {response_data.get('ai_powered')}")
            print(f"Response: {response_data.get('response', 'No response')[:200]}...")
            
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_real_backend())