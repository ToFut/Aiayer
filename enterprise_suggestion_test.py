#!/usr/bin/env python3
"""
Enterprise Suggestion Test Script

This script sends a properly formatted suggestion message directly to the overlay
using the EnterpriseChatWidget format.
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
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("enterprise_suggestion_test")

# WebSocket connection info
WS_URI = "ws://localhost:8765"

async def send_enterprise_suggestion(title="Suggestion", message="Would you like help with this?"):
    """Send a properly formatted suggestion to the overlay using the EnterpriseChatWidget format"""
    try:
        logger.info(f"Connecting to WebSocket server at {WS_URI}")
        
        async with websockets.connect(WS_URI, ping_interval=5, ping_timeout=20) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            logger.info(f"Received welcome: {welcome[:100]}...")
            
            # Create suggestion in EnterpriseChatWidget format
            suggestion = {
                "success": True,
                "response": f"💡 {title}: {message}",
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
            
            # Send the suggestion directly
            await websocket.send(json.dumps(suggestion))
            logger.info(f"✅ Sent enterprise suggestion to overlay")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                logger.info(f"Received response: {response[:100]}...")
                return True
            except asyncio.TimeoutError:
                logger.warning("No response received within timeout")
                return True
                
    except Exception as e:
        logger.error(f"Error sending suggestion: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def send_typed_suggestion(title="Suggestion", message="Would you like help with this?"):
    """Send a suggestion using the type format"""
    try:
        logger.info(f"Connecting to WebSocket server at {WS_URI}")
        
        async with websockets.connect(WS_URI, ping_interval=5, ping_timeout=20) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            logger.info(f"Received welcome: {welcome[:100]}...")
            
            # Create suggestion in typed format
            suggestion = {
                "type": "suggestion",
                "title": title,
                "message": message,
                "session_id": f"suggestion_{int(datetime.now().timestamp())}"
            }
            
            # Send the suggestion
            await websocket.send(json.dumps(suggestion))
            logger.info(f"✅ Sent typed suggestion to overlay")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                logger.info(f"Received response: {response[:100]}...")
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
    """Main function - try both suggestion formats"""
    logger.info("🚀 Testing Enterprise Suggestion System")
    
    # Get message from command line arguments if provided
    title = "Enterprise Suggestion Test"
    message = "This is a test suggestion for the EnterpriseChatWidget"
    
    if len(sys.argv) > 1:
        title = sys.argv[1]
    if len(sys.argv) > 2:
        message = sys.argv[2]
    
    # Try first format
    logger.info("Testing direct format suggestion...")
    success1 = await send_enterprise_suggestion(title, message)
    
    # Try second format
    logger.info("Testing typed suggestion...")
    success2 = await send_typed_suggestion(title, message)
    
    if success1 or success2:
        logger.info("✅ At least one suggestion format worked")
        logger.info("Check the overlay to see if the suggestion appears")
        return True
    else:
        logger.error("❌ Both suggestion formats failed")
        return False

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