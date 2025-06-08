#!/usr/bin/env python3
"""
test_suggestion_with_fixed_do_button.py - Test the complete suggestion flow with the fixed DO button server

This script verifies that suggestions work correctly with the fixed_do_button_server.py,
testing each step of the flow from:
1. Sending a suggestion
2. Receiving it in the overlay
3. Transitioning to Agent mode when accepted
4. Executing the plan

Run this script to test the full integration with sound notifications.
"""

import asyncio
import websockets
import json
import time
import sys
import logging
import os
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("suggestion_fixed_test")

# Configuration
WS_ENDPOINT = "ws://localhost:8765"
PLAN_ID = f"test_plan_{int(time.time())}"

async def check_server_status():
    """Check if the WebSocket server is running on port 8765"""
    try:
        async with websockets.connect(WS_ENDPOINT, timeout=5) as ws:
            # Wait for welcome message
            welcome = await asyncio.wait_for(ws.recv(), timeout=5)
            welcome_data = json.loads(welcome)
            if welcome_data.get("type") == "welcome":
                logger.info("✅ DO Button Server is running and accessible")
                return True
            else:
                logger.warning(f"⚠️ Unexpected welcome message: {welcome_data}")
                return False
    except Exception as e:
        logger.error(f"❌ Cannot connect to DO Button Server: {str(e)}")
        return False

async def test_step1_send_suggestion():
    """Step 1: Send a test suggestion to the overlay"""
    logger.info("STEP 1: Sending test suggestion to overlay")
    
    try:
        # Connect to the WebSocket server
        async with websockets.connect(WS_ENDPOINT) as ws:
            # Wait for welcome message
            welcome = await ws.recv()
            
            # Create suggestion with notification flags
            suggestion = {
                "success": True,
                "response": "💡 Browser Tab Organization: You have many browser tabs open. Would you like me to organize them?",
                "mode": "SUGGEST",
                "processing_time": 0.5,
                "enterprise_validated": True,
                "notification": True,
                "play_sound": True,
                "sound_type": "notification",
                "importance": "high",
                "buttons": [
                    {
                        "id": "do_it",
                        "text": "Yes, help me",
                        "action": "accept",
                        "style": "success"
                    },
                    {
                        "id": "dismiss",
                        "text": "No thanks",
                        "action": "dismiss",
                        "style": "danger"
                    }
                ],
                "interactive": True,
                "plan_id": PLAN_ID,
                "timestamp": time.time()
            }
            
            # Send suggestion
            suggestion_json = json.dumps(suggestion)
            await ws.send(suggestion_json)
            logger.info("✅ Suggestion sent to DO Button Server")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5)
                logger.info(f"Received response: {response[:100]}")
            except asyncio.TimeoutError:
                logger.info("No response received (this is normal)")
                
            return True
            
    except Exception as e:
        logger.error(f"❌ Error sending suggestion: {str(e)}")
        return False

async def test_step2_verify_user_interaction():
    """Step 2: Wait for user to interact with the suggestion"""
    logger.info("STEP 2: Verify user interaction with suggestion")
    
    print("\n" + "="*60)
    print("USER ACTION REQUIRED")
    print("="*60)
    print("Please look at the NextGen overlay chat window and verify:")
    print("1. Do you see the suggestion with sound notification?")
    print("2. Click 'Yes, help me' to accept the suggestion")
    print("\nEnter 'y' when you've seen the suggestion: ")
    
    # Wait for user confirmation
    response = await asyncio.get_event_loop().run_in_executor(None, input)
    
    if response.lower() == 'y':
        logger.info("✅ User confirmed seeing the suggestion")
        return True
    else:
        logger.warning("⚠️ User did not confirm seeing the suggestion")
        return False

