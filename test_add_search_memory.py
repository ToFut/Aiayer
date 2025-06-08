#!/usr/bin/env python3
"""
Test adding and searching memory via WebSocket
"""
import asyncio
import websockets
import json
import logging
import sys
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('test_add_search_memory')

# WebSocket connection info
WS_URI = "ws://localhost:8769"

async def test_memory_system():
    """Test adding and searching for a memory"""
    try:
        logger.info(f"Connecting to {WS_URI}...")
        
        async with websockets.connect(WS_URI) as websocket:
            logger.info("Connected successfully!")
            
            # Receive welcome message
            response = await websocket.recv()
            logger.info(f"Received welcome message: {response}")
            
            # Create a unique test memory
            test_id = uuid.uuid4().hex[:8]
            test_memory = f"This is a test memory with unique ID {test_id} created at {datetime.now().isoformat()}"
            
            # Add the test memory
            logger.info(f"Adding test memory with ID: {test_id}")
            await websocket.send(json.dumps({
                "type": "add_memory",
                "content": test_memory,
                "source": "test",
                "tags": ["test", "verification", test_id]
            }))
            
            # Receive memory added response
            response = await websocket.recv()
            response_data = json.loads(response)
            logger.info(f"Memory added successfully: {response_data.get('success', False)}")
            
            if not response_data.get('success', False):
                logger.error(f"Failed to add memory: {response_data}")
                return False
                
            # Wait a moment for memory indexing
            await asyncio.sleep(1)
            
            # Search for the memory using its unique ID
            logger.info(f"Searching for memory with ID: {test_id}")
            await websocket.send(json.dumps({
                "type": "search_memory",
                "query": f"test memory {test_id}",
                "top_k": 5
            }))
            
            # Receive search results
            response = await websocket.recv()
            response_data = json.loads(response)
            results = response_data.get('results', [])
            result_count = len(results)
            
            logger.info(f"Search returned {result_count} results")
            
            # Verify the results
            if result_count > 0:
                # Check if our test memory is in the results
                found = False
                for result in results:
                    if test_id in result.get('content', ''):
                        found = True
                        logger.info(f"✅ TEST PASSED: Found our test memory with similarity: {result.get('similarity_score')}")
                        logger.info(f"Memory content: {result.get('content')[:100]}...")
                        break
                
                if not found:
                    logger.warning("⚠️ Results returned but our test memory was not found")
                    return False
                    
                return True
            else:
                logger.error("❌ TEST FAILED: No results returned for search")
                return False
                
    except Exception as e:
        logger.error(f"Error in test: {e}")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(test_memory_system())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)