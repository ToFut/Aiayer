#!/usr/bin/env python3
"""
Test Fixed Message Flow
Test the corrected message format between frontend and backend
"""

import asyncio
import json
import logging
import websockets
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_corrected_message_format():
    """Test with the corrected message format"""
    
    logger.info("🧪 Testing CORRECTED message format...")
    
    try:
        async with websockets.connect("ws://localhost:8765") as websocket:
            logger.info("✅ Connected to brain router")
            
            # Wait for welcome message
            welcome = await asyncio.wait_for(websocket.recv(), timeout=5)
            logger.info(f"📬 Welcome: {json.loads(welcome).get('type')}")
            
            # Test with CORRECTED format that matches what the frontend now sends
            corrected_message = {
                "type": "chat_request",  # Correct: brain router expects this
                "mode": "Ask",           # Correct: brain router expects this
                "message": "hello world",
                "session_id": "test_corrected_format"
            }
            
            logger.info("📤 Sending CORRECTED format message...")
            logger.info(f"📝 Message: {corrected_message}")
            
            await websocket.send(json.dumps(corrected_message))
            
            try:
                start_time = time.time()
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                elapsed = time.time() - start_time
                
                response_data = json.loads(response)
                logger.info(f"✅ Response received in {elapsed:.2f}s")
                logger.info(f"📝 Response success: {response_data.get('success')}")
                logger.info(f"📝 Response mode: {response_data.get('mode')}")
                logger.info(f"📝 Response content: {response_data.get('response', '')[:100]}...")
                
                if response_data.get('success'):
                    logger.info("🎉 MESSAGE FORMAT FIX SUCCESSFUL!")
                else:
                    logger.error("❌ Still getting errors in response")
                    
            except asyncio.TimeoutError:
                logger.error("❌ Still timing out with corrected format")
                
    except Exception as e:
        logger.error(f"❌ Connection error: {e}")

async def test_old_vs_new_format():
    """Compare old (broken) vs new (fixed) format"""
    
    logger.info("\n🧪 Testing OLD vs NEW message formats...")
    
    try:
        async with websockets.connect("ws://localhost:8765") as websocket:
            # Wait for welcome
            await websocket.recv()
            
            # Test 1: OLD FORMAT (what frontend was sending before fix)
            logger.info("\n📤 Testing OLD (broken) format...")
            old_format = {
                "type": "ask_request",  # WRONG: brain router doesn't recognize this
                "message": "test old format",
                "user_id": "test_user",
                "session_id": "old_format_test"
            }
            
            await websocket.send(json.dumps(old_format))
            
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                logger.info("❌ Old format unexpectedly got response")
            except asyncio.TimeoutError:
                logger.info("✅ Old format correctly timed out (as expected)")
            
            # Test 2: NEW FORMAT (what frontend sends after fix)
            logger.info("\n📤 Testing NEW (fixed) format...")
            new_format = {
                "type": "chat_request",  # CORRECT: brain router recognizes this
                "mode": "Ask",          # CORRECT: brain router expects this
                "message": "test new format",
                "session_id": "new_format_test"
            }
            
            await websocket.send(json.dumps(new_format))
            
            try:
                start_time = time.time()
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                elapsed = time.time() - start_time
                
                response_data = json.loads(response)
                logger.info(f"✅ New format got response in {elapsed:.2f}s")
                logger.info(f"📝 Success: {response_data.get('success')}")
                
            except asyncio.TimeoutError:
                logger.error("❌ New format still timing out - deeper issue")
                
    except Exception as e:
        logger.error(f"❌ Comparison test error: {e}")

async def main():
    """Run all tests"""
    
    print("=" * 60)
    print("🔧 TESTING MESSAGE FORMAT FIX")
    print("=" * 60)
    print("Issue: Frontend was sending 'ask_request' but backend expects 'chat_request'")
    print("Fix: Updated frontend to send correct format")
    print("=" * 60)
    
    await test_corrected_message_format()
    await test_old_vs_new_format()
    
    print("\n" + "=" * 60)
    print("📊 FIX VERIFICATION RESULTS")
    print("=" * 60)
    print("If new format works and old format times out:")
    print("✅ MESSAGE FORMAT FIX IS SUCCESSFUL")
    print("🎯 Frontend should now display responses instead of hanging")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())