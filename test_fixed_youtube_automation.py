#!/usr/bin/env python3

import asyncio
import websockets
import json
import uuid
from datetime import datetime

async def test_youtube_automation():
    """Test the fixed YouTube automation system"""
    
    try:
        # Connect to the fixed backend
        uri = "ws://localhost:8767"
        print(f"🔌 Connecting to fixed backend at {uri}...")
        
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to backend")
            
            # Send registration
            register_payload = {
                "type": "register",
                "payload": {
                    "client_type": "youtube_automation_test",
                    "version": "1.0.0",
                    "capabilities": ["chat", "agent_execution", "automation", "web_navigation"]
                }
            }
            
            await websocket.send(json.dumps(register_payload))
            print("📝 Sent registration")
            
            # Wait for registration response
            response = await websocket.recv()
            reg_data = json.loads(response)
            print(f"📨 Registration: {reg_data.get('type', 'unknown')}")
            
            # Send YouTube automation request
            agent_payload = {
                "type": "chat_request",
                "mode": "agent",
                "message": "open youtube and search SEGEV",
                "session_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "mode_context": {
                    "mode": "agent",
                    "description": "YouTube automation and search",
                    "target": "youtube.com",
                    "search_query": "SEGEV"
                },
                "user_intent": "web_automation",
                "mode_instructions": "Open YouTube website and search for 'SEGEV' using browser automation"
            }
            
            print(f"\n🎬 Sending YouTube automation request...")
            print(f"🔍 Task: Open YouTube and search for 'SEGEV'")
            await websocket.send(json.dumps(agent_payload))
            
            # Listen for responses
            print("🔄 Waiting for automation response...")
            response_count = 0
            automation_steps = []
            
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=45.0)
                    data = json.loads(response)
                    response_count += 1
                    
                    response_type = data.get("type", "unknown")
                    print(f"📦 Response {response_count}: {response_type}")
                    
                    # Track automation steps
                    if response_type == "automation_step":
                        step = data.get("step", {})
                        automation_steps.append(step)
                        print(f"  🔧 Step: {step.get('description', 'Unknown')}")
                        if step.get("status") == "completed":
                            print(f"    ✅ Completed: {step.get('action', '')}")
                        elif step.get("status") == "failed":
                            print(f"    ❌ Failed: {step.get('error', '')}")
                    
                    # Show automation plan
                    elif response_type == "automation_plan":
                        plan = data.get("plan", {})
                        print(f"📋 Plan: {plan.get('description', 'No description')}")
                        plan_steps = plan.get("steps", [])
                        if plan_steps:
                            print(f"  📝 {len(plan_steps)} steps planned:")
                            for i, step in enumerate(plan_steps, 1):
                                print(f"    {i}. {step}")
                        else:
                            print("  ⚠️ No steps in plan")
                    
                    # Progress updates
                    elif response_type == "progress_update":
                        progress = data.get("progress", {})
                        print(f"📊 Progress: {progress.get('percentage', 0)}% - {progress.get('status', 'Unknown')}")
                    
                    # Final response
                    elif (response_type in ["final_response", "chat_response_complete"] or 
                          data.get("success") is not None):
                        print("✅ Final response received")
                        
                        response_text = data.get("response", data.get("full_response", ""))
                        print(f"\n📋 Full Response:\n{response_text}")
                        
                        # Analyze success
                        if automation_steps:
                            print(f"\n🔧 Automation executed {len(automation_steps)} steps")
                            successful_steps = [s for s in automation_steps if s.get("status") == "completed"]
                            print(f"✅ {len(successful_steps)} steps completed successfully")
                        
                        # Check for success indicators
                        success_keywords = ["opened", "youtube", "searched", "segev", "completed", "executed", "automated"]
                        if any(keyword in response_text.lower() for keyword in success_keywords):
                            print("🎯 Automation appears successful!")
                        else:
                            print("❓ Automation success unclear")
                        
                        break
                    
                    elif response_type == "error":
                        print(f"❌ Error: {data.get('message', 'Unknown error')}")
                        break
                        
                except asyncio.TimeoutError:
                    print("⏰ Timeout waiting for response")
                    break
                except Exception as e:
                    print(f"❌ Error receiving message: {e}")
                    break
            
            print(f"\n📊 Summary:")
            print(f"  📦 Total responses: {response_count}")
            print(f"  🔧 Automation steps: {len(automation_steps)}")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    print("🧪 Testing Fixed YouTube Automation System")
    print("=" * 50)
    asyncio.run(test_youtube_automation())