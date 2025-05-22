#!/usr/bin/env python3
"""
Test script to send suggestion messages to WebSocket server
"""
import asyncio
import json
import websockets
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

async def send_test_suggestion():
    """Connect to WebSocket server and send a test suggestion"""
    try:
        # Connect to the WebSocket server
        uri = "ws://localhost:8768"  # Use the proper port
        async with websockets.connect(uri) as websocket:
            logger.info(f"Connected to {uri}")
            
            # First register as a client
            await websocket.send(json.dumps({
                "type": "connection_established",
                "payload": {
                    "client_type": "test_client",
                    "client_id": "test_suggestion_sender",
                    "timestamp": "2023-01-01T00:00:00Z"
                }
            }))
            
            # Wait for connection acknowledgment
            response = await websocket.recv()
            logger.info(f"Received: {response}")
            
            # Send a test suggestion message
            suggestion = {
                "type": "suggestion",  # this is critical for proper handling
                "content": "I noticed you're working on the WebSocket handling code. Would you like me to help optimize the suggestion rendering?",
                "isSuggestion": True,  # explicit flag
                "buttons": [
                    {"id": "do", "label": "Yes, please", "primary": True},
                    {"id": "adjust", "label": "Adjust", "primary": False},
                    {"id": "dismiss", "label": "No, thanks", "primary": False}
                ]
            }
            
            logger.info(f"Sending suggestion: {suggestion}")
            await websocket.send(json.dumps(suggestion))
            
            # Wait for confirmation
            response = await websocket.recv()
            logger.info(f"Received: {response}")
            
            logger.info("Test suggestion sent successfully")
            
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(send_test_suggestion())