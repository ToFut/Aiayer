import asyncio
from memory.memory_system import MemorySystem
import json

async def main():
    # Initialize memory system
    memory_system = MemorySystem()
    await memory_system.initialize()
    
    # Print current context memory contents
    print("\n=== Current Context Memory Contents ===")
    print("\nContext Memory Keys:")
    for key in memory_system.context_memory.keys():
        print(f"  - {key}")
    
    print("\nSensor Data:")
    if 'sensor_data' in memory_system.context_memory:
        for sensor_type, data in memory_system.context_memory['sensor_data'].items():
            print(f"\n  {sensor_type.upper()} SENSOR:")
            print(f"    Latest timestamp: {list(data.keys())[-1] if data else 'No data'}")
            if data:
                latest_data = data[list(data.keys())[-1]]
                print(f"    Data keys: {list(latest_data.get('data', {}).keys())}")
    
    print("\nSearchable Items:")
    if 'searchable_items' in memory_system.context_memory:
        items = memory_system.context_memory['searchable_items']
        print(f"  Total items: {len(items)}")
        for timestamp, item in list(items.items())[-3:]:  # Show last 3 items
            print(f"\n  Item from {timestamp}:")
            print(f"    Content: {item.get('text', '')[:100]}...")
    
    # Run memory search test
    test_results = await memory_system.test_memory_search()
    
    # Print results in a readable format
    print("\n=== Memory Search Test Results ===")
    for memory_type, results in test_results.items():
        print(f"\n{memory_type.upper()} MEMORY RESULTS:")
        if not results:
            print("  No results found")
            continue
            
        for i, result in enumerate(results):
            print(f"\n  Result {i+1}:")
            print(f"    Score: {result['score']:.2f}")
            print(f"    Content: {result['content'][:100]}...")
            print(f"    Source: {result['source']}")
            print(f"    Timestamp: {result['timestamp']}")
    
    # Cleanup
    await memory_system.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 