#!/usr/bin/env python3
"""
Test DO Button Real Execution

This script sends a real automation plan to the DO button server and verifies execution.
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
        logging.FileHandler("logs/test_do_button_real_execution.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TestDoButtonRealExecution")

async def test_do_button_real_execution():
    """Test the DO button with a real automation plan"""
    try:
        # Connect to DO button server
        uri = "ws://localhost:8765"
        async with websockets.connect(uri) as websocket:
            logger.info(f"✅ Connected to DO button server at {uri}")
            
            # Receive welcome message
            welcome = await websocket.recv()
            logger.info(f"✅ Received welcome message: {welcome[:100]}...")
            
            # Create a realistic automation plan with actual steps
            test_plan_id = f"test_plan_{int(time.time())}"
            test_plan = {
                "id": test_plan_id,
                "title": "Test Real Automation Plan",
                "description": "This is a real automation plan with actual steps",
                "steps": [
                    {
                        "id": f"{test_plan_id}_step_1",
                        "type": "notification",
                        "action": "notify",
                        "content": "Starting automation plan execution...",
                        "position": {"x": 500, "y": 300}
                    },
                    {
                        "id": f"{test_plan_id}_step_2",
                        "type": "pause",
                        "duration": 1.0,
                        "description": "Pause briefly"
                    },
                    {
                        "id": f"{test_plan_id}_step_3",
                        "type": "notification",
                        "action": "notify",
                        "content": "Automation plan executed successfully!",
                        "position": {"x": 500, "y": 400}
                    }
                ],
                "metadata": {
                    "created_at": time.time(),
                    "test_plan": True,
                    "priority": "high"
                }
            }
            
            # Save plan to persistence first
            await save_plan_to_persistence(test_plan_id, test_plan)
            
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
            
            # Wait for responses
            responses = []
            try:
                # Collect responses for up to 5 seconds
                start_time = time.time()
                while time.time() - start_time < 5.0:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    response_data = json.loads(response)
                    responses.append(response_data)
                    logger.info(f"✅ Received response: {response_data}")
                    
                    # If we got a completion message, we can stop waiting
                    if response_data.get("type") == "agent_complete":
                        logger.info(f"✅ Received completion message")
                        break
            except asyncio.TimeoutError:
                # This is expected when we've waited long enough
                pass
                
            # Check responses
            if not responses:
                logger.error("❌ No responses received")
                return False
                
            # Check for progress messages
            progress_messages = [r for r in responses if r.get("type") == "agent_progress"]
            if progress_messages:
                logger.info(f"✅ Received {len(progress_messages)} progress messages")
            else:
                logger.warning("⚠️ No progress messages received")
                
            # Check for error messages
            error_messages = [r for r in responses if r.get("type") == "error"]
            if error_messages:
                logger.error(f"❌ Received error messages: {error_messages}")
                return False
                
            logger.info(f"✅ DO button real execution test completed successfully")
            return True
    except Exception as e:
        logger.error(f"❌ Error testing DO button real execution: {e}")
        return False

async def save_plan_to_persistence(plan_id, plan_data):
    """Save the plan to persistence system"""
    try:
        # Connect to the backend to save the plan
        uri = "ws://localhost:8767/ws"
        async with websockets.connect(uri) as websocket:
            logger.info(f"✅ Connected to backend server at {uri}")
            
            # Receive welcome message
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            client_id = welcome_data.get("client_id")
            logger.info(f"✅ Received welcome message with client_id: {client_id}")
            
            # Create save plan message - use LLM request as a mechanism to save plan
            save_message = {
                "type": "llm_request",
                "client_id": client_id,
                "message": "Save this plan for testing",
                "pending_plan": {
                    "id": plan_id,
                    "plan": plan_data
                }
            }
            
            # Send message to save plan
            await websocket.send(json.dumps(save_message))
            logger.info(f"✅ Sent message to save plan {plan_id}")
            
            # Wait for response (optional)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                logger.info(f"✅ Received response after saving plan: {response[:100]}...")
            except asyncio.TimeoutError:
                logger.warning("⚠️ No response received after saving plan")
                
            return True
    except Exception as e:
        logger.error(f"❌ Error saving plan to persistence: {e}")
        return False

async def test_direct_do_button():
    """Test the DO button directly with a simple plan"""
    try:
        # Connect to DO button server
        uri = "ws://localhost:8765"
        async with websockets.connect(uri) as websocket:
            logger.info(f"✅ Connected to DO button server at {uri}")
            
            # Receive welcome message
            welcome = await websocket.recv()
            logger.info(f"✅ Received welcome message: {welcome[:100]}...")
            
            # Create a simple plan
            test_plan_id = f"test_plan_{int(time.time())}"
            test_plan = {
                "id": test_plan_id,
                "title": "Simple Test Plan",
                "description": "This is a simple test plan",
                "steps": [
                    {
                        "id": f"{test_plan_id}_step_1",
                        "type": "notification",
                        "action": "notify",
                        "content": "Simple plan executed successfully!",
                        "position": {"x": 500, "y": 300}
                    }
                ],
                "metadata": {
                    "created_at": time.time(),
                    "test_plan": True
                }
            }
            
            # Create direct DO button message
            message = {
                "type": "do_button",
                "plan_id": test_plan_id,
                "plan": test_plan
            }
            
            # Send the message
            await websocket.send(json.dumps(message))
            logger.info(f"✅ Sent direct DO button message with plan ID: {test_plan_id}")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                response_data = json.loads(response)
                logger.info(f"✅ Received response: {response_data}")
                
                if response_data.get("type") == "error":
                    logger.error(f"❌ Error response: {response_data.get('error')}")
                    return False
                else:
                    logger.info(f"✅ Direct DO button test successful")
                    return True
            except asyncio.TimeoutError:
                logger.warning("⚠️ No response received within timeout period")
                return False
    except Exception as e:
        logger.error(f"❌ Error testing direct DO button: {e}")
        return False

async def test_button_action():
    """Test the button_action message type"""
    try:
        # Connect to DO button server
        uri = "ws://localhost:8765"
        async with websockets.connect(uri) as websocket:
            logger.info(f"✅ Connected to DO button server at {uri}")
            
            # Receive welcome message
            welcome = await websocket.recv()
            logger.info(f"✅ Received welcome message: {welcome[:100]}...")
            
            # Create a simple plan
            test_plan_id = f"test_plan_{int(time.time())}"
            test_plan = {
                "id": test_plan_id,
                "title": "Button Action Test Plan",
                "description": "This is a test plan for button_action",
                "steps": [
                    {
                        "id": f"{test_plan_id}_step_1",
                        "type": "notification",
                        "action": "notify",
                        "content": "Button action executed successfully!",
                        "position": {"x": 500, "y": 300}
                    }
                ],
                "metadata": {
                    "created_at": time.time(),
                    "test_plan": True
                }
            }
            
            # Create button_action message
            message = {
                "type": "button_action",
                "action": "execute_plan",
                "plan_id": test_plan_id,
                "plan": test_plan
            }
            
            # Send the message
            await websocket.send(json.dumps(message))
            logger.info(f"✅ Sent button_action message with plan ID: {test_plan_id}")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                response_data = json.loads(response)
                logger.info(f"✅ Received response: {response_data}")
                
                if response_data.get("type") == "error":
                    logger.error(f"❌ Error response: {response_data.get('error')}")
                    return False
                else:
                    logger.info(f"✅ Button action test successful")
                    return True
            except asyncio.TimeoutError:
                logger.warning("⚠️ No response received within timeout period")
                return False
    except Exception as e:
        logger.error(f"❌ Error testing button action: {e}")
        return False

async def main():
    """Main function that runs all tests"""
    logger.info("🚀 Starting DO Button Real Execution Test")
    
    # Test 1: DO Button with Real Execution
    logger.info("Test 1: Testing DO button with real execution...")
    do_button_result = await test_do_button_real_execution()
    if do_button_result:
        logger.info("✅ Test 1 passed: DO button real execution is working correctly")
    else:
        logger.error("❌ Test 1 failed: DO button real execution is not working correctly")
        
    # Test 2: Direct DO Button
    logger.info("Test 2: Testing direct DO button...")
    direct_result = await test_direct_do_button()
    if direct_result:
        logger.info("✅ Test 2 passed: Direct DO button is working correctly")
    else:
        logger.error("❌ Test 2 failed: Direct DO button is not working correctly")
        
    # Test 3: Button Action
    logger.info("Test 3: Testing button action...")
    button_action_result = await test_button_action()
    if button_action_result:
        logger.info("✅ Test 3 passed: Button action is working correctly")
    else:
        logger.error("❌ Test 3 failed: Button action is not working correctly")
        
    # Overall result
    if do_button_result and direct_result and button_action_result:
        logger.info("🎉 All tests passed! The DO button system is fully operational")
    else:
        logger.error("❌ Some tests failed. The DO button system may not be completely working")
        
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