#!/usr/bin/env python3
import asyncio
import websockets
import json
import time

async def test_youtube_automation():
    """Test the quick YouTube automation system"""
    uri = "ws://localhost:8767"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔗 Connected to backend")
            
            # Register client
            register_msg = {
                "type": "register",
                "client_id": "test_quick_automation",
                "timestamp": int(time.time() * 1000)
            }
            await websocket.send(json.dumps(register_msg))
            
            # Send YouTube search request in Agent mode
            start_time = time.time()
            agent_msg = {
                "type": "agent_mode",
                "message": "open YouTube and search SEGEV",
                "client_id": "test_quick_automation",
                "timestamp": int(time.time() * 1000)
            }
            
            print("🚀 Sending YouTube automation request...")
            await websocket.send(json.dumps(agent_msg))
            
            # Listen for responses
            step_count = 0
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    data = json.loads(response)
                    response_time = time.time() - start_time
                    
                    if data.get("type") == "agent_plan":
                        print(f"\n⚡ PLAN GENERATED in {response_time:.2f}s")
                        plan = data.get("plan", {})
                        steps = plan.get("steps", [])
                        print(f"📋 Plan has {len(steps)} steps")
                        
                        # Show first few steps to verify quality
                        for i, step in enumerate(steps[:3]):
                            print(f"   Step {i+1}: {step.get('action')} - {step.get('description')}")
                        if len(steps) > 3:
                            print(f"   ... and {len(steps)-3} more steps")
                            
                    elif data.get("type") == "agent_step":
                        step_count += 1
                        step_data = data.get("step", {})
                        print(f"🔧 Step {step_count}: {step_data.get('action')} - {step_data.get('description')}")
                        
                    elif data.get("type") == "agent_complete":
                        total_time = time.time() - start_time
                        print(f"\n✅ AUTOMATION COMPLETE in {total_time:.2f}s")
                        print(f"📊 Executed {step_count} steps")
                        break
                        
                    elif data.get("type") == "error":
                        print(f"❌ Error: {data.get('message')}")
                        break
                        
                except asyncio.TimeoutError:
                    print("⏰ Timeout waiting for response")
                    break
                except Exception as e:
                    print(f"❌ Error: {e}")
                    break
                    
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    print("🧪 Testing Quick YouTube Automation System")
    print("=" * 50)
    asyncio.run(test_youtube_automation())