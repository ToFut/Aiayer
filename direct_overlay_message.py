#!/usr/bin/env python3
"""
Direct Overlay Message - Sends messages directly to the overlay
"""
import asyncio
import websockets
import json
import logging
import time
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# WebSocket endpoints - try both main ports
PORTS = [8765, 8766, 8767]

async def send_to_all_ports():
    """Send test messages to all ports"""
    for port in PORTS:
        await send_to_port(port)
        # Add a small delay between attempts
        await asyncio.sleep(1)

async def send_to_port(port):
    """Send a test message to the specified port"""
    ws_url = f"ws://localhost:{port}"
    if port == 8767:
        ws_url += "/ws"  # Backend requires /ws path
        
    try:
        logger.info(f"Connecting to {ws_url}...")
        
        async with websockets.connect(ws_url) as ws:
            # Wait for welcome message
            welcome = await ws.recv()
            logger.info(f"Port {port} welcome: {welcome[:100]}...")
            
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
            
            # Create multiple message formats to try
            message_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            
            # Format 1: Direct chat message
            msg1 = {
                "type": "chat_message", 
                "mode": "SUGGEST",
                "content": f"⚠️ PORT {port} TEST MESSAGE (chat_message format)",
                "id": message_id,
                "timestamp": timestamp,
                "buttons": [
                    {"text": "I see this!", "value": "seen", "style": "success"},
                    {"text": "Not visible", "value": "not_seen", "style": "danger"}
                ]
            }
            
            # Format 2: Suggestion format
            msg2 = {
                "type": "suggestion",
                "response": f"🔔 PORT {port} TEST MESSAGE (suggestion format)",
                "buttons": [
                    {"text": "I see this!", "value": "seen", "style": "success"},
                    {"text": "Not visible", "value": "not_seen", "style": "danger"}
                ],
                "importance": "high",
                "play_sound": True,
                "plan_id": message_id,
                "timestamp": timestamp
            }
            
            # Format 3: Backend message
            msg3 = {
                "type": "message",
                "message": f"📢 PORT {port} TEST MESSAGE (message format)",
                "mode": "SUGGEST", 
                "buttons": [
                    {"text": "I see this!", "value": "seen", "style": "success"},
                    {"text": "Not visible", "value": "not_seen", "style": "danger"}
                ],
                "timestamp": timestamp
            }
            
            # Format 4: Minimal format
            msg4 = {
                "mode": "SUGGEST",
                "notification": True,
                "message": f"🛑 PORT {port} TEST MESSAGE (minimal format)",
            }
            
            # Send all formats with small delays between them
            formats = [
                ("chat_message", msg1),
                ("suggestion", msg2),
                ("message", msg3),
                ("minimal", msg4)
            ]
            
            for format_name, msg in formats:
                try:
                    logger.info(f"Sending {format_name} format to port {port}...")
                    await ws.send(json.dumps(msg))
                    
                    # Wait for response
                    try:
                        response = await asyncio.wait_for(ws.recv(), timeout=1.0)
                        logger.info(f"Response to {format_name} format: {response[:100]}...")
                    except asyncio.TimeoutError:
                        logger.warning(f"No response to {format_name} format within timeout")
                    
                    # Small delay between messages
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error sending {format_name} format: {e}")
            
            logger.info(f"All message formats sent to port {port}")
            
    except Exception as e:
        logger.error(f"Error connecting to port {port}: {e}")

async def main():
    """Main function"""
    logger.info("=== DIRECT OVERLAY MESSAGE TEST ===")
    logger.info("Sending messages directly to all WebSocket endpoints")
    
    await send_to_all_ports()
    
    logger.info("Test complete.")
    logger.info("If notifications still don't appear, try the emergency fix:")
    logger.info("1. Add the notification.js script to dist/index.html")
    logger.info("2. Restart the overlay: cd overlay && npm run tauri dev")

if __name__ == "__main__":
    asyncio.run(main())