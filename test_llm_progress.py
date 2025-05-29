#!/usr/bin/env python3
"""
Test if LLM is actually processing with progress monitoring
"""

import asyncio
import json
import websockets
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('test_llm_progress')

async def test_with_progress():
    """Test with periodic progress checks"""
    try:
        uri = "ws://localhost:8767"
        logger.info(f"Connecting to {uri}")
        
        async with websockets.connect(uri) as websocket:
            welcome = await websocket.recv()
            logger.info("Connected successfully")
            
            # Send simpler Agent mode request
            test_message = {
                "type": "chat_request",
                "message": "open notepad",
                "mode": "Agent", 
                "client_id": "test_client",
                "timestamp": "2025-05-27T12:00:00.000Z"
            }
            
            logger.info(f"🧪 Testing simpler automation: '{test_message['message']}'")
            start_time = time.time()
            await websocket.send(json.dumps(test_message))
            
            # Try to get response with progress monitoring
            for attempt in range(1, 10):  # Check every 10 seconds for 90 seconds total
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    elapsed = time.time() - start_time
                    
                    logger.info(f"✅ Response received after {elapsed:.1f}s")
                    response_data = json.loads(response)
                    
                    response_text = response_data.get('response', '')
                    
                    # Check what type of response we got
                    if "FAST AUTOMATION PLAN" in response_text:
                        logger.error("❌ Got mock template (this shouldn't happen)")
                        return {"success": False, "type": "mock"}
                    elif "automation" in response_text.lower() and len(response_text) > 50:
                        logger.info("🎯 SUCCESS: Got real automation plan!")
                        logger.info(f"   Response length: {len(response_text)} chars")
                        logger.info(f"   First 200 chars: {response_text[:200]}...")
                        return {"success": True, "type": "real_automation", "time": elapsed}
                    else:
                        logger.info(f"📝 Got response: {response_text[:100]}...")
                        return {"success": "partial", "response": response_text}
                        
                except asyncio.TimeoutError:
                    elapsed = time.time() - start_time
                    logger.info(f"⏳ Still waiting... {elapsed:.1f}s elapsed (attempt {attempt}/9)")
                    continue
                    
            # Final timeout
            logger.error("❌ No response after 90 seconds")
            return {"success": False, "type": "timeout"}
                
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return {"success": False, "error": str(e)}

async def main():
    logger.info("🧪 Testing LLM Progress with Simpler Request")
    logger.info("=" * 50)
    
    result = await test_with_progress()
    
    logger.info("\n" + "=" * 50)
    logger.info("🔍 FINAL RESULT:")
    
    if result.get("success") is True:
        logger.info("🎉 SUCCESS: Universal handler is working with real LLM!")
        logger.info(f"   Response time: {result.get('time', 'unknown')}s")
    elif result.get("type") == "timeout":
        logger.info("⏱️  TIMEOUT: LLM is processing but very slow")
        logger.info("   This confirms real LLM calls are being made")
        logger.info("   Consider using a faster model or reducing complexity")
    else:
        logger.info(f"❓ UNCLEAR: {result}")
    
    return result

if __name__ == "__main__":
    asyncio.run(main())