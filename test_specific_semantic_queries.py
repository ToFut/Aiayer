#!/usr/bin/env python3
"""
Test specific semantic queries that should match our test memories
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
logger = logging.getLogger("semantic_specific")

# More specific semantic queries that should match our test memories
SEMANTIC_QUERIES = [
    {
        "query": "Programming language used for data analysis",
        "expected_content": "Python project",
        "description": "Should match the Python project memory"
    },
    {
        "query": "Web technology making API calls",
        "expected_content": "JavaScript frontend",
        "description": "Should match the JavaScript frontend memory"
    },
    {
        "query": "System that needs to handle more traffic",
        "expected_content": "cloud infrastructure",
        "description": "Should match the cloud infrastructure memory"
    },
    {
        "query": "Asian country known for cuisine",
        "expected_content": "trip to Japan",
        "description": "Should match the Japan trip memory"
    },
    {
        "query": "Pacific island with nice beaches",
        "expected_content": "beaches in Hawaii",
        "description": "Should match the Hawaii beaches memory"
    },
    {
        "query": "Spanish city with Gothic architecture",
        "expected_content": "Barcelona",
        "description": "Should match the Barcelona memory"
    },
    {
        "query": "Restaurant serving pasta dishes",
        "expected_content": "Italian restaurant",
        "description": "Should match the Italian restaurant memory"
    },
    {
        "query": "Japanese food prepared at home",
        "expected_content": "make sushi",
        "description": "Should match the sushi making memory"
    },
    {
        "query": "Spicy food from Southeast Asia",
        "expected_content": "Thai curry",
        "description": "Should match the Thai curry memory"
    }
]

async def test_specific_semantic_queries():
    """Test specific semantic queries"""
    uri = "ws://localhost:8769"
    logger.info(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Wait for welcome message
            response = await websocket.recv()
            response_data = json.loads(response)
            logger.info(f"Received welcome: {response_data['type']}")
            
            # Run semantic queries
            success_count = 0
            for i, test in enumerate(SEMANTIC_QUERIES):
                logger.info(f"Test {i+1}/{len(SEMANTIC_QUERIES)}: {test['description']}")
                logger.info(f"Query: '{test['query']}' (should match '{test['expected_content']}')")
                
                await websocket.send(json.dumps({
                    "type": "search_memory",
                    "query": test['query'],
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
                
                # Check if the expected content is in the results
                found_expected = False
                for result in search_results:
                    content = result.get('content', '')
                    score = result.get('similarity_score', result.get('score', 0))
                    logger.info(f"Result: '{content[:50]}...' (Score: {score:.3f})")
                    
                    if test['expected_content'] in content:
                        found_expected = True
                        logger.info(f"✅ Found expected content! Score: {score:.3f}")
                        success_count += 1
                        break
                
                if not found_expected:
                    logger.warning(f"❌ Expected content not found in results")
                
                logger.info("-" * 50)
                
                # Small delay between queries
                await asyncio.sleep(1)
            
            # Calculate success rate
            success_rate = success_count / len(SEMANTIC_QUERIES) * 100
            logger.info(f"Semantic search success rate: {success_rate:.1f}%")
            logger.info(f"Successfully matched {success_count} out of {len(SEMANTIC_QUERIES)} queries")
            
    except Exception as e:
        logger.error(f"Error in test: {e}", exc_info=True)

if __name__ == "__main__":
    logger.info("Starting specific semantic query test")
    asyncio.run(test_specific_semantic_queries())
    logger.info("Test completed")