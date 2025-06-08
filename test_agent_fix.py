#!/usr/bin/env python3
"""
Test Agent Mode Fix - Checks if the fixed universal automation handler is being used
"""

import asyncio
import websockets
import json
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_agent_mode_fix():
    """Test if agent mode is now using the fixed automation handler"""
    logger.info("🔧 Testing Agent Mode with Fixed Universal Automation Handler...")
    
    try:
        async with websockets.connect('ws://localhost:8767/ws', ping_timeout=10) as ws:
            # Get connection message
            await ws.recv()
            
            # Send agent mode request specifically designed to trigger search path
            test_request = {
                'type': 'chat_request',
                'mode': 'agent',
                'message': 'search for python tutorials in google',
                'client_id': 'fix_verification_test'
            }
            
            logger.info("📤 Sending agent mode search request...")
            await ws.send(json.dumps(test_request))
            
            # Collect responses
            responses = []
            start_time = time.time()
            timeout = 30  # 30 second timeout
            
            plan_received = False
            execution_received = False
            
            while time.time() - start_time < timeout:
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=2)
                    data = json.loads(response)
                    
                    message_type = data.get('type', '')
                    logger.info(f"📥 Received message type: {message_type}")
                    
                    if message_type == 'chat_response':
                        content = data.get('content', '')
                        responses.append(content)
                        
                        # Check for fixed handler indicators in the response
                        if "FIXED" in content or "fixed_handler" in content:
                            logger.info("✅ DETECTED FIXED HANDLER SIGNATURE IN RESPONSE!")
                            
                    elif message_type == 'chat_complete':
                        logger.info("✅ Chat response complete")
                        break
                        
                    elif message_type == 'automation_plan':
                        plan_received = True
                        logger.info("✅ Received automation plan!")
                        # Check if plan contains the DO button
                        if "buttons" in data and any("EXECUTE" in btn.get("text", "") for btn in data.get("buttons", [])):
                            logger.info("✅ Plan includes DO button for execution!")
                        
                    elif message_type == 'automation_execution':
                        execution_received = True
                        logger.info("✅ Automation execution detected!")
                        
                except asyncio.TimeoutError:
                    continue
                    
            full_response = ''.join(responses)
            logger.info(f"📊 Test Results:")
            logger.info(f"Plan Received: {'✅' if plan_received else '❌'}")
            logger.info(f"Execution Support: {'✅' if execution_received else '❌'}")
            
            if "FIXED" in full_response or plan_received:
                logger.info("✅ TEST PASSED: Fixed handler is being used!")
                return True
            else:
                logger.warning("⚠️ TEST FAILED: Could not verify fixed handler usage")
                return False
                
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_agent_mode_fix())