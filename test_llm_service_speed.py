#!/usr/bin/env python3
"""
Test LLM Service Speed with Warmup Manager
"""

import asyncio
import time
import logging
from llm.llm_service import LLMService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_llm_service_speed():
    """Test the enhanced LLM service speed"""
    logger.info("🧪 Testing Enhanced LLM Service Speed...")
    
    # Create LLM service with fastest model
    llm_service = LLMService(model_name="llama3.2:1b")
    
    try:
        # Start the service
        logger.info("🚀 Starting LLM service...")
        start_time = time.time()
        success = await llm_service.start()
        startup_time = time.time() - start_time
        
        if not success:
            logger.error("❌ Failed to start LLM service")
            return
        
        logger.info(f"✅ LLM service started in {startup_time:.2f}s")
        
        # Test queries
        test_queries = [
            "Hello",
            "What is 3+7?", 
            "Briefly explain Python in one sentence.",
            "What's the capital of France?",
            "Name 3 colors."
        ]
        
        total_response_time = 0
        successful_responses = 0
        
        for i, query in enumerate(test_queries, 1):
            logger.info(f"\n🧪 Test {i}: '{query}'")
            
            start_time = time.time()
            response = await llm_service.generate_response(query)
            response_time = time.time() - start_time
            
            if response and not response.startswith("Error:"):
                successful_responses += 1
                total_response_time += response_time
                
                logger.info(f"✅ Response in {response_time:.2f}s: {response[:100]}...")
                
                # Check speed expectations
                if response_time <= 5:
                    logger.info(f"🚀 EXCELLENT: Response within 5s")
                elif response_time <= 10:
                    logger.info(f"✅ GOOD: Response within 10s")
                elif response_time <= 25:
                    logger.info(f"⚠️ ACCEPTABLE: Response within 25s")
                else:
                    logger.error(f"❌ TOO SLOW: Response took {response_time:.2f}s")
            else:
                logger.error(f"❌ Failed response: {response}")
        
        # Summary
        if successful_responses > 0:
            avg_response_time = total_response_time / successful_responses
            logger.info(f"\n📊 PERFORMANCE SUMMARY:")
            logger.info(f"   Successful responses: {successful_responses}/{len(test_queries)}")
            logger.info(f"   Average response time: {avg_response_time:.2f}s")
            logger.info(f"   Total test time: {total_response_time:.2f}s")
            
            if avg_response_time <= 5:
                logger.info("🎉 PERFORMANCE: EXCELLENT - Meeting speed expectations!")
            elif avg_response_time <= 10:
                logger.info("✅ PERFORMANCE: GOOD - Within acceptable range")
            else:
                logger.warning("⚠️ PERFORMANCE: Needs improvement")
        else:
            logger.error("❌ No successful responses")
            
    except Exception as e:
        logger.error(f"❌ Test error: {e}")
    finally:
        await llm_service.stop()

if __name__ == "__main__":
    asyncio.run(test_llm_service_speed())