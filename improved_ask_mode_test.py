#!/usr/bin/env python3
"""
Improved Ask Mode Test Script

This script tests the "ask" mode of the Aiayer system, properly handling
all response types including 'final_response'.
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
TIMEOUT = 120  # seconds

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
            "what's currently visible on my screen?",
            "how is my memory system organized?",
            "what have I been working on today?"
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
            received_final = False
            
            try:
                async with asyncio.timeout(TIMEOUT):
                    while True:
                        response = await websocket.recv()
                        try:
                            data = json.loads(response)
                        except json.JSONDecodeError:
                            logger.error(f"Received invalid JSON: {response[:100]}...")
                            continue
                        
                        # Log the response type
                        msg_type = data.get("type", "unknown")
                        logger.info(f"Received message type: {msg_type}")
                        
                        # Handle different response types
                        if msg_type == "response":
                            response_content = data.get("response", "")
                            full_response += response_content
                            
                            if not data.get("streaming", False):
                                logger.info("Received complete response")
                                break
                                
                        elif msg_type == "stream_end":
                            logger.info("Received stream end")
                            break
                            
                        elif msg_type == "final_response":
                            # Special case for this system
                            received_final = True
                            response_content = data.get("response", "")
                            full_response += response_content
                            logger.info("Received final response")
                            break
                            
                        elif msg_type == "error":
                            logger.error(f"Error from backend: {data.get('message', 'Unknown error')}")
                            break
                            
                        elif msg_type == "progress_update":
                            progress = data.get("progress", 0)
                            stage = data.get("stage", "unknown")
                            logger.info(f"Progress update: {progress}% - {stage}")
                            continue
                
                # Calculate response time
                response_time = time.time() - start_time
                
                # Log the result
                logger.info(f"Test {i} completed in {response_time:.2f}s")
                logger.info(f"Response: {full_response[:200]}..." if len(full_response) > 200 else f"Response: {full_response}")
                
                # Write response to file for analysis
                with open(f"test_response_{i}.json", "w") as f:
                    json.dump({
                        "question": question,
                        "response": full_response,
                        "response_time": response_time,
                        "received_final": received_final
                    }, f, indent=2)
                
            except asyncio.TimeoutError:
                logger.error(f"Response timeout after {TIMEOUT} seconds")
            
            # Wait between tests
            if i < len(questions):
                await asyncio.sleep(3)
        
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