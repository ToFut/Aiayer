#!/usr/bin/env python3

import asyncio
import websockets
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_agent_confirmation():
    """Test the Agent mode confirmation button workflow"""
    
    print("🤖 Testing Agent Mode Confirmation Buttons")
    print("=" * 50)
    
    try:
        # Connect to the backend
        uri = "ws://localhost:8767"
        async with websockets.connect(uri) as websocket:
            logger.info("✅ Connected to backend")
            
            # Wait for connection established
            initial_message = await websocket.recv()
            initial_data = json.loads(initial_message)
            print(f"📥 Initial: {initial_data.get('type', 'unknown')}")
            
            # Send Agent mode request that should trigger UI automation
            request = {
                "type": "chat_request",
                "mode": "Agent",
                "message": 'Type "SEGEV" in the search box',
                "session_id": "test_confirmation_session",
                "timestamp": "2024-01-01T12:00:00Z",
                "mode_context": {
                    "focus": "task_execution",
                    "response_style": "structured_actionable",
                    "priority": "efficiency_and_automation"
                },
                "user_intent": "automation",
                "mode_instructions": "Respond as an intelligent task automation agent. Break down complex requests into actionable steps, suggest optimal workflows and automation, provide specific implementation guidance, and consider efficiency and best practices."
            }
            
            print(f"📤 Sending Agent request: {request['message']}")
            await websocket.send(json.dumps(request))
            
            # Wait for multiple responses (progress updates + final response)
            response_data = None
            for i in range(10):  # Listen for up to 10 messages
                try:
                    response_message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    data = json.loads(response_message)
                    
                    print(f"📥 Message {i+1} - Type: {data.get('type', 'unknown')}")
                    
                    if data.get('type') == 'progress_update':
                        print(f"   Stage: {data.get('stage', '')}")
                        continue
                    elif data.get('type') == 'final_response':
                        response_data = data
                        print(f"   SUCCESS: Got final response!")
                        break
                    else:
                        print(f"   Other: {json.dumps(data, indent=2)}")
                        response_data = data  # Store in case this is the final response
                        
                except asyncio.TimeoutError:
                    print(f"⏰ Timeout waiting for message {i+1}")
                    break
            
            if response_data:
                print(f"📥 Final Response Type: {response_data.get('type', 'unknown')}")
                print(f"📥 Success: {response_data.get('success')}")
                print(f"📥 Mode: {response_data.get('mode', 'unknown')}")
                print(f"📥 Requires Confirmation: {response_data.get('requiresConfirmation', False)}")
                print(f"📥 Agent Session ID: {response_data.get('agentSessionId', 'None')}")
                print(f"📥 Risk Level: {response_data.get('riskLevel', 'None')}")
                print(f"📥 Estimated Duration: {response_data.get('estimatedDuration', 'None')}")
            
            if response_data.get('requiresConfirmation'):
                print("✅ CONFIRMATION BUTTONS SHOULD APPEAR!")
                print(f"🎯 Response: {response_data.get('response', '')[:100]}...")
                
                # Test sending confirmation
                confirmation = {
                    "type": "agent_confirmation",
                    "action": "execute",
                    "sessionId": response_data.get('agentSessionId'),
                    "timestamp": "2024-01-01T12:00:00Z"
                }
                
                print("📤 Sending execution confirmation...")
                await websocket.send(json.dumps(confirmation))
                
                # Wait for progress updates
                for i in range(5):  # Listen for progress updates
                    try:
                        progress_message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        progress_data = json.loads(progress_message)
                        
                        if progress_data.get('type') == 'execution_progress':
                            print(f"🚀 Progress: {progress_data.get('progress', 0)}% - {progress_data.get('currentStep', '')}")
                        elif progress_data.get('type') == 'execution_complete':
                            print(f"✅ Execution Complete: {progress_data.get('result', '')}")
                            break
                        else:
                            print(f"📥 Other: {progress_data.get('type', 'unknown')}")
                            
                    except asyncio.TimeoutError:
                        print("⏰ No more progress updates")
                        break
                
            else:
                print("❌ NO CONFIRMATION BUTTONS - Check backend implementation")
                print(f"🎯 Full Response: {json.dumps(response_data, indent=2)}")
                
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_agent_confirmation())