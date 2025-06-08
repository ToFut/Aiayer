#!/usr/bin/env python3
"""
Test memory interface by adding multiple sample memories and searching for them
"""

import asyncio
import json
import logging
import websockets
import datetime
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("memory_test")

# Sample memories to add
SAMPLE_MEMORIES = [
    {
        "content": "The Python programming language is great for data analysis and machine learning projects.",
        "source": "test",
        "tags": ["python", "programming", "data-science"]
    },
    {
        "content": "JavaScript is the most widely used language for web frontend development.",
        "source": "test",
        "tags": ["javascript", "programming", "web-dev"]
    },
    {
        "content": "Tokyo, Japan has amazing food, especially the sushi restaurants.",
        "source": "test",
        "tags": ["travel", "food", "japan"]
    },
    {
        "content": "The best beaches in Hawaii are on the north shore of Oahu.",
        "source": "test",
        "tags": ["travel", "beaches", "hawaii"]
    }
]

# Test search queries
TEST_SEARCHES = [
    {
        "query": "Programming languages for data analysis",
        "expected_match": "Python"
    },
    {
        "query": "Web development technologies",
        "expected_match": "JavaScript"
    },
    {
        "query": "Food in Japan",
        "expected_match": "sushi"
    },
    {
        "query": "Best beaches for vacation",
        "expected_match": "Hawaii"
    }
]

async def test_memory_interface():
    """Test memory interface with sample memories"""
    uri = "ws://localhost:8769"
    logger.info(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Wait for welcome message
            response = await websocket.recv()
            response_data = json.loads(response)
            logger.info(f"Received welcome: {response_data['type']}")
            
            # Add sample memories
            logger.info(f"Adding {len(SAMPLE_MEMORIES)} sample memories...")
            for memory in SAMPLE_MEMORIES:
                await websocket.send(json.dumps({
                    "type": "add_memory",
                    **memory
                }))
                
                response = await websocket.recv()
                response_data = json.loads(response)
                
                if response_data.get('success'):
                    memory_id = response_data.get('memory_id', 'unknown')
                    logger.info(f"Added memory: '{memory['content'][:30]}...' with ID: {memory_id}")
                else:
                    logger.error(f"Failed to add memory: {response_data.get('error', 'Unknown error')}")
                
                # Small delay to avoid overwhelming the server
                await asyncio.sleep(0.5)
            
            # Give the system time to process the memories
            logger.info("Waiting for memories to be processed...")
            await asyncio.sleep(2)
            
            # Get system stats
            await websocket.send(json.dumps({"type": "get_system_stats"}))
            response = await websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get('type') == 'system_stats':
                stats = response_data.get('stats', {})
                logger.info(f"Total memories: {stats.get('total_memories', 'unknown')}")
            
            # Run test searches
            success_count = 0
            for test in TEST_SEARCHES:
                logger.info(f"Searching for: '{test['query']}' (should match '{test['expected_match']}')")
                
                await websocket.send(json.dumps({
                    "type": "search_memory",
                    "query": test['query'],
                    "top_k": 3,
                    "min_similarity": 0.1
                }))
                
                response = await websocket.recv()
                response_data = json.loads(response)
                
                if response_data.get('type') != 'search_results':
                    logger.error(f"Expected search results, got {response_data.get('type')}")
                    continue
                
                results = response_data.get('results', [])
                logger.info(f"Found {len(results)} results")
                
                found_match = False
                for result in results:
                    content = result.get('content', '')
                    score = result.get('similarity_score', result.get('score', 0))
                    logger.info(f"Result: '{content[:50]}...' (Score: {score:.3f})")
                    
                    if test['expected_match'] in content:
                        found_match = True
                        logger.info(f"✅ Found expected match: '{test['expected_match']}'")
                        success_count += 1
                        break
                
                if not found_match:
                    logger.warning(f"❌ Expected match '{test['expected_match']}' not found in results")
                
                # Add a small delay between searches
                await asyncio.sleep(1)
            
            # Calculate success rate
            success_rate = (success_count / len(TEST_SEARCHES)) * 100
            logger.info(f"Search success rate: {success_rate:.1f}% ({success_count}/{len(TEST_SEARCHES)})")
            
            if success_rate >= 75:
                logger.info("✅ Memory system is working well!")
            elif success_rate >= 50:
                logger.info("⚠️ Memory system is working, but with some issues.")
            else:
                logger.info("❌ Memory system has significant issues.")
            
    except Exception as e:
        logger.error(f"Error in test: {e}", exc_info=True)

if __name__ == "__main__":
    logger.info("Starting memory interface test with sample memories")
    asyncio.run(test_memory_interface())
    logger.info("Test completed")