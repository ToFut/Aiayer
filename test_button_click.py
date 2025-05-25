#!/usr/bin/env python3

import asyncio
import websockets
import json
import time

async def test_button_functionality():
    """Test clicking the DO button to execute automation"""
    
    uri = "ws://localhost:8767"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔗 Connected to backend server")
            
            # Register client
            register_msg = {
                "type": "register", 
                "client_id": f"button_test_{int(time.time())}"
            }
            await websocket.send(json.dumps(register_msg))
            response = await websocket.recv()
            print(f"✅ Registration: {json.loads(response)['type']}")
            
            # Send AGENT request
            agent_request = {
                "type": "chat_request",
                "mode": "Agent",
                "message": "write SEGEV in notepad",
                "timestamp": int(time.time() * 1000)
            }
            
            print(f"\n🤖 Requesting: {agent_request['message']}")
            await websocket.send(json.dumps(agent_request))
            
            # Get response with buttons
            response = await websocket.recv()
            response_data = json.loads(response)
            
            print(f"✅ Got automation plan with {len(response_data['buttons'])} buttons")
            
            # Test clicking the DO button
            do_button = response_data['buttons'][0]  # First button is DO
            plan_id = do_button['plan_id']
            
            print(f"🟢 Clicking DO button (Plan ID: {plan_id})")
            
            button_action = {
                "type": "button_action",
                "action": "execute_plan",
                "plan_id": plan_id,
                "button_data": do_button,
                "timestamp": int(time.time() * 1000)
            }
            
            await websocket.send(json.dumps(button_action))
            
            # Wait for execution response
            print("⏳ Waiting for execution response...")
            exec_response = await websocket.recv()
            exec_data = json.loads(exec_response)
            
            print(f"\n🎯 Execution Result:")
            print(f"  Type: {exec_data['type']}")
            print(f"  Success: {exec_data.get('success', 'Unknown')}")
            print(f"  Action Processed: {exec_data.get('button_action_processed', False)}")
            print(f"  Response: {exec_data.get('response', '')[:200]}...")
            
            if exec_data.get('success'):
                print("✅ Button click executed successfully!")
            else:
                print("❌ Button execution failed")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_button_functionality())