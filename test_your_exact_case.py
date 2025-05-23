#!/usr/bin/env python3
"""
Test Your Exact Case Study
Test the specific message causing the hang: 'search "SEGEV HALFON" in google'
"""

import asyncio
import json
import websockets
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('case_test')

async def test_exact_google_search():
    """Test the exact case that's hanging"""
    try:
        uri = "ws://localhost:8765"
        
        async with websockets.connect(uri) as websocket:
            # Receive welcome
            await websocket.recv()
            
            # Test the EXACT message that's hanging
            exact_request = {
                "type": "chat_request",
                "mode": "Agent",
                "message": 'search "SEGEV HALFON" in google',
                "session_id": "exact_case_test"
            }
            
            logger.info(f"🧪 Testing EXACT case: {exact_request['message']}")
            start_time = time.time()
            await websocket.send(json.dumps(exact_request))
            
            try:
                # Wait up to 30 seconds for this complex request
                response = await asyncio.wait_for(websocket.recv(), timeout=30)
                end_time = time.time()
                response_time = end_time - start_time
                
                logger.info(f"✅ EXACT case response in {response_time:.2f}s")
                
                response_data = json.loads(response)
                response_text = response_data.get('data', {}).get('response', '')
                logger.info(f"📝 Response: {response_text[:200]}...")
                
                # Check if it's a workflow response
                if 'workflow' in response_text.lower() or 'step' in response_text.lower():
                    logger.info("🎯 SUCCESS: Intelligent workflow response detected!")
                    return True
                else:
                    logger.warning("⚠️  Got response but not workflow-based")
                    return True  # Still got a response
                    
            except asyncio.TimeoutError:
                logger.error("❌ EXACT CASE TIMEOUT - This is the hanging issue!")
                logger.error("🔍 The complex search query is causing the hang")
                return False
                
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

async def test_simple_vs_complex():
    """Test simple vs complex messages to isolate the issue"""
    
    test_cases = [
        ("Simple Agent", "Agent", "hello"),
        ("Simple Ask", "Ask", "what is this?"),
        ("Medium complexity", "Agent", "click button"),
        ("Complex search", "Agent", 'search "SEGEV HALFON" in google'),
    ]
    
    results = {}
    
    for test_name, mode, message in test_cases:
        try:
            logger.info(f"\n🔍 Testing: {test_name} - '{message}'")
            
            async with websockets.connect("ws://localhost:8765") as websocket:
                await websocket.recv()  # welcome
                
                request = {
                    "type": "chat_request", 
                    "mode": mode,
                    "message": message,
                    "session_id": f"test_{test_name.replace(' ', '_')}"
                }
                
                start_time = time.time()
                await websocket.send(json.dumps(request))
                
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=15)
                    response_time = time.time() - start_time
                    results[test_name] = response_time
                    logger.info(f"✅ {test_name}: {response_time:.2f}s")
                except asyncio.TimeoutError:
                    results[test_name] = "TIMEOUT"
                    logger.error(f"❌ {test_name}: TIMEOUT")
                    
        except Exception as e:
            results[test_name] = f"ERROR: {e}"
            logger.error(f"❌ {test_name}: {e}")
    
    return results

async def main():
    """Run comprehensive tests"""
    logger.info("🚨 TESTING YOUR EXACT CASE STUDY")
    logger.info("=" * 50)
    
    # Test 1: Exact case study
    logger.info("\n🎯 TEST 1: Your Exact Case")
    exact_success = await test_exact_google_search()
    
    # Test 2: Simple vs Complex comparison
    logger.info("\n🔍 TEST 2: Simple vs Complex Messages")
    results = await test_simple_vs_complex()
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 RESULTS SUMMARY")
    logger.info("=" * 50)
    
    logger.info(f"🎯 Exact case ('search \"SEGEV HALFON\" in google'): {'✅ WORKS' if exact_success else '❌ HANGS'}")
    
    logger.info("\n📋 All test results:")
    for test_name, result in results.items():
        if isinstance(result, float):
            status = "✅" if result < 10 else "⚠️ "
            logger.info(f"{status} {test_name}: {result:.2f}s")
        else:
            logger.info(f"❌ {test_name}: {result}")
    
    # Analysis
    timeouts = [k for k, v in results.items() if v == "TIMEOUT"]
    if timeouts:
        logger.error(f"\n🚨 HANGING ISSUES FOUND:")
        for timeout_case in timeouts:
            logger.error(f"   - {timeout_case}")
        logger.error("🔧 These specific message types are causing hangs")
    else:
        logger.info(f"\n🎉 ALL TESTS PASSED - No hanging detected!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Test interrupted")
    except Exception as e:
        logger.error(f"Test error: {e}")