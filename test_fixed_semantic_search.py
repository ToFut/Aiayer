#!/usr/bin/env python3
"""
Test Fixed Semantic Search
Tests the improved semantic search implementation
"""
import sys
import os
import json
import asyncio
import logging
import time
from datetime import datetime

# Add parent directory to path
sys.path.append('/Users/segevbin/Desktop/SensAI/Aiayer')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import fixed implementation
try:
    from memory.semantic_search_agent_fixed import SemanticSearchAgent, add_memory, search_memories
    logger.info("Successfully imported fixed semantic search components")
except ImportError as e:
    logger.error(f"Error importing fixed semantic search: {e}")
    sys.exit(1)

async def test_fixed_semantic_search():
    """Test the fixed semantic search implementation"""
    print("\n🔍 TESTING FIXED SEMANTIC SEARCH")
    print("=" * 60)
    
    # Initialize new search agent instance to avoid conflicts
    search_agent = SemanticSearchAgent()
    
    # Define test content with distinct topics
    test_contents = [
        {
            "content": "Python development workflow with VSCode for efficient coding",
            "tags": {"development", "python", "workflow"}
        },
        {
            "content": "Semantic search using vector embeddings and cosine similarity",
            "tags": {"ai", "search", "vectors"}
        },
        {
            "content": "Memory system architecture with short-term and long-term storage",
            "tags": {"architecture", "memory", "system"}
        },
        {
            "content": "Debugging memory integration issues with detailed logging",
            "tags": {"debugging", "memory", "logging"}
        },
        {
            "content": "WebSocket server running on port 8765 for real-time communication",
            "tags": {"server", "websocket", "communication"}
        }
    ]
    
    # Add test content
    print("\n📝 Adding test content...")
    for item in test_contents:
        success = await search_agent.add_memory(
            content=item["content"],
            source="test",
            tags=item["tags"]
        )
        print(f"  {'✅' if success else '❌'} {item['content']}")
    
    # Test queries
    test_queries = [
        {
            "query": "python development",
            "expected_match": test_contents[0]["content"],
            "description": "Programming language"
        },
        {
            "query": "semantic vector search",
            "expected_match": test_contents[1]["content"],
            "description": "AI search technology"
        },
        {
            "query": "memory architecture",
            "expected_match": test_contents[2]["content"],
            "description": "System design"
        },
        {
            "query": "debugging issues",
            "expected_match": test_contents[3]["content"],
            "description": "Problem solving"
        },
        {
            "query": "websocket port",
            "expected_match": test_contents[4]["content"],
            "description": "Network communication"
        }
    ]
    
    # Wait a moment for indexing
    await asyncio.sleep(1)
    
    # Test search
    print("\n🔍 Testing search queries...")
    results_summary = []
    
    for test in test_queries:
        print(f"\n  Query: '{test['query']}' ({test['description']})")
        print(f"  Expected match: '{test['expected_match'][:50]}...'")
        
        # Execute search
        start_time = time.time()
        results = await search_agent.search_memories(query=test["query"], top_k=3)
        search_time = time.time() - start_time
        
        # Process results
        found_match = False
        if results:
            print(f"  Found {len(results)} results in {search_time:.4f}s")
            
            for i, result in enumerate(results):
                is_expected = test["expected_match"] == result.content
                if is_expected:
                    found_match = True
                    
                print(f"    {i+1}. {'✓' if is_expected else ' '} [{result.similarity_score:.3f}] {result.content[:50]}...")
                
                if result.relevance_factors:
                    print(f"       Relevance: {', '.join(result.relevance_factors)}")
        else:
            print("  ❌ No results found")
        
        # Store result summary
        results_summary.append({
            "query": test["query"],
            "description": test["description"],
            "expected_match": test["expected_match"],
            "found_expected": found_match,
            "result_count": len(results),
            "search_time": search_time,
            "top_result": results[0].content if results else None,
            "top_score": results[0].similarity_score if results else 0
        })
        
        if found_match:
            print(f"  ✅ Expected match found")
        else:
            print(f"  ❌ Expected match NOT found")
    
    # Test application context
    print("\n🧠 Testing application context...")
    test_query = "development workflow"
    
    print(f"  Query: '{test_query}'")
    print(f"  Context: 'VSCode editor'")
    
    # Execute search with context
    results_without_context = await search_agent.search_memories(query=test_query, top_k=3)
    results_with_context = await search_agent.search_memories(
        query=test_query, 
        top_k=3,
        application_context="VSCode editor"
    )
    
    # Compare results
    print("\n  Without context:")
    for i, result in enumerate(results_without_context):
        print(f"    {i+1}. [{result.similarity_score:.3f}] {result.content[:50]}...")
    
    print("\n  With context:")
    for i, result in enumerate(results_with_context):
        print(f"    {i+1}. [{result.similarity_score:.3f}] {result.content[:50]}...")
    
    # Check if context improved results
    context_improved = False
    if results_with_context and results_without_context:
        python_content = test_contents[0]["content"]
        
        # Check if context boosted the Python development result
        context_score = next((r.similarity_score for r in results_with_context if r.content == python_content), 0)
        non_context_score = next((r.similarity_score for r in results_without_context if r.content == python_content), 0)
        
        if context_score > non_context_score:
            context_improved = True
            print(f"\n  ✅ Context successfully boosted VSCode result:")
            print(f"    Without context: {non_context_score:.3f}")
            print(f"    With context: {context_score:.3f}")
        else:
            print(f"\n  ⚠️ Context did not improve the results as expected")
    
    # Generate summary
    success_count = sum(1 for r in results_summary if r["found_expected"])
    success_rate = success_count / len(test_queries) * 100
    
    print("\n📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Successful queries: {success_count}/{len(test_queries)} ({success_rate:.1f}%)")
    print(f"Average search time: {sum(r['search_time'] for r in results_summary) / len(results_summary):.4f}s")
    print(f"Application context test: {'✅ Passed' if context_improved else '⚠️ Mixed results'}")
    
    # Save results
    results_file = "fixed_semantic_search_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "query_results": results_summary,
            "success_rate": success_rate,
            "context_test_improved": context_improved
        }, f, indent=2)
    
    print(f"\nDetailed results saved to: {results_file}")
    
    if success_rate >= 80:
        print("\n✅ OVERALL ASSESSMENT: Semantic search is now working properly!")
    elif success_rate >= 50:
        print("\n⚠️ OVERALL ASSESSMENT: Semantic search is improved but needs fine-tuning")
    else:
        print("\n❌ OVERALL ASSESSMENT: Semantic search still has significant issues")

if __name__ == "__main__":
    asyncio.run(test_fixed_semantic_search())