#!/usr/bin/env python3

import asyncio
import websockets
import json
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_agent_mode_condition():
    """Test Agent Mode to see debug output about condition triggering"""
    
    uri = "ws://localhost:8767/ws"
    
    try:
        logger.info("🔌 Connecting to backend...")
        async with websockets.connect(uri) as websocket:
            logger.info("✅ Connected to backend")
            
            # Wait for connection_established
            logger.info("⏳ Waiting for connection_established...")
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(response)
                    logger.info(f"📨 Received: {data}")
                    
                    if data.get("type") == "connection_established":
                        logger.info("✅ Connection established")
                        break
                        
                except asyncio.TimeoutError:
                    logger.warning("⚠️ Timeout waiting for connection_established")
                    break
            
            # Test Agent Mode with debug logging
            logger.info("🤖 Testing Agent Mode condition debugging...")
            
            test_message = {
                "type": "chat_request",
                "mode": "agent", 
                "message": "open youtube and search for AI"
            }
            
            logger.info(f"📤 Sending Agent Mode test: {test_message}")
            await websocket.send(json.dumps(test_message))
            
            # Wait for response with debug logs
            logger.info("⏳ Waiting for Agent Mode response with debug output...")
            start_time = time.time()
            
            while time.time() - start_time < 30:  # 30 second timeout
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(response)
                    
                    logger.info(f"📨 Agent Mode Response: {data}")
                    
                    # Check if this is the final response
                    if data.get("type") in ["response", "agent_response", "error"]:
                        logger.info("✅ Got final Agent Mode response")
                        
                        # Check if it contains automation plans or buttons
                        if "execution_plan" in data:
                            logger.info("🎯 Agent Mode triggered successfully - has execution_plan")
                        elif "buttons" in data:
                            logger.info("🎯 Agent Mode triggered successfully - has buttons")
                        else:
                            logger.warning("⚠️ Agent Mode may not have triggered - no execution_plan or buttons")
                            
                        break
                        
                except asyncio.TimeoutError:
                    logger.info("⏳ Still waiting for Agent Mode response...")
                    continue
                except Exception as e:
                    logger.error(f"❌ Error receiving response: {e}")
                    break
            
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    logger.info("🧪 Testing Agent Mode Condition Debugging")
    logger.info("🔍 Looking for debug output about why Agent mode condition isn't triggered")
    asyncio.run(test_agent_mode_condition())