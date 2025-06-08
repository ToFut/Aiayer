#!/usr/bin/env python3
"""
Send Suggestion to Port 8766 - Simplified script to send suggestions to the overlay
"""
import asyncio
import websockets
import json
import logging
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# WebSocket endpoint
WS_URL = "ws://localhost:8766"

async def send_suggestion(message="Test suggestion", importance="high", play_sound=True):
    """Send a suggestion message to port 8766"""
    try:
        logger.info(f"Connecting to {WS_URL}...")
        
        async with websockets.connect(WS_URL) as ws:
            # Wait for welcome message
            welcome = await ws.recv()
            logger.info(f"Welcome message: {welcome[:100]}...")
            
            # Create suggestion message
            message_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            
            suggestion = {
                "type": "suggestion",
                "response": message,
                "buttons": [
                    {"text": "I see this!", "value": "seen", "style": "success"},
                    {"text": "Not visible", "value": "not_seen", "style": "danger"}
                ],
                "importance": importance,
                "play_sound": play_sound,
                "plan_id": message_id,
                "timestamp": timestamp
            }
            
            # Send the suggestion
            logger.info(f"Sending suggestion: {message}")
            await ws.send(json.dumps(suggestion))
            
            # Wait for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                logger.info(f"Response received: {response[:100]}...")
                return True
            except asyncio.TimeoutError:
                logger.warning("No response within timeout")
                return False
                
    except Exception as e:
        logger.error(f"Error connecting to {WS_URL}: {e}")
        return False

async def main():
    """Main function"""
    logger.info("=== SENDING SUGGESTION TO PORT 8766 ===")
    
    # Test message
    test_message = "🔔 IMPORTANT NOTIFICATION - This is a test of the suggestion system"
    
    success = await send_suggestion(test_message)
    
    if success:
        logger.info("Suggestion sent successfully!")
    else:
        logger.warning("Failed to send suggestion or receive confirmation")
    
    logger.info("Test complete.")

if __name__ == "__main__":
    asyncio.run(main())