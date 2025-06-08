#!/usr/bin/env python3
"""
Test script for Enhanced Enterprise Backend
Tests WebSocket connection and message handling in a single session
"""

import asyncio
import json
import logging
import websockets
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def is_intermediate_message(msg_type):
    # Add all known intermediate types here
    return msg_type in {"agent_status_update", "progress_update", "heartbeat", "status"}

async def wait_for_response(websocket, expected_type):
    """Wait for a specific message type, skipping intermediate ones"""
    while True:
        response = await websocket.recv()
        data = json.loads(response)
        msg_type = data.get("type")
        if msg_type == expected_type:
            return data
        elif is_intermediate_message(msg_type):
            logger.info(f"(intermediate) {msg_type}: {data}")
        else:
            logger.warning(f"(unexpected) {msg_type}: {data}")

async def run_tests():
    """Run all tests in a single persistent connection"""
    uri = "ws://localhost:8765"
    logger.info(f"Connecting to {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            # Wait for connection message
            data = await wait_for_response(websocket, "connection_established")
            logger.info("✅ Connection established successfully")
            connection_id = data.get("connection_id")

            # Send registration message
            await websocket.send(json.dumps({
                "type": "register",
                "client_type": "test_client",
                "timestamp": datetime.now().isoformat()
            }))
            data = await wait_for_response(websocket, "registration_success")
            logger.info("✅ Registration successful")

            # Send agent request
            await websocket.send(json.dumps({
                "type": "agent_request",
                "message": "Test agent request",
                "timestamp": datetime.now().isoformat()
            }))
            data = await wait_for_response(websocket, "agent_response_enterprise")
            logger.info("✅ Agent request handled successfully")

            # Send ask request
            await websocket.send(json.dumps({
                "type": "ask_request",
                "message": "Test ask request",
                "timestamp": datetime.now().isoformat()
            }))
            data = await wait_for_response(websocket, "ask_response_enterprise")
            logger.info("✅ Ask request handled successfully")

            logger.info("✅ All tests completed successfully!")
    except Exception as e:
        logger.error(f"❌ Test session failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_tests()) 