#!/usr/bin/env python3
"""
Exact notification test - Uses the exact format from memory_aware_suggestion_monitor.py
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

class Suggestion:
    def __init__(self, title, message, confidence=0.85):
        self.id = f"suggestion_{uuid.uuid4()}"
        self.title = title
        self.message = message
        self.confidence = confidence
        self.timestamp = datetime.now().isoformat()
        
    def to_notification_payload(self):
        """Creates a properly formatted notification payload for the NextGen overlay"""
        return {
            "success": True,
            "response": f"💡 {self.title}: {self.message}",
            "mode": "SUGGEST",
            "processing_time": 0.5,
            "enterprise_validated": True,
            "notification": True,
            "play_sound": True,
            "sound_type": "notification",
            "importance": "high" if self.confidence > 0.8 else "normal",
            "buttons": [
                {
                    "id": "do_it",
                    "text": "I can see this!",
                    "action": "accept",
                    "style": "success"
                },
                {
                    "id": "dismiss",
                    "text": "Still not visible",
                    "action": "dismiss",
                    "style": "danger"
                }
            ],
            "interactive": True,
            "plan_id": self.id,
            "timestamp": time.time()
        }

async def send_notification():
    """Send a notification using the exact format from memory_aware_suggestion_monitor.py"""
    try:
        logger.info(f"Connecting to WebSocket server at {WS_URI}")
        
        async with websockets.connect(WS_URI) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            logger.info(f"Received welcome: {welcome}")
            
            # Create suggestion
            suggestion = Suggestion(
                title="CRITICAL TEST NOTIFICATION",
                message="This is a final test of the notification system using the exact format from memory_aware_suggestion_monitor.py"
            )
            
            # Create notification payload
            payload = suggestion.to_notification_payload()
            
            # Add DO button server format wrapper - try both with and without
            # First without wrapper
            logger.info("Sending notification without DO button format wrapper...")
            await websocket.send(json.dumps(payload))
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                logger.info(f"Response (unwrapped): {response}")
            except asyncio.TimeoutError:
                logger.warning("No response received within timeout for unwrapped message")
                
            # Now try with DO button format wrapper
            do_button_payload = {
                "type": "suggestion",
                "response": payload["response"],
                "buttons": payload["buttons"],
                "importance": payload["importance"],
                "play_sound": payload["play_sound"],
                "plan_id": payload["plan_id"],
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info("Sending notification with DO button format wrapper...")
            await websocket.send(json.dumps(do_button_payload))
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                logger.info(f"Response (wrapped): {response}")
            except asyncio.TimeoutError:
                logger.warning("No response received within timeout for wrapped message")
                
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
        
    return True

if __name__ == "__main__":
    logger.info("=== EXACT NOTIFICATION TEST ===")
    logger.info("Sending notification using the exact format from memory_aware_suggestion_monitor.py")
    
    asyncio.run(send_notification())
    
    logger.info("Test complete. Check if the notification appeared in the overlay.")
    logger.info("If not, try clicking on the overlay window to give it focus.")