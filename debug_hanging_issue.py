#!/usr/bin/env python3
"""
Debug Hanging Issue

Find exactly where the processing is hanging.
"""

import asyncio
import json
import websockets
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('debug')

async def debug_message_processing():
    """Send a message and trace exactly where it hangs"""
    try:
        uri = "ws://localhost:8765"
        logger.info(f"🔌 Connecting to {uri}")
        
        async with websockets.connect(uri) as websocket:
            # Receive welcome
            welcome = await websocket.recv()
            logger.info(f"📨 Welcome received: {json.loads(welcome)['type']}")
            
            # Send simple Ask mode request (should be fastest)
            simple_request = {
                "type": "chat_request",
                "mode": "Ask",
                "message": "hello",
                "session_id": "debug_session"
            }
            
            logger.info(f"📤 Sending simple Ask request...")
            start_time = time.time()
            await websocket.send(json.dumps(simple_request))
            logger.info(f"📤 Message sent at {time.time() - start_time:.2f}s")
            
            # Wait with very short timeout to see if ANY response comes back
            try:
                logger.info("⏳ Waiting for response (10s timeout)...")
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                end_time = time.time()
                logger.info(f"📥 Response received in {end_time - start_time:.2f}s: {response[:100]}...")
                return True
            except asyncio.TimeoutError:
                logger.error("❌ TIMEOUT - No response in 10 seconds")
                logger.error("🔍 The hang is definitely in the message processing pipeline")
                return False
                
    except Exception as e:
        logger.error(f"❌ Debug failed: {e}")
        return False

async def debug_agent_mode():
    """Test Agent mode specifically"""
    try:
        uri = "ws://localhost:8765"
        
        async with websockets.connect(uri) as websocket:
            # Receive welcome
            await websocket.recv()
            
            # Send Agent mode request
            agent_request = {
                "type": "chat_request",
                "mode": "Agent", 
                "message": "hello",
                "session_id": "debug_agent"
            }
            
            logger.info(f"📤 Sending Agent mode request...")
            start_time = time.time()
            await websocket.send(json.dumps(agent_request))
            
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=15)
                end_time = time.time()
                logger.info(f"📥 Agent response in {end_time - start_time:.2f}s: {response[:100]}...")
                return True
            except asyncio.TimeoutError:
                logger.error("❌ Agent mode TIMEOUT")
                return False
                
    except Exception as e:
        logger.error(f"❌ Agent debug failed: {e}")
        return False

async def main():
    """Run debugging tests"""
    logger.info("🚨 DEBUGGING HANGING ISSUE")
    logger.info("=" * 50)
    
    # Test 1: Simple Ask mode
    logger.info("\n🔍 TEST 1: Simple Ask Mode")
    ask_success = await debug_message_processing()
    
    if not ask_success:
        logger.error("❌ Ask mode is hanging - this is a core processing issue")
    else:
        logger.info("✅ Ask mode works - issue may be mode-specific")
    
    # Test 2: Agent mode
    logger.info("\n🔍 TEST 2: Agent Mode")
    agent_success = await debug_agent_mode()
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 DEBUG SUMMARY")
    logger.info("=" * 50)
    
    if not ask_success and not agent_success:
        logger.error("❌ ALL MODES HANGING - Core processing pipeline issue")
        logger.error("🔍 Likely causes:")
        logger.error("   1. get_context_for_query() hanging in semantic search")
        logger.error("   2. Memory system initialization hanging")
        logger.error("   3. WebSocket message handler not processing properly")
    elif not agent_success:
        logger.error("❌ Agent mode specific issue - likely automation engine")
    else:
        logger.info("✅ Basic modes work - issue resolved")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Debug interrupted")
    except Exception as e:
        logger.error(f"Debug error: {e}")