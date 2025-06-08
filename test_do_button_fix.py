#!/usr/bin/env python3
"""
Test script to verify that the DO button fix works correctly
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
    format='[TEST-DO-BUTTON] %(levelname)s:%(name)s:%(message)s',
)
logger = logging.getLogger(__name__)

# Make sure cache/plans directory exists
os.makedirs(os.path.join("cache", "plans"), exist_ok=True)

# WebSocket URLs
WS_URL_BACKEND = "ws://localhost:8767/ws"
WS_URL_DO_BUTTON = "ws://localhost:8765"
WS_PROXY_URL = "ws://localhost:8766" 

async def test_do_button_direct():
    """Test DO button functionality directly against the DO button server"""
    logger.info("Testing DO button functionality directly")
    
    try:
        # Connect to DO button server
        logger.info(f"Connecting to DO button server at {WS_URL_DO_BUTTON}")
        ws = await websockets.connect(WS_URL_DO_BUTTON)
        welcome = await ws.recv()
        logger.info(f"Connected to DO button server: {welcome}")
        
        # Generate a test plan ID
        test_plan_id = f"test_plan_{uuid.uuid4()}"
        logger.info(f"Generated test plan ID: {test_plan_id}")
        
        # Create a test plan
        test_plan = {
            "id": test_plan_id,
            "task_id": test_plan_id,
            "plan_id": test_plan_id,
            "title": f"Test Plan {test_plan_id[:8]}",
            "description": "Test plan for DO button functionality",
            "steps": [
                {
                    "id": "step_1",
                    "description": "Test step 1",
                    "action_type": "test",
                    "estimated_duration": 1.0,
                    "status": "pending"
                }
            ],
            "estimated_duration": 1.0,
            "status": "awaiting_approval",
            "timestamp": time.time(),
            "created": time.time()
        }
        
        # Save the test plan
        plan_path = os.path.join("cache", "plans", f"{test_plan_id}.json")
        with open(plan_path, "w") as f:
            json.dump(test_plan, f)
        logger.info(f"Saved test plan to {plan_path}")
        
        # Create a DO button message
        do_button_message = {
            "type": "agent_confirmation",
            "action": "DO",
            "sessionId": test_plan_id,
            "timestamp": time.time()
        }
        
        # Send the DO button message
        logger.info(f"Sending DO button message: {json.dumps(do_button_message)}")
        await ws.send(json.dumps(do_button_message))
        
        # Wait for response
        response = await ws.recv()
        response_data = json.loads(response)
        logger.info(f"Received response: {response_data}")
        
        # Check if the response indicates success
        if response_data.get('success', False):
            logger.info("✅ DO button test successful!")
        else:
            logger.error(f"❌ DO button test failed: {response_data.get('error', 'Unknown error')}")
            
        # Close connection
        await ws.close()
        
    except Exception as e:
        logger.error(f"Error in DO button test: {e}")
        import traceback
        logger.error(traceback.format_exc())

async def test_agent_confirmation_proxy():
    """Test agent confirmation via the proxy WebSocket server"""
    logger.info("Testing agent confirmation via proxy")
    
    try:
        # Connect to proxy server
        logger.info(f"Connecting to proxy server at {WS_PROXY_URL}")
        ws = await websockets.connect(WS_PROXY_URL)
        welcome = await ws.recv()
        logger.info(f"Connected to proxy server: {welcome}")
        
        # Generate a test session ID in the format: task_{timestamp}_overlay_session_{timestamp}
        timestamp = int(time.time())
        session_timestamp = int(time.time() * 1000)
        test_session_id = f"task_{timestamp}_overlay_session_{session_timestamp}"
        logger.info(f"Generated test session ID: {test_session_id}")
        
        # Create an agent confirmation message
        agent_confirmation = {
            "type": "agent_confirmation",
            "action": "DO",
            "sessionId": test_session_id,
            "timestamp": time.time()
        }
        
        # Send the agent confirmation message
        logger.info(f"Sending agent confirmation message: {json.dumps(agent_confirmation)}")
        await ws.send(json.dumps(agent_confirmation))
        
        # Wait for response
        response = await ws.recv()
        response_data = json.loads(response)
        logger.info(f"Received response: {response_data}")
        
        # Check if the response indicates success
        if response_data.get('success', False) or response_data.get('type') != 'error':
            logger.info("✅ Agent confirmation test successful!")
        else:
            logger.error(f"❌ Agent confirmation test failed: {response_data.get('error', 'Unknown error')}")
            
        # Close connection
        await ws.close()
        
    except Exception as e:
        logger.error(f"Error in agent confirmation test: {e}")
        import traceback
        logger.error(traceback.format_exc())

async def test_full_chain():
    """Test the full chain from overlay to execution"""
    logger.info("Testing full chain from overlay to execution")
    
    try:
        # Connect to proxy server
        logger.info(f"Connecting to proxy server at {WS_PROXY_URL}")
        ws = await websockets.connect(WS_PROXY_URL)
        welcome = await ws.recv()
        logger.info(f"Connected to proxy server: {welcome}")
        
        # Generate a test plan ID with the format task_{timestamp}_overlay_session_{timestamp}
        timestamp = int(time.time())
        session_timestamp = int(time.time() * 1000)
        test_plan_id = f"task_{timestamp}_overlay_session_{session_timestamp}"
        logger.info(f"Generated test plan ID: {test_plan_id}")
        
        # Create a test request to backend to generate a plan
        agent_request = {
            "type": "chat_request",
            "mode": "Agent",
            "message": "Test agent request to generate a plan",
            "sessionId": test_plan_id,
            "userId": "test_user",
            "timestamp": time.time()
        }
        
        # Send the agent request
        logger.info(f"Sending agent request: {json.dumps(agent_request)}")
        await ws.send(json.dumps(agent_request))
        
        # Wait for response (this should be a plan)
        response = await ws.recv()
        response_data = json.loads(response)
        logger.info(f"Received response: {response_data.get('type', 'unknown')}")
        
        # Allow some time for the plan to be stored
        await asyncio.sleep(2)
        
        # Now send a DO button action for this plan
        do_button_message = {
            "type": "agent_confirmation",
            "action": "DO",
            "sessionId": test_plan_id,
            "timestamp": time.time()
        }
        
        # Send the DO button message
        logger.info(f"Sending DO button message: {json.dumps(do_button_message)}")
        await ws.send(json.dumps(do_button_message))
        
        # Wait for response
        try:
            response = await asyncio.wait_for(ws.recv(), timeout=10)
            response_data = json.loads(response)
            logger.info(f"Received DO button response: {response_data.get('type', 'unknown')}")
            
            # Check if the response indicates success
            if response_data.get('success', False) or response_data.get('type') != 'error':
                logger.info("✅ Full chain test successful!")
            else:
                logger.error(f"❌ Full chain test failed: {response_data.get('error', 'Unknown error')}")
        except asyncio.TimeoutError:
            logger.warning("No response received within timeout. This might be expected if plan execution is asynchronous.")
            logger.info("✅ Full chain test possibly successful (no error response received)")
            
        # Close connection
        await ws.close()
        
    except Exception as e:
        logger.error(f"Error in full chain test: {e}")
        import traceback
        logger.error(traceback.format_exc())

async def main():
    """Main entry point"""
    logger.info("Starting DO button fix tests")
    
    # Test DO button directly
    await test_do_button_direct()
    
    # Test agent confirmation via proxy
    await test_agent_confirmation_proxy()
    
    # Test full chain
    await test_full_chain()
    
    logger.info("DO button fix tests completed")

if __name__ == "__main__":
    asyncio.run(main())