#\!/usr/bin/env python3

import asyncio
import websockets
import json
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_agent_debug():
    """Debug test for Agent mode with detailed logging"""
    
    print("🔍 DEBUG: Testing Agent Mode with Full Logging")
    print("=" * 60)
    
    try:
        # Connect to the backend
        uri = "ws://localhost:8767"
        async with websockets.connect(uri) as websocket:
            logger.info("✅ Connected to backend")
            
            # Wait for connection established
            print("⏳ Waiting for initial connection message...")
            initial_message = await websocket.recv()
            initial_data = json.loads(initial_message)
            print(f"📥 Initial: {initial_data}")
            
            # Send Agent mode request
            request = {
                "type": "chat_request",
                "mode": "Agent",
                "message": 'Type "SEGEV" in the search box',
                "session_id": "debug_test_session",
                "timestamp": "2024-01-01T12:00:00Z",
                "mode_context": {
                    "focus": "task_execution",
                    "response_style": "structured_actionable",
                    "priority": "efficiency_and_automation"
                },
                "user_intent": "automation",
                "mode_instructions": "Respond as an intelligent task automation agent."
            }
            
            print(f"📤 Sending Agent request...")
            print(f"    Message: {request['message']}")
            print(f"    Mode: {request['mode']}")
            await websocket.send(json.dumps(request))
            print("✅ Request sent successfully")
            
            # Listen for ALL messages with detailed logging
            message_count = 0
            for i in range(20):  # Listen for up to 20 messages
                try:
                    print(f"\n⏳ Waiting for message {i+1}...")
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    message_count += 1
                    
                    try:
                        data = json.loads(message)
                        msg_type = data.get('type', 'unknown')
                        
                        print(f"📥 Message {message_count} - Type: {msg_type}")
                        
                        # Show key fields for each message type
                        if msg_type == 'progress_update':
                            print(f"    Stage: {data.get('stage', 'N/A')}")
                            print(f"    Mode: {data.get('mode', 'N/A')}")
                            
                        elif msg_type == 'final_response':
                            print(f"    SUCCESS: Got final response!")
                            print(f"    Mode: {data.get('mode', 'N/A')}")
                            print(f"    Success: {data.get('success', 'N/A')}")
                            print(f"    RequiresConfirmation: {data.get('requiresConfirmation', 'N/A')}")
                            print(f"    AgentSessionId: {data.get('agentSessionId', 'N/A')}")
                            print(f"    RiskLevel: {data.get('riskLevel', 'N/A')}")
                            print(f"    EstimatedDuration: {data.get('estimatedDuration', 'N/A')}")
                            
                            if data.get('requiresConfirmation'):
                                print("🎉 CONFIRMATION BUTTONS SHOULD APPEAR!")
                                print(f"    Response: {data.get('response', '')[:150]}...")
                                return True
                            else:
                                print("❌ No confirmation required - this might be a fallback response")
                            
                        elif msg_type == 'error':
                            print(f"    Error: {data.get('error', 'N/A')}")
                            
                        else:
                            print(f"    Unknown type - Full data: {json.dumps(data, indent=2)}")
                            
                    except json.JSONDecodeError:
                        print(f"📥 Raw message {message_count}: {message}")
                        
                except asyncio.TimeoutError:
                    print(f"⏰ Timeout waiting for message {i+1}")
                    break
                except websockets.exceptions.ConnectionClosed:
                    print(f"🔌 Connection closed after {message_count} messages")
                    break
            
            print(f"\n📊 Total messages received: {message_count}")
            if message_count == 0:
                print("❌ NO MESSAGES RECEIVED - Backend might not be responding")
                return False
            else:
                print("❌ NO CONFIRMATION RESPONSE - Check backend implementation")
                return False
                
    except Exception as e:
        logger.error(f"❌ Debug test failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_agent_debug())
    print(f"\n🎯 Test Result: {'PASSED' if result else 'FAILED'}")