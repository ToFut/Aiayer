#!/usr/bin/env python3
"""
Test script for agent mode via WebSocket with correct message format
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
    """Test agent mode via WebSocket with correct message format"""
    
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
            test_query = "search for cats on google"
            logger.info(f"Testing agent mode with query: {test_query}")
            
            # IMPORTANT: Use the correct message format - "chat_request" not "request"
            request = {
                "type": "chat_request",
                "mode": "Agent",  # Agent mode to test automation
                "message": test_query,  # Use "message" not "query"
                "session_id": f"test_session_{int(time.time())}",
                "client_id": "test_client"
            }
            
            # Send request
            await websocket.send(json.dumps(request))
            logger.info("Chat request sent, waiting for response...")
            
            # Wait for responses
            responses = []
            start_time = time.time()
            timeout = 30  # 30 second timeout
            
            while time.time() - start_time < timeout:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2)
                    response_data = json.loads(response)
                    logger.info(f"Received message type: {response_data.get('type')}")
                    
                    if response_data.get('type') == 'final_response':
                        response_text = response_data.get('response', '')
                        responses.append(response_text)
                        logger.info(f"Final response received")
                        break
                    elif response_data.get('type') == 'streaming_response':
                        response_text = response_data.get('content', '')
                        responses.append(response_text)
                        logger.info(f"Streaming response received: {response_text[:50]}...")
                    elif response_data.get('type') == 'chat_complete':
                        logger.info("Chat complete signal received")
                        break
                    
                except asyncio.TimeoutError:
                    logger.info("No response in 2 seconds, continuing to wait...")
                    continue
            
            # Combine all responses
            full_response = ''.join(responses)
            
            # Print summary
            print("\n" + "="*50)
            print("AGENT MODE WEBSOCKET TEST")
            print("="*50)
            print(f"Query: {test_query}")
            print(f"Response length: {len(full_response)}")
            print(f"Processing time: {time.time() - start_time:.2f}s")
            
            print("\nResponse preview (first 300 chars):")
            print("-"*50)
            print(full_response[:300] + "..." if len(full_response) > 300 else full_response)
            print("-"*50)
            
            # Check for success indicators
            has_plan = "AUTOMATION EXECUTION PLAN" in full_response or "PLAN" in full_response
            has_search = "search" in full_response.lower() and "google" in full_response.lower()
            
            print(f"Response contains plan: {'✅' if has_plan else '❌'}")
            print(f"Response mentions search and Google: {'✅' if has_search else '❌'}")
            
            print(f"\nOverall test result: {'✅ PASSED' if has_plan and has_search else '❌ FAILED'}")
            print("="*50)
            
            return has_plan and has_search
            
    except Exception as e:
        logger.error(f"Error during WebSocket test: {e}")
        print(f"\n❌ TEST FAILED: {e}")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_agent_mode())
        if result:
            print("\n✅ Agent mode is working correctly!")
        else:
            print("\n❌ Agent mode test failed!")
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")