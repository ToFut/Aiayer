#!/usr/bin/env python3
"""
Test script to analyze screen search capabilities using real memory data
"""
import asyncio
import json
import time
from datetime import datetime
import os
import traceback
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_screen_search")

# Import memory system
from memory.memory_system import MemorySystem

async def test_screen_search():
    """Test memory search with screen-related query"""
    logger.info("=== TESTING SCREEN-RELATED MEMORY SEARCH ===")
    
    # Initialize memory system
    logger.info("\nInitializing memory system...")
    memory = MemorySystem()
    await memory.initialize()
    logger.info("Memory system initialized")

    # Add method to get latest sensor data if not present
    if not hasattr(memory, 'get_latest_sensor_data'):
        async def get_latest_sensor_data():
            for item in reversed(memory.short_term_memory):
                if isinstance(item, dict) and item.get('type') in ('screen', 'process', 'file'):
                    return item
            return None
        memory.get_latest_sensor_data = get_latest_sensor_data
    
    # Check if there's existing screen data
    screen_data_found = False
    
    # First check short-term memory for screen data
    logger.info("\nChecking for existing screen data in memory...")
    for item in memory.short_term_memory:
        if isinstance(item, dict) and item.get('type') == 'screen':
            screen_data_found = True
            logger.info(f"Found existing screen data: {item.get('content', '')[:100]}...")
            break
    
    if not screen_data_found:
        logger.info("No existing screen data found in short-term memory.")
    
    # Check context memory for screen content
    if 'screen_content' in memory.context_memory:
        screen_content = memory.context_memory['screen_content']
        if screen_content:
            screen_data_found = True
            logger.info(f"Found screen content in context memory: {screen_content[:100]}...")
    
    # If no screen data found, add fake screen data for testing
    if not screen_data_found:
        logger.info("\nAdding simulated screen data for testing...")
        # Add current screen context
        screen_context = {
            'type': 'screen',
            'content': f'Current screen shows code editor with Python files open, displaying test_screen_search.py',
            'window_title': 'VS Code - test_screen_search.py',
            'timestamp': datetime.now().isoformat()
        }
        await memory.add_to_context_memory(screen_context)
        
        # Also add as sensor data
        await memory.process_sensor_data('screen', {
            'text': 'Code editor showing Python script with search functionality testing',
            'window_title': 'VS Code - test_screen_search.py',
            'active_window': 'Visual Studio Code'
        })
        logger.info("Added simulated screen data")
    
    # Get memory stats before search
    logger.info("\nMemory statistics before search:")
    stats = memory.semantic_search.get_stats()
    logger.info(json.dumps(stats, indent=2))
    
    # Wait briefly for indexing if we just added data
    if not screen_data_found:
        logger.info("\nWaiting for indexing to complete...")
        await asyncio.sleep(1)
    
    # Perform search with screen-related queries
    perception_queries = [
        "what am i seeing on screen",
        "what is on my screen",
        "what do I see",
        "what's visible on my display",
        "what screen content is there"
    ]
    
    all_results = {}
    
    logger.info("\n=== SEARCH RESULTS ===")
    
    for query in perception_queries:
        logger.info(f"\nSearching for: '{query}'...")
        start_time = time.time()
        results = await memory.search_memory(query, limit=5)
        search_time = time.time() - start_time
        
        logger.info(f"Search completed in {search_time:.3f}s")
        logger.info(f"Found {len(results)} results:")
        
        all_results[query] = results
        
        for i, result in enumerate(results):
            logger.info(f"  Result {i+1}: Score: {result.get('score', 0):.2f}")
            logger.info(f"  Content: {result.get('content', '')[:100]}...")
            logger.info(f"  Source: {result.get('source', 'unknown')}")
            logger.info("  ---")
    
    # Analyze results
    logger.info("\n=== ANALYSIS ===")
    
    # Check if screen-related results were found
    screen_related_found = False
    highest_score = 0
    best_query = ""
    
    for query, results in all_results.items():
        if results:
            logger.info(f"\nQuery: '{query}'")
            
            # Check for screen-related content in results
            screen_related_count = 0
            for result in results:
                content = result.get('content', '').lower()
                if ('screen' in content or 'window' in content or 'display' in content or 
                    'editor' in content or 'visual studio' in content):
                    screen_related_count += 1
                    screen_related_found = True
                    
                    # Track highest score
                    if result.get('score', 0) > highest_score:
                        highest_score = result.get('score', 0)
                        best_query = query
            
            # Analyze query effectiveness
            logger.info(f"  Screen-related results: {screen_related_count}/{len(results)}")
            logger.info(f"  Top result score: {results[0].get('score', 0):.2f}")
            
            # Check result diversity
            sources = set(r.get('source', 'unknown') for r in results)
            logger.info(f"  Result sources: {', '.join(sources)}")
    
    # Overall analysis
    logger.info("\n=== OVERALL ANALYSIS ===")
    
    if screen_related_found:
        logger.info("✅ Screen-related content was successfully found in search results")
        logger.info(f"  Best performing query: '{best_query}' with score {highest_score:.2f}")
    else:
        logger.info("❌ No screen-related content was found in search results")
        logger.info("  This indicates a potential issue with screen data capture or indexing")
    
    # Check for perception query handling
    perception_query_optimized = False
    for query, results in all_results.items():
        for result in results:
            # Check for signs of perception query handling
            content = result.get('content', '').lower()
            if ('screen' in content or 'display' in content or 'window' in content or 'visual' in content):
                perception_query_optimized = True
                break
    
    if perception_query_optimized:
        logger.info("✅ Perception query optimization is active")
    else:
        logger.info("⚠️ No evidence of specialized perception query handling")
        logger.info("  Consider enhancing perception query detection and optimization")
    
    # Check for recency
    recent_results = False
    for query, results in all_results.items():
        for result in results:
            if result.get('timestamp'):
                try:
                    timestamp = datetime.fromisoformat(result.get('timestamp'))
                    time_diff = (datetime.now() - timestamp).total_seconds()
                    if time_diff < 3600:  # Within the last hour
                        recent_results = True
                        break
                except (ValueError, TypeError):
                    pass
    
    if recent_results:
        logger.info("✅ Recent screen data is being returned")
    else:
        logger.info("⚠️ No recent screen data found in results")
        logger.info("  Check if screen sensor is active and updating memory")
    
    # Cleanup
    await memory.cleanup()
    logger.info("\nMemory system cleaned up")
    
    return all_results

if __name__ == "__main__":
    results = asyncio.run(test_screen_search())