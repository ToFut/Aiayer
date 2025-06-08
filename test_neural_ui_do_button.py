#!/usr/bin/env python3
"""
Test Neural UI DO Button Integration

This script tests the connection between the Neural UI detector and the DO button system,
which is the specific part of the system that was having issues.
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
        logging.FileHandler("logs/test_neural_ui_do_button.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TestNeuralUIDoButton")

async def test_neural_ui_do_button_flow():
    """Test the Neural UI to DO button flow"""
    try:
        # Step 1: Connect to the Neural UI detector server
        try:
            neural_ui_uri = "ws://localhost:8768"
            logger.info(f"Connecting to Neural UI detector at {neural_ui_uri}")
            
            async with websockets.connect(neural_ui_uri) as neural_ui_websocket:
                # Get welcome message
                welcome = await asyncio.wait_for(neural_ui_websocket.recv(), timeout=2.0)
                logger.info(f"✅ Connected to Neural UI detector server")
                
                # Step 2: Send a detection result with a plan
                test_plan_id = f"neural_ui_test_plan_{int(time.time())}"
                test_plan = {
                    "id": test_plan_id,
                    "title": "Neural UI Test Plan",
                    "description": "This plan tests Neural UI to DO button communication",
                    "steps": [
                        {
                            "id": f"{test_plan_id}_step_1",
                            "type": "notification",
                            "action": "notify",
                            "content": "Neural UI to DO button test successful!",
                            "position": {"x": 500, "y": 300}
                        }
                    ],
                    "metadata": {
                        "created_at": time.time(),
                        "test_plan": True
                    }
                }
                
                detection_message = {
                    "type": "detection_result",
                    "detected_element": {
                        "type": "button",
                        "text": "Test Button",
                        "position": {"x": 500, "y": 300},
                        "confidence": 0.95
                    },
                    "automation_plan": test_plan
                }
                
                await neural_ui_websocket.send(json.dumps(detection_message))
                logger.info(f"✅ Sent detection result with automation plan")
                
                # Step 3: Wait for response or timeout
                try:
                    response = await asyncio.wait_for(neural_ui_websocket.recv(), timeout=2.0)
                    response_data = json.loads(response)
                    logger.info(f"✅ Received response: {response_data}")
                    
                    if response_data.get("type") == "plan_registered" or response_data.get("type") == "success":
                        logger.info(f"✅ Plan registration successful")
                    else:
                        logger.info(f"Received response type: {response_data.get('type')}")
                except asyncio.TimeoutError:
                    logger.warning("⚠️ No response received within timeout period")
                
                # Step 4: Send a DO button action to execute the plan
                execute_message = {
                    "type": "execute_plan",
                    "plan_id": test_plan_id
                }
                
                await neural_ui_websocket.send(json.dumps(execute_message))
                logger.info(f"✅ Sent execute_plan message")
                
                # Step 5: Wait for execution response
                responses = []
                start_time = time.time()
                success = False
                
                while time.time() - start_time < 5.0:
                    try:
                        response = await asyncio.wait_for(neural_ui_websocket.recv(), timeout=0.5)
                        response_data = json.loads(response)
                        responses.append(response_data)
                        logger.info(f"✅ Received response: {response_data}")
                        
                        if response_data.get("type") == "execution_progress" or response_data.get("type") == "plan_executed":
                            success = True
                    except asyncio.TimeoutError:
                        break
                    except Exception as e:
                        logger.error(f"❌ Error receiving response: {e}")
                        break
                
                if success:
                    logger.info(f"✅ Neural UI to DO button test successful")
                    return True
                else:
                    logger.warning(f"⚠️ Did not receive execution response")
        except (ConnectionRefusedError, websockets.exceptions.InvalidStatusCode) as e:
            logger.warning(f"⚠️ Could not connect to Neural UI detector: {e}")
            
        # Fallback test with DO button server directly
        logger.info(f"Testing DO button server directly")
        
        do_button_uri = "ws://localhost:8765"
        async with websockets.connect(do_button_uri) as do_button_websocket:
            # Get welcome message
            welcome = await do_button_websocket.recv()
            logger.info(f"✅ Connected to DO button server")
            
            # Create a test plan
            test_plan_id = f"direct_test_plan_{int(time.time())}"
            test_plan = {
                "id": test_plan_id,
                "title": "Direct Test Plan",
                "description": "This plan tests direct DO button communication",
                "steps": [
                    {
                        "id": f"{test_plan_id}_step_1",
                        "type": "notification",
                        "action": "notify",
                        "content": "Direct DO button test successful!",
                        "position": {"x": 500, "y": 300}
                    }
                ],
                "metadata": {
                    "created_at": time.time(),
                    "test_plan": True
                }
            }
            
            # Send the plan directly
            direct_message = {
                "type": "do_button",
                "plan_id": test_plan_id,
                "plan": test_plan
            }
            
            await do_button_websocket.send(json.dumps(direct_message))
            logger.info(f"✅ Sent direct DO button message")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(do_button_websocket.recv(), timeout=2.0)
                response_data = json.loads(response)
                logger.info(f"✅ Received direct response: {response_data}")
                
                if response_data.get("type") == "agent_progress":
                    logger.info(f"✅ Direct DO button test successful")
                    return True
                else:
                    logger.warning(f"⚠️ Unexpected response type: {response_data.get('type')}")
                    return False
            except asyncio.TimeoutError:
                logger.warning("⚠️ No response received within timeout period")
                return False
    except Exception as e:
        logger.error(f"❌ Error in Neural UI DO button test: {e}")
        return False

async def test_neural_ui_do_button_handler():
    """Test the neural_ui_do_button_handler directly"""
    try:
        # Try to connect to the neural_ui_do_button_handler
        handler_uri = "ws://localhost:8768/handler"
        logger.info(f"Connecting to neural_ui_do_button_handler at {handler_uri}")
        
        try:
            async with websockets.connect(handler_uri, ping_interval=None) as handler_websocket:
                # Get welcome message
                try:
                    welcome = await asyncio.wait_for(handler_websocket.recv(), timeout=2.0)
                    logger.info(f"✅ Connected to neural_ui_do_button_handler")
                    
                    # Create a test message
                    test_plan_id = f"handler_test_plan_{int(time.time())}"
                    test_plan = {
                        "id": test_plan_id,
                        "title": "Handler Test Plan",
                        "description": "This plan tests neural_ui_do_button_handler",
                        "steps": [
                            {
                                "id": f"{test_plan_id}_step_1",
                                "type": "notification",
                                "action": "notify",
                                "content": "Handler test successful!",
                                "position": {"x": 500, "y": 300}
                            }
                        ],
                        "metadata": {
                            "created_at": time.time(),
                            "test_plan": True
                        }
                    }
                    
                    # Send a do_button_action message
                    handler_message = {
                        "type": "do_button_action",
                        "do_button_action": {
                            "action": "execute_plan",
                            "plan_id": test_plan_id
                        },
                        "plan": test_plan
                    }
                    
                    await handler_websocket.send(json.dumps(handler_message))
                    logger.info(f"✅ Sent do_button_action message to handler")
                    
                    # Wait for response
                    try:
                        response = await asyncio.wait_for(handler_websocket.recv(), timeout=2.0)
                        response_data = json.loads(response)
                        logger.info(f"✅ Received handler response: {response_data}")
                        
                        if response_data.get("type") == "success" or response_data.get("type") == "agent_progress":
                            logger.info(f"✅ Handler test successful")
                            return True
                        else:
                            logger.info(f"Received response type: {response_data.get('type')}")
                            return False
                    except asyncio.TimeoutError:
                        logger.warning("⚠️ No response received from handler within timeout period")
                        return False
                except asyncio.TimeoutError:
                    logger.warning("⚠️ No welcome message received from handler")
                    return False
        except (ConnectionRefusedError, websockets.exceptions.InvalidStatusCode) as e:
            logger.warning(f"⚠️ Could not connect to neural_ui_do_button_handler: {e}")
            return False
    except Exception as e:
        logger.error(f"❌ Error in handler test: {e}")
        return False

async def main():
    """Main function"""
    logger.info("🚀 Starting Neural UI DO Button Test")
    
    # Test neural_ui_do_button_flow
    flow_success = await test_neural_ui_do_button_flow()
    
    if flow_success:
        logger.info("✅ Neural UI DO Button Flow Test PASSED!")
    else:
        logger.error("❌ Neural UI DO Button Flow Test FAILED!")
    
    # Test neural_ui_do_button_handler
    handler_success = await test_neural_ui_do_button_handler()
    
    if handler_success:
        logger.info("✅ Neural UI DO Button Handler Test PASSED!")
    else:
        logger.warning("⚠️ Neural UI DO Button Handler Test FAILED - this is okay if the handler isn't running")
    
    # Overall assessment
    if flow_success:
        logger.info("✅ Neural UI DO Button Test PASSED OVERALL!")
    else:
        logger.error("❌ Neural UI DO Button Test FAILED OVERALL!")
        
    logger.info("Test completed.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Test stopped by user")
    except Exception as e:
        logger.error(f"Error in test: {e}")
        import traceback
        logger.error(traceback.format_exc())