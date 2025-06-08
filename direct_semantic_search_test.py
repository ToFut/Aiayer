"""
Direct test of the semantic search agent to ensure it's working properly.
This bypasses the enterprise backend integration.
"""

import asyncio
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import directly from the fixed semantic search agent
from memory.semantic_search_agent import SemanticSearchAgent

# Test content
TEST_CONTENT = [
    "Enhanced semantic search using vector embeddings and cosine similarity for intelligent retrieval",
    "Enterprise memory system with contextual awareness for application-specific data",
    "UI detection and automation with precise coordinate calculation",
    "Advanced WebSocket server with secure communication channels",
    "Smart LLM integration with context preservation and request optimization"
]

async def run_direct_test():
    """Run direct test of semantic search"""
    logger.info("🧪 DIRECT SEMANTIC SEARCH TEST")
    logger.info("=" * 70)
    
    # Initialize the semantic search agent directly
    search_agent = SemanticSearchAgent()
    
    # Add test content directly to the agent
    logger.info("\n📝 Adding test content directly...")
    for content in TEST_CONTENT:
        metadata = {
            "source": "direct_test",
            "timestamp": datetime.now().isoformat(),
            "type": "text"
        }
        success = await search_agent.add_memory(content, source="direct_test", metadata=metadata)
        if success:
            logger.info(f"  ✅ Added: {content[:50]}...")
        else:
            logger.error(f"  ❌ Failed to add: {content[:50]}...")
    
    # Wait for indexing
    logger.info("⏳ Waiting for indexing to complete...")
    time.sleep(2)
    
    # Test search queries
    logger.info("\n🔍 Testing search queries directly...")
    
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
            # Perform search directly
            start_time = time.time()
            results = await search_agent.search_memories(query, top_k=3, min_similarity=0.1)
            end_time = time.time()
            
            logger.info(f"\n  Query: '{query}'")
            logger.info(f"  Found {len(results)} results in {end_time - start_time:.4f}s")
            
            if results:
                for i, result in enumerate(results, 1):
                    logger.info(f"    {i}. [{result.similarity_score:.3f}] {result.content[:50]}...")
                    if hasattr(result, 'relevance_factors') and result.relevance_factors:
                        logger.info(f"       Relevance: {', '.join(result.relevance_factors)}")
                
                # Check if we found a reasonable match
                if results[0].similarity_score > 0.2:
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
        logger.info("\n✅ SUCCESS: Direct semantic search is working correctly!")
        return True
    else:
        logger.info("\n⚠️ PARTIAL SUCCESS: Some queries returned good results, but not all.")
        return False

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    success = loop.run_until_complete(run_direct_test())
    
    if success:
        exit(0)
    else:
        exit(1)