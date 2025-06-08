#!/usr/bin/env python3
"""
Test Fixed DO Button Proxy

This script tests the fixed DO button proxy by sending test messages to verify
the plan creation and forwarding logic.
"""

import asyncio
import websockets
import json
import time
import os
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[TEST-PROXY] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TEST_PROXY")

# Create a test session ID with the format used by frontend
test_session_id = f"task_{int(time.time())}_overlay_session_{int(time.time()*1000)}"

# Test message for DO button action
test_message = {
    "type": "agent_confirmation",
    "action": "DO",
    "sessionId": test_session_id,
    "timestamp": time.time()
}

async def check_plan_exists(session_id):
    """Check if plan exists in the cache directory"""
    safe_id = session_id.replace(':', '_').replace('/', '_').replace('\\', '_')
    plan_path = os.path.join("cache", "plans", f"{safe_id}.json")
    
    if os.path.exists(plan_path):
        logger.info(f"✅ Plan file exists: {plan_path}")
        
        # Print plan details
        try:
            with open(plan_path, "r") as f:
                plan = json.load(f)
            logger.info(f"Plan ID: {plan.get('id')}")
            logger.info(f"Plan task_id: {plan.get('task_id')}")
            return True
        except Exception as e:
            logger.error(f"Error reading plan file: {e}")
            return False
    else:
        logger.error(f"❌ Plan file does not exist: {plan_path}")
        return False

async def test_direct_server():
    """Test direct connection to the ultimate DO button server"""
    logger.info(f"Testing direct connection to ultimate DO button server (port 8768)")
    
    try:
        async with websockets.connect("ws://localhost:8768", ping_interval=None) as ws:
            # Wait for welcome message
            try:
                welcome = await asyncio.wait_for(ws.recv(), timeout=2.0)
                logger.info(f"Received welcome from server: {welcome[:100]}")
            except asyncio.TimeoutError:
                logger.warning("No welcome message received from server")
            
            # Send test message
            logger.info(f"Sending test message directly to server: {test_message}")
            await ws.send(json.dumps(test_message))
            
            # Wait for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                logger.info(f"Received response from server: {response[:100]}")
                return True
            except asyncio.TimeoutError:
                logger.error("Timeout waiting for response from server")
                return False
    except Exception as e:
        logger.error(f"Error connecting to server: {e}")
        return False

async def test_proxy():
    """Test connection through the fixed proxy"""
    logger.info(f"Testing connection through fixed proxy (port 8766)")
    
    try:
        async with websockets.connect("ws://localhost:8766", ping_interval=None) as ws:
            # Wait for welcome message
            try:
                welcome = await asyncio.wait_for(ws.recv(), timeout=2.0)
                logger.info(f"Received welcome from proxy: {welcome[:100]}")
            except asyncio.TimeoutError:
                logger.warning("No welcome message received from proxy")
            
            # Send test message
            logger.info(f"Sending test message through proxy: {test_message}")
            await ws.send(json.dumps(test_message))
            
            # Wait for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                logger.info(f"Received response through proxy: {response[:100]}")
                return True
            except asyncio.TimeoutError:
                logger.error("Timeout waiting for response from proxy")
                return False
    except Exception as e:
        logger.error(f"Error connecting to proxy: {e}")
        return False

async def main():
    """Run the tests"""
    print(f"DO Button Proxy Test - Using test session ID: {test_session_id}")
    
    # Check if both servers are running
    server_running = False
    proxy_running = False
    
    try:
        async with websockets.connect("ws://localhost:8768", ping_interval=None, close_timeout=1.0):
            server_running = True
    except:
        pass
    
    try:
        async with websockets.connect("ws://localhost:8766", ping_interval=None, close_timeout=1.0):
            proxy_running = True
    except:
        pass
    
    if not server_running:
        print("❌ Ultimate DO Button Server not running on port 8768!")
        print("Please start the server before running this test.")
        return 1
    
    if not proxy_running:
        print("❌ Fixed DO Button Proxy not running on port 8766!")
        print("Please run: ./start_fixed_do_button_proxy.sh")
        return 1
    
    print("---------------------------------------------------")
    print("Step 1: Testing direct connection to Ultimate DO Button Server")
    success1 = await test_direct_server()
    print(f"Direct server test: {'✅ PASSED' if success1 else '❌ FAILED'}")
    
    print("---------------------------------------------------")
    print("Step 2: Testing connection through Fixed DO Button Proxy")
    success2 = await test_proxy()
    print(f"Proxy test: {'✅ PASSED' if success2 else '❌ FAILED'}")
    
    print("---------------------------------------------------")
    print("Step 3: Verifying plan was created")
    success3 = await check_plan_exists(test_session_id)
    print(f"Plan creation test: {'✅ PASSED' if success3 else '❌ FAILED'}")
    
    # Overall result
    if success1 and success2 and success3:
        print("---------------------------------------------------")
        print("✅ ALL TESTS PASSED!")
        print("The DO Button fix is working correctly.")
        print("---------------------------------------------------")
        return 0
    else:
        print("---------------------------------------------------")
        print("❌ SOME TESTS FAILED!")
        print("Check the logs for details.")
        print("---------------------------------------------------")
        return 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)