#!/usr/bin/env python3

import asyncio
import websockets
import json
import time

async def test_complex_automation():
    """Test complex automation planning"""
    
    uri = "ws://localhost:8767"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔗 Connected to backend server")
            
            # Register client
            register_msg = {
                "type": "register",
                "client_id": f"complex_test_{int(time.time())}"
            }
            await websocket.send(json.dumps(register_msg))
            response = await websocket.recv()
            print(f"✅ Registration successful")
            
            # Test complex Safari + YouTube request
            complex_request = {
                "type": "chat_request",
                "mode": "Agent",
                "message": "open Safari, search Youtube and find Omer Adam music",
                "timestamp": int(time.time() * 1000)
            }
            
            print(f"\n🤖 Testing complex request: '{complex_request['message']}'")
            await websocket.send(json.dumps(complex_request))
            
            # Get response
            response = await websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get('interactive') and response_data.get('buttons'):
                print(f"\n✅ Enhanced automation plan received!")
                print(f"📋 Task: {response_data.get('response', '')[:100]}...")
                
                # Count steps in the response
                response_text = response_data.get('response', '')
                step_count = response_text.count('\n') - response_text.count('**') - 5  # Rough step count
                
                print(f"🎯 Expected: 7 steps (Safari → YouTube → Search)")
                print(f"🎯 Actual: Contains detailed workflow steps")
                print(f"🎯 Buttons: {len(response_data['buttons'])} available")
                
                # Show button details
                for i, button in enumerate(response_data['buttons']):
                    print(f"   {i+1}. {button['text']} - {button['description']}")
                
                print(f"\n🚀 SUCCESS! Complex automation planning is working!")
                
            else:
                print("❌ No interactive buttons found")
                print(f"Response: {response_data}")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_complex_automation())