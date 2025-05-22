#\!/usr/bin/env python3
"""
Test Perception Query
Tests the perception query functionality by sending a test query and checking the response
"""
import asyncio
import websockets
import json
import logging
import os
import time
import sys
from datetime import datetime

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_perception.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('test_perception')

async def check_memory_for_screen_content():
    """Check if memory has screen content"""
    try:
        memory_file = "memory/memory_state.json"
        if not os.path.exists(memory_file):
            print("❌ Memory state file not found")
            return False
            
        with open(memory_file, 'r') as f:
            memory_state = json.load(f)
        
        # Check for screen content in context
        if "context" in memory_state and "screen_content" in memory_state["context"]:
            content = memory_state["context"]["screen_content"]
            if content and len(content) > 0:
                print(f"✅ Memory has screen content ({len(content)} chars)")
                return True
            else:
                print("⚠️ No screen content found in memory")
                return False
                
        print("⚠️ No screen content found in memory")
        return False
        
    except Exception as e:
        logger.error(f"Error checking memory: {e}")
        print(f"❌ Error checking memory: {e}")
        return False

async def test_perception_query():
    """Test a perception query via WebSocket"""
    # First check memory for screen content
    has_screen_content = await check_memory_for_screen_content()
    if not has_screen_content:
        print("⚠️ No screen content found in memory")
    
    # Connect to WebSocket server
    server_url = "ws://localhost:8765"
    print(f"Connecting to WebSocket server at {server_url}...")
    
    try:
        async with websockets.connect(server_url, close_timeout=5) as websocket:
            print("✅ Connected to WebSocket server")
            
            # Process welcome message
            response = await websocket.recv()
            data = json.loads(response)
            logger.info(f"Received welcome message: {data.get('type')}")
            
            # Send identification
            await websocket.send(json.dumps({
                "type": "connection_established",
                "payload": {
                    "client": "test_client",
                    "version": "1.0.0"
                }
            }))
            
            # Wait a moment
            print("⚠️ Waiting 2 seconds to allow server to process context...")
            await asyncio.sleep(2)
            
            # Request context first
            print("ℹ️ Requesting context...")
            await websocket.send(json.dumps({
                "type": "context_request",
                "payload": {
                    "timestamp": datetime.now().isoformat()
                }
            }))
            
            # Wait for context response
            context_response = await websocket.recv()
            context_data = json.loads(context_response)
            if context_data.get("type") == "context_response":
                print("✅ Received context response")
            else:
                print("⚠️ Did not receive context response")
            
            # Send perception query
            query = "what am I seeing?"
            print(f"ℹ️ Sending perception query: '{query}'")
            
            await websocket.send(json.dumps({
                "type": "message",
                "payload": {
                    "message": query,
                    "timestamp": datetime.now().isoformat()
                }
            }))
            
            # Wait for response with timeout
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                data = json.loads(response)
                
                response_type = data.get("type")
                if response_type == "error":
                    error = data.get("payload", {}).get("message", "Unknown error")
                    print(f"❌ Received error: {error}")
                    return False
                
                content = data.get("payload", {}).get("content", "")
                print(f"✅ Received response ({len(content)} chars):")
                print(f"---\n{content}\n---")
                return True
                
            except asyncio.TimeoutError:
                print("❌ Timeout waiting for response")
                return False
                
    except ConnectionRefusedError:
        print("❌ Connection refused - WebSocket server not running")
        return False
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"❌ Error: {e}")
        return False

async def main():
    """Main function"""
    print("\n=== Perception Query Test ===\n")
    
    success = await test_perception_query()
    
    print("\n=== TEST SUMMARY ===\n")
    print(f"Perception Query Test: {'PASSED' if success else 'FAILED'}")
    print(f"{'✅ All tests passed\!' if success else '❌ Some tests failed. See detailed output above.'}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\n❌ Fatal error: {e}")
