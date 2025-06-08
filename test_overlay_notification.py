#!/usr/bin/env python3
"""
Test Overlay Notification - Sends a test notification to the overlay
"""
import asyncio
import websockets
import json
import logging
import uuid
from datetime import datetime
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def send_notification(port=8766, message="Test notification", importance="high", play_sound=True):
    """Send a notification to the specified port"""
    ws_url = f"ws://localhost:{port}"
    if port == 8767:
        ws_url += "/ws"  # Backend requires /ws path
        
    try:
        logger.info(f"Connecting to {ws_url}...")
        
        async with websockets.connect(ws_url) as ws:
            # Wait for welcome message
            welcome = await ws.recv()
            logger.info(f"Welcome message received: {welcome[:100]}...")
            
            # For port 8767 (backend), we need to register first
            if port == 8767:
                register = {
                    "type": "register",
                    "client_type": "notification_test",
                    "client_id": f"direct_test_{uuid.uuid4()}"
                }
                
                await ws.send(json.dumps(register))
                register_response = await ws.recv()
                logger.info(f"Register response: {register_response[:100]}...")
            
            # Create a notification message based on the port
            message_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            
            # Different formats for different ports
            if port == 8766:
                # Format for port 8766
                notification = {
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
            elif port == 8767:
                # Format for port 8767
                notification = {
                    "type": "message",
                    "message": message,
                    "mode": "SUGGEST", 
                    "buttons": [
                        {"text": "I see this!", "value": "seen", "style": "success"},
                        {"text": "Not visible", "value": "not_seen", "style": "danger"}
                    ],
                    "timestamp": timestamp
                }
            else:
                # Default format
                notification = {
                    "type": "chat_message", 
                    "mode": "SUGGEST",
                    "content": message,
                    "id": message_id,
                    "timestamp": timestamp,
                    "buttons": [
                        {"text": "I see this!", "value": "seen", "style": "success"},
                        {"text": "Not visible", "value": "not_seen", "style": "danger"}
                    ]
                }
            
            # Send the notification
            logger.info(f"Sending notification to port {port}: {message}")
            await ws.send(json.dumps(notification))
            
            # Wait for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                logger.info(f"Response received: {response[:100]}...")
                return True
            except asyncio.TimeoutError:
                logger.warning("No response within timeout")
                return False
                
    except Exception as e:
        logger.error(f"Error connecting to {ws_url}: {e}")
        return False

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Send a test notification to the overlay')
    parser.add_argument('--port', type=int, default=8766, help='WebSocket port (default: 8766)')
    parser.add_argument('--message', type=str, default="🔔 TEST NOTIFICATION - Is this visible?", help='Notification message')
    parser.add_argument('--importance', type=str, default="high", choices=["high", "medium", "low"], help='Notification importance')
    parser.add_argument('--no-sound', action='store_true', help='Disable notification sound')
    
    args = parser.parse_args()
    
    logger.info(f"=== SENDING NOTIFICATION TO PORT {args.port} ===")
    
    success = await send_notification(
        port=args.port,
        message=args.message,
        importance=args.importance,
        play_sound=not args.no_sound
    )
    
    if success:
        logger.info("✅ Notification sent successfully!")
    else:
        logger.warning("❌ Failed to send notification or receive confirmation")
    
    logger.info("Test complete.")

if __name__ == "__main__":
    asyncio.run(main())