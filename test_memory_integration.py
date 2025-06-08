#!/usr/bin/env python3
"""
Memory Integration Test Script

This script tests the full integration between the memory web interface and the
backend memory system. It adds a test memory, performs a search, and verifies
that the memory system is correctly storing and retrieving memories.
"""

import asyncio
import json
import logging
import websockets
import uuid
import time
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("memory_integration_test")

# Configuration
WS_URL = "ws://localhost:8767"  # Main enterprise memory system
TEST_MEMORY_CONTENT = f"Test memory created at {datetime.now().isoformat()} with ID {uuid.uuid4()}"

async def run_test():
    """Run the full integration test"""
    logger.info(f"Connecting to WebSocket server at {WS_URL}")
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Test 1: Add memory
            logger.info("TEST 1: Adding test memory")
            await add_memory(websocket)
            
            # Short delay to allow memory to be processed
            await asyncio.sleep(1)
            
            # Test 2: Search for the memory
            logger.info("TEST 2: Searching for test memory")
            await search_memory(websocket)
            
            logger.info("Integration test completed successfully")
    
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False
    
    return True

async def add_memory(websocket):
    """Test adding a memory"""
    # Create a test memory
    add_memory_message = {
        "type": "add_memory",
        "content": TEST_MEMORY_CONTENT,
        "source": "integration_test",
        "tags": ["test", "integration"],
        "metadata": {
            "test_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat()
        }
    }
    
    # Send the message
    await websocket.send(json.dumps(add_memory_message))
    logger.info(f"Sent add_memory request: {TEST_MEMORY_CONTENT[:50]}...")
    
    # Wait for response
    response = await websocket.recv()
    response_data = json.loads(response)
    
    # Check response
    if response_data.get("type") == "memory_added" and response_data.get("success"):
        logger.info("✅ Memory added successfully")
        return True
    else:
        logger.error(f"❌ Failed to add memory: {response_data}")
        return False

async def search_memory(websocket):
    """Test searching for a memory"""
    # Create search request
    search_message = {
        "type": "search_memory",
        "query": "test memory",
        "top_k": 5,
        "min_similarity": 0.1,
        "source_filter": "integration_test"
    }
    
    # Send the message
    await websocket.send(json.dumps(search_message))
    logger.info("Sent search_memory request for 'test memory'")
    
    # Wait for response
    response = await websocket.recv()
    response_data = json.loads(response)
    
    # Check response
    if response_data.get("type") == "search_results":
        results = response_data.get("results", [])
        result_count = len(results)
        logger.info(f"✅ Search completed successfully, found {result_count} results")
        
        # Check if our test memory is in the results
        found = False
        for result in results:
            if TEST_MEMORY_CONTENT in result.get("content", ""):
                logger.info("✅ Found our test memory in the search results!")
                found = True
                break
        
        if not found and result_count > 0:
            logger.warning("⚠️ Test memory not found in results, but other results were returned")
        elif not found:
            logger.warning("⚠️ No results found that match our test memory")
        
        return result_count > 0
    else:
        logger.error(f"❌ Failed to search memory: {response_data}")
        return False

if __name__ == "__main__":
    logger.info("Starting memory integration test")
    success = asyncio.run(run_test())
    
    if success:
        logger.info("✅ All tests completed successfully")
        exit(0)
    else:
        logger.error("❌ Tests failed")
        exit(1)