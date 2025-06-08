#!/usr/bin/env python3
"""
Test script to verify that agent mode automation is working correctly
with the fixed universal automation handler.
"""

import asyncio
import json
import websockets
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_agent_mode():
    """Test agent mode with a search query to verify fixed automation handler"""
    
    uri = "ws://localhost:8767"  # Backend WebSocket server
    
    try:
        logger.info(f"Connecting to backend at {uri}...")
        async with websockets.connect(uri) as websocket:
            # Wait for welcome message
            welcome = await websocket.recv()
            logger.info(f"Received welcome: {welcome}")
            
            # Register client
            await websocket.send(json.dumps({
                "type": "register",
                "client_type": "test_client"
            }))
            reg_response = await websocket.recv()
            logger.info(f"Registration response: {reg_response}")
            
            # Test agent mode with a search query
            test_query = "search for flight tickets to london on google"
            logger.info(f"Testing agent mode with query: {test_query}")
            
            request = {
                "type": "request",
                "mode": "Agent",  # Agent mode to test automation
                "query": test_query,
                "session_id": f"test_session_{int(time.time())}",
                "context": {
                    "test_context": True,
                    "debug_mode": True
                }
            }
            
            # Send request
            await websocket.send(json.dumps(request))
            logger.info("Request sent, waiting for response...")
            
            # Wait for response (with timeout)
            response = await asyncio.wait_for(websocket.recv(), timeout=30)
            response_data = json.loads(response)
            
            # Log and analyze response
            logger.info(f"Response received in {response_data.get('processing_time', 0):.2f}s")
            logger.info(f"Success: {response_data.get('success', False)}")
            logger.info(f"Mode used: {response_data.get('mode', 'unknown')}")
            logger.info(f"Response confidence: {response_data.get('confidence', 0)}")
            
            # Check if response contains automation plan
            response_text = response_data.get('response', '')
            has_plan = "AUTOMATION EXECUTION PLAN" in response_text or "STEP" in response_text
            has_search = "search" in response_text.lower() and "google" in response_text.lower()
            
            logger.info(f"Response contains automation plan: {has_plan}")
            logger.info(f"Response mentions search and Google: {has_search}")
            
            # Print summary
            print("\n" + "="*50)
            print("AGENT MODE TEST SUMMARY")
            print("="*50)
            print(f"Query: {test_query}")
            print(f"Success: {'✅' if response_data.get('success', False) else '❌'}")
            print(f"Contains plan: {'✅' if has_plan else '❌'}")
            print(f"Mentions search and Google: {'✅' if has_search else '❌'}")
            print(f"Processing time: {response_data.get('processing_time', 0):.2f}s")
            print(f"Confidence: {response_data.get('confidence', 0)}")
            
            print("\nResponse preview (first 300 chars):")
            print("-"*50)
            print(response_text[:300] + "..." if len(response_text) > 300 else response_text)
            print("-"*50)
            
            overall_success = response_data.get('success', False) and has_plan and has_search
            print(f"\nOverall test result: {'✅ PASSED' if overall_success else '❌ FAILED'}")
            print("="*50)
            
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        print(f"\n❌ TEST FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_agent_mode())