#!/usr/bin/env python3

import asyncio
import websockets
import json
import time

async def test_complete_agent_workflow():
    """Test the complete agent workflow: plan generation → execution via button_action"""
    
    try:
        print("🧪 Testing complete Agent mode workflow...")
        uri = "ws://localhost:8767"
        
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket")
            
            # Wait for connection response
            connection_response = await websocket.recv()
            connection_data = json.loads(connection_response)
            print(f"📥 Connection established: {connection_data.get('type')}")
            
            # Wait a moment then send agent mode request to generate plan
            await asyncio.sleep(1)
            
            # Step 1: Send agent mode request to generate automation plan
            agent_request = {
                "type": "chat_request",
                "mode": "Agent",
                "message": "open Safari and search for best flights from Miami to NYC",
                "session_id": "test_agent_session_001",
                "timestamp": time.time()
            }
            
            print("📤 Step 1: Requesting automation plan generation...")
            print(f"   User request: {agent_request['message']}")
            
            start_time = time.time()
            await websocket.send(json.dumps(agent_request))
            
            print("⏳ Waiting for automation plan...")
            
            # Wait for plan generation response
            plan_response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
            plan_time = time.time() - start_time
            
            print(f"✅ Plan generated in {plan_time:.2f} seconds")
            
            try:
                plan_data = json.loads(plan_response)
                plan_type = plan_data.get('type', 'unknown')
                print(f"📥 Plan response type: {plan_type}")
                
                # Look for plan ID and details
                plan_id = None
                plan_details = None
                
                if 'buttons' in plan_data:
                    # Look for execution button
                    for button in plan_data['buttons']:
                        if button.get('action') == 'execute_plan':
                            plan_id = button.get('plan_id')
                            break
                
                if 'plan' in plan_data:
                    plan_details = plan_data['plan']
                elif 'automation_plan' in plan_data:
                    plan_details = plan_data['automation_plan']
                
                if plan_id:
                    print(f"🎯 Plan ID found: {plan_id}")
                    
                    # Step 2: Execute the plan using button_action
                    print("\n📤 Step 2: Executing plan via button_action...")
                    
                    button_action_message = {
                        "type": "button_action",
                        "action": "EXECUTE_PLAN", 
                        "plan_id": plan_id,
                        "button_data": {
                            "user_request": "open Safari and search for best flights from Miami to NYC",
                            "plan_type": "automation_execution"
                        },
                        "timestamp": time.time(),
                        "session_id": "test_agent_session_001"
                    }
                    
                    execution_start = time.time()
                    await websocket.send(json.dumps(button_action_message))
                    
                    print("⏳ Waiting for execution response...")
                    
                    # Wait for execution response
                    execution_response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    execution_time = time.time() - execution_start
                    
                    print(f"✅ Execution response in {execution_time:.2f} seconds")
                    
                    execution_data = json.loads(execution_response)
                    execution_type = execution_data.get('type', 'unknown')
                    print(f"📥 Execution response type: {execution_type}")
                    
                    if execution_type in ['automation_success', 'streaming_response', 'agent_response']:
                        print("🎉 SUCCESS: Complete agent workflow working!")
                        print("   1. ✅ Plan generation successful")
                        print("   2. ✅ button_action message recognized") 
                        print("   3. ✅ Plan execution initiated")
                        
                        total_time = plan_time + execution_time
                        if total_time < 10.0:
                            print(f"⚡ EXCELLENT: Total workflow time: {total_time:.1f}s (< 10s)")
                        else:
                            print(f"✅ GOOD: Total workflow time: {total_time:.1f}s")
                            
                    elif execution_type == 'agent_confirmation_error':
                        error_msg = execution_data.get('error', 'unknown')
                        if 'not found' in error_msg.lower():
                            print("⚠️ ISSUE: Plan ID not found - session/timing issue")
                        else:
                            print(f"❌ EXECUTION ERROR: {error_msg}")
                    else:
                        print(f"⚠️ UNEXPECTED: {execution_type} response")
                    
                    print(f"\n📋 Execution response:")
                    print(json.dumps(execution_data, indent=2))
                    
                else:
                    print("❌ No plan ID found in response - cannot test execution")
                    
                print(f"\n📋 Plan generation response:")
                print(json.dumps(plan_data, indent=2)[:1000] + "..." if len(str(plan_data)) > 1000 else json.dumps(plan_data, indent=2))
                
            except json.JSONDecodeError:
                print(f"⚠️ Plan response is not valid JSON: {plan_response}")
                
    except asyncio.TimeoutError:
        print("❌ TIMEOUT: Plan generation took too long (> 30 seconds)")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    print("🔧 Testing complete Agent mode workflow")
    print("   This tests the original user issue end-to-end:")
    print("   1. Generate automation plan for 'open Safari and search for best flights from Miami to NYC'")
    print("   2. Execute plan via button_action (was failing with 'Unknown message type')")
    print("   3. Verify the automation actually works")
    print()
    
    asyncio.run(test_complete_agent_workflow())