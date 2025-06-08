#!/usr/bin/env python3
"""
Test Script to verify the DO button execution flow from the overlay to the backend.
This script will:
1. Send a suggestion notification to the overlay (port 8765)
2. Check if the suggestion is displayed 
3. Send a simulated DO button click
4. Verify the execution flow works end to end
"""

import asyncio
import json
import logging
import sys
import time
import websockets
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("do_button_test")

# WebSocket connection info
WS_URI = "ws://localhost:8765"  # Primary WebSocket server
NEURAL_WS_URI = "ws://localhost:8768"  # Neural UI DO button handler

async def test_suggestion_flow():
    """Test the full suggestion -> DO button execution flow"""
    try:
        # Step 1: Connect to WebSocket server
        logger.info(f"Connecting to WebSocket server at {WS_URI}")
        async with websockets.connect(WS_URI, ping_interval=5, ping_timeout=20) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            logger.info(f"Received welcome: {welcome[:100]}")
            
            # Step 2: Send a suggestion notification with DO button
            logger.info("Sending suggestion notification...")
            
            # Generate a consistent plan ID to use for both suggestion and action
            plan_id = f"test_plan_{int(time.time())}"
            
            suggestion = {
                "type": "do_button",
                "action": "display",
                "plan_id": plan_id,  # Add the plan ID to link suggestion with action
                "content": {
                    "title": "Test Suggestion",
                    "message": "This is a test suggestion for the DO button. Would you like to execute this action?",
                    "buttons": [
                        {
                            "id": "do_it",
                            "text": "Yes, do it",
                            "type": "primary"
                        },
                        {
                            "id": "dismiss",
                            "text": "No thanks",
                            "type": "secondary"
                        }
                    ]
                },
                "notification": True,  # Important: Enable notification
                "play_sound": True,    # Important: Enable sound
                "importance": "high"   # Mark as high importance
            }
            
            await websocket.send(json.dumps(suggestion))
            logger.info("Suggestion notification sent")
            
            # Wait for suggestion acknowledgement
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                logger.info(f"Received suggestion acknowledgement: {response[:100]}")
            except asyncio.TimeoutError:
                logger.warning("No acknowledgement received for suggestion")
            
            # Step 3: Wait a moment for the suggestion to be displayed
            await asyncio.sleep(2)
            
            # Step 4: Send a simulated DO button click (as if user clicked "Yes, do it")
            # Use the same plan_id defined earlier to ensure consistency
            do_button_action = {
                "type": "agent_confirmation",
                "action": "EXECUTE",
                "plan_id": plan_id,  # Use the same plan ID from the suggestion
                "session_id": f"test_session_{int(time.time())}",
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send(json.dumps(do_button_action))
            logger.info("DO button action sent")
            
            # Step 5: Wait for execution responses
            execution_success = False
            execution_progress = 0
            
            # Wait for up to 30 seconds for responses
            timeout_end = time.time() + 30
            while time.time() < timeout_end:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2)
                    try:
                        data = json.loads(response)
                        response_type = data.get("type", "")
                        
                        if response_type == "agent_progress":
                            progress = data.get("progress", 0)
                            message = data.get("message", "")
                            execution_progress = progress
                            logger.info(f"Execution progress: {progress}% - {message}")
                            
                        elif response_type == "agent_execution_success":
                            summary = data.get("summary", "")
                            logger.info(f"Execution success: {summary}")
                            execution_success = True
                            break
                            
                        elif response_type == "agent_execution_error":
                            error = data.get("error", "")
                            logger.error(f"Execution error: {error}")
                            break
                            
                    except json.JSONDecodeError:
                        logger.warning(f"Received non-JSON response: {response[:100]}")
                        
                except asyncio.TimeoutError:
                    # No message received in the timeout period, continue waiting
                    pass
            
            if execution_success:
                logger.info("✅ DO button execution flow completed successfully!")
            else:
                logger.warning(f"⚠️ DO button execution flow did not complete successfully. Progress: {execution_progress}%")
                
            return execution_success
                
    except Exception as e:
        logger.error(f"Error in test_suggestion_flow: {e}")
        return False

async def test_neural_ui_direct():
    """Test direct connection to Neural UI DO button handler"""
    try:
        logger.info(f"Connecting to Neural UI DO button handler at {NEURAL_WS_URI}")
        async with websockets.connect(NEURAL_WS_URI, ping_interval=5, ping_timeout=20) as websocket:
            logger.info("Connected to Neural UI DO button handler")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            logger.info(f"Received welcome from Neural UI handler: {welcome[:100]}")
            
            # Send a direct DO button action
            plan_id = f"test_neural_direct_{int(time.time())}"
            do_button_action = {
                "type": "agent_confirmation",
                "action": "EXECUTE",
                "plan_id": plan_id,  # Add a valid plan ID that will be recognized by the system
                "session_id": f"test_neural_direct_{int(time.time())}",
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send(json.dumps(do_button_action))
            logger.info("Direct DO button action sent to Neural UI handler")
            
            # Wait for execution responses
            execution_success = False
            
            # Wait for up to 30 seconds for responses
            timeout_end = time.time() + 30
            while time.time() < timeout_end:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2)
                    try:
                        data = json.loads(response)
                        response_type = data.get("type", "")
                        
                        if response_type == "agent_progress":
                            progress = data.get("progress", 0)
                            message = data.get("message", "")
                            logger.info(f"Neural UI execution progress: {progress}% - {message}")
                            
                        elif response_type == "agent_execution_success":
                            summary = data.get("summary", "")
                            logger.info(f"Neural UI execution success: {summary}")
                            execution_success = True
                            break
                            
                        elif response_type == "agent_execution_error":
                            error = data.get("error", "")
                            logger.error(f"Neural UI execution error: {error}")
                            break
                            
                    except json.JSONDecodeError:
                        logger.warning(f"Received non-JSON response from Neural UI: {response[:100]}")
                        
                except asyncio.TimeoutError:
                    # No message received in the timeout period, continue waiting
                    pass
            
            if execution_success:
                logger.info("✅ Neural UI direct execution completed successfully!")
            else:
                logger.warning("⚠️ Neural UI direct execution did not complete successfully")
                
            return execution_success
                
    except Exception as e:
        logger.error(f"Error in test_neural_ui_direct: {e}")
        return False

async def main():
    """Run all tests"""
    # Test 1: Full suggestion flow
    full_flow_success = await test_suggestion_flow()
    
    # Test 2: Direct Neural UI connection
    neural_direct_success = await test_neural_ui_direct()
    
    # Report results
    logger.info("\n===== TEST RESULTS =====")
    logger.info(f"Full suggestion flow: {'✅ PASS' if full_flow_success else '❌ FAIL'}")
    logger.info(f"Direct Neural UI connection: {'✅ PASS' if neural_direct_success else '❌ FAIL'}")
    
    if full_flow_success and neural_direct_success:
        logger.info("🎉 All tests passed! DO button execution is working correctly")
        return 0
    else:
        logger.warning("⚠️ Some tests failed. Check the logs for details.")
        return 1

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)