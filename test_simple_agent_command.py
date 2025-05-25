#!/usr/bin/env python3
"""
Test simpler Agent commands that should work with current screen elements.
"""

import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('test_simple_agent')

async def test_simple_commands():
    """Test Agent mode with simpler commands that should work"""
    
    commands_to_test = [
        "click the close button",
        "click the python button",  # We saw this button in earlier tests
        "click the first button on screen"
    ]
    
    try:
        uri = "ws://localhost:8767"
        
        for command in commands_to_test:
            logger.info(f"\n🧪 Testing command: '{command}'")
            
            async with websockets.connect(uri) as websocket:
                # Wait for welcome
                await websocket.recv()
                
                # Send command
                test_message = {
                    "type": "chat_request",
                    "message": command,
                    "mode": "Agent",
                    "client_id": "test_simple",
                    "timestamp": "2025-05-23T17:03:00.000Z"
                }
                
                await websocket.send(json.dumps(test_message))
                
                # Wait for response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                    response_data = json.loads(response)
                    
                    if response_data.get("automation_executed"):
                        logger.info("✅ AUTOMATION EXECUTED!")
                        logger.info(f"   Success: {response_data.get('success', False)}")
                    else:
                        logger.info("⚠️ No automation execution")
                        
                    logger.info(f"   Response type: {response_data.get('type', 'unknown')}")
                    
                except asyncio.TimeoutError:
                    logger.error("❌ Timeout waiting for response")
                
                await asyncio.sleep(2)  # Brief pause between tests
                
    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple_commands())