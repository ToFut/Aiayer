#!/usr/bin/env python3
"""
Test script to verify the enhanced enterprise backend is providing real AI responses
"""
import asyncio
import websockets
import json

async def test_ai_response():
    uri = "ws://localhost:8765"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to enhanced enterprise backend")
            
            # Register first
            register_msg = {
                "type": "register",
                "client_type": "test_client"
            }
            await websocket.send(json.dumps(register_msg))
            response = await websocket.recv()
            print(f"Registration response: {response}")
            
            # Test Agent mode with a real question
            test_msg = {
                "type": "agent_request",
                "mode": "agent", 
                "message": "What are the main benefits of using artificial intelligence in business?",
                "context": {
                    "session_id": "test_session_123",
                    "timestamp": "2025-05-22T14:40:00Z"
                }
            }
            
            print(f"\n📤 Sending test message: {test_msg['message']}")
            await websocket.send(json.dumps(test_msg))
            
            # Wait for response
            response = await websocket.recv()
            response_data = json.loads(response)
            
            print(f"\n📥 Response received:")
            print(f"Type: {response_data.get('type')}")
            print(f"Mode: {response_data.get('mode')}")
            print(f"Success: {response_data.get('success')}")
            print(f"Response: {response_data.get('response', 'No response field')}")
            
            # Check if it's a real AI response (not a template)
            response_text = response_data.get('response', '')
            if 'Professional agent mode response for:' in response_text:
                print("❌ Still getting template responses!")
            else:
                print("✅ Getting real AI responses!")
                
    except Exception as e:
        print(f"❌ Error testing AI response: {e}")

if __name__ == "__main__":
    asyncio.run(test_ai_response())