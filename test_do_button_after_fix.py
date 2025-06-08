#!/usr/bin/env python3
"""
Test DO Button After Fix

This script sends a test message to the DO button server to check if the fix is working correctly.
"""

import asyncio
import websockets
import json
import logging
import time
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/test_do_button_after_fix.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TestDoButtonAfterFix")

async def test_do_button():
    """Test the DO button functionality by sending a test message"""
    try:
        # Connect to DO button server
        uri = "ws://localhost:8765"
        async with websockets.connect(uri) as websocket:
            logger.info(f"✅ Connected to DO button server at {uri}")
            
            # Receive welcome message
            welcome = await websocket.recv()
            logger.info(f"✅ Received welcome message: {welcome[:100]}...")
            
            # Create a test plan with a unique ID
            test_plan_id = f"test_plan_{int(time.time())}"
            test_plan = {
                "id": test_plan_id,
                "title": "Test Plan After Fix",
                "description": "This is a test plan to verify the DO button fix",
                "steps": [
                    {
                        "id": f"{test_plan_id}_step_1",
                        "type": "notification",
                        "action": "notify",
                        "content": "This is a test plan to verify the DO button fix",
                        "position": {"x": 500, "y": 500}
                    }
                ],
                "metadata": {
                    "created_at": time.time(),
                    "test_plan": True
                }
            }
            
            # Create agent confirmation message (DO button click)
            message = {
                "type": "agent_confirmation",
                "action": "DO",
                "sessionId": test_plan_id,
                "plan": test_plan
            }
            
            # Send the message
            await websocket.send(json.dumps(message))
            logger.info(f"✅ Sent agent confirmation message with plan ID: {test_plan_id}")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)
                logger.info(f"✅ Received response: {response_data}")
                
                if response_data.get("type") == "error":
                    logger.error(f"❌ Error response: {response_data.get('error')}")
                    return False
                else:
                    logger.info(f"✅ DO button action executed successfully")
                    return True
            except asyncio.TimeoutError:
                logger.warning("⚠️ No response received within timeout period")
                return False
    except Exception as e:
        logger.error(f"❌ Error testing DO button: {e}")
        return False

async def test_backend_execution():
    """Test plan execution via backend directly"""
    try:
        # Connect to backend server
        uri = "ws://localhost:8767/ws"
        async with websockets.connect(uri) as websocket:
            logger.info(f"✅ Connected to backend server at {uri}")
            
            # Receive welcome message
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            client_id = welcome_data.get("client_id")
            logger.info(f"✅ Received welcome message with client_id: {client_id}")
            
            # Create a test plan with a unique ID
            test_plan_id = f"test_plan_{int(time.time())}"
            test_plan = {
                "id": test_plan_id,
                "title": "Test Plan After Fix (Backend)",
                "description": "This is a test plan to verify the backend execution",
                "steps": [
                    {
                        "id": f"{test_plan_id}_step_1",
                        "type": "notification",
                        "action": "notify",
                        "content": "This is a test plan executed via backend",
                        "position": {"x": 500, "y": 500}
                    }
                ],
                "metadata": {
                    "created_at": time.time(),
                    "test_plan": True
                }
            }
            
            # Register the plan with the backend
            register_message = {
                "type": "register_plan",
                "plan": test_plan,
                "client_id": client_id
            }
            
            await websocket.send(json.dumps(register_message))
            logger.info(f"✅ Sent register_plan message with plan ID: {test_plan_id}")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)
                logger.info(f"✅ Received register response: {response_data}")
                
                # Now send execute plan message
                execute_message = {
                    "type": "execute_plan",
                    "plan_id": test_plan_id,
                    "client_id": client_id
                }
                
                await websocket.send(json.dumps(execute_message))
                logger.info(f"✅ Sent execute_plan message with plan ID: {test_plan_id}")
                
                # Wait for execution response
                execution_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                execution_data = json.loads(execution_response)
                logger.info(f"✅ Received execution response: {execution_data}")
                
                if execution_data.get("type") == "error":
                    logger.error(f"❌ Error response: {execution_data.get('error')}")
                    return False
                else:
                    logger.info(f"✅ Plan executed successfully via backend")
                    return True
            except asyncio.TimeoutError:
                logger.warning("⚠️ No response received within timeout period")
                return False
    except Exception as e:
        logger.error(f"❌ Error testing backend execution: {e}")
        return False

