#!/usr/bin/env python3

import asyncio
import websockets
import json
import time

async def test_agent_mode_buttons():
    """Test AGENT mode to verify interactive buttons are working"""
    
    uri = "ws://localhost:8767"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔗 Connected to backend server")
            
            # Register client
            register_msg = {
                "type": "register",
                "client_id": f"test_client_{int(time.time())}"
            }
            await websocket.send(json.dumps(register_msg))
            response = await websocket.recv()
            print(f"✅ Registration response: {json.loads(response)}")
            
            # Test AGENT mode request
            agent_request = {
                "type": "chat_request",
                "mode": "agent",
                "message": "write SEGEV in notepad",
                "timestamp": int(time.time() * 1000)
            }
            
            print(f"\n🤖 Sending AGENT mode request: {agent_request['message']}")
            await websocket.send(json.dumps(agent_request))
            
            # Wait for response
            print("⏳ Waiting for response...")
            response = await websocket.recv()
            response_data = json.loads(response)
            
            print(f"\n📦 Response received:")
            print(f"Type: {response_data.get('type')}")
            print(f"Message: {response_data.get('message', '')[:200]}...")
            
            # Check for interactive buttons
            if response_data.get('interactive') and response_data.get('buttons'):
                print(f"\n🎯 SUCCESS! Interactive buttons found:")
                for i, button in enumerate(response_data['buttons']):
                    print(f"  Button {i+1}: {button.get('text')} (action: {button.get('action')})")
                
                # Test clicking the DO button
                do_button = next((b for b in response_data['buttons'] if 'do_' in b.get('id', '')), None)
                if do_button:
                    print(f"\n🟢 Testing DO button click...")
                    button_action = {
                        "type": "button_action",
                        "action": do_button['action'],
                        "plan_id": do_button['id'].replace('do_', ''),
                        "button_data": do_button,
                        "timestamp": int(time.time() * 1000)
                    }
                    await websocket.send(json.dumps(button_action))
                    
                    # Wait for execution response
                    exec_response = await websocket.recv()
                    exec_data = json.loads(exec_response)
                    print(f"✅ Execution response: {exec_data.get('message', '')[:200]}...")
            else:
                print("❌ No interactive buttons found in response!")
                print(f"Interactive: {response_data.get('interactive')}")
                print(f"Buttons: {response_data.get('buttons')}")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_agent_mode_buttons())