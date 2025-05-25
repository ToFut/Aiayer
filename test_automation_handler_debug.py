#!/usr/bin/env python3

import asyncio
import websockets
import json
import uuid
from datetime import datetime

async def test_automation_handler():
    """Test if automation handler is being called in Agent mode"""
    
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
                    "client_type": "automation_debug_client",
                    "version": "1.0.0",
                    "capabilities": ["chat", "automation", "debug"]
                }
            }
            
            await websocket.send(json.dumps(register_payload))
            print("📝 Sent registration")
            
            # Wait for registration response
            response = await websocket.recv()
            reg_data = json.loads(response)
            print(f"📨 Registration response type: {reg_data.get('type')}")
            
            # Test simple Agent mode with clear automation intent
            agent_payload = {
                "type": "chat_request",
                "mode": "agent",
                "message": "click the submit button",  # Clear automation command
                "session_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "mode_context": {
                    "mode": "agent",
                    "description": "UI automation mode"
                },
                "user_intent": "automation",
                "mode_instructions": "Execute UI automation tasks."
            }
            
            print(f"🤖 Sending CLEAR AUTOMATION request: '{agent_payload['message']}'")
            await websocket.send(json.dumps(agent_payload))
            
            # Listen for response and analyze
            print("🔄 Listening for automation response...")
            response_count = 0
            
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=20.0)
                    data = json.loads(response)
                    response_count += 1
                    
                    print(f"📦 Response {response_count}: Type={data.get('type')}")
                    
                    # Look for final response
                    if (data.get("type") == "final_response" or 
                        data.get("success") is not None):
                        
                        response_text = data.get("response", "")
                        print(f"\n📋 Final Response Analysis:")
                        print(f"Response: {response_text}")
                        
                        # Check for automation indicators
                        automation_keywords = [
                            "TASK EXECUTED", "AUTOMATION ATTEMPTED", "executed successfully",
                            "steps performed", "clicking", "automation", "execute", "command"
                        ]
                        
                        manual_keywords = [
                            "manual steps", "instructions", "automation not available", 
                            "fallback", "remember", "conversation", "helpful"
                        ]
                        
                        automation_found = any(keyword.lower() in response_text.lower() 
                                             for keyword in automation_keywords)
                        manual_found = any(keyword.lower() in response_text.lower() 
                                         for keyword in manual_keywords)
                        
                        print(f"\n🔍 Analysis:")
                        print(f"✅ Automation indicators: {automation_found}")
                        print(f"❌ Manual/fallback indicators: {manual_found}")
                        
                        if automation_found and not manual_found:
                            print("✅ SUCCESS: Agent mode appears to be executing automation!")
                        elif manual_found:
                            print("❌ ISSUE: Agent mode is providing manual instructions instead of automation")
                        else:
                            print("❓ UNCLEAR: Response doesn't clearly indicate automation or manual mode")
                        
                        break
                    
                    elif data.get("type") == "error":
                        print(f"❌ Error: {data}")
                        break
                        
                except asyncio.TimeoutError:
                    print("⏰ Timeout waiting for response")
                    break
                except Exception as e:
                    print(f"❌ Error: {e}")
                    break
            
            print(f"\n📊 Total responses: {response_count}")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    print("🧪 Testing Agent mode automation handler...")
    asyncio.run(test_automation_handler())