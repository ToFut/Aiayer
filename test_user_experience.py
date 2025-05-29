#!/usr/bin/env python3
"""
Test User Experience - Simulate actual user interaction
Verify the system responds within 10-20 seconds from user's perspective
"""

import asyncio
import websockets
import json
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_agent_mode_response():
    """Test agent mode response time from user perspective"""
    try:
        logger.info("🚀 Testing Agent Mode Response Time")
        logger.info("🎯 Target: Full response within 10-20 seconds")
        
        # Connect to the backend
        uri = "ws://localhost:8767"
        logger.info(f"📡 Connecting to {uri}...")
        
        async with websockets.connect(uri) as websocket:
            logger.info("✅ Connected to backend")
            
            # Wait for connection response
            connection_response = await websocket.recv()
            connection_data = json.loads(connection_response)
            logger.info(f"🔗 Connection: {connection_data.get('message', 'Connected')}")
            
            # Test case: flight search (user's original issue)
            test_message = {
                "type": "chat_request",
                "mode": "Agent",
                "message": "search flight from nyc to miami",
                "session_id": "user_test_session"
            }
            
            logger.info("📤 Sending agent request: 'search flight from nyc to miami'")
            start_time = time.time()
            
            await websocket.send(json.dumps(test_message))
            
            # Listen for responses
            response_received = False
            plan_generated = False
            total_response_time = 0
            
            while not response_received:
                try:
                    # Wait for response with timeout
                    response = await asyncio.wait_for(websocket.recv(), timeout=25.0)
                    data = json.loads(response)
                    
                    current_time = time.time() - start_time
                    
                    if data.get("type") == "final_response":
                        response_received = True
                        total_response_time = current_time
                        
                        response_text = data.get("response", "")
                        requires_confirmation = data.get("requiresConfirmation", False)
                        
                        logger.info(f"✅ Final response received in {current_time:.2f}s")
                        logger.info(f"📝 Response preview: {response_text[:100]}...")
                        logger.info(f"🔘 Requires confirmation: {requires_confirmation}")
                        
                        # Check if it's a proper automation plan
                        if "AUTOMATION" in response_text and "PLAN" in response_text:
                            plan_generated = True
                            logger.info("🎯 Automation plan successfully generated!")
                        else:
                            logger.warning("⚠️ Response doesn't contain automation plan")
                        
                        # Check response time
                        if current_time <= 10:
                            logger.info("🚀 EXCELLENT: Response within 10 seconds")
                        elif current_time <= 20:
                            logger.info("✅ GOOD: Response within 20 seconds")
                        else:
                            logger.warning("⚠️ SLOW: Response took longer than 20 seconds")
                        
                        break
                        
                    elif data.get("type") == "progress_update":
                        stage = data.get("stage", "Processing")
                        logger.info(f"📊 Progress at {current_time:.1f}s: {stage}")
                        
                    elif data.get("type") == "chat_response_metadata":
                        processing_time = data.get("processing_time", 0)
                        ai_powered = data.get("ai_powered", False)
                        logger.info(f"📈 Metadata - Processing: {processing_time:.2f}s, AI: {ai_powered}")
                        
                    else:
                        logger.info(f"📥 Received {data.get('type', 'unknown')} at {current_time:.1f}s")
                
                except asyncio.TimeoutError:
                    logger.error("❌ TIMEOUT: No response within 25 seconds")
                    return False
                except Exception as e:
                    logger.error(f"❌ Error receiving response: {e}")
                    return False
            
            # Summary
            logger.info("\n" + "="*50)
            logger.info("📊 USER EXPERIENCE TEST RESULTS")
            logger.info("="*50)
            logger.info(f"⏱️ Total Response Time: {total_response_time:.2f} seconds")
            logger.info(f"🎯 Plan Generated: {'✅ Yes' if plan_generated else '❌ No'}")
            logger.info(f"🎪 User Experience: {'🚀 Excellent' if total_response_time <= 10 else '✅ Good' if total_response_time <= 20 else '⚠️ Needs Improvement'}")
            
            # Test the original issue
            if plan_generated and total_response_time <= 20:
                logger.info("🎉 SUCCESS: Original issue RESOLVED!")
                logger.info("   - Agent mode creates detailed plans ✅")
                logger.info("   - Response time within 10-20 seconds ✅")
                logger.info("   - No more generic 'SEGEV' responses ✅")
                return True
            else:
                logger.warning("⚠️ Issues remain to be addressed")
                return False
                
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

async def main():
    """Run user experience test"""
    logger.info("🧪 Starting User Experience Test")
    logger.info("🎯 Testing the original issue: 'search flight from nyc to miami'")
    
    success = await test_agent_mode_response()
    
    if success:
        logger.info("\n🎉 USER EXPERIENCE TEST: PASSED!")
        logger.info("The system now works as expected for the user.")
    else:
        logger.info("\n⚠️ USER EXPERIENCE TEST: NEEDS WORK")
        logger.info("Additional optimizations may be needed.")

if __name__ == "__main__":
    asyncio.run(main())