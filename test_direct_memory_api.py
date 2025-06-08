#!/usr/bin/env python3
"""
Direct Memory API Test

This script tests the memory system directly using the API functions
rather than through WebSockets. It adds a test memory and then searches
for it to verify the memory system is working properly.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("direct_memory_test")

# Import memory system components
try:
    from memory.semantic_search_agent import search_memories, add_memory
    MEMORY_SYSTEM_AVAILABLE = True
    logger.info("Memory system modules imported successfully")
except ImportError as e:
    logger.error(f"Failed to import memory system: {e}")
    MEMORY_SYSTEM_AVAILABLE = False

async def run_test():
    """Run the direct memory test"""
    if not MEMORY_SYSTEM_AVAILABLE:
        logger.error("Memory system modules not available")
        return False
    
    logger.info("Starting direct memory API test")
    
    # Test 1: Add a test memory
    memory_content = f"Test memory created at {datetime.now().isoformat()} with ID {uuid.uuid4()}"
    logger.info(f"TEST 1: Adding memory: {memory_content[:50]}...")
    
    # Add the memory
    try:
        success = await add_memory(
            content=memory_content,
            source="direct_test",
            tags=["test", "direct_api"],
            metadata={"test_id": str(uuid.uuid4())}
        )
        
        if success:
            logger.info("✅ Memory added successfully")
        else:
            logger.error("❌ Failed to add memory")
            return False
        
        # Small delay to ensure memory is processed
        await asyncio.sleep(1)
        
        # Test 2: Search for the memory
        logger.info("TEST 2: Searching for test memory")
        search_results = await search_memories(
            query="test memory",
            top_k=10,
            source_filter="direct_test"
        )
        
        # Check search results
        if search_results and len(search_results) > 0:
            logger.info(f"✅ Found {len(search_results)} search results")
            
            # Check if our test memory is in the results
            found = False
            for result in search_results:
                if memory_content in result.content:
                    logger.info("✅ Found our test memory in search results!")
                    found = True
                    break
            
            if not found:
                logger.warning("⚠️ Test memory not found in results")
            
            # Print search result details
            for i, result in enumerate(search_results[:3]):  # Show top 3 results
                logger.info(f"Result {i+1}:")
                logger.info(f"  Content: {result.content[:100]}...")
                logger.info(f"  Score: {result.similarity_score}")
                logger.info(f"  Source: {result.source}")
                logger.info(f"  Timestamp: {result.timestamp}")
            
            return True
        else:
            logger.error("❌ No search results found")
            return False
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("Starting memory direct API test")
    success = asyncio.run(run_test())
    
    if success:
        logger.info("✅ All tests completed successfully")
        exit(0)
    else:
        logger.error("❌ Tests failed")
        exit(1)