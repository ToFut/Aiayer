#!/usr/bin/env python3
"""
Test Backend Client
This script tests the backend response flow by sending a chat message to the backend WebSocket server.
"""

import asyncio
import json
import logging
import websockets
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# WebSocket URL for the backend server
BACKEND_URL = "ws://localhost:8767"

# Test message to send
TEST_MESSAGE = {
    "type": "chat_request",
    "mode": "General",  # Try Agent, Ask, Suggest, or General
    "message": "What's the current time?",
    "session_id": f"test_session_{int(time.time())}",
    "client_id": f"test_client_{int(time.time())}"
}

async def test_backend_response():
    """Test function that connects to the backend and sends a test message"""
    try:
        logger.info(f"Connecting to {BACKEND_URL}...")
        async with websockets.connect(BACKEND_URL) as websocket:
            # Wait for connection response
            response = await websocket.recv()
            logger.info(f"Connection response: {response[:100]}...")
            
            # Send test message
            logger.info(f"Sending test message: {TEST_MESSAGE}")
            await websocket.send(json.dumps(TEST_MESSAGE))
            
            # Wait for response with a timeout
            try:
                logger.info("Waiting for response...")
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                response_data = json.loads(response)
                
                logger.info(f"Response type: {response_data.get('type')}")
                if 'response' in response_data:
                    logger.info(f"Response content: {response_data['response'][:200]}...")
                else:
                    logger.info(f"Response data: {json.dumps(response_data, indent=2)}")
                
                # Try to receive any additional messages
                try:
                    while True:
                        more_response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        more_data = json.loads(more_response)
                        logger.info(f"Additional response type: {more_data.get('type')}")
                        if 'response' in more_data:
                            logger.info(f"Additional response content: {more_data['response'][:100]}...")
                except asyncio.TimeoutError:
                    logger.info("No more messages received")
                
                return True
            except asyncio.TimeoutError:
                logger.error("Timeout waiting for response")
                return False
    except Exception as e:
        logger.error(f"Error in test: {e}")
        return False

def run_mode_test(mode):
    """Run a test with a specific chat mode"""
    TEST_MESSAGE["mode"] = mode
    TEST_MESSAGE["message"] = f"Test message in {mode} mode. Please respond."
    
    logger.info(f"\n===== TESTING {mode.upper()} MODE =====")
    asyncio.run(test_backend_response())

async def test_all_modes():
    """Test all chat modes sequentially"""
    modes = ["General", "Ask", "Suggest", "Agent"]
    for mode in modes:
        TEST_MESSAGE["mode"] = mode
        TEST_MESSAGE["message"] = f"Test message in {mode} mode. Please respond."
        
        logger.info(f"\n===== TESTING {mode.upper()} MODE =====")
        await test_backend_response()
        # Small delay between tests
        await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        logger.info("=== BACKEND RESPONSE TEST ===")
        logger.info("This test checks if the backend server properly responds to chat messages.")
        
        # Choose which test to run
        test_type = input("Run test for: (1) All modes, (2) General, (3) Ask, (4) Suggest, (5) Agent: ")
        
        if test_type == "1":
            asyncio.run(test_all_modes())
        elif test_type == "2":
            run_mode_test("General")
        elif test_type == "3":
            run_mode_test("Ask")
        elif test_type == "4":
            run_mode_test("Suggest")
        elif test_type == "5":
            run_mode_test("Agent")
        else:
            logger.info("Invalid option, running General mode test")
            run_mode_test("General")
            
        logger.info("\n=== TEST COMPLETED ===")
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}")