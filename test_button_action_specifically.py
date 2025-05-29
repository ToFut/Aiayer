#!/usr/bin/env python3

import asyncio
import websockets
import json
import time

async def test_button_action_after_connection():
    """Test button_action specifically after connection is established"""
    
    try:
        print("🧪 Testing button_action message handling after connection...")
        uri = "ws://localhost:8767"
        
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket")
            
            # First, wait for connection response
            connection_response = await websocket.recv()
            connection_data = json.loads(connection_response)
            print(f"📥 Connection established: {connection_data.get('type')}")
            
            # Wait a moment then send the actual button_action
            await asyncio.sleep(1)
            
            # Send the button_action message that was originally failing
            button_action_message = {
                "type": "button_action",
                "action": "EXECUTE_PLAN", 
                "plan_id": "safari_flight_search_001",
                "button_data": {
                    "user_request": "open Safari and search for best flights from Miami to NYC",
                    "plan_type": "automation_execution",
                    "automation_mode": "agent"
                },
                "timestamp": time.time(),
                "session_id": "test_session_001"
            }
            
            print(f"📤 Sending button_action message...")
            print(f"   Original issue: 'Unknown message type: button_action'")
            print(f"   Expected: Automation plan generation and execution")
            
            # Send message and measure response time
            start_time = time.time()
            await websocket.send(json.dumps(button_action_message))
            
            print("⏳ Waiting for automation response...")
            
            try:
                # Wait for response with longer timeout for automation planning
                response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                end_time = time.time()
                response_time = end_time - start_time
                
                print(f"✅ Received response in {response_time:.2f} seconds")
                
                try:
                    response_data = json.loads(response)
                    response_type = response_data.get('type', 'unknown')
                    print(f"📥 Response type: {response_type}")
                    print(f"📥 Response status: {response_data.get('status', 'unknown')}")
                    
                    # Check if this is actually an automation response
                    if response_type in ['automation_plan', 'agent_response', 'streaming_response']:
                        print("🎯 SUCCESS: button_action processed as automation request!")
                        
                        if 'plan' in response_data:
                            print("📋 Automation plan received:")
                            plan = response_data['plan']
                            print(f"   Action: {plan.get('action', 'unknown')}")
                            print(f"   Target: {plan.get('target', 'unknown')}")
                            
                        if response_time < 5.0:
                            print("⚡ EXCELLENT: Fast handler response (< 5 seconds)")
                        elif response_time < 15.0:
                            print("✅ GOOD: Reasonable response time (< 15 seconds)")
                        else:
                            print(f"⚠️ SLOW: Took {response_time:.1f} seconds")
                            
                    elif response_type == 'error':
                        error_msg = response_data.get('error', 'unknown error')
                        if 'Unknown message type' in error_msg:
                            print("❌ FAILED: Still getting 'Unknown message type' error")
                            print(f"   Error: {error_msg}")
                        else:
                            print(f"❌ FAILED: Other error - {error_msg}")
                    else:
                        print(f"⚠️ UNEXPECTED: Received {response_type} instead of automation response")
                    
                    print(f"\n📋 Full response:")
                    print(json.dumps(response_data, indent=2))
                    
                except json.JSONDecodeError:
                    print(f"⚠️ Response is not valid JSON: {response}")
                    
            except asyncio.TimeoutError:
                print("❌ TIMEOUT: No response received within 30 seconds")
                print("   This suggests automation handler is hanging or not responding")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    print("🔧 Testing the specific button_action fix")
    print("   Original user request: 'open Safari and search for best flights from Miami to NYC'")
    print("   Original error: 'Unknown message type: button_action'")
    print("   Expected result: Automation plan generation for Safari + flight search")
    print()
    
    asyncio.run(test_button_action_after_connection())