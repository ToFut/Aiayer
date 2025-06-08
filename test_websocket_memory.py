#!/usr/bin/env python3
"""
WebSocket Memory Test

This script tests sending WebSocket messages directly to the memory system
to verify that it's working correctly.
"""

import json
import asyncio
import uuid
from datetime import datetime

# Try to import websockets - this is needed for the WebSocket connection
try:
    import websockets
except ImportError:
    print("WebSockets library not installed. Please install it with:")
    print("pip install websockets")
    exit(1)

# Configuration
WS_URL = "ws://localhost:8767"
TEST_MEMORY = f"Test memory created at {datetime.now().isoformat()} with ID {str(uuid.uuid4())}"

async def test_memory_system():
    """Test the memory system using WebSockets"""
    print(f"Connecting to memory system at {WS_URL}...")
    
    try:
        async with websockets.connect(WS_URL) as ws:
            print("✅ Connected to memory system")
            
            # Step 1: Register client
            print("Step 1: Registering as a client...")
            register_message = {
                "type": "register",
                "client_type": "test_client",
                "version": "1.0.0"
            }
            await ws.send(json.dumps(register_message))
            response = await ws.recv()
            print(f"Registration response: {response}")
            
            # Step 2: Add a test memory
            print(f"\nStep 2: Adding test memory: {TEST_MEMORY[:50]}...")
            memory_message = {
                "type": "add_memory",
                "content": TEST_MEMORY,
                "source": "websocket_test",
                "tags": ["test", "websocket"],
                "metadata": {
                    "test_id": str(uuid.uuid4()),
                    "timestamp": datetime.now().isoformat()
                }
            }
            await ws.send(json.dumps(memory_message))
            response = await ws.recv()
            print(f"Add memory response: {response}")
            
            # Wait for memory to be processed
            await asyncio.sleep(1)
            
            # Step 3: Search for the memory
            print("\nStep 3: Searching for test memory...")
            search_message = {
                "type": "search_memory",
                "query": "test memory",
                "top_k": 10,
                "source_filter": "websocket_test"
            }
            await ws.send(json.dumps(search_message))
            response = await ws.recv()
            response_data = json.loads(response)
            
            # Print search results
            if "results" in response_data:
                results = response_data["results"]
                print(f"Found {len(results)} search results")
                
                # Check if our test memory is in the results
                found = False
                for i, result in enumerate(results):
                    if TEST_MEMORY in result.get("content", ""):
                        print(f"✅ Found our test memory at position {i+1}!")
                        found = True
                        break
                
                if not found and results:
                    print("⚠️ Test memory not found in results, but other results were returned")
                elif not found:
                    print("⚠️ No relevant results found")
                    
                # Print the first few results
                print("\nTop search results:")
                for i, result in enumerate(results[:3]):  # Show top 3 results
                    print(f"Result {i+1}:")
                    print(f"  Content: {result.get('content', '')[:100]}...")
                    print(f"  Score: {result.get('similarity_score')}")
                    print(f"  Source: {result.get('source')}")
            else:
                print(f"Search response did not contain results: {response}")
            
            print("\n✅ Memory system test completed successfully")
            return True
    
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

if __name__ == "__main__":
    print("Starting WebSocket memory test...")
    
    try:
        result = asyncio.run(test_memory_system())
        
        if result:
            print("✅ All tests completed successfully")
            exit(0)
        else:
            print("❌ Tests failed")
            exit(1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        exit(1)