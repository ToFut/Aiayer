#!/usr/bin/env python3
"""
Test script to check bridge connection between overlay and automation server
"""
import asyncio
import websockets
import json
import time
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('bridge_connection_test')

async def test_bridge_connection():
    """Test if the overlay bridge can properly forward screen sharing messages"""
    
    # First, connect to automation server directly
    print("STEP 1: Connecting to automation server directly (port 8765)...")
    
    try:
        async with websockets.connect("ws://localhost:8765") as direct_ws:
            logger.info("✅ Successfully connected to automation server on port 8765")
            
            # Test a basic message
            await direct_ws.send(json.dumps({
                "type": "register", 
                "client_id": "test_bridge_client"
            }))
            
            response = await asyncio.wait_for(direct_ws.recv(), timeout=2)
            logger.info(f"Received from automation server: {json.loads(response)['type']}")
            
            logger.info("Automation server connection test passed")
    except Exception as e:
        logger.error(f"❌ Failed to connect to automation server on port 8765: {e}")
        print("ERROR: Automation server is not running on port 8765")
        return False
    
    # Next, connect to bridge server
    print("\nSTEP 2: Connecting to bridge server on port 8767...")
    
    try:
        async with websockets.connect("ws://localhost:8767") as bridge_ws:
            logger.info("✅ Successfully connected to bridge server on port 8767")
            
            # Register as client
            await bridge_ws.send(json.dumps({
                "type": "register",
                "payload": {
                    "client_type": "ui",
                    "version": "1.0.0",
                    "capabilities": ["overlay_display", "user_interaction"],
                    "timestamp": int(time.time() * 1000)
                }
            }))
            
            # Wait for registration response
            try:
                reg_response = await asyncio.wait_for(bridge_ws.recv(), timeout=2)
                logger.info(f"Registration response: {reg_response[:100]}...")
            except asyncio.TimeoutError:
                logger.warning("No registration response received from bridge")
            
            # Try to request screen sharing
            logger.info("Sending screen sharing request to bridge...")
            await bridge_ws.send(json.dumps({
                "type": "start_screen_sharing",
                "payload": {
                    "resolution": "auto",
                    "fps": 5,
                    "compression": 80,
                    "client_id": "test_bridge_client",
                    "timestamp": int(time.time() * 1000)
                }
            }))
            
            # Wait for any response for 5 seconds
            logger.info("Waiting for responses from bridge...")
            start_time = time.time()
            frame_received = False
            
            while time.time() - start_time < 5:
                try:
                    response = await asyncio.wait_for(bridge_ws.recv(), timeout=1)
                    response_data = json.loads(response)
                    response_type = response_data.get("type", "unknown")
                    
                    logger.info(f"Received message type from bridge: {response_type}")
                    
                    if response_type == "screen_frame":
                        frame_received = True
                        frame_size = len(response_data.get("payload", {}).get("data", "")) // 1024
                        logger.info(f"✅ Screen frame received! Size: {frame_size}KB")
                        break
                except asyncio.TimeoutError:
                    logger.info("Waiting for bridge response...")
            
            # Check if we got a screen frame
            if frame_received:
                logger.info("✅ Bridge successfully forwarded screen sharing request!")
            else:
                logger.warning("❌ No screen frame received from bridge within timeout")
                
            # Stop screen sharing
            await bridge_ws.send(json.dumps({
                "type": "stop_screen_sharing",
                "payload": {}
            }))
            
            logger.info("Stopped screen sharing")
    except Exception as e:
        logger.error(f"❌ Failed to connect to bridge server on port 8767: {e}")
        print("ERROR: Bridge server is not running on port 8767")
        return False
    
    print("\nTest Summary:")
    print("1. Automation server (port 8765): ✅ CONNECTED")
    print("2. Bridge server (port 8767): " + ("✅ CONNECTED" if 'bridge_ws' in locals() else "❌ FAILED"))
    print("3. Screen sharing through bridge: " + ("✅ WORKING" if frame_received else "❌ FAILED"))
    
    return True

if __name__ == "__main__":
    asyncio.run(test_bridge_connection())