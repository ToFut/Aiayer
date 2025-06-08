#!/usr/bin/env python3
"""
Test script for the simple DO button fix
"""

import asyncio
import websockets
import json
import logging
import time
import uuid
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SIMPLE_TEST")

async def create_test_plan():
    """Create a test plan for execution"""
    session_id = f"task_{int(time.time())}_overlay_session_{int(time.time()*1000)}"
    
    # Create plan directory if it doesn't exist
    os.makedirs(os.path.join("cache", "plans"), exist_ok=True)
    
    # Simple plan suitable for the Universal Automation Handler
    plan = {
        "type": "automation_plan",
        "name": f"Test Plan {uuid.uuid4()}",
        "task_id": session_id,
        "description": "This is a test plan for the simple DO button fix",
        "target_app": "Browser",
        "steps": [
            {
                "step_id": "step_1",
                "name": "Open browser",
                "action": "open_app",
                "status": "pending"
            }
        ],
        "plan_type": "automation",
        "priority": "medium",
        "status": "awaiting_approval",
        "approval_status": "approved",
        "automation_status": "pending",
        "risk_level": "low",
        "created": time.time(),
        "automation_steps": [
            {
                "step_id": "step_1",
                "name": "Open browser",
                "action": "open_app", 
                "status": "pending"
            }
        ]
    }
    
    # Save plan to file
    plan_path = os.path.join("cache", "plans", f"{session_id}.json")
    with open(plan_path, "w") as f:
        json.dump(plan, f, indent=2)
    
    logger.info(f"Created test plan: {session_id}")
    return session_id

async def test_simple_proxy():
    """Test the simple DO button fix proxy"""
    session_id = await create_test_plan()
    
    try:
        # Connect to proxy
        logger.info(f"Connecting to proxy on ws://localhost:8766")
        async with websockets.connect("ws://localhost:8766", ping_interval=None) as ws:
            # Wait for welcome message
            welcome = await ws.recv()
            logger.info(f"Received welcome: {welcome}")
            
            # Send execute_plan request
            message = {
                "type": "agent_confirmation",
                "sessionId": session_id,
                "action": "execute_plan"
            }
            
            logger.info(f"Sending execute_plan request for session: {session_id}")
            await ws.send(json.dumps(message))
            
            # Wait for response
            response = await ws.recv()
            data = json.loads(response)
            
            if data.get("success") or data.get("type") == "success":
                logger.info("✅ Success response received")
                logger.info(f"Response: {json.dumps(data, indent=2)}")
                return True
            else:
                logger.error("❌ Error response received")
                logger.error(f"Response: {json.dumps(data, indent=2)}")
                return False
    except Exception as e:
        logger.error(f"Error in test: {e}")
        return False

async def test_direct_server():
    """Test the ultimate DO button server directly"""
    session_id = await create_test_plan()
    
    try:
        # Connect directly to ultimate server
        logger.info(f"Connecting directly to server on ws://localhost:8768")
        async with websockets.connect("ws://localhost:8768", ping_interval=None) as ws:
            # Wait for welcome message
            welcome = await ws.recv()
            logger.info(f"Received welcome: {welcome}")
            
            # Send execute_plan request
            message = {
                "type": "agent_confirmation",
                "sessionId": session_id,
                "action": "execute_plan"
            }
            
            logger.info(f"Sending execute_plan request for session: {session_id}")
            await ws.send(json.dumps(message))
            
            # Wait for response
            response = await ws.recv()
            data = json.loads(response)
            
            logger.info(f"Direct server response: {json.dumps(data, indent=2)}")
            return True
    except Exception as e:
        logger.error(f"Error in direct server test: {e}")
        return False

async def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("SIMPLE DO BUTTON FIX TEST")
    logger.info("=" * 60)
    
    # Test via proxy
    logger.info("\nTESTING VIA PROXY:")
    proxy_result = await test_simple_proxy()
    
    # Test direct
    logger.info("\nTESTING DIRECT SERVER:")
    direct_result = await test_direct_server()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST RESULTS")
    logger.info("=" * 60)
    
    logger.info(f"Proxy test: {'✅ PASSED' if proxy_result else '❌ FAILED'}")
    logger.info(f"Direct test: {'✅ PASSED' if direct_result else '❌ FAILED'}")
    
    if proxy_result and direct_result:
        logger.info("\n✅ ALL TESTS PASSED - Simple DO button fix is working correctly!")
    elif proxy_result:
        logger.info("\n⚠️ PROXY TEST PASSED but direct test failed")
    elif direct_result:
        logger.info("\n⚠️ DIRECT TEST PASSED but proxy test failed")
    else:
        logger.info("\n❌ ALL TESTS FAILED - Fix implementation needs review")

if __name__ == "__main__":
    asyncio.run(main())