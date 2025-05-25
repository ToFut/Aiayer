#!/usr/bin/env python3

import asyncio
import websockets
import json
import uuid

async def test_agent_mode():
    """Test Agent mode with 'write SEGEV in notepad' to verify LLM parsing fix"""
    
    uri = "ws://localhost:8767"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔗 Connected to backend")
            
            # Register as test client
            register_msg = {
                "type": "register", 
                "client_type": "test_client",
                "version": "1.0.0"
            }
            await websocket.send(json.dumps(register_msg))
            print("✅ Registered with backend")
            
            # Send Agent mode command
            session_id = str(uuid.uuid4())
            test_message = {
                "type": "chat_request",
                "mode": "Agent",
                "message": "write SEGEV in notepad",
                "session_id": session_id
            }
            
            print(f"🚀 Sending Agent command: {test_message['message']}")
            print(f"📋 Session ID: {session_id}")
            await websocket.send(json.dumps(test_message))
            
            # Listen for responses
            response_count = 0
            max_responses = 10
            
            while response_count < max_responses:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    data = json.loads(response)
                    response_count += 1
                    
                    print(f"\n📨 Response {response_count}:")
                    print(f"Type: {data.get('type', 'unknown')}")
                    
                    if data.get("type") == "agent_confirmation":
                        print("🎯 AGENT CONFIRMATION RECEIVED!")
                        print(f"Session ID: {data.get('sessionId')}")
                        print(f"Requires Confirmation: {data.get('requiresConfirmation')}")
                        print(f"Risk Level: {data.get('riskLevel')}")
                        print(f"Estimated Duration: {data.get('estimatedDuration')}")
                        
                        # Check execution plan details
                        plan = data.get('executionPlan', {})
                        print(f"Action: {plan.get('action', 'unknown')}")
                        print(f"Target: {plan.get('target_description', 'unknown')}")
                        print(f"Text to Type: {plan.get('text_to_type', 'unknown')}")
                        
                        # Verify single action (not multiple)
                        action = plan.get('action', '')
                        if '|' in action:
                            print(f"❌ ISSUE: Multiple actions detected: {action}")
                        else:
                            print(f"✅ SUCCESS: Single action detected: {action}")
                        
                        # Send confirmation to execute
                        confirm_msg = {
                            "type": "agent_confirmation",
                            "sessionId": session_id,
                            "action": "execute"
                        }
                        print(f"📤 Sending execution confirmation...")
                        await websocket.send(json.dumps(confirm_msg))
                        
                    elif data.get("type") == "execution_progress":
                        print(f"⚡ EXECUTION PROGRESS:")
                        print(f"Step: {data.get('currentStep', 'unknown')}")
                        print(f"Progress: {data.get('progress', 0)}%")
                        print(f"Status: {data.get('status', 'unknown')}")
                        
                    elif data.get("type") == "execution_complete":
                        print(f"🏁 EXECUTION COMPLETE:")
                        print(f"Success: {data.get('success', False)}")
                        print(f"Result: {data.get('result', 'unknown')}")
                        break
                        
                    elif data.get("type") == "final_response":
                        print(f"💬 Final Response: {data.get('message', '')[:200]}...")
                        
                        # Check if this contains agent confirmation data
                        if data.get('requiresConfirmation'):
                            print(f"🎯 CONFIRMATION DETECTED IN FINAL RESPONSE!")
                            print(f"Requires Confirmation: {data.get('requiresConfirmation')}")
                            print(f"Risk Level: {data.get('riskLevel')}")
                            print(f"Estimated Duration: {data.get('estimatedDuration')}")
                            
                            # Check execution plan details
                            plan = data.get('executionPlan', {})
                            print(f"Action: {plan.get('action', 'unknown')}")
                            print(f"Target: {plan.get('target_description', 'unknown')}")
                            print(f"Text to Type: {plan.get('text_to_type', 'unknown')}")
                            
                            # Verify single action (not multiple)
                            action = plan.get('action', '')
                            if '|' in action:
                                print(f"❌ ISSUE: Multiple actions detected: {action}")
                            else:
                                print(f"✅ SUCCESS: Single action detected: {action}")
                            
                            # Send confirmation to execute
                            confirm_msg = {
                                "type": "agent_confirmation",
                                "session_id": session_id,
                                "action": "DO"
                            }
                            print(f"📤 Sending execution confirmation...")
                            await websocket.send(json.dumps(confirm_msg))
                        
                    else:
                        print(f"📋 Other response: {json.dumps(data, indent=2)[:200]}...")
                        
                except asyncio.TimeoutError:
                    print("⏰ Timeout waiting for response")
                    break
                except Exception as e:
                    print(f"❌ Error receiving response: {e}")
                    break
            
            print(f"\n🏁 Test completed after {response_count} responses")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    print("🧪 Testing Agent mode LLM parsing fix...")
    asyncio.run(test_agent_mode())