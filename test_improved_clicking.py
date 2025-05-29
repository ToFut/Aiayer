#!/usr/bin/env python3

import asyncio
import websockets
import json
import time

async def test_improved_clicking():
    """Test the improved click coordinates for YouTube search"""
    
    uri = "ws://localhost:8767"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔗 Connected to backend server")
            
            # Register client
            register_msg = {
                "type": "register",
                "client_id": f"click_test_{int(time.time())}"
            }
            await websocket.send(json.dumps(register_msg))
            response = await websocket.recv()
            print(f"✅ Registration successful")
            
            # Send AGENT request
            agent_request = {
                "type": "chat_request",
                "mode": "Agent",
                "message": "open Safari, search Youtube and find Omer Adam music",
                "timestamp": int(time.time() * 1000)
            }
            
            print(f"\n🤖 Requesting automation plan...")
            await websocket.send(json.dumps(agent_request))
            
            # Get response with buttons
            response = await websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get('interactive') and response_data.get('buttons'):
                print(f"✅ Got automation plan with buttons")
                
                # Click the DO button to test improved coordinates
                plan_id = response_data['plan_id']
                print(f"🟢 Clicking DO button to test improved coordinates...")
                
                button_action = {
                    "type": "button_action",
                    "action": "execute_plan",
                    "plan_id": plan_id,
                    "button_data": response_data['buttons'][0],
                    "timestamp": int(time.time() * 1000)
                }
                
                await websocket.send(json.dumps(button_action))
                
                print(f"📊 Execution started! Check the logs for improved click coordinates.")
                print(f"🎯 Expected: Click at (735, 140) instead of (735, 100)")
                print(f"📝 Look for log messages showing 'Using improved YouTube search coordinates'")
                
                # Wait a moment for execution to start
                await asyncio.sleep(2)
                
            else:
                print("❌ No interactive buttons found")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_improved_clicking())