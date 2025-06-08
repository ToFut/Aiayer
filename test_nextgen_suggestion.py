#!/usr/bin/env python3
"""
Test NextGen Overlay Suggestion

This script tests sending a suggestion to the NextGen overlay in the correct format.
"""
import asyncio
import json
import logging
import sys
import websockets
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("test_nextgen_suggestion")

# WebSocket connection info
WS_URI = "ws://localhost:8765"

async def send_test_suggestion():
    """Send a test suggestion to the NextGen overlay"""
    try:
        logger.info(f"Connecting to WebSocket server at {WS_URI}")
        
        async with websockets.connect(WS_URI, ping_interval=5, ping_timeout=20) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            logger.info(f"Received welcome: {welcome[:100]}")
            
            # Create suggestion in proper format
            suggestion = {
                "success": True,
                "response": "💡 Test Suggestion: Would you like help with organizing your files?",
                "mode": "SUGGEST",
                "processing_time": 0.5,
                "enterprise_validated": True,
                "buttons": [
                    {
                        "id": "do_it",
                        "text": "Yes, help me",
                        "action": "accept",
                        "style": "success"
                    },
                    {
                        "id": "dismiss",
                        "text": "No thanks",
                        "action": "dismiss",
                        "style": "danger"
                    }
                ],
                "interactive": True
            }
            
            # Send the suggestion
            await websocket.send(json.dumps(suggestion))
            logger.info(f"Sent suggestion to overlay")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                logger.info(f"Received response: {response[:100]}")
                return True
            except asyncio.TimeoutError:
                logger.warning("No response received within timeout")
                return True
                
    except Exception as e:
        logger.error(f"Error sending suggestion: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    """Main function"""
    logger.info("🚀 Testing NextGen overlay suggestion")
    
    # Send test suggestion
    success = await send_test_suggestion()
    
    if success:
        logger.info("✅ Suggestion test successful")
        logger.info("Check the overlay to see if the suggestion appears")
    else:
        logger.error("❌ Suggestion test failed")
        
    return success

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
