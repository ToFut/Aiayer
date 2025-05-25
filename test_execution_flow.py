#!/usr/bin/env python3

import asyncio
import websockets
import json
import time

async def test_execution_flow():
    """Test the complete execution flow with progress updates"""
    
    uri = "ws://localhost:8767"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔗 Connected to backend server")
            
            # Register client
            register_msg = {
                "type": "register",
                "client_id": f"exec_test_{int(time.time())}"
            }
            await websocket.send(json.dumps(register_msg))
            response = await websocket.recv()
            print(f"✅ Registration successful")
            
            # Send AGENT request
            agent_request = {
                "type": "chat_request",
                "mode": "Agent",
                "message": "write SEGEV in notepad",
                "timestamp": int(time.time() * 1000)
            }
            
            print(f"\n🤖 Requesting automation plan...")
            await websocket.send(json.dumps(agent_request))
            
            # Get response with buttons
            response = await websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get('interactive') and response_data.get('buttons'):
                print(f"✅ Got automation plan with buttons")
                
                # Click the DO button
                plan_id = response_data['plan_id']
                print(f"🟢 Clicking DO button (Plan ID: {plan_id})")
                
                button_action = {
                    "type": "button_action",
                    "action": "execute_plan",
                    "plan_id": plan_id,
                    "button_data": response_data['buttons'][0],
                    "timestamp": int(time.time() * 1000)
                }
                
                await websocket.send(json.dumps(button_action))
                
                print(f"⏳ Waiting for execution progress and completion...")
                
                # Listen for progress updates and completion
                message_count = 0
                while message_count < 5:  # Listen for a few messages
                    try:
                        exec_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        exec_data = json.loads(exec_response)
                        message_count += 1
                        
                        print(f"\n📨 Message {message_count}: {exec_data.get('type')}")
                        
                        if exec_data.get('type') == 'execution_progress':
                            progress = exec_data.get('progress', 0)
                            step = exec_data.get('currentStep', 'Unknown')
                            print(f"📊 Progress: {progress}% - {step}")
                            
                        elif exec_data.get('type') == 'execution_complete':
                            print(f"✅ Execution completed!")
                            print(f"Success: {exec_data.get('success')}")
                            print(f"Response: {exec_data.get('response', '')[:100]}...")
                            break
                            
                        elif exec_data.get('type') == 'button_action_response':
                            print(f"🎯 Button action response received")
                            print(f"Success: {exec_data.get('success')}")
                            
                        else:
                            print(f"📋 Other message: {exec_data.get('type')}")
                            
                    except asyncio.TimeoutError:
                        print("⏰ Timeout waiting for next message")
                        break
                        
                print(f"\n🎉 Test completed! Check the logs for execution details.")
                
            else:
                print("❌ No interactive buttons in response")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_execution_flow())