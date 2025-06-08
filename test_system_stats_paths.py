#!/usr/bin/env python3
"""
Test script for system_stats handler to verify it can handle different memory_state.json paths
"""

import asyncio
import websockets
import json
import sys
import os
import shutil

async def test_system_stats():
    """Test the system_stats handler with different memory_state.json locations"""
    original_files = {}
    created_files = []
    
    try:
        # Save original state of any existing memory state files
        possible_paths = [
            os.path.join('memory', 'memory_state.json'),
            os.path.join('memory', 'memory', 'memory_state.json'),
            'memory_state.json'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                print(f"Backing up existing {path}")
                with open(path, 'r') as f:
                    original_files[path] = f.read()
                    
        # Test with memory/memory/memory_state.json
        print("\n--- TEST 1: Using memory/memory/memory_state.json ---")
        os.makedirs(os.path.join('memory', 'memory'), exist_ok=True)
        
        # Create test memory state file
        test_memory_state = {
            "short_term": [{"id": "mem1", "content": "Test memory 1"}],
            "long_term": [{"id": "mem2", "content": "Test memory 2"}, {"id": "mem3", "content": "Test memory 3"}]
        }
        
        # Remove other memory state files temporarily
        for path in possible_paths:
            if os.path.exists(path) and path != os.path.join('memory', 'memory', 'memory_state.json'):
                if path not in original_files:  # Only save if not already saved
                    with open(path, 'r') as f:
                        original_files[path] = f.read()
                os.rename(path, f"{path}.temp")
                print(f"Temporarily moved {path} to {path}.temp")
        
        # Create our test memory state file
        with open(os.path.join('memory', 'memory', 'memory_state.json'), 'w') as f:
            json.dump(test_memory_state, f)
            created_files.append(os.path.join('memory', 'memory', 'memory_state.json'))
            print(f"Created test memory state file with 1 short-term and 2 long-term memories")
        
        # Test the system stats endpoint
        result = await test_memory_stats_endpoint()
        
        # Test with memory/memory_state.json
        print("\n--- TEST 2: Using memory/memory_state.json ---")
        # Remove the previous test file
        os.remove(os.path.join('memory', 'memory', 'memory_state.json'))
        created_files.remove(os.path.join('memory', 'memory', 'memory_state.json'))
        
        # Update test memory state
        test_memory_state = {
            "short_term": [{"id": "mem1", "content": "Test memory 1"}, {"id": "mem4", "content": "Test memory 4"}],
            "long_term": [{"id": "mem2", "content": "Test memory 2"}]
        }
        
        with open(os.path.join('memory', 'memory_state.json'), 'w') as f:
            json.dump(test_memory_state, f)
            created_files.append(os.path.join('memory', 'memory_state.json'))
            print(f"Created test memory state file with 2 short-term and 1 long-term memories")
        
        # Test the system stats endpoint
        result = await test_memory_stats_endpoint()
        
        # Test with root memory_state.json
        print("\n--- TEST 3: Using root memory_state.json ---")
        # Remove the previous test file
        os.remove(os.path.join('memory', 'memory_state.json'))
        created_files.remove(os.path.join('memory', 'memory_state.json'))
        
        # Update test memory state
        test_memory_state = {
            "short_term": [{"id": "mem1", "content": "Test memory 1"}, {"id": "mem4", "content": "Test memory 4"}, {"id": "mem5", "content": "Test memory 5"}],
            "long_term": []
        }
        
        with open('memory_state.json', 'w') as f:
            json.dump(test_memory_state, f)
            created_files.append('memory_state.json')
            print(f"Created test memory state file with 3 short-term and 0 long-term memories")
        
        # Test the system stats endpoint
        result = await test_memory_stats_endpoint()
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        # Restore any moved files
        for path in possible_paths:
            temp_path = f"{path}.temp"
            if os.path.exists(temp_path):
                os.rename(temp_path, path)
                print(f"Restored {path} from {temp_path}")
        
        # Restore original files
        for path, content in original_files.items():
            with open(path, 'w') as f:
                f.write(content)
                print(f"Restored original content for {path}")
        
        # Clean up any created files that weren't restored
        for path in created_files:
            if os.path.exists(path) and path not in original_files:
                os.remove(path)
                print(f"Removed test file {path}")

async def test_memory_stats_endpoint():
    """Connect to the backend and test the system_stats handler"""
    try:
        # Connect to the backend server
        async with websockets.connect('ws://localhost:8767') as websocket:
            print("Connected to Enhanced Enterprise Backend")
            
            # Receive welcome message
            response = await websocket.recv()
            print(f"Received welcome message")
            
            # Send register message
            register_msg = {
                "type": "register",
                "client": "test_client",
                "version": "1.0.0"
            }
            await websocket.send(json.dumps(register_msg))
            response = await websocket.recv()
            print(f"Registered successfully")
            
            # Send get_system_stats request
            stats_msg = {
                "type": "get_system_stats"
            }
            print("Sending system_stats request...")
            await websocket.send(json.dumps(stats_msg))
            
            # Wait for response
            response = await websocket.recv()
            stats_data = json.loads(response)
            
            # Check if we got a proper response
            if stats_data.get("type") == "system_stats":
                print("\n✅ SUCCESS: Received system_stats response!")
                
                # Extract memory metrics
                memory_available = stats_data.get("memory_system_available", False)
                memory_stats = stats_data.get("stats", {})
                total_memories = memory_stats.get("total_memories", 0)
                short_term_count = memory_stats.get("short_term_count", 0)
                long_term_count = memory_stats.get("long_term_count", 0)
                
                print(f"Memory system available: {memory_available}")
                print(f"Total memories: {total_memories}")
                print(f"Short-term memories: {short_term_count}")
                print(f"Long-term memories: {long_term_count}")
                
                return True
            else:
                print("\n❌ ERROR: Did not receive proper system_stats response")
                print(f"Response type: {stats_data.get('type')}")
                return False
                
    except Exception as e:
        print(f"Error connecting to backend: {e}")
        return False

if __name__ == "__main__":
    print("Testing system_stats handler with different memory state file paths...")
    result = asyncio.run(test_system_stats())
    sys.exit(0 if result else 1)