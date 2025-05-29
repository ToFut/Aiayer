#!/usr/bin/env python3

import asyncio
import websockets
import json
import time

async def test_agent_mode_with_fast_handler():
    """Test agent mode with the corrected Fast handler priority"""
    
    try:
        print("🧪 Testing Agent mode with Fast handler priority...")
        uri = "ws://localhost:8767"
        
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket")
            
            # Test the button_action message that was failing before
            test_message = {
                "type": "button_action",
                "action": "EXECUTE_PLAN", 
                "plan_id": "test_plan_001",
                "button_data": {
                    "user_request": "open Safari and search for best flights from Miami to NYC",
                    "plan_type": "automation_execution"
                },
                "timestamp": time.time()
            }
            
            print(f"📤 Sending button_action message...")
            print(f"   Message: {test_message}")
            
            # Send message and measure response time
            start_time = time.time()
            await websocket.send(json.dumps(test_message))
            
            print("⏳ Waiting for response...")
            
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                end_time = time.time()
                response_time = end_time - start_time
                
                print(f"✅ Received response in {response_time:.2f} seconds")
                
                try:
                    response_data = json.loads(response)
                    print(f"📥 Response type: {response_data.get('type', 'unknown')}")
                    print(f"📥 Response status: {response_data.get('status', 'unknown')}")
                    
                    if response_time < 2.0:
                        print("🚀 SUCCESS: Fast handler is working! (< 2 seconds)")
                    elif response_time < 10.0:
                        print("⚡ GOOD: Response within reasonable time (< 10 seconds)")
                    else:
                        print("⚠️ SLOW: Response took longer than expected")
                        
                    # Check if it's an automation plan response
                    if 'plan' in response_data or 'automation_plan' in response_data:
                        print("🎯 SUCCESS: Agent mode automation plan generated!")
                        
                    print(f"\n📋 Full response:")
                    print(json.dumps(response_data, indent=2))
                    
                except json.JSONDecodeError:
                    print(f"⚠️ Response is not valid JSON: {response}")
                    
            except asyncio.TimeoutError:
                print("❌ TIMEOUT: No response received within 10 seconds")
                print("   This suggests the WebSocket connection or handler is still slow")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    print("🔧 Testing Agent mode button_action fix with Fast handler priority")
    print("   This should now work in under 2 seconds instead of 29+ seconds")
    print("   Previous issue: 'Unknown message type: button_action' - FIXED")
    print("   Previous issue: 29s Universal handler timeout - SHOULD BE FIXED")
    print()
    
    asyncio.run(test_agent_mode_with_fast_handler())