#!/usr/bin/env python3
"""
Test Agent Mode functionality to verify execution buttons appear
"""
import asyncio
import websockets
import json
import time

async def test_agent_mode():
    uri = "ws://localhost:8767"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to backend WebSocket")
            
            # Send Agent mode message
            test_message = {
                "type": "chat_message",
                "data": {
                    "message": "open Safari and go to google.com",
                    "mode": "agent",
                    "session_id": "test_session_001"
                }
            }
            
            print(f"📤 Sending Agent mode message: {test_message['data']['message']}")
            await websocket.send(json.dumps(test_message))
            
            # Wait for responses (connection + agent response)
            print("⏳ Waiting for responses...")
            
            # First response is usually connection established
            response1 = await websocket.recv()
            response1_data = json.loads(response1)
            print(f"📥 First response type: {response1_data.get('type', 'unknown')}")
            
            # Wait for actual agent response
            response2 = await websocket.recv()
            response_data = json.loads(response2)
            print(f"📥 Agent response type: {response_data.get('type', 'unknown')}")
            
            if response_data.get('type') == 'streaming_response':
                print(f"📝 Response: {response_data.get('data', {}).get('response', 'No response text')}")
                
                # Check for buttons
                buttons = response_data.get('data', {}).get('buttons', [])
                if buttons:
                    print(f"✅ SUCCESS: Found {len(buttons)} execution buttons!")
                    for i, button in enumerate(buttons):
                        print(f"   Button {i+1}: {button.get('text', 'No text')} - {button.get('action', 'No action')}")
                else:
                    print("❌ FAIL: No execution buttons found")
                
                # Check for plan_id
                plan_id = response_data.get('data', {}).get('plan_id')
                if plan_id:
                    print(f"✅ Plan ID: {plan_id}")
                else:
                    print("⚠️ No plan_id found")
                    
            else:
                print(f"❌ Unexpected response type: {response_data.get('type')}")
                print(f"Raw response: {response}")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_agent_mode())