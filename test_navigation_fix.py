#!/usr/bin/env python3

import asyncio
import websockets
import json
import time

async def test_navigation_fix():
    """Test the fixed navigation system"""
    uri = 'ws://localhost:8767'
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔌 Connected to Enhanced Enterprise Backend")
            
            # Wait for connection established
            response = await websocket.recv()
            conn_data = json.loads(response)
            print(f"✅ Connection: {conn_data.get('message', 'Connected')}")
            
            # Send chat request in agent mode with navigation
            test_message = {
                'type': 'chat_request',
                'mode': 'Agent',
                'message': 'open YouTube and search SEGEV',
                'session_id': 'test_navigation'
            }
            
            print(f"🚀 Testing: {test_message['message']}")
            await websocket.send(json.dumps(test_message))
            
            # Listen for responses
            plan_received = False
            
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=30)
                    result = json.loads(response)
                    
                    print(f"📨 Received: {result.get('type', 'unknown')}")
                    
                    if result.get('type') == 'final_response':
                        plan_received = True
                        requires_confirmation = result.get('requiresConfirmation', False)
                        agent_session_id = result.get('agentSessionId')
                        execution_plan = result.get('executionPlan', {})
                        
                        print(f"📋 Plan received: {result.get('response', 'No plan')}")
                        print(f"🔧 Requires confirmation: {requires_confirmation}")
                        print(f"📊 Steps: {execution_plan.get('total_steps', 0)}")
                        print(f"🎯 Action: {execution_plan.get('action', 'unknown')}")
                        print(f"🎯 Target: {execution_plan.get('target', 'unknown')}")
                        
                        if requires_confirmation and agent_session_id:
                            print(f"🚀 Proceeding with execution...")
                            
                            # Send confirmation to execute the plan
                            confirm_message = {
                                'type': 'agent_confirmation',
                                'action': 'EXECUTE',
                                'sessionId': agent_session_id
                            }
                            
                            await websocket.send(json.dumps(confirm_message))
                            print("✅ Execution command sent")
                        else:
                            print("❌ No confirmation required or missing session ID")
                            break
                    
                    elif result.get('type') in ['agent_execution_success', 'agent_execution_error']:
                        success = result.get('type') == 'agent_execution_success'
                        message = result.get('summary') or result.get('error', 'No message')
                        
                        print(f"🏁 Execution result: {success}")
                        print(f"💬 Message: {message}")
                        
                        if success:
                            print("🎉 Navigation system working perfectly!")
                        else:
                            print("⚠️ Execution had issues - check logs")
                        break
                    
                    elif result.get('type') == 'agent_progress':
                        step = result.get('step', 0)
                        message = result.get('message', 'Processing...')
                        progress = result.get('progress', 0)
                        print(f"🔄 Step {step}: {message} ({progress}%)")
                        # Continue listening for more progress updates
                    
                    elif result.get('type') == 'error':
                        error_msg = result.get('error', 'Unknown error')
                        print(f"❌ Error: {error_msg}")
                        break
                        
                except asyncio.TimeoutError:
                    print("⏰ Timeout waiting for response")
                    break
                except Exception as e:
                    print(f"❌ Error receiving response: {e}")
                    break
            
            if not plan_received:
                print("❌ Agent plan never received - check backend logs")
                
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    print("🧪 Testing Navigation Fix...")
    asyncio.run(test_navigation_fix())