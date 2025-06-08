#!/usr/bin/env python3
"""
Verify the memory interface WebSocket connection and add a test memory
"""

import asyncio
import json
import logging
import websockets
import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("verify_interface")

async def verify_memory_interface():
    """Verify memory interface by adding a test memory and searching for it"""
    uri = "ws://localhost:8769"
    logger.info(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Wait for welcome message
            response = await websocket.recv()
            response_data = json.loads(response)
            logger.info(f"Received welcome: {response_data['type']}")
            
            # Add a test memory
            test_memory = {
                "type": "add_memory",
                "content": f"This is a verification test memory added at {datetime.datetime.now().isoformat()}",
                "source": "verification_test",
                "tags": ["test", "verification", "interface"]
            }
            logger.info(f"Adding test memory: {test_memory['content']}")
            
            await websocket.send(json.dumps(test_memory))
            response = await websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get('success'):
                memory_id = response_data.get('memory_id', 'unknown')
                logger.info(f"Test memory added successfully with ID: {memory_id}")
            else:
                logger.error(f"Failed to add test memory: {response_data.get('error', 'Unknown error')}")
                return
            
            # Search for the test memory
            await asyncio.sleep(1)  # Give it a moment to be indexed
            
            search_query = {
                "type": "search_memory",
                "query": "verification test memory",
                "top_k": 5,
                "min_similarity": 0.1
            }
            logger.info(f"Searching for test memory: {search_query['query']}")
            
            await websocket.send(json.dumps(search_query))
            response = await websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get('type') == 'search_results':
                results = response_data.get('results', [])
                logger.info(f"Found {len(results)} results")
                
                found_our_memory = False
                for result in results:
                    content = result.get('content', '')
                    score = result.get('similarity_score', result.get('score', 0))
                    logger.info(f"Result: '{content[:50]}...' (Score: {score:.3f})")
                    
                    if "verification test memory" in content:
                        found_our_memory = True
                        logger.info(f"✅ Found our verification test memory! Score: {score:.3f}")
                        break
                
                if not found_our_memory:
                    logger.warning("❌ Our verification test memory was not found in search results")
            else:
                logger.error(f"Unexpected response type: {response_data.get('type')}")
            
            # Get system stats
            logger.info("Getting system stats...")
            await websocket.send(json.dumps({"type": "get_system_stats"}))
            response = await websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get('type') == 'system_stats':
                stats = response_data.get('stats', {})
                logger.info(f"Total memories: {stats.get('total_memories', 'unknown')}")
                logger.info(f"Short-term memories: {stats.get('short_term_count', 'unknown')}")
                logger.info(f"Long-term memories: {stats.get('long_term_count', 'unknown')}")
                logger.info(f"Average search time: {stats.get('search_stats', {}).get('avg_search_time_ms', 'unknown')}ms")
            else:
                logger.error(f"Unexpected response type: {response_data.get('type')}")
            
            logger.info("Verification complete - the memory interface is working correctly!")
            
    except Exception as e:
        logger.error(f"Error in verification: {e}", exc_info=True)

if __name__ == "__main__":
    logger.info("Starting memory interface verification")
    asyncio.run(verify_memory_interface())
    logger.info("Verification completed")