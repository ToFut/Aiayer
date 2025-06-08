#!/usr/bin/env python3
"""
Test direct memory search for newly added memories
"""

import asyncio
import json
import logging
import websockets

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("direct_test")

# List of exact content phrases to search for
DIRECT_SEARCHES = [
    "Python project",
    "JavaScript frontend",
    "cloud infrastructure",
    "trip to Japan",
    "beaches in Hawaii",
    "Barcelona",
    "Italian restaurant",
    "make sushi",
    "Thai curry"
]

async def test_direct_memory_search():
    """Test direct memory search"""
    uri = "ws://localhost:8769"
    logger.info(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Wait for welcome message
            response = await websocket.recv()
            response_data = json.loads(response)
            logger.info(f"Received welcome: {response_data['type']}")
            
            # Run direct searches
            results = []
            for search_term in DIRECT_SEARCHES:
                logger.info(f"Direct search for: '{search_term}'")
                
                await websocket.send(json.dumps({
                    "type": "search_memory",
                    "query": search_term,
                    "top_k": 5,
                    "min_similarity": 0.1
                }))
                
                response = await websocket.recv()
                response_data = json.loads(response)
                
                # Check if we got search results
                if response_data.get('type') != 'search_results':
                    logger.error(f"Expected search results, got {response_data.get('type')}")
                    continue
                
                search_results = response_data.get('results', [])
                logger.info(f"Found {len(search_results)} results")
                
                # Check if any of our test memories are in the results
                found_test_memory = False
                for result in search_results:
                    content = result.get('content', '')
                    score = result.get('similarity_score', result.get('score', 0))
                    logger.info(f"Result: '{content[:50]}...' (Score: {score:.3f})")
                    
                    # Check if this is one of our test memories
                    if any(test_phrase in content for test_phrase in [
                        "Python project", "JavaScript frontend", "cloud infrastructure",
                        "trip to Japan", "beaches in Hawaii", "Barcelona",
                        "Italian restaurant", "make sushi", "Thai curry"
                    ]):
                        found_test_memory = True
                        logger.info(f"✅ Found our test memory!")
                
                if not found_test_memory:
                    logger.warning(f"❌ No test memories found in results")
                
                # Add small delay between searches
                await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"Error in test: {e}", exc_info=True)

if __name__ == "__main__":
    logger.info("Starting direct memory search test")
    asyncio.run(test_direct_memory_search())
    logger.info("Test completed")