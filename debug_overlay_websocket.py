#!/usr/bin/env python3
"""
Debug Overlay WebSocket Connection
This script tests the WebSocket connection from the overlay to the backend server
"""

import asyncio
import websockets
import json
import logging
import sys
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("debug_overlay_websocket")

# Test parameters
TEST_MESSAGE = "Hello, this is a test message from the debugging client"
TEST_PORTS = [8765, 8766, 8767, 8768]  # Ports to test
TEST_TIMEOUT = 5  # Timeout in seconds

async def test_websocket_port(port):
    """Test WebSocket connection to a specific port"""
    url = f"ws://localhost:{port}"
    client_id = f"debug_client_{int(time.time())}"
    
    logger.info(f"🔄 Testing connection to {url}...")
    
    try:
        async with websockets.connect(url, ping_timeout=TEST_TIMEOUT) as ws:
            logger.info(f"✅ Connected to {url}")
            
            # Send identification message
            logger.info(f"📤 Sending identification message...")
            await ws.send(json.dumps({
                "type": "connection_established",
                "payload": {
                    "client": "debug_client",
                    "version": "1.0.0"
                }
            }))
            
            # Wait for response
            logger.info(f"📥 Waiting for initial response...")
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=TEST_TIMEOUT)
                logger.info(f"📥 Received: {response[:200]}...")
            except asyncio.TimeoutError:
                logger.warning(f"⚠️ Timeout waiting for initial response")
            
            # Send test chat message
            logger.info(f"📤 Sending test chat message...")
            test_chat = {
                "type": "chat_request",
                "mode": "Ask",
                "message": TEST_MESSAGE,
                "session_id": client_id,
                "timestamp": datetime.now().isoformat()
            }
            await ws.send(json.dumps(test_chat))
            
            # Wait for chat response
            logger.info(f"📥 Waiting for chat response...")
            try:
                chat_response = await asyncio.wait_for(ws.recv(), timeout=TEST_TIMEOUT)
                logger.info(f"📥 Received chat response: {chat_response[:200]}...")
                
                # Parse response
                try:
                    response_data = json.loads(chat_response)
                    logger.info(f"📊 Response type: {response_data.get('type', 'unknown')}")
                    logger.info(f"📊 Response success: {response_data.get('success', False)}")
                    if "response" in response_data:
                        logger.info(f"📊 Response content: {response_data['response'][:100]}...")
                except json.JSONDecodeError:
                    logger.error(f"❌ Invalid JSON in response")
            except asyncio.TimeoutError:
                logger.warning(f"⚠️ Timeout waiting for chat response")
            
            # Return success
            return {
                "port": port, 
                "status": "connected",
                "responses_received": True
            }
    except Exception as e:
        logger.error(f"❌ Connection error for port {port}: {str(e)}")
        return {
            "port": port,
            "status": "failed",
            "error": str(e)
        }

async def main():
    """Test connections to all ports"""
    results = []
    
    # Test each port
    for port in TEST_PORTS:
        result = await test_websocket_port(port)
        results.append(result)
        # Short delay between tests
        await asyncio.sleep(1)
    
    # Print summary
    logger.info("="*50)
    logger.info("📋 TEST RESULTS SUMMARY")
    logger.info("="*50)
    for result in results:
        port = result["port"]
        status = result["status"]
        if status == "connected":
            logger.info(f"✅ Port {port}: Connected successfully")
        else:
            logger.info(f"❌ Port {port}: Failed - {result.get('error', 'Unknown error')}")
    
    # Provide recommendations
    logger.info("="*50)
    logger.info("🔧 RECOMMENDATIONS")
    logger.info("="*50)
    
    # Check which ports are working
    working_ports = [r["port"] for r in results if r["status"] == "connected"]
    
    if 8767 in working_ports:
        logger.info("✅ Port 8767 is working correctly - this is the main backend port")
        logger.info("👉 Update the overlay config.js to use 'ws://localhost:8767' for all connections")
    elif not working_ports:
        logger.info("❌ No ports are working - check if backend servers are running")
        logger.info("👉 Run ./RESTART_FIXED_SYSTEM.sh to restart all backend services")
    else:
        logger.info(f"⚠️ Port 8767 is not working, but ports {working_ports} are available")
        logger.info("👉 Check if the enhanced_enterprise_backend_with_context.py is running")
        logger.info("👉 Run 'lsof -i :8767' to see what's using the port")
    
    logger.info("="*50)

if __name__ == "__main__":
    asyncio.run(main())