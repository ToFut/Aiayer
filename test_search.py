#!/usr/bin/env python3
"""
Test script for memory search functionality
"""
import asyncio
from memory.memory_system import MemorySystem
from memory.enhanced_semantic_search import enhanced_search

async def main():
    # Initialize memory system
    print("Initializing memory system...")
    memory_system = MemorySystem()
    await memory_system.initialize()
    
    # Print memory statistics
    stats = enhanced_search.get_stats()
    print(f"Memory search stats: {stats}")
    
    # Test search with a few different queries
    print("\nSearch for 'current screen content':")
    results = await memory_system.search_memory('current screen content', limit=2)
    print(f"Found {len(results)} results")
    for i, result in enumerate(results):
        print(f"Result {i+1}: Score: {result.get('score', 0)}")
        print(f"Content: {result.get('content', '')[:100]}...")
        print(f"Source: {result.get('source', 'unknown')}")
        print("---")
    
    print("\nSearch for 'what was I working on':")
    results = await memory_system.search_memory('what was I working on', limit=2)
    print(f"Found {len(results)} results")
    for i, result in enumerate(results):
        print(f"Result {i+1}: Score: {result.get('score', 0)}")
        print(f"Content: {result.get('content', '')[:100]}...")
        print(f"Source: {result.get('source', 'unknown')}")
        print("---")
    
    # Cleanup
    await memory_system.cleanup()
    print("Memory system cleaned up")

if __name__ == "__main__":
    asyncio.run(main())