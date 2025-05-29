#!/usr/bin/env python3

import asyncio
import websockets
import json
import uuid
from datetime import datetime

async def open_youtube_and_search():
    """Open YouTube and search for SEGEV"""
    
    try:
        # Connect to backend
        uri = "ws://localhost:8767"
        print(f"🔌 Connecting to {uri}...")
        
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to backend")
            
            # Send registration
            register_payload = {
                "type": "register",
                "payload": {
                    "client_type": "youtube_automation_client",
                    "version": "1.0.0",
                    "capabilities": ["chat", "agent_execution", "automation", "web_navigation"]
                }
            }
            
            await websocket.send(json.dumps(register_payload))
            print("📝 Sent registration")
            
            # Wait for registration response
            response = await websocket.recv()
            reg_data = json.loads(response)
            print(f"📨 Registration response: {reg_data}")
            
            # Send agent request to open YouTube and search for SEGEV
            agent_payload = {
                "type": "chat_request",
                "mode": "agent",
                "message": "Open YouTube and search for SEGEV",
                "session_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "mode_context": {
                    "mode": "agent",
                    "description": "Web automation and navigation mode",
                    "target_site": "youtube.com",
                    "search_term": "SEGEV"
                },
                "user_intent": "web_automation",
                "mode_instructions": "1. Open a web browser 2. Navigate to YouTube.com 3. Find the search box 4. Type 'SEGEV' 5. Press Enter or click search button",
                "automation_context": {
                    "action_type": "web_search",
                    "site": "youtube",
                    "query": "SEGEV"
                }
            }
            
            print(f"🎬 Sending YouTube automation request...")
            print(f"🔍 Search term: SEGEV")
            await websocket.send(json.dumps(agent_payload))
            
            # Listen for response
            print("🔄 Listening for automation response...")
            response_count = 0
            
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=60.0)
                    data = json.loads(response)
                    response_count += 1
                    
                    print(f"📦 Response {response_count}: {data.get('type', 'unknown')}")
                    
                    # Show any step-by-step automation updates
                    if data.get("type") == "automation_step":
                        step_info = data.get("step", {})
                        print(f"🔧 Automation Step: {step_info.get('description', 'Unknown step')}")
                        if step_info.get("status") == "completed":
                            print(f"✅ Step completed: {step_info.get('action', 'Unknown action')}")
                        elif step_info.get("status") == "failed":
                            print(f"❌ Step failed: {step_info.get('error', 'Unknown error')}")
                    
                    # Show planning information
                    elif data.get("type") == "automation_plan":
                        plan = data.get("plan", {})
                        print(f"📋 Automation Plan: {plan.get('description', 'No description')}")
                        steps = plan.get("steps", [])
                        for i, step in enumerate(steps, 1):
                            print(f"   {i}. {step}")
                    
                    # Look for final response or completion
                    elif (data.get("type") == "final_response" or 
                          data.get("type") == "chat_response_complete" or
                          data.get("success") is not None):
                        print("✅ Final response received")
                        
                        response_text = data.get("response", data.get("full_response", ""))
                        print(f"\n📋 Full Response: {response_text}")
                        
                        # Check if automation was successful
                        if any(keyword in response_text.lower() for keyword in [
                            "opened", "youtube", "searched", "segev", "completed", "found"
                        ]):
                            print("✅ YouTube automation appears successful")
                        else:
                            print("❓ Automation status unclear from response")
                        
                        break
                    
                    elif data.get("type") == "error":
                        print(f"❌ Error received: {data}")
                        break
                        
                except asyncio.TimeoutError:
                    print("⏰ Timeout waiting for response")
                    break
                except Exception as e:
                    print(f"❌ Error receiving message: {e}")
                    break
            
            print(f"\n📊 Total responses received: {response_count}")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("💡 Make sure the automation backend is running on port 8767")

if __name__ == "__main__":
    print("🎬 Starting YouTube automation...")
    print("🔍 Task: Open YouTube and search for 'SEGEV'")
    print("=" * 50)
    asyncio.run(open_youtube_and_search())