#!/usr/bin/env python3
"""
Combined Notification Test - Try multiple notification formats at once to ensure display
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

# WebSocket endpoints
PROXY_ENDPOINT = "ws://localhost:8766"  # Proxy bridge
DO_BUTTON_ENDPOINT = "ws://localhost:8765"  # Direct DO button server
BACKEND_ENDPOINT = "ws://localhost:8767/ws"  # Backend server

async def send_to_proxy():
    """Send notification to proxy bridge"""
    try:
        logger.info(f"Connecting to proxy bridge at {PROXY_ENDPOINT}")
        
        async with websockets.connect(PROXY_ENDPOINT) as ws:
            # Wait for welcome
            welcome = await ws.recv()
            logger.info(f"Proxy welcome: {welcome[:100]}...")
            
            # Create a combined format notification
            plan_id = f"notification_{uuid.uuid4()}"
            
            # Try format 1: Direct chat message
            message1 = {
                "type": "chat_message",
                "mode": "SUGGEST",
                "sender": "system",
                "message": "🚨 URGENT NOTIFICATION TEST 🚨\n\nThis is a test of the notification system using chat_message format.",
                "buttons": [
                    {
                        "text": "I see this!",
                        "value": "seen",
                        "style": "success"
                    }
                ],
                "plan_id": plan_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # Send to proxy
            logger.info("Sending chat_message format...")
            await ws.send(json.dumps(message1))
            
            # Wait for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                logger.info(f"Response: {response[:100]}...")
            except asyncio.TimeoutError:
                logger.warning("No response received within timeout")
            
            await asyncio.sleep(1)
            
            # Try format 2: suggestion format
            message2 = {
                "type": "suggestion",
                "response": "⚠️ SUGGESTION TEST FORMAT ⚠️\n\nThis is a test of the notification system using suggestion format.",
                "buttons": [
                    {
                        "text": "I see this!",
                        "value": "seen",
                        "style": "success"
                    }
                ],
                "importance": "high",
                "play_sound": True,
                "plan_id": f"{plan_id}_2",
                "timestamp": datetime.now().isoformat()
            }
            
            # Send to proxy
            logger.info("Sending suggestion format...")
            await ws.send(json.dumps(message2))
            
            # Wait for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                logger.info(f"Response: {response[:100]}...")
            except asyncio.TimeoutError:
                logger.warning("No response received within timeout")
            
            await asyncio.sleep(1)
            
            # Try format 3: notification format
            message3 = {
                "type": "notification",
                "title": "NOTIFICATION TEST",
                "message": "🔔 This is a test of the notification system using notification format.",
                "buttons": [
                    {
                        "text": "I see this!",
                        "value": "seen",
                        "style": "success"
                    }
                ],
                "importance": "high",
                "play_sound": True,
                "plan_id": f"{plan_id}_3",
                "timestamp": datetime.now().isoformat()
            }
            
            # Send to proxy
            logger.info("Sending notification format...")
            await ws.send(json.dumps(message3))
            
            # Wait for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                logger.info(f"Response: {response[:100]}...")
            except asyncio.TimeoutError:
                logger.warning("No response received within timeout")
            
            return True
    except Exception as e:
        logger.error(f"Error sending to proxy: {e}")
        return False

async def send_directly_to_backend():
    """Send notification directly to backend"""
    try:
        logger.info(f"Connecting to backend at {BACKEND_ENDPOINT}")
        
        async with websockets.connect(BACKEND_ENDPOINT) as ws:
            # Wait for welcome
            welcome = await ws.recv()
            logger.info(f"Backend welcome: {welcome[:100]}...")
            
            # Register
            register = {
                "type": "register",
                "client_type": "test_client",
                "client_id": f"test_{uuid.uuid4()}"
            }
            
            await ws.send(json.dumps(register))
            
            # Wait for registration response
            register_response = await ws.recv()
            logger.info(f"Register response: {register_response[:100]}...")
            
            # Create a direct chat message to display
            chat_message = {
                "type": "direct_chat_message",
                "mode": "SUGGEST",
                "message": "🔔 BACKEND NOTIFICATION TEST 🔔\n\nThis is a test sent directly to the backend server.",
                "buttons": [
                    {
                        "text": "I see this!",
                        "value": "seen",
                        "style": "success"
                    }
                ],
                "timestamp": datetime.now().isoformat()
            }
            
            # Send to backend
            logger.info("Sending direct_chat_message to backend...")
            await ws.send(json.dumps(chat_message))
            
            # Wait for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                logger.info(f"Response: {response[:100]}...")
            except asyncio.TimeoutError:
                logger.warning("No response received within timeout")
            
            return True
    except Exception as e:
        logger.error(f"Error sending to backend: {e}")
        return False

async def send_to_do_button():
    """Send notification to DO button server"""
    try:
        logger.info(f"Connecting to DO button server at {DO_BUTTON_ENDPOINT}")
        
        async with websockets.connect(DO_BUTTON_ENDPOINT) as ws:
            # Wait for welcome
            welcome = await ws.recv()
            logger.info(f"DO button welcome: {welcome[:100]}...")
            
            # Create a button action that might trigger notification
            button_action = {
                "type": "button_action",
                "action": "DO",
                "plan_id": f"test_plan_{uuid.uuid4()}",
                "display_notification": True,
                "notification_text": "🛑 DO BUTTON TEST 🛑\n\nThis is a test of the notification system via DO button server.",
                "timestamp": datetime.now().isoformat()
            }
            
            # Send to DO button server
            logger.info("Sending button_action to DO button server...")
            await ws.send(json.dumps(button_action))
            
            # Wait for responses
            try:
                for _ in range(3):
                    response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                    logger.info(f"Response: {response[:100]}...")
            except asyncio.TimeoutError:
                logger.warning("No more responses received")
            
            return True
    except Exception as e:
        logger.error(f"Error sending to DO button server: {e}")
        return False

async def main():
    """Run all notification tests"""
    logger.info("=== COMBINED NOTIFICATION TEST ===")
    logger.info("Sending notifications using multiple formats and servers")
    
    # Send to all servers
    proxy_result = await send_to_proxy()
    backend_result = await send_directly_to_backend()
    do_button_result = await send_to_do_button()
    
    # Print results
    logger.info("\n=== TEST RESULTS ===")
    logger.info(f"Proxy Bridge Test: {'✅ Completed' if proxy_result else '❌ Failed'}")
    logger.info(f"Backend Test: {'✅ Completed' if backend_result else '❌ Failed'}")
    logger.info(f"DO Button Test: {'✅ Completed' if do_button_result else '❌ Failed'}")
    
    logger.info("\nCheck the overlay to see if any notifications appear.")
    logger.info("If notifications still don't appear, try these steps:")
    logger.info("1. Restart the overlay: cd overlay && npm run tauri dev")
    logger.info("2. Run the overlay connection checker: python3 check_overlay_connections.py")
    logger.info("3. Check system logs for any errors: cat logs/overlay/bridge.log")

if __name__ == "__main__":
    asyncio.run(main())