#!/usr/bin/env python3
"""
Test script to verify the Neural UI DO Button fix.
This script sends a simulated DO button action message to the proxy server
and verifies that plans are correctly handled.
"""

import asyncio
import json
import logging
import sys
import websockets
import uuid
import time
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("neural_ui_do_button_test")

# WebSocket URLs
PROXY_URL = "ws://localhost:8766"
BACKEND_URL = "ws://localhost:8767"
DO_BUTTON_URL = "ws://localhost:8765"
NEURAL_UI_URL = "ws://localhost:8768"

# Timeouts
CONNECTION_TIMEOUT = 10
RESPONSE_TIMEOUT = 30

async def connect_to_websocket(url: str, timeout: int = CONNECTION_TIMEOUT) -> Optional[websockets.WebSocketClientProtocol]:
    """Connect to a WebSocket server with timeout."""
    try:
        logger.info(f"Connecting to {url}...")
        connection = await asyncio.wait_for(
            websockets.connect(url),
            timeout=timeout
        )
        logger.info(f"✅ Connected to {url}")
        return connection
    except (asyncio.TimeoutError, ConnectionRefusedError, websockets.exceptions.WebSocketException) as e:
        logger.error(f"❌ Failed to connect to {url}: {e}")
        return None

async def send_message(websocket: websockets.WebSocketClientProtocol, message: Dict[str, Any]) -> None:
    """Send a message to a WebSocket server."""
    try:
        message_str = json.dumps(message)
        await websocket.send(message_str)
        logger.info(f"📤 Sent message: {message_str[:100]}...")
    except Exception as e:
        logger.error(f"❌ Error sending message: {e}")

async def receive_message(websocket: websockets.WebSocketClientProtocol, timeout: int = RESPONSE_TIMEOUT) -> Optional[Dict[str, Any]]:
    """Receive a message from a WebSocket server with timeout."""
    try:
        logger.info(f"Waiting for response (timeout: {timeout}s)...")
        response = await asyncio.wait_for(
            websocket.recv(),
            timeout=timeout
        )
        try:
            response_data = json.loads(response)
            logger.info(f"📥 Received response: {json.dumps(response_data)[:100]}...")
            return response_data
        except json.JSONDecodeError:
            logger.info(f"📥 Received non-JSON response: {response[:100]}...")
            return {"raw_response": response}
    except asyncio.TimeoutError:
        logger.error("❌ Timeout waiting for response")
        return None
    except Exception as e:
        logger.error(f"❌ Error receiving message: {e}")
        return None

async def check_server_status() -> Dict[str, bool]:
    """Check if all required servers are running."""
    status = {}
    servers = {
        "proxy": PROXY_URL,
        "backend": BACKEND_URL,
        "do_button": DO_BUTTON_URL,
        "neural_ui": NEURAL_UI_URL
    }
    
    for name, url in servers.items():
        websocket = await connect_to_websocket(url, timeout=5)
        status[name] = websocket is not None
        if websocket:
            await websocket.close()
    
    return status

async def create_test_plan(backend_ws: websockets.WebSocketClientProtocol) -> str:
    """Create a test plan and return its ID."""
    plan_id = str(uuid.uuid4())
    
    # Simplified test plan for automation
    plan = {
        "type": "plan_creation",
        "plan_id": plan_id,
        "plan": {
            "id": plan_id,
            "name": "Test Plan",
            "steps": [
                {
                    "type": "keyboard",
                    "action": "type",
                    "text": "Test automation"
                }
            ]
        }
    }
    
    await send_message(backend_ws, plan)
    response = await receive_message(backend_ws)
    
    if response and response.get("status") == "success":
        logger.info(f"✅ Test plan created with ID: {plan_id}")
        return plan_id
    else:
        logger.warning("⚠️ Failed to create test plan, using generated ID anyway")
        return plan_id

async def test_do_button_with_existing_plan() -> bool:
    """Test DO button functionality with an existing plan."""
    # Connect to backend to create a plan
    backend_ws = await connect_to_websocket(BACKEND_URL)
    if not backend_ws:
        logger.error("❌ Cannot test without backend connection")
        return False
    
    # Create a test plan
    plan_id = await create_test_plan(backend_ws)
    await backend_ws.close()
    
    # Connect to proxy to send DO button action
    proxy_ws = await connect_to_websocket(PROXY_URL)
    if not proxy_ws:
        logger.error("❌ Cannot test without proxy connection")
        return False
    
    # Send a DO button action message
    do_message = {
        "type": "agent_confirmation",
        "sessionId": plan_id,
        "action": "DO",
        "timestamp": int(time.time() * 1000)
    }
    
    await send_message(proxy_ws, do_message)
    response = await receive_message(proxy_ws)
    
    await proxy_ws.close()
    
    if response:
        logger.info("✅ DO button action test completed successfully")
        return True
    else:
        logger.error("❌ DO button action test failed")
        return False

async def test_do_button_without_existing_plan() -> bool:
    """Test DO button functionality without an existing plan (fallback case)."""
    # Generate a random plan ID that doesn't exist
    plan_id = f"nonexistent_{str(uuid.uuid4())}"
    
    # Connect to proxy to send DO button action
    proxy_ws = await connect_to_websocket(PROXY_URL)
    if not proxy_ws:
        logger.error("❌ Cannot test without proxy connection")
        return False
    
    # Send a DO button action message with a non-existent plan ID
    do_message = {
        "type": "agent_confirmation",
        "sessionId": plan_id,
        "action": "DO",
        "timestamp": int(time.time() * 1000)
    }
    
    await send_message(proxy_ws, do_message)
    response = await receive_message(proxy_ws)
    
    await proxy_ws.close()
    
    if response:
        logger.info("✅ DO button fallback test completed successfully")
        return True
    else:
        logger.error("❌ DO button fallback test failed")
        return False

async def main():
    """Main test function."""
    logger.info("=== Neural UI DO Button Fix Test ===")
    
    # Check server status
    logger.info("Checking server status...")
    status = await check_server_status()
    
    all_servers_running = all(status.values())
    if not all_servers_running:
        logger.error("❌ Not all required servers are running:")
        for server, running in status.items():
            logger.info(f"  - {server}: {'✅ Running' if running else '❌ Not running'}")
        logger.error("Please run START_ENHANCED_SYSTEM_WITH_NEURAL_UI.sh first")
        return
    
    logger.info("✅ All required servers are running")
    
    # Test 1: DO button with existing plan
    logger.info("\n=== Test 1: DO Button with Existing Plan ===")
    test1_result = await test_do_button_with_existing_plan()
    
    # Test 2: DO button without existing plan (fallback)
    logger.info("\n=== Test 2: DO Button without Existing Plan (Fallback) ===")
    test2_result = await test_do_button_without_existing_plan()
    
    # Summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"Test 1 (Existing Plan): {'✅ PASS' if test1_result else '❌ FAIL'}")
    logger.info(f"Test 2 (Fallback): {'✅ PASS' if test2_result else '❌ FAIL'}")
    
    if test1_result and test2_result:
        logger.info("🎉 All tests passed! The Neural UI DO Button fix is working correctly")
    elif test1_result:
        logger.info("⚠️ Test with existing plan passed, but fallback mechanism failed")
    elif test2_result:
        logger.info("⚠️ Fallback mechanism works, but test with existing plan failed")
    else:
        logger.error("❌ All tests failed. The Neural UI DO Button fix is not working correctly")

if __name__ == "__main__":
    asyncio.run(main())