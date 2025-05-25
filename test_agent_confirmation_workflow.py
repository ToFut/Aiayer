#!/usr/bin/env python3

import asyncio
import websockets
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_agent_confirmation_workflow():
    """Test the complete Agent mode confirmation workflow"""
    
    try:
        # Connect to the backend
        uri = "ws://localhost:8767"
        async with websockets.connect(uri) as websocket:
            logger.info("🔗 Connected to backend")
            
            # Register as a test client
            register_msg = {
                "type": "register",
                "clientType": "test_client",
                "version": "1.0.0"
            }
            await websocket.send(json.dumps(register_msg))
            response = await websocket.recv()
            logger.info(f"📝 Registration response: {response}")
            
            # Send Agent mode request that should trigger confirmation
            agent_request = {
                "type": "chat_request",
                "message": "write in notepad SEGEV",
                "mode": "agent"
            }
            
            logger.info("🤖 Sending Agent mode request...")
            await websocket.send(json.dumps(agent_request))
            
            # Wait for the agent confirmation response (may receive multiple messages)
            logger.info("⏳ Waiting for agent confirmation response...")
            
            confirmation_response = None
            for attempt in range(5):  # Try up to 5 messages
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    response_data = json.loads(response)
                    
                    logger.info(f"📨 Message {attempt + 1}: {json.dumps(response_data, indent=2)}")
                    
                    # Check if this is the confirmation request
                    if response_data.get("requiresConfirmation"):
                        confirmation_response = response_data
                        logger.info("✅ Found confirmation response!")
                        break
                        
                except asyncio.TimeoutError:
                    logger.warning(f"⏰ Timeout on message {attempt + 1}")
                    break
            
            # Check if we got a confirmation request
            if confirmation_response:
                logger.info("✅ Got confirmation request with buttons!")
                session_id = confirmation_response.get("agentSessionId") or confirmation_response.get("sessionId")
                
                # Simulate clicking the DO button
                confirmation_msg = {
                    "type": "agent_confirmation",
                    "sessionId": session_id,
                    "action": "execute"  # Frontend sends "execute", backend maps to "DO"
                }
                
                logger.info("🔘 Simulating DO button click...")
                await websocket.send(json.dumps(confirmation_msg))
                
                # Wait for execution progress and completion
                logger.info("⏳ Waiting for execution progress...")
                
                execution_started = False
                execution_completed = False
                
                # Listen for progress updates and completion
                for _ in range(30):  # Wait up to 30 messages
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                        response_data = json.loads(response)
                        
                        logger.info(f"📨 Progress update: {json.dumps(response_data, indent=2)}")
                        
                        if response_data.get("type") == "execution_progress":
                            execution_started = True
                            logger.info(f"🔄 Progress: {response_data.get('progress', 0)}% - {response_data.get('step', 'Unknown step')}")
                            
                        elif response_data.get("type") == "execution_complete":
                            execution_completed = True
                            logger.info("✅ Execution completed!")
                            break
                            
                    except asyncio.TimeoutError:
                        logger.warning("⏰ Timeout waiting for response")
                        break
                
                # Summary
                if execution_started and execution_completed:
                    logger.info("🎉 COMPLETE WORKFLOW SUCCESS: Confirmation → Progress → Completion")
                elif execution_started:
                    logger.warning("⚠️ PARTIAL SUCCESS: Got progress but no completion")
                else:
                    logger.error("❌ WORKFLOW FAILED: No execution progress received")
                    
            else:
                logger.error("❌ No confirmation request received")
                logger.error("This means the Agent mode is not working correctly")
                
    except Exception as e:
        logger.error(f"💥 Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_agent_confirmation_workflow())