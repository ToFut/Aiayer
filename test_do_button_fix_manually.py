#!/usr/bin/env python3
"""
Manual test script for DO button fix

This script tests the entire DO button fix chain by:
1. Creating a test plan directly
2. Sending a DO button request to the proxy on port 8766
3. Verifying the response
"""

import asyncio
import websockets
import json
import time
import uuid
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DO_BUTTON_FIX_TEST")

# Create a test plan
async def create_test_plan():
    """Create a test plan file directly"""
    os.makedirs(os.path.join("cache", "plans"), exist_ok=True)
    
    plan_id = f"test_plan_{uuid.uuid4()}"
    task_id = f"task_{int(time.time())}"
    session_id = f"overlay_session_{int(time.time()*1000)}"
    full_session_id = f"{task_id}_{session_id}"
    
    # Create plan data in the format expected by the Ultimate DO Button Server
    timestamp = time.time()
    plan_data = {
        "task_id": full_session_id,
        "plan_id": full_session_id,
        "title": "Test Plan for DO Button Fix",
        "description": "This plan tests the DO button fix",
        "steps": [
            {
                "id": "step_1",
                "description": "Open Google Chrome",
                "action_type": "open_app",
                "target": "Google Chrome",
                "estimated_duration": 1.0,
                "status": "pending"
            },
            {
                "id": "step_2",
                "description": "Click search box",
                "action_type": "click",
                "coordinates": {"x": 500, "y": 300},
                "estimated_duration": 1.0,
                "status": "pending"
            }
        ],
        "estimated_duration": 2.0,
        "status": "awaiting_approval",
        "creation_time": timestamp,
        "timestamp": timestamp,
        "created": timestamp,
        # Universal Automation Plan fields
        "type": "automation_plan",
        "name": "Test Plan for DO Button Fix",
        "description": "This plan tests the DO button fix",
        "target_app": "Google Chrome",
        "plan_type": "automation",
        "priority": "medium",
        "approval_status": "approved",
        "automation_status": "pending",
        "risk_level": "low",
        "automation_steps": [
            {
                "step_id": "step_1",
                "name": "Open Google Chrome",
                "action": "open_app",
                "target": "Google Chrome",
                "status": "pending"
            },
            {
                "step_id": "step_2", 
                "name": "Click search box",
                "action": "click",
                "coordinates": {"x": 500, "y": 300},
                "status": "pending"
            }
        ]
    }
    
    # Save the plan to a file
    plan_path = os.path.join("cache", "plans", f"{full_session_id}.json")
    with open(plan_path, "w") as f:
        json.dump(plan_data, f, indent=2)
    
    logger.info(f"Created test plan at {plan_path}")
    return full_session_id

# Send DO button request
async def send_do_button_request(session_id):
    """Send a DO button request to the proxy"""
    try:
        logger.info(f"Connecting to DO button proxy at ws://localhost:8766")
        async with websockets.connect("ws://localhost:8766", ping_interval=None) as ws:
            # Wait for welcome message
            welcome = await ws.recv()
            logger.info(f"Received welcome message: {welcome}")
            
            # Send agent confirmation message
            message = {
                "type": "agent_confirmation",
                "sessionId": session_id,
                "action": "execute_plan"
            }
            
            logger.info(f"Sending DO button request with session ID: {session_id}")
            await ws.send(json.dumps(message))
            
            # Wait for response
            response = await ws.recv()
            response_data = json.loads(response)
            
            logger.info(f"Received response: {json.dumps(response_data, indent=2)}")
            
            if response_data.get("success") or response_data.get("type") == "success":
                logger.info("✅ DO button request successful!")
                return True
            else:
                logger.error(f"❌ DO button request failed: {response_data.get('error', 'Unknown error')}")
                return False
                
    except Exception as e:
        logger.error(f"Error sending DO button request: {e}")
        return False

# Test ultimate DO button server directly
async def test_ultimate_do_button_server(session_id):
    """Test the ultimate DO button server directly"""
    try:
        logger.info(f"Connecting to Ultimate DO Button Server at ws://localhost:8768")
        async with websockets.connect("ws://localhost:8768", ping_interval=None) as ws:
            # Wait for welcome message
            welcome = await ws.recv()
            logger.info(f"Received welcome message from Ultimate DO Button Server: {welcome}")
            
            # Send agent confirmation message
            message = {
                "type": "agent_confirmation",
                "sessionId": session_id,
                "action": "execute_plan"
            }
            
            logger.info(f"Sending DO button request directly to Ultimate DO Button Server")
            await ws.send(json.dumps(message))
            
            # Wait for response
            response = await ws.recv()
            response_data = json.loads(response)
            
            logger.info(f"Received response from Ultimate DO Button Server: {json.dumps(response_data, indent=2)}")
            
            if response_data.get("success") or response_data.get("type") == "success":
                logger.info("✅ Direct Ultimate DO Button Server request successful!")
                return True
            else:
                logger.error(f"❌ Direct Ultimate DO Button Server request failed: {response_data.get('error', 'Unknown error')}")
                return False
                
    except Exception as e:
        logger.error(f"Error testing Ultimate DO Button Server: {e}")
        return False

# Main function
async def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("MANUAL DO BUTTON FIX TEST")
    logger.info("=" * 60)
    
    # Create a test plan
    session_id = await create_test_plan()
    logger.info(f"Created test plan with session ID: {session_id}")
    
    # Test proxy
    logger.info("\n" + "=" * 60)
    logger.info("TESTING DO BUTTON PROXY")
    logger.info("=" * 60)
    proxy_success = await send_do_button_request(session_id)
    
    # Test ultimate DO button server directly
    logger.info("\n" + "=" * 60)
    logger.info("TESTING ULTIMATE DO BUTTON SERVER DIRECTLY")
    logger.info("=" * 60)
    direct_success = await test_ultimate_do_button_server(session_id)
    
    # Overall result
    logger.info("\n" + "=" * 60)
    logger.info("TEST RESULTS")
    logger.info("=" * 60)
    
    if proxy_success and direct_success:
        logger.info("✅ BOTH TESTS PASSED")
        logger.info("The DO button fix is working correctly!")
    elif proxy_success:
        logger.info("⚠️ PARTIAL SUCCESS")
        logger.info("DO button proxy is working, but direct Ultimate DO Button Server test failed")
    elif direct_success:
        logger.info("⚠️ PARTIAL SUCCESS")
        logger.info("Ultimate DO Button Server is working, but DO button proxy test failed")
    else:
        logger.info("❌ ALL TESTS FAILED")
        logger.info("The DO button fix is not working correctly")
        
    logger.info("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())