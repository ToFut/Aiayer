"""
Test client for the Enterprise Semantic Search integration.
This connects to the enterprise backend and tests the memory search functionality.
"""

import asyncio
import json
import logging
import sys
import time
import websockets
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test queries for memory search
TEST_QUERIES = [
    "vector embeddings search",
    "enterprise memory context",
    "ui automation coordinates",
    "websocket communication",
    "llm integration"
]

async def test_memory_search():
    """Connect to enterprise backend and test memory search"""
    
    logger.info("🧪 TESTING ENTERPRISE SEMANTIC SEARCH CLIENT")
    logger.info("=" * 70)
    
    # Connect to enterprise backend
    uri = "ws://localhost:8767"
    logger.info(f"📡 Connecting to enterprise backend at {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            # Wait for connection established message
            response = await websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get("type") == "connection_established":
                client_id = response_data.get("client_id")
                logger.info(f"✅ Connected as client ID: {client_id}")
                logger.info(f"Server features: {response_data.get('ai_features', {})}")
            else:
                logger.error(f"❌ Unexpected initial response: {response_data}")
                return False
            
            # Add test content to memory
            logger.info("\n📝 Adding test content to memory...")
            test_content = [
                "Enterprise semantic search with vector embeddings for efficient retrieval",
                "Context-aware memory system for application-specific intelligence",
                "UI element detection with precise automation capabilities",
                "WebSocket server implementation for real-time communication",
                "LLM integration with context preservation and streaming responses"
            ]
            
            for content in test_content:
                memory_add_message = {
                    "type": "memory_update",
                    "content": content,
                    "source": "test_client",
                    "metadata": {
                        "timestamp": datetime.now().isoformat(),
                        "type": "text"
                    }
                }
                
                await websocket.send(json.dumps(memory_add_message))
                logger.info(f"  📤 Added: {content[:50]}...")
            
            # Wait for indexing
            logger.info("⏳ Waiting for indexing to complete...")
            time.sleep(2)
            
            # Test memory search for each query
            logger.info("\n🔍 Testing memory search queries...")
            success_count = 0
            
            for query in TEST_QUERIES:
                search_message = {
                    "type": "memory_search",
                    "query": query,
                    "top_k": 3,
                    "application_context": None
                }
                
                logger.info(f"\n  Query: '{query}'")
                
                # Send memory search request
                await websocket.send(json.dumps(search_message))
                
                # Wait for response
                response = await websocket.recv()
                search_results = json.loads(response)
                
                if search_results.get("type") == "memory_search_response":
                    results = search_results.get("results", [])
                    count = len(results)
                    elapsed = search_results.get("elapsed_time", 0)
                    
                    logger.info(f"  Found {count} results in {elapsed}s")
                    
                    if count > 0:
                        for i, result in enumerate(results, 1):
                            similarity = result.get("similarity", 0.0)
                            content = result.get("content", "")
                            relevance = ", ".join(result.get("relevance_factors", []))
                            logger.info(f"    {i}. [{similarity:.3f}] {content[:50]}...")
                            if relevance:
                                logger.info(f"       Relevance: {relevance}")
                        
                        # Check if we found a reasonable match
                        if results[0].get("similarity", 0) > 0.2:
                            logger.info("  ✅ Found relevant results")
                            success_count += 1
                        else:
                            logger.info("  ⚠️ Results found but low similarity")
                    else:
                        logger.info("  ❌ No results found")
                else:
                    logger.error(f"  ❌ Unexpected search response: {search_results}")
            
            # Print summary
            logger.info("\n📊 TEST SUMMARY")
            logger.info("=" * 70)
            logger.info(f"Successful queries: {success_count}/{len(TEST_QUERIES)} ({success_count/len(TEST_QUERIES)*100:.1f}%)")
            
            if success_count >= len(TEST_QUERIES) * 0.8:
                logger.info("\n✅ SUCCESS: Enterprise semantic search integration is working!")
                return True
            else:
                logger.info("\n⚠️ PARTIAL SUCCESS: Some queries returned good results, but not all.")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error connecting to enterprise backend: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(test_memory_search())
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(130)