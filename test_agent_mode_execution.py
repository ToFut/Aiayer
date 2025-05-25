#!/usr/bin/env python3

import asyncio
import websockets
import json
import uuid
from datetime import datetime

async def test_agent_mode():
    """Test Agent mode specifically to see execution flow"""
    
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
                    "client_type": "agent_test_client",
                    "version": "1.0.0",
                    "capabilities": ["chat", "agent_execution", "automation"]
                }
            }
            
            await websocket.send(json.dumps(register_payload))
            print("📝 Sent registration")
            
            # Wait for registration response
            response = await websocket.recv()
            reg_data = json.loads(response)
            print(f"📨 Registration response: {reg_data}")
            
            # Test Agent mode with a simple task
            agent_payload = {
                "type": "chat_request",
                "mode": "agent",
                "message": "Open the calculator app",
                "session_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "mode_context": {
                    "mode": "agent",
                    "description": "UI automation and task execution mode"
                },
                "user_intent": "app_automation",
                "mode_instructions": "Execute the requested task using UI automation capabilities."
            }
            
            print(f"🤖 Sending Agent mode request: {agent_payload['message']}")
            await websocket.send(json.dumps(agent_payload))
            
            # Listen for response
            print("🔄 Listening for Agent mode response...")
            response_count = 0
            
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    data = json.loads(response)
                    response_count += 1
                    
                    print(f"📦 Response {response_count}: {data}")
                    
                    # Look for final response or completion
                    if (data.get("type") == "final_response" or 
                        data.get("type") == "chat_response_complete" or
                        data.get("success") is not None):
                        print("✅ Final response received")
                        
                        # Check if it actually mentions execution
                        response_text = data.get("response", data.get("full_response", ""))
                        print(f"\n📋 Full Agent Response: {response_text}")
                        
                        # Analyze response content
                        if any(keyword in response_text.lower() for keyword in [
                            "executing", "opening", "clicked", "launched", "automated"
                        ]):
                            print("✅ Response indicates task execution")
                        else:
                            print("❌ Response does not indicate actual task execution")
                            print("🔍 This suggests Agent mode is not performing automation")
                        
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

if __name__ == "__main__":
    print("🧪 Testing Agent mode execution...")
    asyncio.run(test_agent_mode())