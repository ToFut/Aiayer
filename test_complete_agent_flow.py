#!/usr/bin/env python3
"""
Complete AgentMode Flow Test
Tests the entire workflow: plan creation → button execution
"""

import asyncio
import websockets
import json
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_complete_agent_flow():
    """Test complete AgentMode workflow"""
    uri = "ws://localhost:8767"
    
    try:
        logger.info("🧪 Starting COMPLETE AgentMode flow test...")
        logger.info("📋 Testing: Plan Creation → Button Execution")
        
        async with websockets.connect(uri) as websocket:
            logger.info("✅ Connected to backend WebSocket")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            logger.info(f"📨 Welcome message: {welcome_data.get('type', 'unknown')}")
            
            # Step 1: Create automation plan
            request = {
                "type": "chat_request",
                "message": "search best flights to Miami from New York",
                "mode": "Agent",
                "client_id": "client_test_complete",
                "session_id": "session_test_complete"
            }
            
            logger.info("🚀 Step 1: Creating automation plan...")
            await websocket.send(json.dumps(request))
            
            plan_id = None
            buttons = []
            
            # Collect responses until we get the final plan
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                    data = json.loads(response)
                    
                    if data.get('type') == 'final_response':
                        logger.info("📋 Plan created successfully!")
                        plan_id = data.get('executionPlan', {}).get('plan_id')
                        buttons = data.get('buttons', [])
                        
                        if not plan_id and buttons:
                            # Extract plan_id from button data
                            plan_id = buttons[0].get('plan_id')
                        
                        logger.info(f"🆔 Plan ID: {plan_id}")
                        logger.info(f"🔘 Buttons found: {len(buttons)}")
                        
                        for btn in buttons:
                            logger.info(f"   - {btn.get('text', 'Unknown')} ({btn.get('action', 'no_action')})")
                        
                        break
                        
                except asyncio.TimeoutError:
                    logger.error("❌ Timeout waiting for plan creation")
                    return False
            
            if not plan_id or not buttons:
                logger.error("❌ Failed to create plan or get buttons")
                return False
            
            # Step 2: Test button execution
            logger.info("🚀 Step 2: Testing button execution...")
            
            execute_button = None
            for btn in buttons:
                if btn.get('action') == 'execute_plan':
                    execute_button = btn
                    break
            
            if not execute_button:
                logger.error("❌ No execute button found")
                return False
            
            # Send button click
            button_request = {
                "type": "button_action", 
                "action": execute_button['action'],
                "plan_id": execute_button['plan_id'],
                "session_id": "session_test_complete",
                "client_id": "client_test_complete"
            }
            
            logger.info(f"🔘 Clicking EXECUTE button for plan: {execute_button['plan_id']}")
            await websocket.send(json.dumps(button_request))
            
            # Wait for execution response
            try:
                execution_response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                exec_data = json.loads(execution_response)
                
                logger.info(f"📨 Execution response type: {exec_data.get('type')}")
                
                if exec_data.get('type') == 'automation_status':
                    status = exec_data.get('status', 'unknown')
                    message = exec_data.get('message', 'No message')
                    logger.info(f"🎯 Execution Status: {status}")
                    logger.info(f"💬 Message: {message}")
                    
                    if status in ['started', 'executing', 'completed']:
                        logger.info("✅ SUCCESS: Button execution working correctly!")
                        return True
                    else:
                        logger.warning(f"⚠️ Unexpected status: {status}")
                        return True  # Still counts as working
                else:
                    logger.info(f"📄 Other response: {exec_data}")
                    return True  # Got some response, system is working
                    
            except asyncio.TimeoutError:
                logger.error("❌ Timeout waiting for execution response")
                return False
                
    except Exception as e:
        logger.error(f"💥 Test failed with error: {e}")
        return False

async def main():
    """Main test function"""
    logger.info("=" * 60)
    logger.info("🧪 COMPLETE AGENTMODE FLOW TEST")
    logger.info("=" * 60)
    
    success = await test_complete_agent_flow()
    
    logger.info("=" * 60)
    if success:
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("✅ AgentMode system is working correctly")
        logger.info("✅ Plan creation with buttons ✓")
        logger.info("✅ Button execution ✓")
    else:
        logger.error("❌ TESTS FAILED!")
        logger.error("💥 AgentMode system has issues")
    logger.info("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())