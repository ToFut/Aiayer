#\!/usr/bin/env python3
"""
Test DO Button Fix Verification
This test specifically verifies the Agent Mode DO button execution fix
"""

import asyncio
import json
import websockets
import uuid
import time
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Test config
WS_URL = "ws://localhost:8767"
CLIENT_ID = f"test_client_{uuid.uuid4().hex[:8]}"
SESSION_ID = f"test_session_{uuid.uuid4().hex[:8]}"

async def send_agent_message(ws, message):
    """Send an agent mode message and get the plan response"""
    logger.info(f"Sending agent message: {message}")
    
    await ws.send(json.dumps({
        "type": "chat_message",
        "mode": "Agent",
        "message": message,
        "client_id": CLIENT_ID,
        "session_id": SESSION_ID,
        "timestamp": time.time()
    }))
    
    # Wait for agent_automation_plan response
    while True:
        response = await ws.recv()
        response_data = json.loads(response)
        logger.info(f"Received response type: {response_data.get('type')}")
        
        if response_data.get("type") == "agent_automation_plan":
            logger.info("✅ Received agent_automation_plan response")
            return response_data
        
        # If we get an error, log and return
        if response_data.get("type") == "error":
            logger.error(f"Error response: {response_data.get('error')}")
            return response_data

async def execute_plan(ws, plan_id):
    """Execute a plan and monitor progress updates"""
    logger.info(f"Executing plan: {plan_id}")
    
    # Send execution request
    await ws.send(json.dumps({
        "type": "agent_confirmation",
        "action": "DO",
        "client_id": CLIENT_ID,
        "session_id": SESSION_ID,
        "plan_id": plan_id,
        "timestamp": time.time()
    }))
    
    # Track progress updates
    progress_updates = []
    execution_completed = False
    timeout = time.time() + 30  # 30 second timeout
    
    # Wait for progress updates and final completion
    while time.time() < timeout and not execution_completed:
        response = await ws.recv()
        response_data = json.loads(response)
        
        # Handle different response types
        if response_data.get("type") == "agent_progress":
            logger.info(f"Progress update: {response_data.get('progress')}% - {response_data.get('message')}")
            progress_updates.append(response_data)
            
        elif response_data.get("type") == "agent_execution_success":
            logger.info(f"✅ Execution completed successfully: {response_data.get('summary')}")
            execution_completed = True
            return {
                "success": True, 
                "progress_updates": progress_updates,
                "execution_result": response_data
            }
            
        elif response_data.get("type") == "agent_execution_error":
            logger.error(f"❌ Execution failed: {response_data.get('error')}")
            return {
                "success": False,
                "progress_updates": progress_updates,
                "error": response_data.get("error")
            }
            
        elif response_data.get("type") == "error":
            logger.error(f"❌ Error response: {response_data.get('error')}")
            return {
                "success": False,
                "progress_updates": progress_updates,
                "error": response_data.get("error")
            }
    
    if not execution_completed:
        logger.error("❌ Execution timed out")
        return {
            "success": False,
            "progress_updates": progress_updates,
            "error": "Execution timed out"
        }

async def test_agent_mode_execution():
    """Test Agent Mode DO button execution fix"""
    logger.info("🧪 Testing Agent Mode DO button execution fix")
    
    try:
        # Connect to WebSocket
        async with websockets.connect(WS_URL) as ws:
            logger.info(f"Connected to {WS_URL}")
            
            # 1. Register client
            await ws.send(json.dumps({
                "type": "register",
                "client_id": CLIENT_ID,
                "timestamp": time.time()
            }))
            
            # Wait for registration confirmation
            response = await ws.recv()
            response_data = json.loads(response)
            
            if response_data.get("type") \!= "registration_successful":
                logger.error(f"Registration failed: {response_data}")
                return False
            
            logger.info("✅ Client registered successfully")
            
            # 2. Send Agent mode message to get a plan
            plan_response = await send_agent_message(ws, "open calculator")
            
            if not plan_response.get("success", False):
                logger.error("Failed to get automation plan")
                return False
            
            plan_id = plan_response.get("plan_id")
            logger.info(f"✅ Got plan ID: {plan_id}")
            
            # 3. Execute the plan
            execution_result = await execute_plan(ws, plan_id)
            
            # 4. Verify results
            if execution_result.get("success"):
                progress_updates = execution_result.get("progress_updates", [])
                if len(progress_updates) >= 2:
                    logger.info(f"✅ Received {len(progress_updates)} progress updates")
                    logger.info("✅ DO button execution fix is working correctly")
                    return True
                else:
                    logger.warning(f"⚠️ Only received {len(progress_updates)} progress updates (expected at least 2)")
                    return False
            else:
                logger.error(f"❌ Plan execution failed: {execution_result.get('error')}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        return False

async def main():
    """Run the test"""
    logger.info("🧪 Starting DO Button Fix Verification Test")
    
    # Run the test
    success = await test_agent_mode_execution()
    
    if success:
        logger.info("✅ TEST PASSED: Agent Mode DO button execution fix is working correctly")
        logger.info("All progress updates were received as expected")
        sys.exit(0)
    else:
        logger.error("❌ TEST FAILED: Agent Mode DO button execution fix is not working correctly")
        logger.error("Progress updates were not received as expected")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
EOF < /dev/null