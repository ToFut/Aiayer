#!/usr/bin/env python3

import asyncio
import websockets
import json
import time

async def test_execution_debug():
    """Debug version with longer timeout and more detailed logging"""
    
    uri = "ws://localhost:8767"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔗 Connected to backend server")
            
            # Register client
            register_msg = {
                "type": "register",
                "client_id": f"debug_test_{int(time.time())}"
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
            
            print(f"\n🤖 Sending automation request...")
            await websocket.send(json.dumps(agent_request))
            
            # Get response with buttons
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"✅ Got response: {response_data.get('type')} with {len(response_data.get('buttons', []))} buttons")
            
            if response_data.get('interactive') and response_data.get('buttons'):
                # Click DO button
                plan_id = response_data['plan_id']
                print(f"\n🟢 Clicking DO button for plan: {plan_id}")
                
                button_action = {
                    "type": "button_action",
                    "action": "execute_plan",
                    "plan_id": plan_id,
                    "button_data": response_data['buttons'][0],
                    "timestamp": int(time.time() * 1000)
                }
                
                await websocket.send(json.dumps(button_action))
                print(f"📤 Button action sent, waiting for responses...")
                
                # Listen for ALL responses with longer timeout
                message_count = 0
                while message_count < 10:  # Listen for more messages
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=10.0)  # Longer timeout
                        data = json.loads(response)
                        message_count += 1
                        
                        print(f"\n📨 Message {message_count}:")
                        print(f"   Type: {data.get('type')}")
                        print(f"   Success: {data.get('success')}")
                        
                        if data.get('type') == 'execution_progress':
                            print(f"   Progress: {data.get('progress')}%")
                            print(f"   Step: {data.get('currentStep')}")
                            
                        elif data.get('type') == 'execution_complete':
                            print(f"   🎯 EXECUTION COMPLETED!")
                            print(f"   Response: {data.get('response', '')[:100]}...")
                            break
                            
                        elif data.get('response'):
                            print(f"   Response: {data.get('response', '')[:100]}...")
                            
                    except asyncio.TimeoutError:
                        print(f"⏰ Timeout after {message_count} messages")
                        break
                        
                print(f"\n📊 Total messages received: {message_count}")
                
            else:
                print("❌ No interactive buttons found")
                
    except Exception as e:
        print(f"❌ Debug test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_execution_debug())