#!/usr/bin/env python3
"""
Test Agent mode to verify it's now working properly after the fix.
"""

import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('test_agent_mode')

async def test_agent_mode():
    """Test Agent mode with a simple automation command"""
    try:
        # Connect to the backend
        uri = "ws://localhost:8767"
        logger.info(f"Connecting to {uri}")
        
        async with websockets.connect(uri) as websocket:
            # Wait for welcome message
            welcome = await websocket.recv()
            logger.info(f"Received: {welcome}")
            
            # Send Agent mode message
            test_message = {
                "type": "chat_request",
                "message": "write my name in notepad",
                "mode": "Agent",
                "client_id": "test_client",
                "timestamp": "2025-05-23T17:02:00.000Z"
            }
            
            logger.info(f"Sending Agent mode test: {test_message['message']}")
            await websocket.send(json.dumps(test_message))
            
            # Wait for response with timeout
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                response_data = json.loads(response)
                
                logger.info(f"✅ Received response: {response_data.get('type', 'unknown')}")
                
                if response_data.get("automation_executed"):
                    logger.info("🎯 AGENT MODE AUTOMATION EXECUTED!")
                    logger.info(f"   Success: {response_data.get('success', False)}")
                    logger.info(f"   Response: {response_data.get('response', 'N/A')[:100]}...")
                elif "agent" in response_data.get("response", "").lower():
                    logger.info("🤖 LLM response received (automation may have failed)")
                    logger.info(f"   Response: {response_data.get('response', 'N/A')[:100]}...")
                else:
                    logger.info("📝 Generic response received")
                    logger.info(f"   Response: {response_data.get('response', 'N/A')[:100]}...")
                
                return response_data
                
            except asyncio.TimeoutError:
                logger.error("❌ No response received within 30 seconds")
                return {"error": "timeout"}
                
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return {"error": str(e)}

async def main():
    logger.info("🧪 Testing Agent Mode Fix")
    logger.info("=" * 40)
    
    result = await test_agent_mode()
    
    logger.info("\n" + "=" * 40)
    if result.get("automation_executed"):
        logger.info("🎉 SUCCESS: Agent mode automation is working!")
    elif result.get("error"):
        logger.info(f"💥 FAILED: {result['error']}")
    else:
        logger.info("⚠️  PARTIAL: Got response but no automation execution")
    
    return result

if __name__ == "__main__":
    asyncio.run(main())