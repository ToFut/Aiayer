#!/usr/bin/env python3
"""
Send Overlay Notification - Simplified script to send notifications to the overlay

Usage examples:
  python3 send_overlay_notification.py --message "Important alert! System requires attention."
  python3 send_overlay_notification.py --port 8767 --message "Backend notification test"
  python3 send_overlay_notification.py --importance medium --no-sound
"""
import asyncio
import websockets
import json
import logging
import uuid
from datetime import datetime
import argparse
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def send_notification(port=8766, message="Test notification", importance="high", play_sound=True, buttons=None):
    """Send a notification to the specified port"""
    ws_url = f"ws://localhost:{port}"
    if port == 8767:
        ws_url += "/ws"  # Backend requires /ws path
    
    if buttons is None:
        buttons = [
            {"text": "I see this!", "value": "seen", "style": "success"},
            {"text": "Not visible", "value": "not_seen", "style": "danger"}
        ]
        
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
                # Format for port 8766 - CONFIRMED WORKING
                notification = {
                    "type": "suggestion",
                    "response": message,
                    "buttons": buttons,
                    "importance": importance,
                    "play_sound": play_sound,
                    "plan_id": message_id,
                    "timestamp": timestamp
                }
            elif port == 8767:
                # Format for port 8767 - UNTESTED
                notification = {
                    "type": "message",
                    "message": message,
                    "mode": "SUGGEST", 
                    "buttons": buttons,
                    "timestamp": timestamp
                }
            else:
                # Default format - UNTESTED
                notification = {
                    "type": "chat_message", 
                    "mode": "SUGGEST",
                    "content": message,
                    "id": message_id,
                    "timestamp": timestamp,
                    "buttons": buttons
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

async def try_all_ports(message, importance, play_sound, buttons):
    """Try sending to all ports and report which ones work"""
    results = {}
    
    for port in [8765, 8766, 8767]:
        logger.info(f"Attempting notification on port {port}...")
        success = await send_notification(
            port=port,
            message=f"[PORT {port}] {message}",
            importance=importance,
            play_sound=play_sound,
            buttons=buttons
        )
        results[port] = success
        # Add a small delay between attempts
        await asyncio.sleep(1)
    
    # Return a summary
    working_ports = [port for port, success in results.items() if success]
    return working_ports

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Send a notification to the overlay')
    parser.add_argument('--port', type=int, default=8766, help='WebSocket port (default: 8766, use 0 to try all ports)')
    parser.add_argument('--message', type=str, default="🔔 NOTIFICATION - Is this visible?", help='Notification message')
    parser.add_argument('--importance', type=str, default="high", choices=["high", "medium", "low"], help='Notification importance')
    parser.add_argument('--no-sound', action='store_true', help='Disable notification sound')
    parser.add_argument('--custom-buttons', action='store_true', help='Use custom buttons')
    
    args = parser.parse_args()
    
    # Configure custom buttons if requested
    buttons = None
    if args.custom_buttons:
        buttons = [
            {"text": "👍 Works Great!", "value": "works", "style": "success"},
            {"text": "⚠️ Partially Works", "value": "partial", "style": "warning"},
            {"text": "❌ Not Working", "value": "not_working", "style": "danger"}
        ]
    
    # Try all ports or just the specified one
    if args.port == 0:
        logger.info("=== TRYING ALL AVAILABLE PORTS ===")
        working_ports = await try_all_ports(
            message=args.message,
            importance=args.importance,
            play_sound=not args.no_sound,
            buttons=buttons
        )
        
        if working_ports:
            logger.info(f"✅ Notification sent successfully to ports: {working_ports}")
            logger.info(f"For future use, recommend using port {working_ports[0]}")
        else:
            logger.error("❌ Failed to send notification to any port")
    else:
        logger.info(f"=== SENDING NOTIFICATION TO PORT {args.port} ===")
        
        success = await send_notification(
            port=args.port,
            message=args.message,
            importance=args.importance,
            play_sound=not args.no_sound,
            buttons=buttons
        )
        
        if success:
            logger.info("✅ Notification sent successfully!")
        else:
            logger.warning("❌ Failed to send notification or receive confirmation")
    
    logger.info("Test complete.")

if __name__ == "__main__":
    asyncio.run(main())