async def test_step3_send_mode_transition():
    """Step 3: Send mode transition from Suggest to Agent"""
    logger.info("STEP 3: Sending mode transition to Agent")
    
    try:
        # Connect to the WebSocket server
        async with websockets.connect(WS_ENDPOINT) as ws:
            # Wait for welcome message
            welcome = await ws.recv()
            
            # Create Agent mode payload
            agent_payload = {
                "success": True,
                "response": f"🤖 Ready to organize your browser tabs. I'll perform the following steps:",
                "mode": "Agent",
                "processing_time": 0.3,
                "enterprise_validated": True,
                "notification": False,
                "plan_id": PLAN_ID,
                "buttons": [
                    {
                        "id": "execute_plan",
                        "text": "Execute Now",
                        "action": "execute_plan",
                        "style": "success"
                    },
                    {
                        "id": "cancel",
                        "text": "Cancel",
                        "action": "cancel",
                        "style": "danger"
                    }
                ],
                "interactive": True,
                "requires_approval": True,
                "plan": {
                    "id": PLAN_ID,
                    "title": "Browser Tab Organization",
                    "steps": [
                        {"description": "Step 1: Analyze current open tabs", "type": "analysis"},
                        {"description": "Step 2: Group similar tabs by category", "type": "action"},
                        {"description": "Step 3: Create bookmarks for organized tabs", "type": "action"},
                        {"description": "Step 4: Close duplicate or unnecessary tabs", "type": "action"}
                    ],
                    "estimated_duration": "1 minute",
                    "risk_level": "low"
                }
            }
            
            # Send mode transition
            agent_json = json.dumps(agent_payload)
            await ws.send(agent_json)
            logger.info("✅ Agent mode transition sent")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Error sending mode transition: {str(e)}")
        return False

async def test_step4_verify_mode_transition():
    """Step 4: Verify that mode transition is visible to user"""
    logger.info("STEP 4: Verify mode transition in UI")
    
    print("\n" + "="*60)
    print("USER ACTION REQUIRED")
    print("="*60)
    print("In the NextGen overlay chat window, verify:")
    print("1. Did the UI switch to Agent mode with a plan?")
    print("2. Can you see the 'Execute Now' button?")
    print("3. Click 'Execute Now' to test plan execution")
    print("\nEnter 'y' when you've seen the Agent mode transition: ")
    
    # Wait for user confirmation
    response = await asyncio.get_event_loop().run_in_executor(None, input)
    
    if response.lower() == 'y':
        logger.info("✅ User confirmed seeing the Agent mode transition")
        return True
    else:
        logger.warning("⚠️ User did not confirm seeing the Agent mode transition")
        return False

async def test_step5_simulate_execution():
    """Step 5: Simulate plan execution with progress updates"""
    logger.info("STEP 5: Simulating plan execution")
    
    try:
        # Connect to the WebSocket server
        async with websockets.connect(WS_ENDPOINT) as ws:
            # Wait for welcome message
            welcome = await ws.recv()
            
            # Send execution progress updates
            steps = [
                {"progress": 25, "currentStep": "Analyzing current open tabs", "stepNumber": 1, "totalSteps": 4},
                {"progress": 50, "currentStep": "Grouping similar tabs by category", "stepNumber": 2, "totalSteps": 4},
                {"progress": 75, "currentStep": "Creating bookmarks for organized tabs", "stepNumber": 3, "totalSteps": 4},
                {"progress": 100, "currentStep": "Closing duplicate tabs", "stepNumber": 4, "totalSteps": 4}
            ]
            
            for step in steps:
                # Create progress update
                progress_update = {
                    "type": "execution_progress",
                    "progress": step["progress"],
                    "currentStep": step["currentStep"],
                    "stepNumber": step["stepNumber"],
                    "totalSteps": step["totalSteps"]
                }
                
                # Send progress update
                await ws.send(json.dumps(progress_update))
                logger.info(f"✅ Sent progress update: {step['progress']}% - {step['currentStep']}")
                
                # Wait between updates
                await asyncio.sleep(1.5)
            
            # Send completion message
            completion = {
                "type": "execution_complete",
                "result": "Browser tabs successfully organized! Created 3 bookmark categories and closed 5 duplicate tabs.",
                "timestamp": time.time()
            }
            
            await ws.send(json.dumps(completion))
            logger.info("✅ Sent execution completion message")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Error simulating execution: {str(e)}")
        return False

