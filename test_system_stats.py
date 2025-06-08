#!/usr/bin/env python3
"""
Test script for system_stats handler in enhanced_enterprise_backend_with_context.py
"""

import asyncio
import websockets
import json
import sys

async def test_system_stats():
    """Test the system_stats handler in the backend server"""
    try:
        # Connect to the backend server
        async with websockets.connect('ws://localhost:8767') as websocket:
            print("Connected to Enhanced Enterprise Backend")
            
            # Receive welcome message
            response = await websocket.recv()
            print(f"Received welcome: {response[:100]}...")
            
            # Send register message
            register_msg = {
                "type": "register",
                "client": "test_client",
                "version": "1.0.0"
            }
            await websocket.send(json.dumps(register_msg))
            response = await websocket.recv()
            print(f"Register response: {response[:100]}...")
            
            # Send get_system_stats request
            stats_msg = {
                "type": "get_system_stats"
            }
            print("\nSending system_stats request...")
            await websocket.send(json.dumps(stats_msg))
            
            # Wait for response
            response = await websocket.recv()
            stats_data = json.loads(response)
            print("\nSystem stats response:")
            print(json.dumps(stats_data, indent=2))
            
            # Check if we got a proper response
            if stats_data.get("type") == "system_stats":
                print("\n✅ SUCCESS: Received system_stats response!")
                
                # Extract some key metrics
                memory_available = stats_data.get("memory_system_available", False)
                memory_stats = stats_data.get("stats", {})
                total_memories = memory_stats.get("total_memories", 0)
                
                print(f"Memory system available: {memory_available}")
                print(f"Total memories: {total_memories}")
                print(f"Short-term memories: {memory_stats.get('short_term_count', 0)}")
                print(f"Long-term memories: {memory_stats.get('long_term_count', 0)}")
            else:
                print("\n❌ ERROR: Did not receive proper system_stats response")
                print(f"Response type: {stats_data.get('type')}")
                
    except Exception as e:
        print(f"Error: {e}")
        return False
        
    return True

if __name__ == "__main__":
    print("Testing system_stats handler...")
    result = asyncio.run(test_system_stats())
    sys.exit(0 if result else 1)