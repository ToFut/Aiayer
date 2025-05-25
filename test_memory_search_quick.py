#!/usr/bin/env python3
"""
Quick test of memory search functionality
"""
import sys
import asyncio
import json

# Add memory module to path
sys.path.append('/Users/segevbin/Desktop/SensAI/Aiayer')

async def test_memory_search():
    """Quick test of memory search"""
    try:
        from memory.memory_system import MemorySystem
        
        print("🔍 Testing Memory Search...")
        memory_system = MemorySystem()
        
        # Test search for development activities
        results = await memory_system.search_memory(
            query="development coding cursor",
            limit=3,
            context_aware=True
        )
        
        print(f"\n📋 Search Results for 'development coding cursor':")
        if results:
            for i, result in enumerate(results, 1):
                print(f"  {i}. Score: {result.get('score', 0):.3f}")
                print(f"     Type: {result.get('memory_type', 'unknown')}")
                print(f"     Content preview: {str(result.get('content', ''))[:100]}...")
        else:
            print("  No results found")
        
        # Test search for productivity
        results2 = await memory_system.search_memory(
            query="productivity workflow",
            limit=3,
            context_aware=True
        )
        
        print(f"\n📋 Search Results for 'productivity workflow':")
        if results2:
            for i, result in enumerate(results2, 1):
                print(f"  {i}. Score: {result.get('score', 0):.3f}")
                print(f"     Type: {result.get('memory_type', 'unknown')}")
        else:
            print("  No results found")
        
        print("\n✅ Memory search test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_memory_search())