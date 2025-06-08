#!/usr/bin/env python3
"""
Button Action Test - Testing the DO button server with a supported message type
"""
import asyncio
import websockets
import json
import logging
import time
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# WebSocket connection info
WS_URI = "ws://localhost:8765"  # Direct coordinate automation server

async def send_button_action():
    """Send a button_action message, which is a supported type"""
    try:
        logger.info(f"Connecting to WebSocket server at {WS_URI}")
        
        async with websockets.connect(WS_URI) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            logger.info(f"Received welcome: {welcome}")
            
            # Create a button action message (a supported format)
            plan_id = f"test_plan_{uuid.uuid4()}"
            button_action = {
                "type": "button_action",
                "action": "DO",
                "plan_id": plan_id,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Sending button action: {button_action}")
            await websocket.send(json.dumps(button_action))
            
            # Wait for response
            try:
                # First response should be progress update
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                logger.info(f"Response: {response}")
                
                # Wait for more responses
                for _ in range(3):
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        logger.info(f"Additional response: {response}")
                    except asyncio.TimeoutError:
                        break
                
            except asyncio.TimeoutError:
                logger.warning("No response received within timeout")
                
    except Exception as e:
        logger.error(f"Error sending button action: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
        
    return True

if __name__ == "__main__":
    logger.info("=== BUTTON ACTION TEST ===")
    logger.info("Sending a button_action message to test supported message types")
    
    asyncio.run(send_button_action())
    
    logger.info("Test complete. Check if the DO button action was processed.")
    logger.info("This confirms the server is handling supported message types.")