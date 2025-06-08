#!/usr/bin/env python3
"""
Final Suggestion Test - Focus on the working suggestion format
"""
import asyncio
import websockets
import json
import logging
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# WebSocket endpoint
PROXY_ENDPOINT = "ws://localhost:8766"  # Proxy bridge

async def send_suggestion(title, message):
    """Send a suggestion notification using the working format"""
    try:
        logger.info(f"Connecting to proxy bridge at {PROXY_ENDPOINT}")
        
        async with websockets.connect(PROXY_ENDPOINT) as ws:
            # Wait for welcome
            welcome = await ws.recv()
            logger.info(f"Proxy welcome: {welcome[:100]}...")
            
            # Create a suggestion message (confirmed working format)
            plan_id = f"suggestion_{uuid.uuid4()}"
            suggestion = {
                "type": "suggestion",
                "response": f"💡 {title}\n\n{message}",
                "buttons": [
                    {
                        "text": "I can see this!",
                        "value": "seen",
                        "style": "success"
                    },
                    {
                        "text": "Still not visible",
                        "value": "not_seen",
                        "style": "danger"
                    }
                ],
                "importance": "high",
                "play_sound": True,
                "plan_id": plan_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # Send suggestion
            logger.info(f"Sending suggestion: {title}")
            await ws.send(json.dumps(suggestion))
            
            # Wait for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                logger.info(f"Response: {response[:100]}...")
                return True
            except asyncio.TimeoutError:
                logger.warning("No response received within timeout")
                return False
            
    except Exception as e:
        logger.error(f"Error sending suggestion: {e}")
        return False

async def main():
    """Run the final suggestion test"""
    logger.info("=== FINAL SUGGESTION TEST ===")
    logger.info("Sending suggestion using the confirmed working format")
    
    # Send a suggestion
    title = "FINAL NOTIFICATION TEST"
    message = "This is the final test of the suggestion notification system.\n\nIf you can see this message with buttons below, the fix was successful!"
    
    result = await send_suggestion(title, message)
    
    if result:
        logger.info("\n✅ Suggestion sent successfully!")
        logger.info("Check the overlay to see if the notification appears.")
        logger.info("If you can see the notification with buttons, the fix is working correctly.")
    else:
        logger.info("\n❌ Failed to send suggestion")
        logger.info("Try restarting the overlay and/or the bridge server.")
    
    logger.info("\nTroubleshooting tips:")
    logger.info("1. Ensure the overlay is running: cd overlay && npm run tauri dev")
    logger.info("2. Verify bridge server is running: ps aux | grep fix_do_button_connection_bridge")
    logger.info("3. Check overlay config.js has correct WebSocket URLs")
    logger.info("4. Inspect browser console for any errors in the overlay app")
    logger.info("5. Try clicking on the overlay to ensure it has focus")

if __name__ == "__main__":
    asyncio.run(main())