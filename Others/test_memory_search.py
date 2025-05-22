#!/usr/bin/env python3
"""
Test script to demonstrate memory search functionality in the MemorySystem
"""
import asyncio
import json
from datetime import datetime

# Import the memory system
from memory.memory_system import MemorySystem
from memory.enhanced_semantic_search import enhanced_search

async def main():
    print("=== Testing Memory Search Functionality ===")
    
    # Initialize memory system
    print("\nInitializing memory system...")
    memory = MemorySystem()
    await memory.initialize()
    print("Memory system initialized")
    
    # Add sample data to memory
    print("\nAdding test data to memory...")
    
    # Add message about coding
    coding_message = {
        'type': 'user_message',
        'content': 'I am working on a Python project with semantic search capabilities',
        'timestamp': datetime.now().isoformat()
    }
    await memory.add_message(coding_message)
    print("Added coding message")
    
    # Add message about yesterday
    yesterday_message = {
        'type': 'user_message',
        'content': 'Yesterday I was debugging the screen sensor integration',
        'timestamp': datetime.now().isoformat()
    }
    await memory.add_message(yesterday_message)
    print("Added yesterday message")
    
    # Add current screen context
    screen_context = {
        'type': 'context',
        'content': 'Current screen shows code editor with Python files',
        'window_title': 'VS Code - memory_system.py',
        'timestamp': datetime.now().isoformat()
    }
    await memory.add_to_context_memory(screen_context)
    print("Added screen context")
    
    # Wait briefly for indexing
    print("\nWaiting for indexing to complete...")
    await asyncio.sleep(1)
    
    # Test various searches
    print("\n=== Search Results ===")
    
    # Search for yesterday's activities
    print("\n1. Searching for 'what was I working on yesterday'...")
    results = await memory.search_memory('what was I working on yesterday', limit=2)
    print(f"Found {len(results)} results:")
    for i, result in enumerate(results):
        print(f"  Result {i+1}: Score: {result.get('score', 0):.2f}")
        print(f"  Content: {result.get('content', '')[:100]}...")
        print(f"  Source: {result.get('source', 'unknown')}")
        print("  ---")
    
    # Search for current screen
    print("\n2. Searching for 'what is on my screen'...")
    results = await memory.search_memory('what is on my screen', limit=2)
    print(f"Found {len(results)} results:")
    for i, result in enumerate(results):
        print(f"  Result {i+1}: Score: {result.get('score', 0):.2f}")
        print(f"  Content: {result.get('content', '')[:100]}...")
        print(f"  Source: {result.get('source', 'unknown')}")
        print("  ---")
    
    # Search for Python project
    print("\n3. Searching for 'python project'...")
    results = await memory.search_memory('python project', limit=2)
    print(f"Found {len(results)} results:")
    for i, result in enumerate(results):
        print(f"  Result {i+1}: Score: {result.get('score', 0):.2f}")
        print(f"  Content: {result.get('content', '')[:100]}...")
        print(f"  Source: {result.get('source', 'unknown')}")
        print("  ---")
    
    # Get memory stats
    stats = enhanced_search.get_stats()
    print("\nMemory search stats:")
    print(json.dumps(stats, indent=2))
    
    # Cleanup
    await memory.cleanup()
    print("\nMemory system cleaned up")

if __name__ == "__main__":
    asyncio.run(main())