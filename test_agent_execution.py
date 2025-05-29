#!/usr/bin/env python3
"""
Test script to properly trigger agent mode and monitor execution
"""

import asyncio
import websockets
import json
import time

async def test_agent_execution():
    """Test agent mode execution with proper message flow"""
    uri = "ws://localhost:8767"
    
    try:
        async with websockets.connect(uri) as websocket:
            # Register as client
            register_msg = {
                "type": "register",
                "client_type": "automation_client",
                "client_id": f"test_agent_{int(time.time())}"
            }
            await websocket.send(json.dumps(register_msg))
            response = await websocket.recv()
            print(f"✅ Registration: {json.loads(response)['type']}")
            
            # Send agent mode request
            agent_request = {
                "type": "chat_request",
                "message": "open notes app",
                "mode": "agent",
                "client_id": f"test_agent_{int(time.time())}"
            }
            await websocket.send(json.dumps(agent_request))
            print("🤖 Sent agent request: 'open notes app'")
            
            # Wait for planning response
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"📋 Planning response: {response_data.get('type', 'unknown')}")
            
            if response_data.get('type') == 'automation_plan':
                print(f"🎯 Plan created with {len(response_data.get('steps', []))} steps")
                
                # Send approval to start execution
                approval_msg = {
                    "type": "button_action",
                    "action": "approve_execution",
                    "plan_id": response_data.get('plan_id')
                }
                await websocket.send(json.dumps(approval_msg))
                print("✅ Sent execution approval")
                
                # Monitor execution progress
                execution_complete = False
                step_count = 0
                
                while not execution_complete and step_count < 20:  # Max 20 iterations
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        response_data = json.loads(response)
                        
                        msg_type = response_data.get('type')
                        
                        if msg_type == 'step_progress':
                            step_num = response_data.get('step_number')
                            description = response_data.get('description', 'Unknown step')
                            status = response_data.get('status', 'unknown')
                            print(f"🔄 Step {step_num}: {description} - {status}")
                            
                        elif msg_type == 'step_completed':
                            step_num = response_data.get('step_number')
                            print(f"✅ Step {step_num} completed")
                            
                        elif msg_type == 'step_failed':
                            step_num = response_data.get('step_number')
                            error = response_data.get('error', 'Unknown error')
                            print(f"❌ Step {step_num} failed: {error}")
                            
                        elif msg_type == 'automation_complete':
                            success_rate = response_data.get('success_rate', 0)
                            print(f"🎉 Automation completed with {success_rate}% success rate")
                            execution_complete = True
                            
                        step_count += 1
                        
                    except asyncio.TimeoutError:
                        print("⏱️ Timeout waiting for execution update")
                        break
                        
            else:
                print(f"❌ Unexpected response: {response_data}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_agent_execution())