async def test_agent_confirmation():
    """Test agent confirmation via backend"""
    try:
        # Connect to backend server
        uri = "ws://localhost:8767/ws"
        async with websockets.connect(uri) as websocket:
            logger.info(f"✅ Connected to backend server at {uri}")
            
            # Receive welcome message
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            client_id = welcome_data.get("client_id")
            logger.info(f"✅ Received welcome message with client_id: {client_id}")
            
            # Create a test plan with a unique ID
            test_plan_id = f"test_plan_{int(time.time())}"
            test_plan = {
                "id": test_plan_id,
                "title": "Test Plan After Fix (Agent Confirmation)",
                "description": "This is a test plan to verify agent confirmation",
                "steps": [
                    {
                        "id": f"{test_plan_id}_step_1",
                        "type": "notification",
                        "action": "notify",
                        "content": "This is a test plan executed via agent confirmation",
                        "position": {"x": 500, "y": 500}
                    }
                ],
                "metadata": {
                    "created_at": time.time(),
                    "test_plan": True
                }
            }
            
            # Create agent confirmation message
            agent_message = {
                "type": "agent_confirmation",
                "action": "DO",
                "sessionId": test_plan_id,
                "plan": test_plan,
                "client_id": client_id
            }
            
            await websocket.send(json.dumps(agent_message))
            logger.info(f"✅ Sent agent_confirmation message with plan ID: {test_plan_id}")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)
                logger.info(f"✅ Received agent confirmation response: {response_data}")
                
                if response_data.get("type") == "error":
                    logger.error(f"❌ Error response: {response_data.get('error')}")
                    return False
                else:
                    logger.info(f"✅ Agent confirmation handled successfully")
                    return True
            except asyncio.TimeoutError:
                logger.warning("⚠️ No response received within timeout period")
                return False
    except Exception as e:
        logger.error(f"❌ Error testing agent confirmation: {e}")
        return False

async def main():
    """Main function that runs all tests"""
    logger.info("🚀 Starting DO Button Test After Fix")
    
    # Test 1: DO Button via WebSocket
    logger.info("Test 1: Testing DO button via direct WebSocket connection...")
    do_button_result = await test_do_button()
    if do_button_result:
        logger.info("✅ Test 1 passed: DO button is working correctly")
    else:
        logger.error("❌ Test 1 failed: DO button is not working correctly")
        
    # Test 2: Backend Execution
    logger.info("Test 2: Testing plan execution via backend...")
    backend_result = await test_backend_execution()
    if backend_result:
        logger.info("✅ Test 2 passed: Backend execution is working correctly")
    else:
        logger.error("❌ Test 2 failed: Backend execution is not working correctly")
        
    # Test 3: Agent Confirmation
    logger.info("Test 3: Testing agent confirmation via backend...")
    agent_result = await test_agent_confirmation()
    if agent_result:
        logger.info("✅ Test 3 passed: Agent confirmation is working correctly")
    else:
        logger.error("❌ Test 3 failed: Agent confirmation is not working correctly")
        
    # Overall result
    if do_button_result and backend_result and agent_result:
        logger.info("🎉 All tests passed! The DO button fix is working correctly")
    else:
        logger.error("❌ Some tests failed. The DO button fix may not be completely working")
        
    logger.info("Tests completed.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Test stopped by user")
    except Exception as e:
        logger.error(f"Error in test: {e}")
        import traceback
        logger.error(traceback.format_exc())