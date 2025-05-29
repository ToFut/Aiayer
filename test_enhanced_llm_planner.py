#!/usr/bin/env python3

import asyncio
import websockets
import json
import uuid
from datetime import datetime

async def test_enhanced_automation():
    """Test the enhanced LLM automation planner"""
    
    try:
        # Connect to enhanced backend
        uri = "ws://localhost:8767"
        print(f"🔌 Connecting to enhanced backend at {uri}...")
        
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to enhanced backend")
            
            # Register
            register_payload = {
                "type": "register",
                "payload": {
                    "client_type": "enhanced_automation_test",
                    "version": "1.0.0",
                    "capabilities": ["chat", "agent_execution", "automation"]
                }
            }
            
            await websocket.send(json.dumps(register_payload))
            response = await websocket.recv()
            reg_data = json.loads(response)
            print(f"📨 Registration: {reg_data.get('type', 'unknown')}")
            
            # Test YouTube search automation
            session_id = str(uuid.uuid4())
            agent_payload = {
                "type": "chat_request",
                "mode": "agent",
                "message": "open YouTube and search for SEGEV",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "mode_context": {
                    "mode": "agent",
                    "description": "Enhanced YouTube automation with detailed Mac-specific steps",
                    "environment": "macOS",
                    "screen_resolution": "1470x956"
                }
            }
            
            print(f"\n🎬 Testing Enhanced YouTube Automation...")
            print(f"🔍 Request: {agent_payload['message']}")
            await websocket.send(json.dumps(agent_payload))
            
            # Wait for the automation plan
            plan_id = None
            automation_steps = []
            
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=60.0)
                    data = json.loads(response)
                    
                    response_type = data.get("type", "unknown")
                    print(f"📦 Response: {response_type}")
                    
                    if data.get("plan_id"):
                        plan_id = data["plan_id"]
                        print(f"\n📋 Plan Created: {plan_id}")
                        
                        # Show plan details
                        response_text = data.get("response", "")
                        if "Automation Plan:" in response_text:
                            print("📝 Plan Details:")
                            plan_lines = response_text.split("Automation Plan:")[1].split("Plan ID:")[0].strip()
                            for line in plan_lines.split('\n'):
                                if line.strip():
                                    print(f"  {line.strip()}")
                        
                        # Execute the plan immediately
                        button_payload = {
                            "type": "button_action",
                            "action": "execute_plan",
                            "plan_id": plan_id,
                            "session_id": session_id,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        print(f"\n🟢 Executing automation plan...")
                        await websocket.send(json.dumps(button_payload))
                        
                    elif response_type == "progress_update":
                        progress = data.get("progress", {})
                        print(f"📊 Progress: {progress.get('percentage', 0)}% - {progress.get('status', 'Unknown')}")
                        
                    elif response_type == "automation_step":
                        step = data.get("step", {})
                        automation_steps.append(step)
                        print(f"🔧 Step: {step.get('description', 'Unknown')} ({step.get('status', 'unknown')})")
                        
                    elif response_type == "final_response":
                        response_text = data.get("response", "")
                        print(f"\n📋 Final Response:")
                        print(response_text)
                        
                        # Analyze the automation quality
                        print(f"\n📊 Automation Analysis:")
                        print(f"  📦 Total steps tracked: {len(automation_steps)}")
                        
                        # Check for execution indicators
                        execution_keywords = ["executed", "completed", "automation", "steps", "success"]
                        if any(keyword in response_text.lower() for keyword in execution_keywords):
                            print("  ✅ Response indicates automation execution")
                        else:
                            print("  ❓ Response may not indicate actual execution")
                        
                        # Check for detailed steps
                        if "Step" in response_text and len(automation_steps) > 0:
                            print("  ✅ Detailed step-by-step execution detected")
                        else:
                            print("  ❌ No detailed step execution detected")
                        
                        break
                        
                    elif response_type == "error":
                        print(f"❌ Error: {data.get('message', 'Unknown error')}")
                        break
                        
                except asyncio.TimeoutError:
                    print("⏰ Timeout waiting for response")
                    break
                except Exception as e:
                    print(f"❌ Error: {e}")
                    break
            
            print(f"\n🎯 Test Summary:")
            print(f"  📋 Plan ID: {plan_id or 'Not created'}")
            print(f"  🔧 Steps tracked: {len(automation_steps)}")
            print(f"  ✅ Enhanced LLM planner test completed")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    print("🧪 Enhanced LLM Automation Planner Test")
    print("🎯 Testing detailed Mac-specific automation plans")
    print("=" * 60)
    asyncio.run(test_enhanced_automation())