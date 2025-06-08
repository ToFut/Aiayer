#!/usr/bin/env python3
"""
Test fixed WebSocket server that properly handles chat_response message type
"""

import asyncio
import websockets
import json
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_fixed_websocket.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('test_fixed_websocket')

async def test_send_chat_response():
    """Test sending a chat_response message to the server"""
    try:
        uri = "ws://localhost:8768"  # Adjust to your server port
        logger.info(f"Connecting to WebSocket server at {uri}")
        
        async with websockets.connect(uri) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Send chat_response message
            chat_response = {
                "type": "chat_response",
                "payload": {
                    "success": True,
                    "response": "This is a test response that should be handled properly",
                    "mode": "ASK",
                    "processing_time": 0.5
                },
                "client_id": f"client_{int(time.time())}",
                "timestamp": str(int(time.time()))
            }
            
            logger.info(f"Sending chat_response message: {chat_response}")
            await websocket.send(json.dumps(chat_response))
            
            # Wait for response
            logger.info("Waiting for response...")
            response = await websocket.recv()
            response_data = json.loads(response)
            
            logger.info(f"Received response: {response_data}")
            
            if response_data.get('type') == 'error':
                logger.error(f"Server returned error: {response_data.get('error')}")
                return False
            else:
                logger.info("Test successful - server handled chat_response properly")
                return True
                
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        return False

async def test_send_chat_request():
    """Test sending a chat_request message to the server"""
    try:
        uri = "ws://localhost:8768"  # Adjust to your server port
        logger.info(f"Connecting to WebSocket server at {uri}")
        
        async with websockets.connect(uri) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Send chat_request message
            chat_request = {
                "type": "chat_request",
                "query": "Hello, this is a test query",
                "mode": "ask",
                "timestamp": str(int(time.time()))
            }
            
            logger.info(f"Sending chat_request message: {chat_request}")
            await websocket.send(json.dumps(chat_request))
            
            # Wait for response
            logger.info("Waiting for response...")
            response = await websocket.recv()
            response_data = json.loads(response)
            
            logger.info(f"Received response: {response_data}")
            
            if response_data.get('type') == 'error':
                logger.error(f"Server returned error: {response_data.get('error')}")
                return False
            elif response_data.get('type') == 'chat_response':
                logger.info("Test successful - server processed chat_request and returned chat_response")
                return True
            else:
                logger.warning(f"Unexpected response type: {response_data.get('type')}")
                return False
                
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        return False

async def main():
    """Run the tests"""
    logger.info("Testing fixed WebSocket server handling of chat_response and chat_request")
    
    # Test sending chat_response
    chat_response_result = await test_send_chat_response()
    
    # Add a small delay between tests
    await asyncio.sleep(1)
    
    # Test sending chat_request
    chat_request_result = await test_send_chat_request()
    
    # Summary
    logger.info("=" * 50)
    logger.info("TEST RESULTS")
    logger.info("=" * 50)
    logger.info(f"chat_response test: {'✅ PASSED' if chat_response_result else '❌ FAILED'}")
    logger.info(f"chat_request test: {'✅ PASSED' if chat_request_result else '❌ FAILED'}")
    
    if chat_response_result and chat_request_result:
        logger.info("🎉 All tests passed! The WebSocket server is fixed.")
    else:
        logger.info("❌ Some tests failed. Check the logs for details.")

if __name__ == "__main__":
    asyncio.run(main())