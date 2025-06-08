"""
Test script to verify that the fixed semantic search agent works
correctly with the enterprise backend.

This script:
1. Initializes the enterprise backend with the semantic search agent
2. Adds test content to the memory system
3. Performs search queries to verify the search works
4. Reports detailed results
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import semantic search components
from memory.semantic_search_agent import SemanticSearchAgent, add_memory
from enhanced_enterprise_backend_with_context import ContextualAIBackend

# Test content
TEST_CONTENT = [
    "Enhanced semantic search using vector embeddings and cosine similarity for intelligent retrieval",
    "Enterprise memory system with contextual awareness for application-specific data",
    "UI detection and automation with precise coordinate calculation",
    "Advanced WebSocket server with secure communication channels",
    "Smart LLM integration with context preservation and request optimization"
]

async def run_test():
    """Run the integration test"""
    logger.info("🧪 TESTING ENTERPRISE SEMANTIC SEARCH INTEGRATION")
    logger.info("=" * 70)
    
    # Initialize the enterprise backend
    logger.info("📚 Initializing enterprise backend...")
    backend = ContextualAIBackend()
    
    # Check if semantic agent is properly initialized
    if backend.semantic_agent is None:
        logger.error("❌ Semantic agent not initialized in enterprise backend!")
        return False
    
    logger.info("✅ Enterprise backend initialized with semantic agent")
    
    # Add test content to memory
    logger.info("\n📝 Adding test content to memory...")
    for content in TEST_CONTENT:
        metadata = {
            "source": "enterprise_test",
            "timestamp": datetime.now().isoformat(),
            "type": "text"
        }
        # Use the add_memory function with proper parameters
        await add_memory(content, source="enterprise_test", 
                        metadata=metadata)
        logger.info(f"  ✅ {content[:50]}...")
    
    # Wait for indexing
    logger.info("⏳ Waiting for indexing to complete...")
    time.sleep(2)
    
    # Test search queries through the backend's semantic agent
    logger.info("\n🔍 Testing search queries...")
    
    test_queries = [
        "vector embeddings search",
        "enterprise memory context",
        "ui automation coordinates",
        "websocket communication",
        "llm integration"
    ]
    
    success_count = 0
    
    for query in test_queries:
        try:
            # Use the backend's semantic agent directly
            start_time = time.time()
            results = await backend.semantic_agent.search_memories(query, top_k=3)
            end_time = time.time()
            
            logger.info(f"\n  Query: '{query}'")
            logger.info(f"  Found {len(results)} results in {end_time - start_time:.4f}s")
            
            if results:
                for i, result in enumerate(results, 1):
                    logger.info(f"    {i}. [{result.similarity_score:.3f}] {result.content[:50]}...")
                
                # Check if we found a reasonable match
                if results[0].similarity_score > 0.3:
                    logger.info("  ✅ Found relevant results")
                    success_count += 1
                else:
                    logger.info("  ⚠️ Results found but low similarity")
            else:
                logger.info("  ❌ No results found")
        except Exception as e:
            logger.error(f"  ❌ Error during search: {str(e)}")
    
    # Print summary
    logger.info("\n📊 TEST SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Successful queries: {success_count}/{len(test_queries)} ({success_count/len(test_queries)*100:.1f}%)")
    
    if success_count >= len(test_queries) * 0.8:
        logger.info("\n✅ SUCCESS: Enterprise semantic search integration working correctly!")
        return True
    else:
        logger.info("\n⚠️ PARTIAL SUCCESS: Some queries returned good results, but not all.")
        return False

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    success = loop.run_until_complete(run_test())
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)