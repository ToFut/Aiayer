#!/usr/bin/env python3
"""
Simple Ask Mode Test Script

This script tests only the "ask" mode of the Aiayer system, which should respond 
faster than agent mode. It sends two simple questions and prints the responses.
"""

import asyncio
import json
import logging
import time
import websockets
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
BACKEND_URL = "ws://localhost:8767"
TIMEOUT = 60  # seconds

async def test_ask_mode():
    """Test the ask mode with two simple questions"""
    try:
        # Connect to the backend
        logger.info(f"Connecting to backend at {BACKEND_URL}")
        websocket = await websockets.connect(BACKEND_URL)
        
        # Wait for the connection established message
        connection_message = await websocket.recv()
        data = json.loads(connection_message)
        if data.get("type") == "connection_established":
            client_id = data.get("client_id", "unknown")
            logger.info(f"Successfully connected with client ID: {client_id}")
        else:
            logger.warning(f"Unexpected connection message: {data}")
            return
            
        # Create a unique session ID
        session_id = f"test_ask_{int(time.time())}_{random.randint(1000, 9999)}"
        
        # Test questions to send in ask mode
        questions = [
            "what applications are currently running on my system?",
            "what's currently visible on my screen?"
        ]
        
        # Run tests
        for i, question in enumerate(questions, 1):
            logger.info(f"Test {i}: Sending ask mode question: '{question}'")
            
            # Send the request
            request = {
                "type": "chat_request",
                "mode": "ask",
                "message": question,
                "session_id": session_id
            }
            await websocket.send(json.dumps(request))
            
            # Wait for response with timeout
            start_time = time.time()
            full_response = ""
            
            try:
                async with asyncio.timeout(TIMEOUT):
                    while True:
                        response = await websocket.recv()
                        data = json.loads(response)
                        
                        # Log the response type
                        logger.info(f"Received message type: {data.get('type', 'unknown')}")
                        
                        if data.get("type") == "response":
                            response_content = data.get("response", "")
                            full_response += response_content
                            
                            if not data.get("streaming", False):
                                # This is the final response
                                break
                                
                        elif data.get("type") == "stream_end":
                            # End of streaming response
                            break
                            
                        elif data.get("type") == "error":
                            logger.error(f"Error from backend: {data.get('message', 'Unknown error')}")
                            break
                
                # Calculate response time
                response_time = time.time() - start_time
                
                # Log the result
                logger.info(f"Test {i} completed in {response_time:.2f}s")
                logger.info(f"Response: {full_response[:200]}..." if len(full_response) > 200 else f"Response: {full_response}")
                
            except asyncio.TimeoutError:
                logger.error(f"Response timeout after {TIMEOUT} seconds")
            
            # Wait between tests
            if i < len(questions):
                await asyncio.sleep(2)
        
        # Close the connection
        await websocket.close()
        logger.info("Tests completed")
        
    except Exception as e:
        logger.error(f"Error during test: {e}")

async def main():
    """Main function"""
    await test_ask_mode()

if __name__ == "__main__":
    asyncio.run(main())