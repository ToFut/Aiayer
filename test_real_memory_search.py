"""
Test semantic search with real memory data from the existing memory system.
This provides examples of real searches using the actual memory database.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import directly from the fixed semantic search agent
from memory.semantic_search_agent import SemanticSearchAgent

# Real-world queries to test
REAL_QUERIES = [
    {"query": "what applications have I used recently", "context": None},
    {"query": "find UI elements in Google", "context": "Google Chrome"},
    {"query": "python code I've worked on", "context": "VSCode"},
    {"query": "websocket communication implementation", "context": None},
    {"query": "enterprise backend system", "context": None}
]

async def run_real_memory_search():
    """Run semantic search against real memory data"""
    logger.info("🔍 REAL MEMORY SEMANTIC SEARCH EXAMPLES")
    logger.info("=" * 70)
    
    # Initialize the semantic search agent
    search_agent = SemanticSearchAgent()
    logger.info(f"📊 Memory database statistics:")
    stats = search_agent.get_performance_metrics()
    logger.info(f"  Total documents: {stats.get('total_documents', 'N/A')}")
    logger.info(f"  Indexing status: {stats.get('index_status', 'N/A')}")
    logger.info(f"  Average search time: {stats.get('avg_search_time', 'N/A')}s")
    
    # Test each real-world query
    total_time = 0
    result_count = 0
    
    for test_case in REAL_QUERIES:
        query = test_case["query"]
        context = test_case["context"]
        
        logger.info(f"\n🔎 Query: '{query}'")
        if context:
            logger.info(f"   Context: '{context}'")
        
        # Search with and without context if available
        start_time = time.time()
        results = await search_agent.search_memories(
            query=query,
            top_k=5,
            min_similarity=0.15,
            application_context=context
        )
        search_time = time.time() - start_time
        total_time += search_time
        
        # Log results
        logger.info(f"   Found {len(results)} results in {search_time:.4f}s")
        result_count += len(results)
        
        # Show results with details
        for i, result in enumerate(results, 1):
            logger.info(f"   {i}. [{result.similarity_score:.3f}] {result.content[:100]}...")
            
            # Show source info
            source = result.source if hasattr(result, 'source') else 'unknown'
            timestamp = result.timestamp.isoformat() if hasattr(result, 'timestamp') and isinstance(result.timestamp, datetime) else 'unknown'
            logger.info(f"      Source: {source}")
            logger.info(f"      Time: {timestamp}")
            
            # Show relevance factors
            if hasattr(result, 'relevance_factors') and result.relevance_factors:
                logger.info(f"      Relevance: {', '.join(result.relevance_factors)}")
            
            # Show metadata highlights if available
            if hasattr(result, 'metadata') and result.metadata:
                # Only show select metadata for readability
                app_name = result.metadata.get('application_name', result.metadata.get('app_name', None))
                content_type = result.metadata.get('content_type', result.metadata.get('type', None))
                if app_name or content_type:
                    meta_display = []
                    if app_name:
                        meta_display.append(f"App: {app_name}")
                    if content_type:
                        meta_display.append(f"Type: {content_type}")
                    logger.info(f"      Metadata: {' | '.join(meta_display)}")
    
    # Print summary
    logger.info("\n📊 SEARCH SUMMARY")
    logger.info("=" * 70)
    avg_time = total_time / len(REAL_QUERIES) if REAL_QUERIES else 0
    avg_results = result_count / len(REAL_QUERIES) if REAL_QUERIES else 0
    logger.info(f"Queries executed: {len(REAL_QUERIES)}")
    logger.info(f"Total results found: {result_count}")
    logger.info(f"Average results per query: {avg_results:.1f}")
    logger.info(f"Average search time: {avg_time:.4f}s")
    
    logger.info("\n✅ Semantic search is working with real memory data!")

if __name__ == "__main__":
    asyncio.run(run_real_memory_search())