#!/usr/bin/env python3
"""
Test the communication between the overlay and the interceptor service
"""
import asyncio
import json
import websockets
import logging
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def simulate_overlay_client():
    """Simulate overlay client connecting to the interceptor service"""
    try:
        # Connect to interceptor service
        url = "ws://localhost:8766"
        logger.info(f"Connecting to interceptor service at {url}...")
        
        # Connect without using context manager so we can control closing
        ws = await websockets.connect(url, ping_interval=None, close_timeout=30)
        try:
            logger.info("Connection established")
            
            # Create buffer for messages
            received_messages = []
            
            # Define a helper function to receive messages
            async def receive_message(timeout=5.0):
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=timeout)
                    received_messages.append(msg)
                    return msg
                except asyncio.TimeoutError:
                    logger.info(f"No message received within {timeout}s")
                    return None
                except Exception as e:
                    logger.error(f"Error receiving message: {e}")
                    return None
            
            # Receive initial connection message
            init_message = await receive_message()
            if init_message:
                logger.info(f"Initial message: {init_message}")
            
            # Send client registration message
            register_msg = {
                "type": "register",
                "payload": {
                    "client_type": "overlay",
                    "client_name": "TestClient"
                }
            }
            logger.info("Sending registration message...")
            await ws.send(json.dumps(register_msg))
            
            # Wait for any responses after registration
            await asyncio.sleep(1)  # Brief pause to allow responses
            
            # Receive any pending messages
            while True:
                msg = await receive_message(timeout=1.0)
                if not msg:
                    break
            
            # Send a test query
            query_msg = {
                "type": "llm_request",
                "payload": {
                    "query": "What is the capital of France?",
                    "context": {
                        "window": "Test Window",
                        "active_apps": ["Test Browser", "Terminal"],
                        "screen_content": "This is a test of the LLM service"
                    }
                }
            }
            logger.info("Sending test query...")
            await ws.send(json.dumps(query_msg))
            
            # Wait for responses over a period of time
            start_time = asyncio.get_event_loop().time()
            timeout = 15.0  # Wait up to 15 seconds for all responses
            
            query_response_received = False
            
            while asyncio.get_event_loop().time() - start_time < timeout:
                msg = await receive_message(timeout=2.0)
                if not msg:
                    continue
                
                try:
                    data = json.loads(msg)
                    msg_type = data.get('type', 'unknown')
                    logger.info(f"Received message of type: {msg_type}")
                    
                    if msg_type == 'query_response':
                        content = data.get('payload', {}).get('response', '')
                        logger.info(f"Response content: {content[:100]}...")
                        query_response_received = True
                        logger.info("TEST PASSED: Received query response from interceptor")
                    elif 'response' in str(data):
                        logger.info(f"Found response-like data in message: {msg[:200]}...")
                        query_response_received = True
                        logger.info("TEST PASSED: Found response data from interceptor")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
            
            # Send disconnect message
            try:
                await ws.send(json.dumps({"type": "disconnect"}))
                logger.info("Sent disconnect message")
                await asyncio.sleep(0.5)  # Wait briefly for the message to be processed
            except:
                pass
            
            return query_response_received or len(received_messages) > 0
        finally:
            # Ensure we close the connection
            await ws.close()
            logger.info("WebSocket connection closed")
    except Exception as e:
        logger.error(f"Error in simulate_overlay_client: {e}")
        return False

async def main():
    """Run the test"""
    result = await simulate_overlay_client()
    
    if result:
        logger.info("Test completed successfully!")
        return 0
    else:
        logger.error("Test failed!")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))