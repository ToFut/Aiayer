#!/usr/bin/env python3
"""
Test Fast Agent Mode Response Times
Validates that agent mode planning is now fast
"""

import asyncio
import websockets
import json
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_fast_agent_responses():
    """Test that agent mode responses are now fast"""
    logger.info("🧪 Testing Fast Agent Mode Response Times...")
    
    try:
        # Connect to enhanced backend
        uri = "ws://localhost:8765"
        async with websockets.connect(uri) as websocket:
            logger.info("✅ Connected to backend")
            
            # Test agent queries
            test_queries = [
                {"query": "Open Calculator app", "expected_time": 15},
                {"query": "Search Google for AI news", "expected_time": 15},
                {"query": "Open Safari and go to github.com", "expected_time": 20}
            ]
            
            successful_tests = 0
            total_tests = len(test_queries)
            
            for i, test in enumerate(test_queries, 1):
                logger.info(f"\n🧪 Agent Test {i}: '{test['query']}'")
                
                # Send agent mode request
                start_time = time.time()
                request_id = f"agent_test_{int(time.time() * 1000)}"
                
                message = {
                    "type": "chat_request",
                    "mode": "agent",
                    "message": test['query'],
                    "client_id": request_id,
                    "timestamp": start_time
                }
                
                await websocket.send(json.dumps(message))
                
                # Wait for planning response
                planning_completed = False
                while not planning_completed:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=30)
                        data = json.loads(response)
                        
                        # Check for planning completion or buttons
                        if (data.get("type") in ["final_response", "suggestion"] and 
                            data.get("client_id") == request_id and
                            ("buttons" in data or "interactive" in data)):
                            
                            planning_time = time.time() - start_time
                            response_text = data.get("response", data.get("content", ""))
                            
                            logger.info(f"⚡ Agent planning completed in {planning_time:.2f}s")
                            logger.info(f"📋 Plan: {response_text[:150]}...")
                            
                            # Check if planning meets speed expectations
                            if planning_time <= test['expected_time']:
                                if planning_time <= 10:
                                    logger.info(f"🚀 EXCELLENT: Agent planning within 10s")
                                else:
                                    logger.info(f"✅ GOOD: Agent planning within {test['expected_time']}s")
                                successful_tests += 1
                            else:
                                logger.error(f"❌ TOO SLOW: Agent planning took {planning_time:.2f}s (expected ≤{test['expected_time']}s)")
                            
                            planning_completed = True
                            break
                            
                    except asyncio.TimeoutError:
                        logger.error(f"❌ TIMEOUT: No agent response received within 30s")
                        break
                    except Exception as e:
                        logger.error(f"❌ Error receiving response: {e}")
                        break
                
                # Small delay between tests
                await asyncio.sleep(2)
            
            # Summary
            logger.info(f"\n📊 FAST AGENT MODE TEST RESULTS:")
            logger.info(f"   Successful: {successful_tests}/{total_tests}")
            logger.info(f"   Success Rate: {(successful_tests/total_tests)*100:.1f}%")
            
            if successful_tests == total_tests:
                logger.info("🎉 SUCCESS: All agent planning is now FAST!")
                logger.info("✅ Agent mode meets speed expectations")
            elif successful_tests > 0:
                logger.info("⚠️ PARTIAL SUCCESS: Some agent responses improved")
            else:
                logger.error("❌ FAILED: Agent responses still too slow")
                
    except Exception as e:
        logger.error(f"❌ Test error: {e}")

async def main():
    """Main test function"""
    logger.info("🚀 Fast Agent Mode Test Starting...")
    logger.info("Expected: Agent planning should be ≤15s, ideally ≤10s")
    
    await test_fast_agent_responses()
    
    logger.info("\n🏁 Fast Agent Mode Test Complete")

if __name__ == "__main__":
    asyncio.run(main())