#!/usr/bin/env python3
"""
Direct WebSocket Client for Overlay Chat Testing
This script directly connects to the WebSocket server and sends a message
to test the chat functionality.
"""
import asyncio
import websockets
import json
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

async def test_chat(uri="ws://localhost:8765", query="Show me some examples of what you can do"):
    """Send a test chat message through WebSocket."""
    try:
        logger.info(f"Connecting to {uri}...")
        async with websockets.connect(uri, ping_interval=None, close_timeout=5) as websocket:
            logger.info(f"Connected to {uri}")
            
            # Wait for initial connection message
            init_message = await websocket.recv()
            logger.info(f"Initial connection message: {init_message}")
            
            # Step 1: Register as overlay_chat client
            register_message = {
                "type": "register",
                "payload": {
                    "client_type": "overlay_chat",
                    "client_id": f"test_client_{int(datetime.now().timestamp())}",
                    "version": "1.0.0"
                }
            }
            
            logger.info(f"Sending registration message: {register_message}")
            await websocket.send(json.dumps(register_message))
            
            # Wait for registration confirmation
            try:
                reg_response = await asyncio.wait_for(websocket.recv(), timeout=5)
                logger.info(f"Registration response: {reg_response}")
            except asyncio.TimeoutError:
                logger.warning("No registration response received")
            
            # Step 2: Send chat message
            logger.info(f"Sending chat message: {query}")
            message = {
                "type": "llm_request",
                "payload": {
                    "query": query,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            await websocket.send(json.dumps(message))
            logger.info("Chat message sent")
            
            # Step 3: Wait for response with timeout
            start_time = datetime.now().timestamp()
            timeout = 60  # seconds
            
            while datetime.now().timestamp() - start_time < timeout:
                try:
                    remaining = timeout - (datetime.now().timestamp() - start_time)
                    logger.info(f"Waiting for response... (timeout in {remaining:.1f}s)")
                    
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    logger.info(f"Received response: {response}")
                    
                    # Parse response
                    data = json.loads(response)
                    msg_type = data.get('type')
                    
                    # Check if this is an LLM response
                    if msg_type in ['query_response', 'llm_response']:
                        payload = data.get('payload', {})
                        if 'response' in payload:
                            content = payload['response']
                            logger.info(f"LLM response content: {content}")
                            return content
                        elif 'content' in payload:
                            content = payload['content']
                            logger.info(f"LLM response content: {content}")
                            return content
                
                except asyncio.TimeoutError:
                    logger.info("No response in last 5 seconds, continuing to wait...")
                except Exception as e:
                    logger.error(f"Error receiving response: {e}")
            
            logger.error(f"Timeout after {timeout} seconds waiting for LLM response")
            return None
            
    except Exception as e:
        logger.error(f"Connection error: {e}")
        return None

if __name__ == "__main__":
    # Get query from command line args if provided
    query = "Show me some examples of what you can do" 
    if len(sys.argv) > 1:
        query = sys.argv[1]
    
    # Try both WebSocket server ports
    response = asyncio.run(test_chat("ws://localhost:8765", query))
    
    if not response:
        logger.warning("Failed to get response from port 8765, trying port 8767...")
        response = asyncio.run(test_chat("ws://localhost:8767", query))
    
    if response:
        logger.info("Test completed successfully with valid response")
    else:
        logger.error("Failed to get response from both WebSocket servers")