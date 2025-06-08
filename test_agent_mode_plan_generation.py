#!/usr/bin/env python3
"""
Test Agent Mode Plan Generation

This script tests the plan generation in Agent Mode to diagnose why plans aren't being created.
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
        logging.FileHandler("logs/test_agent_mode_plan_generation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TestAgentModePlanGeneration")

async def test_agent_mode_request():
    """Test sending an agent mode request to the backend"""
    try:
        # Connect to backend server
        uri = "ws://localhost:8767/ws"
        logger.info(f"Connecting to backend at {uri}")
        
        async with websockets.connect(uri) as websocket:
            # Get welcome message
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            client_id = welcome_data.get("client_id")
            logger.info(f"✅ Connected to backend with client_id: {client_id}")
            
            # Create an agent mode request
            agent_request = {
                "type": "agent_mode_request",
                "client_id": client_id,
                "message": "Open Google and search for weather in San Francisco",
                "current_app": "Chrome",
                "timestamp": time.time()
            }
            
            # Send the request
            await websocket.send(json.dumps(agent_request))
            logger.info(f"✅ Sent agent_mode_request")
            
            # Wait for responses
            responses = []
            start_time = time.time()
            plan_created = False
            
            while time.time() - start_time < 30.0:  # Wait up to 30 seconds for a response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    response_data = json.loads(response)
                    responses.append(response_data)
                    logger.info(f"✅ Received response: {json.dumps(response_data)[:200]}...")
                    
                    # Check if this response contains a plan
                    if "plan" in response_data:
                        plan_created = True
                        logger.info(f"✅ Plan created in response!")
                        break
                        
                    # Also check for plan_id in the response
                    if "plan_id" in response_data:
                        plan_created = True
                        logger.info(f"✅ Plan ID found in response: {response_data.get('plan_id')}")
                        break
                    
                    # Check if response contains an automation_plan
                    if "automation_plan" in response_data:
                        plan_created = True
                        logger.info(f"✅ Automation plan found in response!")
                        break
                except asyncio.TimeoutError:
                    logger.info(f"Waiting for more responses...")
                except Exception as e:
                    logger.error(f"❌ Error receiving response: {e}")
                    break
            
            # Check if a plan was created
            if plan_created:
                logger.info(f"✅ Agent mode successfully created a plan!")
                return True
            else:
                logger.error(f"❌ Agent mode did not create a plan within 30 seconds")
                logger.info(f"Received {len(responses)} responses without a plan")
                return False
    except Exception as e:
        logger.error(f"❌ Error in agent mode test: {e}")
        return False

async def test_agent_mode_with_llm():
    """Test agent mode with direct LLM connection"""
    try:
        # Connect to LLM service
        llm_uri = "ws://localhost:8770/ws"
        logger.info(f"Trying to connect to LLM service at {llm_uri}")
        
        try:
            async with websockets.connect(llm_uri) as llm_websocket:
                # Get welcome message
                welcome = await asyncio.wait_for(llm_websocket.recv(), timeout=2.0)
                logger.info(f"✅ Connected to LLM service")
                
                # Create an agent mode request directly to LLM
                llm_request = {
                    "type": "agent_mode_request",
                    "message": "Open Google and search for weather in San Francisco",
                    "current_app": "Chrome",
                    "timestamp": time.time()
                }
                
                # Send the request
                await llm_websocket.send(json.dumps(llm_request))
                logger.info(f"✅ Sent agent_mode_request to LLM service")
                
                # Wait for response
                try:
                    response = await asyncio.wait_for(llm_websocket.recv(), timeout=20.0)
                    response_data = json.loads(response)
                    logger.info(f"✅ Received LLM response: {json.dumps(response_data)[:200]}...")
                    
                    # Check if response contains a plan
                    if "plan" in response_data or "automation_plan" in response_data:
                        logger.info(f"✅ LLM service generated a plan!")
                        return True
                    else:
                        logger.warning(f"⚠️ LLM response didn't contain a plan")
                        return False
                except asyncio.TimeoutError:
                    logger.warning(f"⚠️ No response from LLM service within timeout")
                    return False
        except (ConnectionRefusedError, asyncio.TimeoutError) as e:
            logger.warning(f"⚠️ Could not connect to LLM service: {e}")
    except Exception as e:
        logger.error(f"❌ Error in LLM service test: {e}")
    
    # If we couldn't connect to LLM service, try the alternative method
    return await test_agent_mode_plan_generation()

async def test_agent_mode_plan_generation():
    """Test the plan generation aspect of agent mode directly"""
    try:
        # Connect to backend server
        uri = "ws://localhost:8767/ws"
        logger.info(f"Connecting to backend at {uri}")
        
        async with websockets.connect(uri) as websocket:
            # Get welcome message
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            client_id = welcome_data.get("client_id")
            logger.info(f"✅ Connected to backend with client_id: {client_id}")
            
            # Create a direct plan generation request
            plan_request = {
                "type": "generate_plan",
                "client_id": client_id,
                "task": "Open Google and search for weather in San Francisco",
                "current_app": "Chrome",
                "timestamp": time.time()
            }
            
            # Send the request
            await websocket.send(json.dumps(plan_request))
            logger.info(f"✅ Sent generate_plan request")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=20.0)
                response_data = json.loads(response)
                logger.info(f"✅ Received response: {json.dumps(response_data)[:200]}...")
                
                # Check if the response type indicates an error
                if response_data.get("type") == "error":
                    logger.error(f"❌ Error response: {response_data.get('error')}")
                    return False
                
                # Check if this response contains a plan
                if "plan" in response_data:
                    logger.info(f"✅ Plan generated successfully!")
                    return True
                else:
                    logger.warning(f"⚠️ Response didn't contain a plan")
                    return False
            except asyncio.TimeoutError:
                logger.warning(f"⚠️ No response within timeout period")
                return False
    except Exception as e:
        logger.error(f"❌ Error in plan generation test: {e}")
        return False

async def check_pending_plans():
    """Check if there are any pending plans in the system"""
    try:
        # Connect to DO button server to check for plans
        uri = "ws://localhost:8765"
        logger.info(f"Connecting to DO button server at {uri} to check for plans")
        
        async with websockets.connect(uri) as websocket:
            # Get welcome message
            welcome = await websocket.recv()
            logger.info(f"✅ Connected to DO button server")
            
            # Send a request to check pending plans
            check_request = {
                "type": "check_pending_plans"
            }
            
            await websocket.send(json.dumps(check_request))
            logger.info(f"✅ Sent check_pending_plans request")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                response_data = json.loads(response)
                logger.info(f"✅ Received response: {response_data}")
                
                # Check if there are any plans
                if "plans" in response_data:
                    plans = response_data.get("plans", [])
                    if plans:
                        logger.info(f"✅ Found {len(plans)} pending plans")
                        return True
                    else:
                        logger.warning(f"⚠️ No pending plans found")
                        return False
                else:
                    logger.warning(f"⚠️ Response didn't contain plans information")
                    return False
            except asyncio.TimeoutError:
                logger.warning(f"⚠️ No response within timeout period")
                return False
    except Exception as e:
        logger.error(f"❌ Error checking pending plans: {e}")
        return False

async def main():
    """Main function"""
    logger.info("🚀 Starting Agent Mode Plan Generation Test")
    
    # Check for existing plans
    logger.info("Checking for existing plans...")
    plans_exist = await check_pending_plans()
    
    if plans_exist:
        logger.info("✅ Plans already exist in the system")
    else:
        logger.info("No existing plans found, testing plan generation...")
        
        # Test agent mode request
        logger.info("Testing agent mode request...")
        agent_mode_success = await test_agent_mode_request()
        
        if agent_mode_success:
            logger.info("✅ Agent Mode Test PASSED!")
        else:
            logger.error("❌ Agent Mode Test FAILED!")
            
            # Try alternate approach with LLM service
            logger.info("Testing agent mode with LLM service...")
            llm_success = await test_agent_mode_with_llm()
            
            if llm_success:
                logger.info("✅ Agent Mode with LLM Test PASSED!")
            else:
                logger.error("❌ Agent Mode with LLM Test FAILED!")
                
                # Try direct plan generation
                logger.info("Testing direct plan generation...")
                plan_gen_success = await test_agent_mode_plan_generation()
                
                if plan_gen_success:
                    logger.info("✅ Plan Generation Test PASSED!")
                else:
                    logger.error("❌ Plan Generation Test FAILED!")
    
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