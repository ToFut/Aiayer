#!/usr/bin/env python3
"""
Direct Notification Test - Sends action suggestions directly to the overlay chat
Bypasses the LLM and plan persistence system to test notification functionality
"""

import asyncio
import json
import uuid
import logging
import websockets
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/direct_notification_test.log')
    ]
)

logger = logging.getLogger(__name__)

# WebSocket ports
UI_PORT = 8766  # Overlay UI port
BACKEND_PORT = 8767  # Backend server port

async def send_direct_notification(message, port=8766, buttons=None, importance="high", play_sound=True):
    """Send a direct notification to the specified WebSocket port"""
    ws_url = f"ws://localhost:{port}"
    if port == 8767:
        ws_url += "/ws"  # Backend requires /ws path
    
    notification_id = f"notification_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}"
    
    if buttons is None:
        buttons = [
            {"text": "✅ Got it", "value": "understood", "style": "success"},
            {"text": "❌ Dismiss", "value": "dismiss", "style": "danger"}
        ]
    
    try:
        logger.info(f"Connecting to {ws_url}...")
        async with websockets.connect(ws_url) as ws:
            # Wait for welcome message
            welcome = await ws.recv()
            logger.info(f"Connected! Welcome message: {welcome[:100]}...")
            
            # Register with backend if needed
            if port == 8767:
                register_msg = {
                    "type": "register",
                    "client_type": "notification_test",
                    "client_id": f"direct_test_{uuid.uuid4()}"
                }
                await ws.send(json.dumps(register_msg))
                response = await ws.recv()
                logger.info(f"Registration response: {response[:100]}...")
            
            # Create notification based on port type
            if port == 8766:  # UI Overlay port
                notification = {
                    "type": "suggestion",
                    "response": message,
                    "buttons": buttons,
                    "importance": importance,
                    "play_sound": play_sound,
                    "notification": True,
                    "plan_id": notification_id,
                    "timestamp": datetime.now().isoformat()
                }
            else:  # Backend port
                notification = {
                    "type": "message",
                    "message": message,
                    "mode": "SUGGEST",
                    "buttons": buttons,
                    "importance": importance,
                    "play_sound": play_sound, 
                    "notification": True,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Send notification
            logger.info(f"Sending notification to port {port}: {json.dumps(notification, indent=2)}")
            await ws.send(json.dumps(notification))
            
            # Wait for response with timeout
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                logger.info(f"Response received: {response[:100]}...")
                return True
            except asyncio.TimeoutError:
                logger.warning("No response received within timeout")
                return False
    
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        return False

async def send_legacy_format(message, port=8766, buttons=None, importance="high", play_sound=True):
    """Send notification using legacy format"""
    ws_url = f"ws://localhost:{port}"
    
    if buttons is None:
        buttons = [
            {"text": "✅ Got it", "value": "understood", "style": "success"},
            {"text": "❌ Dismiss", "value": "dismiss", "style": "danger"}
        ]
    
    try:
        logger.info(f"Connecting to {ws_url} with legacy format...")
        async with websockets.connect(ws_url) as ws:
            # Wait for welcome message
            welcome = await ws.recv()
            logger.info(f"Connected! Welcome message: {welcome[:100]}...")
            
            # Legacy format
            notification = {
                "success": True,
                "response": message,
                "mode": "SUGGEST",
                "notification": True,
                "play_sound": play_sound,
                "importance": importance,
                "buttons": buttons,
                "interactive": True,
                "timestamp": datetime.now().isoformat()
            }
            
            # Send notification
            logger.info(f"Sending legacy notification to port {port}")
            await ws.send(json.dumps(notification))
            
            # Wait for response with timeout
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                logger.info(f"Legacy response received: {response[:100]}...")
                return True
            except asyncio.TimeoutError:
                logger.warning("No response for legacy format within timeout")
                return False
    
    except Exception as e:
        logger.error(f"Error sending legacy notification: {e}")
        return False

async def test_both_formats(message="🔔 ACTION SUGGESTION: This is a test notification"):
    """Test both notification formats for maximum compatibility"""
    
    # First try standard format on UI port
    result1 = await send_direct_notification(
        message=message,
        port=8766,
        importance="high",
        play_sound=True
    )
    
    # Then try legacy format on UI port
    result2 = await send_legacy_format(
        message=message,
        port=8766,
        importance="high",
        play_sound=True
    )
    
    # Try backend port if UI port fails
    if not (result1 or result2):
        logger.warning("UI port notifications failed, trying backend port...")
        result3 = await send_direct_notification(
            message=message,
            port=8767,
            importance="high", 
            play_sound=True
        )
        return result3
    
    return result1 or result2

async def main():
    """Main function"""
    print("\n=== DIRECT NOTIFICATION TEST ===\n")
    print("This script sends notification messages directly to the overlay chat")
    print("to test if notifications are properly displayed.\n")
    
    try:
        message = input("Enter notification message (or press Enter for default): ")
    except (EOFError, KeyboardInterrupt):
        # Handle non-interactive execution
        message = ""
        
    if not message:
        message = "🔔 ACTION SUGGESTION: Based on your current screen, I recommend opening the browser."
    
    print("\nSending test notification...")
    success = await test_both_formats(message)
    
    if success:
        print("\n✅ Notification test successful!")
        print("Check the overlay chat for the notification.")
    else:
        print("\n❌ Notification test failed.")
        print("Check logs for details and ensure the overlay is running.")
    
    print("\nThis indicates whether the notification system works without relying on LLM or plan persistence.")

if __name__ == "__main__":
    asyncio.run(main())