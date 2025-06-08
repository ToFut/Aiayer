#!/usr/bin/env python3
"""
Diagnostic script to check the overlay response handling
This script connects to both WebSocket endpoints and sends test messages
"""
import asyncio
import websockets
import json
import logging
import sys
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def test_connection(url, message_type):
    """Connect to WebSocket endpoint and send a test message"""
    try:
        logger.info(f"Connecting to {url}...")
        async with websockets.connect(url, close_timeout=5) as websocket:
            logger.info(f"Connected to {url}")
            
            # Register with server
            register_msg = {
                "type": "register",
                "payload": {
                    "client_type": "diagnostic_tool",
                    "version": "1.0.0",
                    "capabilities": ["text"]
                }
            }
            
            logger.info(f"Sending registration to {url}")
            await websocket.send(json.dumps(register_msg))
            
            # Wait for registration response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2)
                logger.info(f"Registration response from {url}: {response[:100]}...")
            except asyncio.TimeoutError:
                logger.warning(f"No registration response from {url}")
            
            # Wait a moment
            await asyncio.sleep(1)
            
            # Send test message
            if message_type == "query":
                test_msg = {
                    "type": "llm_request",
                    "payload": {
                        "query": "This is a test message from diagnostic tool",
                        "mode": "ask",
                        "session_id": "diagnostic_session_" + str(int(time.time())),
                        "user_id": "diagnostic_user"
                    }
                }
            else:
                test_msg = {
                    "type": "notification",
                    "payload": {
                        "title": "Diagnostic Notification",
                        "message": "This is a test notification from diagnostic tool",
                        "level": "info"
                    }
                }
            
            logger.info(f"Sending test message to {url}: {json.dumps(test_msg)}")
            await websocket.send(json.dumps(test_msg))
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                logger.info(f"Response from {url}: {response[:200]}...")
                return True
            except asyncio.TimeoutError:
                logger.warning(f"No response from {url}")
                return False
                
    except (websockets.exceptions.ConnectionClosedError, ConnectionRefusedError) as e:
        logger.error(f"Connection error for {url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error for {url}: {e}")
        return False

async def send_direct_test_message():
    """Send a direct test message to both WebSocket endpoints"""
    ports = [8765, 8766, 8767]
    results = {}
    
    for port in ports:
        url = f"ws://localhost:{port}"
        logger.info(f"Testing query response on {url}")
        query_result = await test_connection(url, "query")
        results[f"{port}_query"] = query_result
        
        logger.info(f"Testing notification on {url}")
        notif_result = await test_connection(url, "notification")
        results[f"{port}_notification"] = notif_result
    
    return results

def print_summary(results):
    """Print a summary of the test results"""
    print("\n========== OVERLAY RESPONSE DIAGNOSTIC SUMMARY ==========")
    for endpoint, success in results.items():
        port, test_type = endpoint.split("_")
        status = "✅ WORKING" if success else "❌ FAILED"
        print(f"Port {port} - {test_type.upper()}: {status}")
    
    # Analysis
    print("\n========== ANALYSIS ==========")
    
    # Check if any endpoint is working
    if any(results.values()):
        print("✅ At least one endpoint is responding.")
    else:
        print("❌ All endpoints failed. The system appears to be down.")
    
    # Check interceptor
    if results.get("8766_query"):
        print("✅ The interceptor on port 8766 is handling queries correctly.")
    else:
        print("❌ The interceptor on port 8766 is not handling queries.")
    
    # Check main backend
    if results.get("8767_query"):
        print("✅ The main backend on port 8767 is handling queries correctly.")
    else:
        print("❌ The main backend on port 8767 is not handling queries.")
    
    # Recommendation
    print("\n========== RECOMMENDATION ==========")
    if results.get("8766_query"):
        print("✓ The overlay should connect to port 8766 (the interceptor)")
    elif results.get("8767_query"):
        print("✓ The overlay should connect to port 8767 (main backend)")
    else:
        print("! Both ports are unavailable. Restart the backend services.")
    
    print("\nNext steps:")
    if not any(results.values()):
        print("1. Restart all backend services with: ./RESTART_FIXED_SYSTEM.sh")
        print("2. Start the overlay response interceptor: python Others/overlay_response_interceptor.py")
    elif not results.get("8766_query"):
        print("1. Start the overlay response interceptor: python Others/overlay_response_interceptor.py")
    
    print("3. Make sure the overlay is connecting to port 8766 in app.svelte")
    print("4. Restart the overlay: ./RESTART_OVERLAY.sh")

if __name__ == "__main__":
    logger.info("Starting overlay response diagnostic tool...")
    results = asyncio.run(send_direct_test_message())
    print_summary(results)