#!/usr/bin/env python3
import asyncio
import websockets
import json
import sys
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('notification_debug')

async def try_all_formats_and_ports(message):
    """Try all possible notification formats on all ports"""
    ports = [8765, 8766, 8767, 8768]
    
    # Different notification formats to try
    formats = [
        # Format 1: Direct brain router response format (based on EnterpriseChatWidget.svelte line 233)
        {
            "success": True,
            "response": message,
            "mode": "Suggest"
        },
        
        # Format 2: With type field
        {
            "type": "chat_response",
            "success": True,
            "response": message,
            "mode": "Suggest"
        },
        
        # Format 3: Legacy notification format
        {
            "type": "notification",
            "message": message,
            "importance": "high",
            "play_sound": True
        },
        
        # Format 4: With brain router fields
        {
            "success": True,
            "response": message,
            "mode": "Suggest",
            "processing_time": 0.1,
            "enterprise_validated": True
        },
        
        # Format 5: Direct response format
        {
            "response": message,
            "mode": "Suggest"
        }
    ]
    
    # Try each format on each port
    for port in ports:
        for i, format_data in enumerate(formats):
            try:
                logger.info(f"Trying format #{i+1} on port {port}")
                await send_notification(format_data, port)
                await asyncio.sleep(1)  # Wait a bit between attempts
            except Exception as e:
                logger.error(f"Error with format #{i+1} on port {port}: {e}")

async def send_notification(data, port):
    """Send a notification with the given data to the specified port"""
    ws_url = f"ws://localhost:{port}"
    if port == 8767:
        ws_url += "/ws"  # Some servers require /ws path
    
    logger.info(f"Connecting to {ws_url}")
    
    try:
        async with websockets.connect(ws_url, ping_interval=None, close_timeout=2) as ws:
            # Receive welcome message
            try:
                welcome = await asyncio.wait_for(ws.recv(), timeout=2.0)
                logger.info(f"Connected to {ws_url}. Welcome: {welcome[:100]}...")
            except asyncio.TimeoutError:
                logger.warning(f"No welcome message from {ws_url}")
            
            # Add timestamp to data
            data["timestamp"] = datetime.now().isoformat()
            
            # Send notification
            logger.info(f"Sending to {ws_url}: {json.dumps(data)}")
            await ws.send(json.dumps(data))
            
            # Try to get a response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                logger.info(f"Response from {ws_url}: {response[:100]}...")
            except asyncio.TimeoutError:
                logger.warning(f"No response from {ws_url}")
            
            logger.info(f"Completed notification attempt to {ws_url}")
            
    except Exception as e:
        logger.error(f"Connection error with {ws_url}: {e}")

if __name__ == "__main__":
    message = sys.argv[1] if len(sys.argv) > 1 else "Test notification sent at " + datetime.now().strftime("%H:%M:%S")
    logger.info(f"Starting notification debug with message: {message}")
    
    asyncio.run(try_all_formats_and_ports(message))
    logger.info("Completed all notification attempts")