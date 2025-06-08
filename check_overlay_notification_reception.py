#!/usr/bin/env python3
"""
Test Script to check if the overlay is correctly receiving notifications
through our WebSocket proxy.
"""

import asyncio
import json
import logging
import sys
import time
import websockets
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("overlay_notification_checker")

# WebSocket connection info - Connect to our proxy
PROXY_WS_URI = "ws://localhost:8766"

async def send_test_notification():
    """Send a test notification through the proxy and monitor logs"""
    try:
        logger.info(f"Connecting to proxy at {PROXY_WS_URI}")
        async with websockets.connect(PROXY_WS_URI, ping_interval=5, ping_timeout=20) as websocket:
            logger.info("Connected to proxy WebSocket")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            logger.info(f"Received welcome from proxy: {welcome[:100]}...")
            
            # Send a test notification in all supported formats
            logger.info("Sending test notification in format 1 (suggestion)")
            notification1 = {
                "type": "suggestion",
                "response": "This is a test notification (Format 1: suggestion type)",
                "buttons": [
                    {
                        "id": "confirm",
                        "text": "Confirm",
                        "type": "primary"
                    },
                    {
                        "id": "dismiss",
                        "text": "Dismiss",
                        "type": "secondary"
                    }
                ],
                "importance": "high",
                "play_sound": True
            }
            
            await websocket.send(json.dumps(notification1))
            logger.info("Test notification 1 sent")
            
            # Wait a bit for the notification to be processed
            await asyncio.sleep(2)
            
            # Send a test notification in format 2 (do_button)
            logger.info("Sending test notification in format 2 (do_button)")
            notification2 = {
                "type": "do_button",
                "action": "display",
                "plan_id": f"test_plan_{int(time.time())}",
                "content": {
                    "title": "Test DO Button",
                    "message": "This is a test notification (Format 2: do_button type)",
                    "buttons": [
                        {
                            "id": "execute",
                            "text": "Execute",
                            "type": "primary"
                        },
                        {
                            "id": "cancel",
                            "text": "Cancel",
                            "type": "secondary"
                        }
                    ]
                },
                "notification": True,
                "play_sound": True
            }
            
            await websocket.send(json.dumps(notification2))
            logger.info("Test notification 2 sent")
            
            # Wait for any responses
            logger.info("Waiting for responses...")
            try:
                for _ in range(3):  # Try to receive up to 3 messages
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=3)
                        logger.info(f"Received response: {response[:100]}...")
                    except asyncio.TimeoutError:
                        logger.info("No more responses received within timeout")
                        break
            except Exception as e:
                logger.error(f"Error receiving responses: {e}")
            
            logger.info("Test complete. Check the overlay to see if notifications are visible.")
            logger.info("If notifications are visible, the fix is working correctly!")
            
    except Exception as e:
        logger.error(f"Error in send_test_notification: {e}")
        return False
    
    return True

async def check_proxy_connections():
    """Check if the proxy is correctly connected to the DO button server and Neural UI server"""
    try:
        # Check proxy port
        import socket
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            result = s.connect_ex(('localhost', 8766))
            if result == 0:
                logger.info("✅ Proxy server is running on port 8766")
            else:
                logger.error("❌ Proxy server is not running on port 8766")
                return False
        
        # Check DO button server port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            result = s.connect_ex(('localhost', 8765))
            if result == 0:
                logger.info("✅ DO button server is running on port 8765")
            else:
                logger.error("❌ DO button server is not running on port 8765")
                return False
        
        # Check Neural UI server port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            result = s.connect_ex(('localhost', 8768))
            if result == 0:
                logger.info("✅ Neural UI server is running on port 8768")
            else:
                logger.error("❌ Neural UI server is not running on port 8768")
                # Non-critical, continue anyway
        
        return True
    
    except Exception as e:
        logger.error(f"Error checking proxy connections: {e}")
        return False

async def check_overlay_connection():
    """Check if the overlay is connected to the proxy"""
    # Check the proxy log file to see if any clients are connected
    try:
        import os
        
        log_path = "logs/websocket/do_button_proxy.log"
        if os.path.exists(log_path):
            connected = False
            try:
                with open(log_path, "r") as f:
                    log_content = f.read()
                    if "Client" in log_content and "connected" in log_content:
                        connected = True
                        logger.info("✅ Found client connection in proxy logs")
                    else:
                        logger.warning("⚠️ No client connections found in proxy logs")
            except Exception as e:
                logger.error(f"Error reading proxy log: {e}")
            
            return connected
        else:
            logger.warning(f"⚠️ Proxy log file not found at {log_path}")
            return False
    except Exception as e:
        logger.error(f"Error checking overlay connection: {e}")
        return False

async def main():
    """Run all checks"""
    logger.info("==== OVERLAY NOTIFICATION RECEPTION CHECK ====")
    
    # Step 1: Check if proxy is running and connected to required servers
    logger.info("\n=== Step 1: Checking proxy connections ===")
    proxy_ok = await check_proxy_connections()
    
    if not proxy_ok:
        logger.error("❌ Proxy connection check failed")
        logger.error("Please ensure the proxy is running using START_ENHANCED_SYSTEM_WITH_NEURAL_UI.sh")
        return 1
    
    # Step 2: Check if overlay is connected to proxy
    logger.info("\n=== Step 2: Checking overlay connection ===")
    overlay_connected = await check_overlay_connection()
    
    if not overlay_connected:
        logger.warning("⚠️ No overlay connection found")
        logger.warning("Please ensure the overlay is running and connected to ws://localhost:8766")
        logger.warning("Continue anyway to send test notifications...")
    
    # Step 3: Send test notification
    logger.info("\n=== Step 3: Sending test notifications ===")
    notification_sent = await send_test_notification()
    
    if not notification_sent:
        logger.error("❌ Failed to send test notifications")
        return 1
    
    logger.info("\n==== TEST SUMMARY ====")
    logger.info(f"Proxy connections: {'✅ OK' if proxy_ok else '❌ FAILED'}")
    logger.info(f"Overlay connection: {'✅ OK' if overlay_connected else '⚠️ NOT FOUND'}")
    logger.info(f"Test notifications: {'✅ SENT' if notification_sent else '❌ FAILED'}")
    
    logger.info("\nPlease check the overlay to see if the notifications are visible.")
    logger.info("If notifications are visible, the fix is working correctly!")
    
    return 0

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Check interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)