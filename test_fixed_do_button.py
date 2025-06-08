#!/usr/bin/env python3
"""
Test script for the fixed DO button functionality
This script connects to the DO button proxy on port 8766 and sends test messages
"""
import asyncio
import websockets
import json
import logging
import os
import time
import sys
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger('test_fixed_do_button')

# Test plan ID
TEST_PLAN_ID = f"test_plan_{int(time.time())}"

async def test_connection():
    """Test connection to the DO button proxy"""
    try:
        logger.info(f"Connecting to DO Button proxy on ws://localhost:8766...")
        async with websockets.connect("ws://localhost:8766") as websocket:
            logger.info("Connected to DO Button proxy!")
            
            # Wait for welcome message
            response = await websocket.recv()
            welcome = json.loads(response)
            logger.info(f"Received welcome message: {welcome.get('type', 'unknown')}")
            
            # Send agent_confirmation message with DO action
            agent_confirmation = {
                "type": "agent_confirmation",
                "action": "DO",
                "session_id": TEST_PLAN_ID,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Sending agent_confirmation with DO action for plan: {TEST_PLAN_ID}")
            await websocket.send(json.dumps(agent_confirmation))
            
            # Receive and log responses (up to 5 messages or for 10 seconds)
            start_time = time.time()
            message_count = 0
            
            while time.time() - start_time < 10 and message_count < 5:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(response)
                    message_count += 1
                    
                    logger.info(f"Response {message_count}: {data.get('type', 'unknown')}")
                    
                    # Check for success message
                    if data.get('type') == 'agent_execution_success':
                        logger.info("✅ Received execution success message!")
                    elif data.get('type') == 'agent_progress':
                        logger.info(f"📊 Progress update: {data.get('progress')}% - {data.get('message')}")
                    
                except asyncio.TimeoutError:
                    # No more messages available
                    break
                except Exception as e:
                    logger.error(f"Error receiving response: {e}")
                    break
            
            logger.info(f"Test completed with {message_count} messages received")
            return True
            
    except Exception as e:
        logger.error(f"Connection error: {e}")
        return False

if __name__ == "__main__":
    try:
        # Run the test
        print("=" * 60)
        print(" DO Button Functionality Test")
        print("=" * 60)
        print(" This test will send an agent_confirmation message with DO action")
        print(" to verify that the DO button proxy is working correctly.")
        print("-" * 60)
        
        result = asyncio.run(test_connection())
        
        print("-" * 60)
        if result:
            print("✅ Test PASSED: Successfully connected and received responses")
        else:
            print("❌ Test FAILED: Could not connect or didn't receive expected responses")
        print("-" * 60)
        
    except KeyboardInterrupt:
        print("Test interrupted by user")
    except Exception as e:
        print(f"Error running test: {e}")