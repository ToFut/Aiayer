#!/usr/bin/env python3
import asyncio
import websockets
import json
import logging
import sys
import os
from datetime import datetime
import uuid
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/fixed_notification.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('fixed_notification')

async def send_chat_notification(message, port=8768, mode="Suggest", importance="high", play_sound=True):
    """
    Send a notification that exactly matches what EnterpriseChatWidget.svelte expects.
    This targets the handleBackendMessage function, specifically the format:
    { success: true, response: "message", mode: "Suggest" }
    """
    # Connection URL
    ws_url = f"ws://localhost:{port}"
    if port == 8767:
        ws_url += "/ws"  # Backend requires /ws path
    
    logger.info(f"🔔 Sending notification to {ws_url} using CHAT FORMAT")
    
    try:
        # Connect to WebSocket server
        async with websockets.connect(ws_url, ping_interval=None) as websocket:
            # Receive welcome message
            welcome = await websocket.recv()
            logger.info(f"Connected to server: {welcome[:100]}...")
            
            # Create notification in the exact format expected by EnterpriseChatWidget.svelte
            notification = {
                "success": True,
                "response": message,
                "mode": mode,
                "processing_time": 0.1,
                "enterprise_validated": True,
                "timestamp": datetime.now().isoformat()
            }
            
            # Send notification
            await websocket.send(json.dumps(notification))
            logger.info(f"📩 Notification sent: {json.dumps(notification)[:100]}...")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                logger.info(f"✅ Response received: {response[:100]}...")
                return True
            except asyncio.TimeoutError:
                logger.warning("⚠️ No response received, but notification might still be processed")
                return True
                
    except Exception as e:
        logger.error(f"❌ Error sending notification to {ws_url}: {e}")
        return False

async def send_legacy_notification(message, port=8765, importance="high", play_sound=True):
    """Send a notification using legacy format"""
    # Connection URL
    ws_url = f"ws://localhost:{port}"
    if port == 8767:
        ws_url += "/ws"  # Backend requires /ws path
    
    notification_id = f"notification_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}"
    logger.info(f"🔔 Sending notification to {ws_url} using LEGACY FORMAT")
    
    try:
        # Connect to WebSocket server
        async with websockets.connect(ws_url, ping_interval=None) as websocket:
            # Receive welcome message
            welcome = await websocket.recv()
            logger.info(f"Connected to server: {welcome[:100]}...")
            
            # Create notification in legacy format
            notification = {
                "type": "notification",
                "notification_id": notification_id,
                "message": message,
                "importance": importance,
                "play_sound": play_sound,
                "timestamp": datetime.now().isoformat()
            }
            
            # Send notification
            await websocket.send(json.dumps(notification))
            logger.info(f"📩 Notification sent: {json.dumps(notification)[:100]}...")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                logger.info(f"✅ Response received: {response[:100]}...")
                return True
            except asyncio.TimeoutError:
                logger.warning("⚠️ No response received, but notification might still be processed")
                return True
                
    except Exception as e:
        logger.error(f"❌ Error sending notification to {ws_url}: {e}")
        return False

async def send_all_formats(message, ports=None):
    """Send the notification using all available formats to all ports"""
    if ports is None:
        ports = [8765, 8766, 8767, 8768]
    
    results = []
    
    # Try chat format on all ports
    for port in ports:
        result = await send_chat_notification(message, port)
        results.append({
            "port": port,
            "format": "chat",
            "success": result
        })
    
    # Try legacy format on all ports
    for port in ports:
        result = await send_legacy_notification(message, port)
        results.append({
            "port": port,
            "format": "legacy",
            "success": result
        })
    
    # Summary
    successes = [r for r in results if r["success"]]
    logger.info(f"📊 Summary: {len(successes)}/{len(results)} notifications succeeded")
    for success in successes:
        logger.info(f"✅ Success: Port {success['port']} using {success['format']} format")
    
    return successes

def main():
    parser = argparse.ArgumentParser(description='Send a notification to the overlay')
    parser.add_argument('message', help='The notification message to send')
    parser.add_argument('--port', type=int, help='WebSocket port (default: try all ports)', default=None)
    parser.add_argument('--mode', help='Notification mode (default: Suggest)', default="Suggest")
    parser.add_argument('--format', help='Notification format (chat, legacy, all)', default="all")
    
    args = parser.parse_args()
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    if args.port:
        ports = [args.port]
    else:
        ports = [8765, 8766, 8767, 8768]
    
    if args.format == "chat":
        # Create and run a coroutine that runs all the tasks
        async def run_all_chat():
            return await asyncio.gather(*[send_chat_notification(args.message, port, args.mode) for port in ports])
        asyncio.run(run_all_chat())
    elif args.format == "legacy":
        async def run_all_legacy():
            return await asyncio.gather(*[send_legacy_notification(args.message, port) for port in ports])
        asyncio.run(run_all_legacy())
    else:  # all formats
        asyncio.run(send_all_formats(args.message, ports))

if __name__ == "__main__":
    main()