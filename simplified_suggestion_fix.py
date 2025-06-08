#!/usr/bin/env python3
"""
Simplified NextGen Overlay Suggestion Fix

This script provides a standalone solution for sending suggestions to the NextGen overlay
without requiring any modifications to the existing server.
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
logger = logging.getLogger("simplified_suggestion_fix")

# WebSocket connection info
WS_URI = "ws://localhost:8765"

async def send_suggestion_to_overlay(title="Suggestion", message="Would you like help with this?"):
    """Send a properly formatted suggestion to the NextGen overlay"""
    try:
        logger.info(f"Connecting to WebSocket server at {WS_URI}")
        
        async with websockets.connect(WS_URI, ping_interval=5, ping_timeout=20) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            logger.info(f"Received welcome: {welcome[:100]}...")
            
            # Create direct chat message in the EXACT format expected by NextGenAppleChatWidget
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
            logger.info(f"✅ Sent properly formatted suggestion to overlay")
            
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
    """Main function"""
    logger.info("🚀 Sending suggestion to NextGen overlay")
    
    # Get message from command line arguments if provided
    title = "Productivity Suggestion"
    message = "Would you like help optimizing your workflow?"
    
    if len(sys.argv) > 1:
        title = sys.argv[1]
    if len(sys.argv) > 2:
        message = sys.argv[2]
    
    # Send suggestion
    success = await send_suggestion_to_overlay(title, message)
    
    if success:
        logger.info("✅ Suggestion sent successfully")
        logger.info("Check the overlay to see if the suggestion appears")
    else:
        logger.error("❌ Failed to send suggestion")
        
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