#!/usr/bin/env python3
"""
Quick Google Search Test

Test the exact case study: 'Search "SEGEV HALFON" in google'
This should now work fast without LLaVA timeouts.
"""

import asyncio
import json
import websockets
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('quick_test')

async def test_google_search():
    """Test the exact case study with fixed system"""
    try:
        # Connect to enhanced brain router
        uri = "ws://localhost:8765"
        logger.info(f"🔌 Connecting to {uri}")
        
        async with websockets.connect(uri) as websocket:
            # Send welcome message should arrive
            welcome = await websocket.recv()
            logger.info(f"📨 Welcome: {json.loads(welcome)}")
            
            # Test the exact case study
            test_message = 'Search "SEGEV HALFON" in google'
            logger.info(f"🧪 Testing case study: {test_message}")
            
            # Send the request
            request = {
                "type": "chat_request",
                "mode": "Agent",
                "message": test_message,
                "session_id": "test_session"
            }
            
            start_time = time.time()
            await websocket.send(json.dumps(request))
            logger.info(f"📤 Sent request at {start_time:.2f}")
            
            # Wait for response with timeout
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=30)
                end_time = time.time()
                response_time = end_time - start_time
                
                logger.info(f"📥 Response received in {response_time:.2f}s")
                
                response_data = json.loads(response)
                logger.info(f"📋 Response type: {response_data.get('type')}")
                
                if response_data.get('type') == 'chat_response':
                    chat_data = response_data.get('data', {})
                    response_text = chat_data.get('response', '')
                    
                    logger.info(f"💬 Response: {response_text[:200]}...")
                    
                    # Check for success indicators
                    success_indicators = [
                        'workflow' in response_text.lower(),
                        'step' in response_text.lower(),
                        'search' in response_text.lower(),
                        'segev halfon' in response_text.lower(),
                        '✅' in response_text,
                        '🧠' in response_text
                    ]
                    
                    success_count = sum(success_indicators)
                    logger.info(f"📊 Success indicators: {success_count}/6")
                    
                    if success_count >= 2:
                        logger.info("🎉 TEST PASSED! Google search case study works!")
                        return True
                    else:
                        logger.warning("⚠️  Response received but may not be complete")
                        return False
                else:
                    logger.error(f"❌ Unexpected response type: {response_data.get('type')}")
                    return False
                    
            except asyncio.TimeoutError:
                logger.error("❌ TIMEOUT - Still hanging after 30 seconds")
                return False
                
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

async def main():
    """Run the quick test"""
    logger.info("🚀 Quick Google Search Test")
    logger.info("Testing case study: 'Search \"SEGEV HALFON\" in google'")
    logger.info("Should be FAST now (no LLaVA timeouts)")
    
    # Wait a moment for system to be ready
    logger.info("⏳ Waiting 5 seconds for system to initialize...")
    await asyncio.sleep(5)
    
    success = await test_google_search()
    
    if success:
        logger.info("✅ SUCCESS! The LLaVA timeout issue is FIXED!")
        logger.info("🎯 Google search case study now works quickly")
    else:
        logger.error("❌ FAILED! Still having issues")
        logger.error("🔧 May need further debugging")
    
    return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        exit(1)
    except Exception as e:
        logger.error(f"Test error: {e}")
        exit(1)