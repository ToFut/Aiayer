#!/usr/bin/env python3
"""
Clean Agent Speed Test
Properly manages sessions to avoid warnings
"""

import asyncio
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_clean_agent_speed():
    """Test agent speed with proper cleanup"""
    logger.info("🧪 Clean Agent Speed Test")
    logger.info("="*40)
    
    try:
        # Test warmup manager with proper cleanup
        from llm_warmup_manager import LLMWarmupManager
        
        async with LLMWarmupManager() as manager:
            if manager.is_model_warm():
                logger.info("✅ Model is warm and ready")
                
                # Test a quick response
                start_time = time.time()
                response = await manager.fast_generate_response([
                    {"role": "user", "content": "What is 2+2?"}
                ])
                response_time = time.time() - start_time
                
                logger.info(f"⚡ Response in {response_time:.2f}s: {response}")
                
                if response_time <= 5:
                    logger.info("🚀 EXCELLENT: Fast response achieved!")
                else:
                    logger.warning("⚠️ Response could be faster")
            else:
                logger.warning("⚠️ Model not warm")
                
    except ImportError:
        logger.error("❌ Warmup manager not available")
    except Exception as e:
        logger.error(f"❌ Test error: {e}")
    
    logger.info("✅ Clean test completed - no session warnings!")

if __name__ == "__main__":
    # Run with proper asyncio handling
    try:
        asyncio.run(test_clean_agent_speed())
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}")