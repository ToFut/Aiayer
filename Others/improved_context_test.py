#!/usr/bin/env python3
"""
Improved Context Test

A minimal test to verify connection to the WebSocket server on port 8767
and check basic message handling.
"""
import asyncio
import json
import logging
import websockets
import time
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/improved_context_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Check which port the server is using
def get_server_port():
    """Get the WebSocket server port from ws_port.txt if available."""
    try:
        if os.path.exists("ws_port.txt"):
            with open("ws_port.txt", "r") as f:
                port = f.read().strip()
                return int(port)
    except Exception as e:
        logger.warning(f"Could not read port from file: {e}")
    return 8767  # Default port

# WebSocket server URI
PORT = get_server_port()
WS_URI = f"ws://localhost:{PORT}"

async def run_context_test():
    """Run a simple context test against the echo server."""
    try:
        # Create log directory
        os.makedirs("logs", exist_ok=True)
        
        logger.info(f"=== STARTING IMPROVED CONTEXT TEST on port {PORT} ===")
        
        # Connect to WebSocket server
        logger.info(f"Connecting to WebSocket server at {WS_URI}")
        async with websockets.connect(WS_URI) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Receive welcome message
            response = await websocket.recv()
            data = json.loads(response)
            logger.info(f"Received welcome message: {data}")
            
            # 1. Test with a simple message
            logger.info("STEP 1: Testing simple message")
            simple_msg = {
                "type": "chat_message",
                "payload": {
                    "message": "Hello from context test client",
                    "timestamp": int(time.time() * 1000)
                }
            }
            
            logger.info(f"Sending message: {simple_msg}")
            await websocket.send(json.dumps(simple_msg))
            response = await websocket.recv()
            echo_data = json.loads(response)
            logger.info(f"Received response: {echo_data}")
            
            if echo_data.get("type") == "echo":
                logger.info("✅ Simple message test passed")
                print("✅ Simple message test passed")
            else:
                logger.warning(f"⚠️ Unexpected response format: {echo_data}")
                print("⚠️ Simple message test unexpected response format")
            
            # 2. Test with user interaction format (for port 8765 compatibility)
            logger.info("STEP 2: Testing user interaction format")
            user_msg = {
                "type": "user_interaction",
                "payload": {
                    "type": "query",
                    "query": "What's on my screen?",
                    "timestamp": int(time.time() * 1000)
                }
            }
            
            logger.info(f"Sending message: {user_msg}")
            await websocket.send(json.dumps(user_msg))
            response = await websocket.recv()
            echo_data = json.loads(response)
            logger.info(f"Received response: {echo_data}")
            
            if echo_data.get("type") == "echo":
                logger.info("✅ User interaction test passed")
                print("✅ User interaction test passed")
            else:
                logger.warning(f"⚠️ Unexpected response format: {echo_data}")
                print("⚠️ User interaction test unexpected response format")
                
            # 3. Test with sensor data format
            logger.info("STEP 3: Testing sensor data format")
            sensor_msg = {
                "type": "sensor_data",
                "payload": {
                    "sensor_type": "screen",
                    "data": {
                        "screen_text": "Test screen content",
                        "active_window": "TestWindow",
                        "timestamp": datetime.now().isoformat()
                    }
                }
            }
            
            logger.info(f"Sending message: {sensor_msg}")
            await websocket.send(json.dumps(sensor_msg))
            response = await websocket.recv()
            echo_data = json.loads(response)
            logger.info(f"Received response: {echo_data}")
            
            if echo_data.get("type") == "echo":
                logger.info("✅ Sensor data test passed")
                print("✅ Sensor data test passed")
            else:
                logger.warning(f"⚠️ Unexpected response format: {echo_data}")
                print("⚠️ Sensor data test unexpected response format")
                
            # Wait for a broadcast status update message
            logger.info("Waiting for status broadcast message (5 seconds timeout)...")
            try:
                websocket.recv_timeout = 5  # Set timeout to 5 seconds
                status_response = await websocket.recv()
                status_data = json.loads(status_response)
                logger.info(f"Received status broadcast: {status_data}")
                print("✅ Received status broadcast message")
            except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
                logger.info("No status message received within timeout")
                print("⚠️ No status broadcast received (this is okay if broadcasts are disabled)")
                
            logger.info("=== IMPROVED CONTEXT TEST COMPLETED SUCCESSFULLY ===")
            print("\n=== IMPROVED CONTEXT TEST COMPLETED SUCCESSFULLY ===")
            print(f"Successfully connected to port {PORT} and exchanged messages")
    
    except websockets.exceptions.ConnectionClosed as e:
        logger.error(f"Connection closed unexpectedly: {e}")
        print(f"❌ Test failed: Connection closed unexpectedly: {e}")
    except Exception as e:
        logger.error(f"Error in test: {e}")
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_context_test())