#!/usr/bin/env python3
"""
Comprehensive test for semantic memory capabilities
"""

import asyncio
import json
import logging
import websockets
import time
import datetime
import random

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/semantic_memory_test.log', mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("semantic_test")

# Test data - semantically related but using different words
TEST_MEMORIES = [
    # Technology memories
    {
        "content": "I was working on a Python project to analyze data from our sensors.",
        "source": "test",
        "tags": ["work", "programming", "python"]
    },
    {
        "content": "The JavaScript frontend is making API calls to our backend services.",
        "source": "test",
        "tags": ["work", "programming", "javascript"]
    },
    {
        "content": "Our cloud infrastructure needs to scale to handle increasing traffic.",
        "source": "test",
        "tags": ["work", "cloud", "infrastructure"]
    },
    
    # Travel memories
    {
        "content": "The trip to Japan was amazing, especially the food in Tokyo.",
        "source": "test",
        "tags": ["travel", "japan", "food"]
    },
    {
        "content": "Visiting the beaches in Hawaii was a relaxing vacation experience.",
        "source": "test",
        "tags": ["travel", "hawaii", "vacation"]
    },
    {
        "content": "The architecture in Barcelona's Gothic Quarter is stunning.",
        "source": "test",
        "tags": ["travel", "spain", "architecture"]
    },
    
    # Food memories
    {
        "content": "The new Italian restaurant has excellent pasta dishes.",
        "source": "test",
        "tags": ["food", "restaurant", "italian"]
    },
    {
        "content": "I learned how to make sushi at home with fresh ingredients.",
        "source": "test",
        "tags": ["food", "cooking", "japanese"]
    },
    {
        "content": "The spicy Thai curry at the local market was incredibly flavorful.",
        "source": "test",
        "tags": ["food", "thai", "spicy"]
    }
]

# Semantic search test queries with expected semantic matches
SEMANTIC_TESTS = [
    {
        "query": "Software development projects",
        "expected_categories": ["python", "javascript", "programming"],
        "description": "Should match programming-related memories"
    },
    {
        "query": "International travel experiences",
        "expected_categories": ["travel", "japan", "hawaii", "spain"],
        "description": "Should match travel-related memories"
    },
    {
        "query": "Culinary experiences and dishes",
        "expected_categories": ["food", "restaurant", "cooking"],
        "description": "Should match food-related memories"
    },
    {
        "query": "Computer code and software",
        "expected_categories": ["programming", "python", "javascript"],
        "description": "Should match programming without using the word 'programming'"
    },
    {
        "query": "Vacation destinations",
        "expected_categories": ["travel", "hawaii", "japan", "spain"],
        "description": "Should match travel memories using 'vacation' concept"
    },
    {
        "query": "Web development",
        "expected_categories": ["javascript", "programming"],
        "description": "Should match frontend development memories"
    },
    {
        "query": "Asian cuisine",
        "expected_categories": ["japanese", "thai", "food"],
        "description": "Should match Asian food memories"
    }
]

async def test_semantic_capabilities():
    """Test semantic memory capabilities"""
    uri = "ws://localhost:8769"
    logger.info(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Wait for welcome message
            response = await websocket.recv()
            response_data = json.loads(response)
            logger.info(f"Received welcome: {response_data['type']}")
            
            # Ping to check system availability
            await websocket.send(json.dumps({"type": "ping"}))
            response = await websocket.recv()
            response_data = json.loads(response)
            
            if not response_data.get('memory_system_available', False):
                logger.error("Memory system is not available!")
                return
            
            logger.info("Memory system is available. Adding test memories...")
            
            # Add test memories
            for i, memory in enumerate(TEST_MEMORIES):
                logger.info(f"Adding memory {i+1}/{len(TEST_MEMORIES)}: {memory['content'][:30]}...")
                await websocket.send(json.dumps({
                    "type": "add_memory",
                    **memory
                }))
                
                response = await websocket.recv()
                response_data = json.loads(response)
                
                if not response_data.get('success', False):
                    logger.error(f"Failed to add memory: {response_data.get('error', 'Unknown error')}")
                else:
                    logger.info(f"Successfully added memory with ID: {response_data.get('memory_id')}")
                
                # Small delay to avoid overwhelming the server
                await asyncio.sleep(0.5)
            
            logger.info("All test memories added. Running semantic search tests...")
            
            # Run semantic search tests
            results = []
            for i, test in enumerate(SEMANTIC_TESTS):
                logger.info(f"Test {i+1}/{len(SEMANTIC_TESTS)}: {test['description']}")
                logger.info(f"Query: '{test['query']}'")
                
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
                
                # Analyze results
                found_categories = set()
                for result in search_results:
                    # Extract tags
                    tags = result.get('tags', [])
                    if isinstance(tags, str):
                        tags = tags.split(',')
                    
                    # Add tags to found categories
                    found_categories.update(tags)
                    
                    # Log the result with similarity score
                    score = result.get('similarity_score', result.get('score', 0))
                    logger.info(f"Result: '{result.get('content', '')[:50]}...' (Score: {score:.3f})")
                
                # Check if expected categories were found
                expected = set(test['expected_categories'])
                matches = expected.intersection(found_categories)
                missing = expected - found_categories
                
                success_percentage = len(matches) / len(expected) * 100 if expected else 0
                
                test_result = {
                    "query": test['query'],
                    "description": test['description'],
                    "success_percentage": success_percentage,
                    "matches": list(matches),
                    "missing": list(missing),
                    "found_categories": list(found_categories)
                }
                
                results.append(test_result)
                
                if missing:
                    logger.warning(f"Missing expected categories: {missing}")
                else:
                    logger.info(f"All expected categories found!")
                
                logger.info(f"Test completed with {success_percentage:.1f}% match rate")
                logger.info("-" * 50)
                
                # Small delay between tests
                await asyncio.sleep(1)
            
            # Calculate overall performance
            overall_success = sum(r['success_percentage'] for r in results) / len(results)
            logger.info(f"Overall semantic search performance: {overall_success:.1f}%")
            
            # Output summary
            logger.info("\n===== SEMANTIC SEARCH TEST SUMMARY =====")
            for i, result in enumerate(results):
                logger.info(f"Test {i+1}: {result['query']}")
                logger.info(f"  - Success: {result['success_percentage']:.1f}%")
                logger.info(f"  - Matches: {', '.join(result['matches'])}")
                logger.info(f"  - Missing: {', '.join(result['missing']) if result['missing'] else 'None'}")
            
            logger.info(f"\nOVERALL PERFORMANCE: {overall_success:.1f}%")
            logger.info("======================================")
            
    except Exception as e:
        logger.error(f"Error in test: {e}", exc_info=True)

if __name__ == "__main__":
    logger.info("Starting semantic memory capability test")
    asyncio.run(test_semantic_capabilities())
    logger.info("Test completed")