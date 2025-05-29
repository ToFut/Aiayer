#!/usr/bin/env python3
"""
Test Fast System Response Times
Validates that AI responses now come within 10 seconds as expected
"""

import asyncio
import websockets
import json
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_fast_responses():
    """Test that AI responses are now fast"""
    logger.info("🧪 Testing Fast AI Response System...")
    
    try:
        # Connect to enhanced backend
        uri = "ws://localhost:8765"
        async with websockets.connect(uri) as websocket:
            logger.info("✅ Connected to backend")
            
            # Test queries
            test_queries = [
                {"query": "Hello", "mode": "ask", "expected_time": 10},
                {"query": "What is 5+3?", "mode": "ask", "expected_time": 10},
                {"query": "Explain Python briefly", "mode": "suggest", "expected_time": 10}
            ]
            
            successful_tests = 0
            total_tests = len(test_queries)
            
            for i, test in enumerate(test_queries, 1):
                logger.info(f"\n🧪 Test {i}: '{test['query']}' (mode: {test['mode']})")
                
                # Send request
                start_time = time.time()
                request_id = f"test_{int(time.time() * 1000)}"
                
                message = {
                    "type": "chat_request",
                    "mode": test['mode'],
                    "message": test['query'],
                    "client_id": request_id,
                    "timestamp": start_time
                }
                
                await websocket.send(json.dumps(message))
                
                # Wait for response
                response_received = False
                while not response_received:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=30)
                        data = json.loads(response)
                        
                        # Check for final response or stream complete
                        if (data.get("type") in ["final_response", "stream_complete"] and 
                            data.get("client_id") == request_id):
                            
                            response_time = time.time() - start_time
                            response_text = data.get("response", data.get("full_response", ""))
                            
                            logger.info(f"⚡ Response in {response_time:.2f}s: {response_text[:100]}...")
                            
                            # Check if response meets speed expectations
                            if response_time <= test['expected_time']:
                                if response_time <= 5:
                                    logger.info(f"🚀 EXCELLENT: Response within 5s")
                                else:
                                    logger.info(f"✅ GOOD: Response within {test['expected_time']}s")
                                successful_tests += 1
                            else:
                                logger.error(f"❌ TOO SLOW: Response took {response_time:.2f}s (expected ≤{test['expected_time']}s)")
                            
                            response_received = True
                            break
                            
                    except asyncio.TimeoutError:
                        logger.error(f"❌ TIMEOUT: No response received within 30s")
                        break
                    except Exception as e:
                        logger.error(f"❌ Error receiving response: {e}")
                        break
                
                # Small delay between tests
                await asyncio.sleep(1)
            
            # Summary
            logger.info(f"\n📊 FAST RESPONSE TEST RESULTS:")
            logger.info(f"   Successful: {successful_tests}/{total_tests}")
            logger.info(f"   Success Rate: {(successful_tests/total_tests)*100:.1f}%")
            
            if successful_tests == total_tests:
                logger.info("🎉 SUCCESS: All responses are now FAST!")
                logger.info("✅ ollama3.2:1b is responding within expected timeframes")
            elif successful_tests > 0:
                logger.info("⚠️ PARTIAL SUCCESS: Some responses improved")
            else:
                logger.error("❌ FAILED: Responses still too slow")
                
    except Exception as e:
        logger.error(f"❌ Test error: {e}")

async def main():
    """Main test function"""
    logger.info("🚀 Fast System Test Starting...")
    logger.info("Expected: All AI responses should be ≤10s, ideally ≤5s")
    
    await test_fast_responses()
    
    logger.info("\n🏁 Fast System Test Complete")

if __name__ == "__main__":
    asyncio.run(main())