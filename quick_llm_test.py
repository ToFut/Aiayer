#!/usr/bin/env python3
"""
Quick LLM Service Test
"""

import asyncio
import time
import logging
from llm_warmup_manager import get_warmup_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def quick_test():
    """Quick test of warmed model"""
    logger.info("🧪 Quick LLM Test...")
    
    # Get warmed manager
    manager = await get_warmup_manager()
    
    if manager.is_model_warm():
        logger.info(f"✅ Model {manager.get_current_model()} ready")
        
        # Fast test
        start_time = time.time()
        response = await manager.fast_generate_response([
            {"role": "user", "content": "What is 2+2?"}
        ])
        elapsed = time.time() - start_time
        
        logger.info(f"⚡ Response in {elapsed:.2f}s: {response}")
        
        if elapsed <= 10:
            logger.info("✅ PERFORMANCE: Good - within 10s expectation")
        else:
            logger.warning(f"⚠️ PERFORMANCE: Slow - took {elapsed:.2f}s")
    else:
        logger.error("❌ Model not ready")
    
    await manager.stop()

if __name__ == "__main__":
    asyncio.run(quick_test())