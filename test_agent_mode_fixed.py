#!/usr/bin/env python3
"""
Test Agent Mode LLM Planning and Execution
This script tests if the Agent Mode now correctly creates real LLM plans and executes them.
"""

import asyncio
import json
import logging
import time
import websockets
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_agent_mode_llm_planning():
    """Test if Agent Mode now provides real LLM plans"""
    logger.info("🧪 Testing Agent Mode LLM planning...")
    
    # Connect to the backend WebSocket
    async with websockets.connect("ws://localhost:8767") as websocket:
        # Wait for connection established message
        response = await websocket.recv()
        logger.info(f"Connected to backend, received: {json.loads(response)['type']}")
        
        # Send an Agent Mode request
        request = {
            "type": "chat_request",
            "mode": "Agent",
            "message": "search for python tutorials on google",
            "session_id": f"test_{int(time.time())}",
            "client_id": f"test_client_{int(time.time())}"
        }
        
        logger.info(f"📤 Sending Agent Mode request: {request['message']}")
        await websocket.send(json.dumps(request))
        
        # Wait for response with plan
        plan_received = False
        real_llm_plan = False
        plan_id = None
        
        while True:
            response = await websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get("type") == "agent_automation_plan":
                logger.info("✅ Received agent_automation_plan response!")
                plan_received = True
                plan_id = response_data.get("plan_id")
                
                # Check if this is a real LLM plan
                if "universal_intelligent_automation" in response_data:
                    real_llm_plan = True
                    logger.info("✅ Confirmed real LLM plan using universal_intelligent_automation")
                elif "ai_powered" in response_data and response_data.get("ai_powered") == True:
                    real_llm_plan = True
                    logger.info("✅ Confirmed AI-powered plan")
                
                # Print plan details
                logger.info(f"📋 Plan ID: {plan_id}")
                logger.info(f"📋 Response: {response_data.get('response')[:200]}...")
                
                # Extract buttons
                buttons = response_data.get("buttons", [])
                if buttons:
                    logger.info(f"🔘 Plan has {len(buttons)} buttons:")
                    for button in buttons:
                        logger.info(f"  - {button.get('text')}: {button.get('action')}")
                
                break
                
            elif response_data.get("type") == "final_response":
                logger.info("✅ Received final_response!")
                plan_received = True
                
                # Check for interactive buttons
                if response_data.get("interactive", False) and response_data.get("buttons"):
                    plan_id = response_data.get("plan_id")
                    logger.info(f"📋 Plan ID: {plan_id}")
                    logger.info(f"📋 Response: {response_data.get('response')[:200]}...")
                    
                    # Check if this is a real LLM plan
                    if "universal_planning" in response_data or "ai_powered" in response_data:
                        real_llm_plan = True
                        logger.info("✅ Confirmed real LLM plan")
                    
                    # Extract buttons
                    buttons = response_data.get("buttons", [])
                    if buttons:
                        logger.info(f"🔘 Plan has {len(buttons)} buttons:")
                        for button in buttons:
                            logger.info(f"  - {button.get('text')}: {button.get('action')}")
                
                break
        
        if not plan_received:
            logger.error("❌ Did not receive a plan response!")
            return False, None
        
        if not real_llm_plan:
            logger.warning("⚠️ Received a plan, but it doesn't appear to be a real LLM plan")
        
        logger.info(f"✅ Successfully received Agent Mode plan with ID: {plan_id}")
        return True, plan_id

async def test_agent_mode_execution(plan_id: str):
    """Test if Agent Mode properly executes plans"""
    if not plan_id:
        logger.error("❌ Cannot test execution without a plan ID")
        return False
    
    logger.info(f"🧪 Testing Agent Mode execution for plan: {plan_id}")
    
    # Connect to the backend WebSocket
    async with websockets.connect("ws://localhost:8767") as websocket:
        # Wait for connection established message
        response = await websocket.recv()
        logger.info(f"Connected to backend, received: {json.loads(response)['type']}")
        
        # Send a button action request to execute the plan
        request = {
            "type": "button_action",
            "action": "execute_plan",
            "plan_id": plan_id,
            "session_id": f"test_exec_{int(time.time())}",
            "client_id": f"test_client_{int(time.time())}"
        }
        
        logger.info(f"📤 Sending execute_plan request for plan: {plan_id}")
        await websocket.send(json.dumps(request))
        
        # Wait for execution progress and result
        execution_started = False
        execution_completed = False
        max_wait_time = 30  # seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)
                
                # Log all responses for debugging
                logger.info(f"📥 Received response type: {response_data.get('type')}")
                
                if response_data.get("type") == "agent_progress":
                    execution_started = True
                    progress = response_data.get("progress", 0)
                    step = response_data.get("step", 0)
                    message = response_data.get("message", "")
                    logger.info(f"📊 Execution progress: {progress}% - Step {step}: {message}")
                
                elif response_data.get("type") in ["agent_execution_success", "plan_execution_success"]:
                    execution_completed = True
                    logger.info("✅ Execution completed successfully!")
                    logger.info(f"📋 Result: {response_data.get('summary', '')}")
                    break
                    
                elif response_data.get("type") in ["agent_execution_error", "plan_execution_error"]:
                    logger.error(f"❌ Execution failed: {response_data.get('error', 'Unknown error')}")
                    return False
            
            except asyncio.TimeoutError:
                logger.warning("⏳ Waiting for execution updates...")
        
        if not execution_started:
            logger.error("❌ Execution never started!")
            return False
        
        if not execution_completed:
            logger.warning("⚠️ Execution started but may not have completed within timeout")
            return False
        
        logger.info("✅ Agent Mode execution test passed!")
        return True

async def main():
    """Main function to test Agent Mode LLM and Execution"""
    logger.info("🧪 Starting Agent Mode LLM and Execution Test")
    
    # Test LLM planning
    logger.info("🧪 Testing LLM planning...")
    planning_success, plan_id = await test_agent_mode_llm_planning()
    
    # Test execution if planning succeeded
    execution_success = False
    if planning_success and plan_id:
        logger.info("🧪 Testing execution...")
        execution_success = await test_agent_mode_execution(plan_id)
    
    # Summary
    logger.info("
🔍 Test Summary:")
    logger.info(f"LLM planning: {'✅' if planning_success else '❌'}")
    logger.info(f"Plan execution: {'✅' if execution_success else '❌'}")
    
    if planning_success and execution_success:
        logger.info("
✅ Agent Mode LLM and Execution Test passed!")
    else:
        logger.info("
❌ Agent Mode LLM and Execution Test failed!")

if __name__ == "__main__":
    asyncio.run(main())
