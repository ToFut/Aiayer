#!/usr/bin/env python3
"""
Test Fast Automation System
Verify the fast automation handler is working and responding within 10-20 seconds
"""

import asyncio
import time
import logging
import json
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_fast_automation():
    """Test the fast automation system"""
    try:
        # Import the fast automation handler
        from fast_universal_automation_handler import fast_universal_automation_handler
        
        logger.info("⚡ Fast Universal Automation Handler loaded successfully")
        
        # Test different types of requests
        test_requests = [
            "search flight from nyc to miami",
            "find Python tutorials on Google", 
            "open Calculator and compute 15 * 27",
            "search for MacBook deals on Amazon",
            "check Twitter feed"
        ]
        
        results = []
        
        for i, request in enumerate(test_requests, 1):
            logger.info(f"\n🧪 Test {i}/5: {request}")
            
            start_time = time.time()
            
            try:
                # Test plan creation
                result = await fast_universal_automation_handler.create_universal_automation_plan(
                    request, f"test_session_{i}"
                )
                
                processing_time = time.time() - start_time
                
                success = result.get("success", False)
                plan_id = result.get("plan_id", "unknown")
                response_text = result.get("response", "No response")
                
                logger.info(f"✅ Plan created in {processing_time:.2f}s - Success: {success}")
                logger.info(f"📋 Plan ID: {plan_id}")
                logger.info(f"📝 Response preview: {response_text[:100]}...")
                
                # Test if response time is within target
                within_target = processing_time <= 20.0
                logger.info(f"⏱️ Time target (≤20s): {'✅ PASS' if within_target else '❌ FAIL'}")
                
                # Test button action handling (simulate EXECUTE)
                if success and plan_id:
                    button_start_time = time.time()
                    
                    button_result = await fast_universal_automation_handler.handle_button_action(
                        "execute_plan", plan_id, f"test_session_{i}"
                    )
                    
                    button_time = time.time() - button_start_time
                    button_success = button_result.get("success", False)
                    
                    logger.info(f"🔘 Button action in {button_time:.2f}s - Success: {button_success}")
                
                results.append({
                    "request": request,
                    "success": success,
                    "processing_time": processing_time,
                    "within_target": within_target,
                    "plan_created": success,
                    "button_tested": success and plan_id
                })
                
            except Exception as e:
                processing_time = time.time() - start_time
                logger.error(f"❌ Test {i} failed after {processing_time:.2f}s: {e}")
                results.append({
                    "request": request,
                    "success": False,
                    "processing_time": processing_time,
                    "error": str(e),
                    "within_target": processing_time <= 20.0
                })
        
        # Generate summary report
        logger.info("\n" + "="*60)
        logger.info("📊 FAST AUTOMATION SYSTEM TEST RESULTS")
        logger.info("="*60)
        
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r.get("success", False))
        avg_time = sum(r["processing_time"] for r in results) / total_tests
        within_target_count = sum(1 for r in results if r.get("within_target", False))
        
        logger.info(f"📈 Success Rate: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)")
        logger.info(f"⚡ Average Response Time: {avg_time:.2f} seconds")
        logger.info(f"🎯 Within Target (≤20s): {within_target_count}/{total_tests} ({within_target_count/total_tests*100:.1f}%)")
        
        # Detailed results
        logger.info("\n📋 Detailed Results:")
        for i, result in enumerate(results, 1):
            status = "✅ PASS" if result.get("success", False) else "❌ FAIL"
            time_status = "⚡ FAST" if result.get("within_target", False) else "🐌 SLOW"
            logger.info(f"{i}. {result['request'][:40]}... - {status} - {result['processing_time']:.2f}s {time_status}")
        
        # Performance assessment
        logger.info(f"\n🏆 PERFORMANCE ASSESSMENT:")
        if avg_time <= 10:
            logger.info("🚀 EXCELLENT: Average response time ≤ 10 seconds")
        elif avg_time <= 20:
            logger.info("✅ GOOD: Average response time ≤ 20 seconds")
        else:
            logger.info("⚠️ NEEDS IMPROVEMENT: Average response time > 20 seconds")
        
        if within_target_count == total_tests:
            logger.info("🎯 PERFECT: All requests within 20-second target")
        elif within_target_count >= total_tests * 0.8:
            logger.info("✅ GOOD: 80%+ requests within target")
        else:
            logger.info("⚠️ NEEDS OPTIMIZATION: <80% requests within target")
        
        logger.info("="*60)
        
        return results
        
    except ImportError as e:
        logger.error(f"❌ Fast automation handler not available: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return None

async def test_backend_integration():
    """Test integration with the enhanced backend"""
    try:
        logger.info("\n🔌 Testing Backend Integration...")
        
        # Import the backend
        from enhanced_enterprise_backend_with_context import ContextualAIBackend
        
        backend = ContextualAIBackend()
        
        # Check if fast automation is available
        fast_available = hasattr(backend, 'FAST_AUTOMATION_AVAILABLE') or 'FAST_AUTOMATION_AVAILABLE' in globals()
        logger.info(f"⚡ Fast automation in backend: {'✅ Available' if fast_available else '❌ Not Available'}")
        
        # Test a sample agent request simulation
        test_message = {
            "type": "chat_request",
            "mode": "Agent",
            "message": "search flight from nyc to miami",
            "session_id": "test_backend_session"
        }
        
        logger.info("🧪 Testing agent mode automation plan creation...")
        start_time = time.time()
        
        # This would normally be called via WebSocket, but we're testing the logic
        response = await backend.handle_contextual_chat_request(test_message, "test_client")
        
        backend_time = time.time() - start_time
        logger.info(f"🔧 Backend response time: {backend_time:.2f}s")
        
        if response.get("success", False):
            logger.info("✅ Backend integration successful")
        else:
            logger.warning(f"⚠️ Backend integration issue: {response.get('error', 'Unknown error')}")
        
        return backend_time
        
    except Exception as e:
        logger.error(f"❌ Backend integration test failed: {e}")
        return None

async def main():
    """Run all tests"""
    logger.info("🚀 Starting Fast Automation System Tests")
    logger.info("🎯 Target: Response time ≤ 10-20 seconds")
    
    # Test the fast automation handler directly
    results = await test_fast_automation()
    
    # Test backend integration
    backend_time = await test_backend_integration()
    
    # Final summary
    if results:
        avg_time = sum(r["processing_time"] for r in results) / len(results)
        logger.info(f"\n🏁 FINAL SUMMARY:")
        logger.info(f"⚡ Fast Handler Average: {avg_time:.2f}s")
        if backend_time:
            logger.info(f"🔧 Backend Integration: {backend_time:.2f}s")
        
        if avg_time <= 20:
            logger.info("🎉 SUCCESS: System meets 10-20 second target!")
        else:
            logger.info("⚠️ OPTIMIZATION NEEDED: System exceeds 20-second target")
    
    logger.info("\n✅ Test completed!")

if __name__ == "__main__":
    asyncio.run(main())