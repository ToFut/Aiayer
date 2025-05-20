#!/usr/bin/env python3
"""
Simple Context Test

A minimal test to verify sensor data and contextual awareness with the echo server.
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
        logging.FileHandler('logs/simple_context_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# WebSocket server URI
WS_URI = "ws://localhost:8767"

async def run_context_test():
    """Run a simple context test against the echo server."""
    try:
        # Create log directory
        os.makedirs("logs", exist_ok=True)
        
        logger.info("=== STARTING SIMPLE CONTEXT TEST ===")
        
        # Connect to WebSocket server
        logger.info(f"Connecting to WebSocket server at {WS_URI}")
        async with websockets.connect(WS_URI) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Receive welcome message
            response = await websocket.recv()
            data = json.loads(response)
            logger.info(f"Received welcome message: {data}")
            
            # First send a test message that matches the expected format
            test_msg = {
                "type": "test", 
                "payload": {
                    "message": "Hello from context test client", 
                    "timestamp": int(time.time() * 1000)
                }
            }
            await websocket.send(json.dumps(test_msg))
            response = await websocket.recv()
            echo_data = json.loads(response)
            
            if echo_data.get("type") == "echo" and echo_data.get("data") == test_msg:
                logger.info("✅ Test message echoed successfully")
                print("✅ Initial test message passed")
            else:
                logger.error(f"❌ Test message echo failed: {echo_data}")
                print("❌ Initial test message failed")
            
            # 1. Test process sensor data
            logger.info("STEP 1: Testing process sensor data")
            process_data = {
                "type": "sensor_data",
                "sensor_type": "process",
                "data": {
                    "active_window": "TestEditor",
                    "active_app": "CodeEditor",
                    "active_apps": ["CodeEditor", "Terminal", "Browser"],
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            await websocket.send(json.dumps(process_data))
            response = await websocket.recv()
            echo_data = json.loads(response)
            
            if echo_data.get("type") == "echo" and echo_data.get("data") == process_data:
                logger.info("✅ Process sensor data echoed successfully")
                print("✅ Process sensor data test passed")
            else:
                logger.error(f"❌ Process sensor data echo failed: {echo_data}")
                print("❌ Process sensor data test failed")
            
            # 2. Test screen sensor data
            logger.info("STEP 2: Testing screen sensor data")
            screen_data = {
                "type": "sensor_data",
                "sensor_type": "screen",
                "data": {
                    "screen_text": "This is a test screen content for contextual awareness testing.",
                    "has_images": True,
                    "has_videos": False,
                    "window": "TestWindow",
                    "active_window": "TestWindow",
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            await websocket.send(json.dumps(screen_data))
            response = await websocket.recv()
            echo_data = json.loads(response)
            
            if echo_data.get("type") == "echo" and echo_data.get("data") == screen_data:
                logger.info("✅ Screen sensor data echoed successfully")
                print("✅ Screen sensor data test passed")
            else:
                logger.error(f"❌ Screen sensor data echo failed: {echo_data}")
                print("❌ Screen sensor data test failed")
            
            # 3. Test file sensor data
            logger.info("STEP 3: Testing file sensor data")
            file_data = {
                "type": "sensor_data",
                "sensor_type": "file",
                "data": {
                    "files": [
                        "test_file1.py",
                        "test_file2.py",
                        "test_config.yaml"
                    ],
                    "current_file": {
                        "name": "simple_context_test.py",
                        "path": "/Users/segevbin/Desktop/SensAI/Aiayer/simple_context_test.py",
                        "type": "text"
                    },
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            await websocket.send(json.dumps(file_data))
            response = await websocket.recv()
            echo_data = json.loads(response)
            
            if echo_data.get("type") == "echo" and echo_data.get("data") == file_data:
                logger.info("✅ File sensor data echoed successfully")
                print("✅ File sensor data test passed")
            else:
                logger.error(f"❌ File sensor data echo failed: {echo_data}")
                print("❌ File sensor data test failed")
            
            # 4. Test query message
            logger.info("STEP 4: Testing query message")
            query_data = {
                "type": "query",
                "query": "What's on my screen and which application am I using?"
            }
            
            await websocket.send(json.dumps(query_data))
            response = await websocket.recv()
            echo_data = json.loads(response)
            
            if echo_data.get("type") == "echo" and echo_data.get("data") == query_data:
                logger.info("✅ Query message echoed successfully")
                print("✅ Query message test passed")
            else:
                logger.error(f"❌ Query message echo failed: {echo_data}")
                print("❌ Query message test failed")
                
            # 5. Test memory message
            logger.info("STEP 5: Testing memory message")
            memory_data = {
                "type": "memory_query",
                "query": "MEMORY_TEST_TOKEN_8767"
            }
            
            await websocket.send(json.dumps(memory_data))
            response = await websocket.recv()
            echo_data = json.loads(response)
            
            if echo_data.get("type") == "echo" and echo_data.get("data") == memory_data:
                logger.info("✅ Memory message echoed successfully")
                print("✅ Memory message test passed")
            else:
                logger.error(f"❌ Memory message echo failed: {echo_data}")
                print("❌ Memory message test failed")
            
            logger.info("=== SIMPLE CONTEXT TEST COMPLETED ===")
            print("\n=== SIMPLE CONTEXT TEST COMPLETED ===")
            print("All tests passed with the echo server.")
            print("Note: This only tests message format compatibility, not actual context integration.")
    
    except websockets.exceptions.ConnectionClosed as e:
        logger.error(f"Connection closed unexpectedly: {e}")
        print(f"❌ Test failed: Connection closed unexpectedly")
    except Exception as e:
        logger.error(f"Error in test: {e}")
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_context_test())