async def test_step6_verify_execution():
    """Step 6: Verify execution progress and completion"""
    logger.info("STEP 6: Verify execution progress and completion in UI")
    
    print("\n" + "="*60)
    print("USER ACTION REQUIRED")
    print("="*60)
    print("In the NextGen overlay chat window, verify:")
    print("1. Did you see the execution progress updates?")
    print("2. Did you see the completion message?")
    print("\nEnter 'y' when you've seen the execution complete: ")
    
    # Wait for user confirmation
    response = await asyncio.get_event_loop().run_in_executor(None, input)
    
    if response.lower() == 'y':
        logger.info("✅ User confirmed seeing execution progress and completion")
        return True
    else:
        logger.warning("⚠️ User did not confirm seeing execution completion")
        return False

async def run_tests():
    """Run all test steps"""
    print("\n" + "="*80)
    print(" PROACTIVE SUGGESTION SYSTEM TEST WITH FIXED DO BUTTON SERVER ".center(80, "="))
    print("="*80 + "\n")
    
    # Step 0: Check server status
    server_ok = await check_server_status()
    if not server_ok:
        logger.error("❌ Test cannot continue: DO Button Server is not running")
        return False
    
    # Step 1: Send suggestion
    step1_result = await test_step1_send_suggestion()
    if not step1_result:
        logger.error("❌ Test cannot continue: Failed to send suggestion")
        return False
    
    # Step 2: Verify user interaction
    step2_result = await test_step2_verify_user_interaction()
    
    # Step 3: Send mode transition
    step3_result = await test_step3_send_mode_transition()
    if not step3_result:
        logger.error("❌ Test cannot continue: Failed to send mode transition")
        return False
    
    # Step 4: Verify mode transition
    step4_result = await test_step4_verify_mode_transition()
    
    # Step 5: Simulate execution
    step5_result = await test_step5_simulate_execution()
    if not step5_result:
        logger.error("❌ Test cannot continue: Failed to simulate execution")
        return False
    
    # Step 6: Verify execution
    step6_result = await test_step6_verify_execution()
    
    # Print results summary
    print("\n" + "="*80)
    print(" TEST RESULTS SUMMARY ".center(80, "="))
    print("="*80)
    print(f"Step 1 - Send Suggestion: {'✅ PASS' if step1_result else '❌ FAIL'}")
    print(f"Step 2 - Verify User Interaction: {'✅ PASS' if step2_result else '❌ FAIL'}")
    print(f"Step 3 - Send Mode Transition: {'✅ PASS' if step3_result else '❌ FAIL'}")
    print(f"Step 4 - Verify Mode Transition: {'✅ PASS' if step4_result else '❌ FAIL'}")
    print(f"Step 5 - Simulate Execution: {'✅ PASS' if step5_result else '❌ FAIL'}")
    print(f"Step 6 - Verify Execution: {'✅ PASS' if step6_result else '❌ FAIL'}")
    print("-"*80)
    
    overall_result = all([step1_result, step2_result, step3_result, step4_result, step5_result, step6_result])
    print(f"Overall Test Result: {'✅ PASS' if overall_result else '❌ FAIL'}")
    print("="*80 + "\n")
    
    return overall_result

async def verify_overlay_access():
    """Verify that user has access to the overlay"""
    print("\n" + "="*60)
    print("OVERLAY ACCESS VERIFICATION")
    print("="*60)
    print("Before running this test, make sure:")
    print("1. The NextGen overlay is running and visible")
    print("2. START_ENHANCED_SYSTEM.sh has been executed")
    print("3. All system components are running")
    print("\nDo you have access to the NextGen overlay? (y/n): ")
    
    # Wait for user confirmation
    response = await asyncio.get_event_loop().run_in_executor(None, input)
    
    if response.lower() == 'y':
        return True
    else:
        logger.error("❌ Test cannot continue: User does not have access to the overlay")
        print("\nPlease make sure the overlay is running by:")
        print("1. Starting the system: ./START_ENHANCED_SYSTEM.sh")
        print("2. Launching the overlay interface")
        return False

if __name__ == "__main__":
    try:
        # Verify overlay access first
        loop = asyncio.get_event_loop()
        has_overlay = loop.run_until_complete(verify_overlay_access())
        
        if has_overlay:
            # Run the tests
            result = loop.run_until_complete(run_tests())
            sys.exit(0 if result else 1)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error in tests: {str(e)}")
        sys.exit(1)