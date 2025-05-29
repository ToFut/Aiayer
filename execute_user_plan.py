#!/usr/bin/env python3

import asyncio
import websockets
import json
import time

async def execute_user_flight_plan():
    """Execute the user's Safari flight search plan"""
    
    try:
        print("🚀 Executing your Safari flight search plan...")
        uri = "ws://localhost:8767"
        
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to backend")
            
            # Wait for connection response
            connection_response = await websocket.recv()
            print("📥 Connection established")
            
            await asyncio.sleep(1)
            
            # Execute the plan that was generated
            plan_id = "fast_fallback_1748368019_overlay_session_1748368008976"
            
            button_action_message = {
                "type": "button_action",
                "action": "EXECUTE_PLAN", 
                "plan_id": plan_id,
                "button_data": {
                    "user_request": "open Safari and search for best flights",
                    "plan_type": "automation_execution"
                },
                "timestamp": time.time(),
                "session_id": "overlay_session_1748368008976"
            }
            
            print(f"🎯 Executing plan: {plan_id}")
            print("📤 Sending execution command...")
            
            start_time = time.time()
            await websocket.send(json.dumps(button_action_message))
            
            print("⏳ Waiting for execution...")
            
            # Wait for execution response
            response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
            execution_time = time.time() - start_time
            
            print(f"✅ Response received in {execution_time:.2f} seconds")
            
            try:
                response_data = json.loads(response)
                response_type = response_data.get('type', 'unknown')
                
                print(f"📥 Response type: {response_type}")
                
                if response_type in ['automation_success', 'streaming_response', 'agent_response']:
                    print("🎉 SUCCESS: Safari flight search automation executed!")
                elif response_type == 'agent_execution_error':
                    print("⚠️ Execution had issues, but the button_action message was processed correctly")
                    error = response_data.get('error', 'unknown')
                    print(f"   Error details: {error}")
                elif response_type == 'agent_confirmation_error':
                    print("⚠️ Plan validation issue")
                    error = response_data.get('error', 'unknown')
                    print(f"   Error details: {error}")
                else:
                    print(f"📋 Response: {response_type}")
                
                # Show response details
                if 'message' in response_data:
                    print(f"💬 Message: {response_data['message']}")
                    
                print(f"\n📋 Full response:")
                print(json.dumps(response_data, indent=2))
                
            except json.JSONDecodeError:
                print(f"⚠️ Non-JSON response: {response}")
                
    except asyncio.TimeoutError:
        print("❌ TIMEOUT: Execution took too long")
    except Exception as e:
        print(f"❌ Execution failed: {e}")

if __name__ == "__main__":
    print("🔧 Executing your Safari flight search automation")
    print("   Plan ID: fast_fallback_1748368019_overlay_session_1748368008976")
    print("   Task: Open Safari and search for best flights")
    print()
    
    asyncio.run(execute_user_flight_plan())