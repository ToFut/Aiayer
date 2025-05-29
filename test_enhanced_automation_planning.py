#!/usr/bin/env python3

import asyncio
import websockets
import json
import time

async def test_enhanced_automation_planning():
    """Test the enhanced Fast handler with LLM for real automation planning"""
    
    try:
        print("🧪 Testing enhanced automation planning...")
        uri = "ws://localhost:8767"
        
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket")
            
            # Wait for connection response
            connection_response = await websocket.recv()
            connection_data = json.loads(connection_response)
            print(f"📥 Connection established: {connection_data.get('type')}")
            
            await asyncio.sleep(1)
            
            # Test with your original request
            agent_request = {
                "type": "chat_request",
                "mode": "Agent",
                "message": "open Safari and search for best flights from Miami to NYC",
                "session_id": "enhanced_test_session_001",
                "timestamp": time.time()
            }
            
            print("📤 Requesting enhanced automation plan...")
            print(f"   Request: {agent_request['message']}")
            print("   Expected: Real automation steps (not 0 steps)")
            
            start_time = time.time()
            await websocket.send(json.dumps(agent_request))
            
            print("⏳ Waiting for enhanced automation plan...")
            
            # Wait for plan generation response
            plan_response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
            plan_time = time.time() - start_time
            
            print(f"✅ Plan generated in {plan_time:.2f} seconds")
            
            try:
                plan_data = json.loads(plan_response)
                response_text = plan_data.get('response', '')
                
                print("\n📋 Plan Analysis:")
                
                # Check if it's a real plan with steps
                if 'Steps: 0 actions' in response_text:
                    print("❌ STILL GETTING EMPTY PLAN: 0 steps")
                    print("   Issue: LLM enhancement didn't work")
                elif 'Steps:' in response_text and 'actions' in response_text:
                    # Extract step count
                    import re
                    step_match = re.search(r'Steps: (\d+)', response_text)
                    if step_match:
                        step_count = int(step_match.group(1))
                        if step_count > 0:
                            print(f"🎉 SUCCESS: Real automation plan with {step_count} steps!")
                            print("   ✅ LLM enhancement working")
                        else:
                            print("❌ Still 0 steps")
                    else:
                        print("⚠️ Could not parse step count")
                else:
                    print("⚠️ Unexpected plan format")
                
                # Check for real automation content
                if any(keyword in response_text.lower() for keyword in ['safari', 'open', 'click', 'type', 'navigate']):
                    print("✅ Plan contains real automation keywords")
                else:
                    print("❌ Plan lacks automation content")
                
                # Check duration
                if 'Duration: 0.0s' in response_text:
                    print("❌ Still showing 0.0s duration (fallback plan)")
                else:
                    print("✅ Has realistic duration estimate")
                
                print(f"\n📋 Plan Response Preview:")
                preview = response_text[:300] + "..." if len(response_text) > 300 else response_text
                print(preview)
                
                # Check if we can extract a plan ID
                buttons = plan_data.get('buttons', [])
                execute_button = None
                for button in buttons:
                    if button.get('action') == 'execute_plan':
                        execute_button = button
                        break
                
                if execute_button:
                    plan_id = execute_button.get('plan_id', '')
                    print(f"\n🆔 Plan ID: {plan_id}")
                    
                    if 'fast_fallback' in plan_id:
                        print("⚠️ Using fallback plan (LLM not working)")
                    elif any(keyword in plan_id for keyword in ['universal', 'llm', 'enhanced']):
                        print("✅ Using enhanced LLM plan")
                    else:
                        print("📋 Plan ID type unclear")
                
            except json.JSONDecodeError:
                print(f"⚠️ Response is not valid JSON: {plan_response}")
                
    except asyncio.TimeoutError:
        print("❌ TIMEOUT: Plan generation took too long")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    print("🔧 Testing Enhanced Automation Planning")
    print("   Goal: Verify the Fast handler now has real LLM planning")
    print("   Original issue: Fast handler had 0 steps, no real automation")
    print("   Expected: Real Safari automation steps with LLM planning")
    print()
    
    asyncio.run(test_enhanced_automation_planning())