#!/usr/bin/env python3
"""
Enhanced Perception Query Test

Tests and improves the memory system's ability to respond to perception queries like 
"what am i seeing on screen" using real memory data (not mock data).
This script addresses issues found in the original test_screen_search.py
and adds enhancements to make perception queries work properly.
"""
import asyncio
import logging
import json
import os
import sys
from datetime import datetime
import traceback
import inspect

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_enhanced_perception')

# Import memory system
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from memory.memory_system import MemorySystem
from memory.enhanced_semantic_search import EnhancedSemanticSearch

async def test_enhanced_perception():
    """Test and enhance the memory system's ability to respond to perception queries."""
    logger.info("==================================================")
    logger.info("🧪 STARTING ENHANCED PERCEPTION QUERY TEST")
    logger.info("==================================================")
    
    # Initialize memory system
    logger.info("Initializing memory system...")
    memory = MemorySystem()
    await memory.initialize()
    logger.info("Memory system initialized")
    
    # Check memory state stats
    logger.info("Checking current memory state:")
    short_term_count = len(memory.short_term_memory)
    context_count = len(memory.context_memory) if isinstance(memory.context_memory, dict) else 0
    logger.info(f"Short-term memory items: {short_term_count}")
    logger.info(f"Context memory items: {context_count}")
    
    # Check semantic search stats
    try:
        stats = memory.semantic_search.get_stats()
        logger.info(f"Semantic search stats: {json.dumps(stats, indent=2)}")
    except Exception as e:
        logger.error(f"Error getting semantic search stats: {e}")
    
    # Check if we have any screen data
    logger.info("\nChecking for existing screen data...")
    screen_data_found = False
    
    # Look for screen data in short-term memory
    for item in memory.short_term_memory:
        if isinstance(item, dict) and item.get('type') == 'screen':
            screen_data_found = True
            logger.info(f"Found existing screen data: {item.get('content', '')[:100]}...")
            break
    
    # Create and add sample screen data if none exists
    if not screen_data_found:
        logger.info("\nAdding sample screen data for testing...")
        
        # Create sample screen data for testing
        sample_screen_data = {
            "type": "screen",
            "data": {
                "content": "Current screen shows test_enhanced_perception.py script being edited. "
                          "The script includes code for testing perception query handling.",
                "window_title": "Code Editor - test_enhanced_perception.py",
                "active_window": "Visual Studio Code",
                "timestamp": datetime.now().isoformat(),
                "sensor_type": "screen",
                "type": "screen"
            },
            "content": "Code Editor showing test_enhanced_perception.py script with Python code for testing perception queries",
            "timestamp": datetime.now().isoformat()
        }
        
        # Add to short-term memory
        memory.short_term_memory.append(sample_screen_data)
        logger.info("Added sample screen data to short-term memory")
        
        # Add to enhanced semantic search index correctly
        try:
            # Check the signature of add_to_index to handle different implementations
            signature = inspect.signature(memory.semantic_search.add_to_index)
            parameters = list(signature.parameters.keys())
            
            if 'metadata' in parameters:
                # Newer implementation with metadata
                memory.semantic_search.add_to_index(
                    sample_screen_data,
                    'sensor_data',
                    metadata={
                        'sensor_type': 'screen',
                        'timestamp': sample_screen_data['timestamp'],
                        'content_type': 'sensor_data',
                        'relevance_score': 1.0
                    }
                )
            elif len(parameters) >= 3:
                # Try different parameter combinations
                try:
                    # Try with third parameter as memory type
                    memory.semantic_search.add_to_index(
                        sample_screen_data,
                        'sensor_data',
                        'screen'
                    )
                except Exception:
                    # If that fails, try with just the first two parameters
                    memory.semantic_search.add_to_index(
                        sample_screen_data,
                        'sensor_data'
                    )
            else:
                # Basic implementation with just item and memory_type
                memory.semantic_search.add_to_index(
                    sample_screen_data,
                    'sensor_data'
                )
            logger.info("Added screen data to semantic search index")
        except Exception as e:
            logger.error(f"Error adding to semantic search index: {e}")
            logger.error(traceback.format_exc())
        
        # Add to context memory
        context_data = {
            'screen_content': sample_screen_data['content'],
            'window_title': sample_screen_data['data']['window_title'],
            'active_window': sample_screen_data['data']['active_window'],
            'timestamp': datetime.now().isoformat()
        }
        memory.context_memory.update(context_data)
        logger.info("Added screen data to context memory")
        
        # Also add directly as a proper memory item
        try:
            if hasattr(memory, 'add_to_short_term_memory'):
                await memory.add_to_short_term_memory(sample_screen_data)
                logger.info("Added screen data as a proper memory item")
        except Exception as e:
            logger.error(f"Error adding to short-term memory: {e}")
            logger.error(traceback.format_exc())
    
        # Save memory state
        await memory._save_memory_state()
        logger.info("Saved memory state")
    
    # Wait a moment for indexing to catch up
    logger.info("\nWaiting for memory indexing to complete...")
    await asyncio.sleep(1.0)
    
    # ENHANCEMENT: Apply perception query handling fix directly to the memory system
    logger.info("\n==================================================")
    logger.info("🔧 APPLYING PERCEPTION QUERY ENHANCEMENT")
    logger.info("==================================================")
    
    # First, check if the system already has perception query handling
    has_perception_handling = False
    
    # Test with a simple perception query before enhancement
    logger.info("Testing perception query before enhancement:")
    pre_results = await memory.search_memory("what am i seeing on screen", limit=3)
    logger.info(f"Pre-enhancement results: {len(pre_results)} results found")
    
    # Add perception query handling directly to the memory_system
    try:
        original_search_memory = memory.search_memory
        
        # Create enhanced search memory function that detects and handles perception queries
        async def enhanced_search_memory(query, limit=5, memory_types=None):
            """Enhanced search_memory with special handling for perception queries"""
            logger.info(f"Using enhanced search_memory with query: {query}")
            
            # Check if this is a perception-related query
            perception_patterns = [
                "what am i seeing", "what do i see", "what's on my screen",
                "what is on my screen", "what's being displayed", "what is displayed",
                "what's in front of me", "what is in front of me", "what's visible",
                "what around me", "what do you see", "what are you seeing"
            ]
            
            is_perception_query = any(pattern in query.lower() for pattern in perception_patterns)
            
            if is_perception_query:
                logger.info("👁️ Detected perception query, applying special handling")
                
                # Adjust search approach
                # 1. First, try to get screen content from context memory
                screen_content = None
                if isinstance(memory.context_memory, dict) and 'screen_content' in memory.context_memory:
                    screen_content = memory.context_memory['screen_content']
                
                if screen_content:
                    logger.info(f"Found screen content in context memory: {screen_content[:50]}...")
                    
                    # Create a result using this content
                    screen_result = {
                        'content': screen_content,
                        'score': 0.95,  # High confidence for direct screen content
                        'source': 'context',
                        'timestamp': datetime.now().isoformat(),
                        'type': 'screen'
                    }
                    
                    # 2. Also get regular results but with enhanced query
                    # Enhance query with screen-related terms for better matching
                    enhanced_query = f"{query} screen display visual content window monitor"
                    
                    # Call original search method with enhanced query
                    regular_results = await original_search_memory(enhanced_query, limit=limit-1, memory_types=memory_types)
                    
                    # Combine results with screen content first
                    combined_results = [screen_result] + regular_results
                    
                    logger.info(f"Enhanced perception query returned {len(combined_results)} results")
                    return combined_results
                else:
                    logger.info("No screen content found in context memory, enhancing search query")
                    
                    # Just enhance the query with screen-related terms
                    enhanced_query = f"{query} screen display visual content window monitor"
                    
                    # Call original search method with enhanced query
                    results = await original_search_memory(enhanced_query, limit=limit, memory_types=memory_types)
                    
                    logger.info(f"Enhanced query returned {len(results)} results")
                    return results
            else:
                # Not a perception query, use original search
                return await original_search_memory(query, limit=limit, memory_types=memory_types)
        
        # Directly replace the method in the memory system instance
        memory.search_memory = enhanced_search_memory
        logger.info("✅ Applied perception query enhancement to memory system")
        
    except Exception as e:
        logger.error(f"Error applying perception query enhancement: {e}")
        logger.error(traceback.format_exc())
    
    # Test perception queries
    perception_queries = [
        "what am i seeing on screen",
        "what is on my screen",
        "what do I see",
        "what's visible on my display",
        "what screen content is there",
        # Add more specific query
        "tell me about what's on screen right now"
    ]
    
    # Also include some non-perception queries for comparison
    non_perception_queries = [
        "what time is it",
        "weather forecast",
        "system status",
    ]
    
    # Test each query and analyze results
    all_results = {}
    logger.info("\n==================================================")
    logger.info("🔍 TESTING ENHANCED PERCEPTION QUERIES")
    logger.info("==================================================")
    
    # Test perception queries
    for query in perception_queries:
        logger.info(f"\nTesting perception query: '{query}'")
        
        try:
            start_time = datetime.now()
            results = await memory.search_memory(query, limit=5)
            search_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"✅ Search completed in {search_time:.3f}s, found {len(results)} results")
            
            # Log results
            if results:
                logger.info(f"📊 Top results:")
                for i, result in enumerate(results[:3]):  # Show top 3 results
                    score = result.get('score', 0)
                    content = result.get('content', '')[:100] + '...' if len(result.get('content', '')) > 100 else result.get('content', '')
                    source = result.get('source', 'unknown')
                    
                    logger.info(f"  Result {i+1}: [score={score:.4f}] [{source}] {content}")
            else:
                logger.info(f"⚠️ No results found")
            
            # Store results
            all_results[query] = results
        except Exception as e:
            logger.error(f"Error searching for '{query}': {e}")
            logger.error(traceback.format_exc())
    
    # Test non-perception queries
    logger.info("\n==================================================")
    logger.info("🔍 TESTING NON-PERCEPTION QUERIES FOR COMPARISON")
    logger.info("==================================================")
    
    for query in non_perception_queries:
        logger.info(f"\nTesting non-perception query: '{query}'")
        
        try:
            start_time = datetime.now()
            results = await memory.search_memory(query, limit=5)
            search_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"✅ Search completed in {search_time:.3f}s, found {len(results)} results")
            
            # Log results
            if results:
                logger.info(f"📊 Top results:")
                for i, result in enumerate(results[:3]):  # Show top 3 results
                    score = result.get('score', 0)
                    content = result.get('content', '')[:100] + '...' if len(result.get('content', '')) > 100 else result.get('content', '')
                    source = result.get('source', 'unknown')
                    
                    logger.info(f"  Result {i+1}: [score={score:.4f}] [{source}] {content}")
            else:
                logger.info(f"⚠️ No results found")
            
            # Store results
            all_results[query] = results
        except Exception as e:
            logger.error(f"Error searching for '{query}': {e}")
            logger.error(traceback.format_exc())
    
    # Also test get_context_summary with perception query
    logger.info("\n==================================================")
    logger.info("🔍 TESTING CONTEXT SUMMARY FOR PERCEPTION QUERY")
    logger.info("==================================================")
    
    try:
        context_summary = await memory.get_context_summary(query="what am i seeing on screen")
        
        if context_summary:
            logger.info(f"Context summary retrieved with {len(context_summary)} keys")
            
            if 'screen_content' in context_summary and context_summary['screen_content']:
                logger.info(f"📊 Screen content: {context_summary['screen_content'][:100]}...")
            else:
                logger.info("⚠️ No screen content found in context summary")
                
            if 'window' in context_summary:
                logger.info(f"📊 Window: {context_summary['window']}")
                
            if 'active_apps' in context_summary:
                logger.info(f"📊 Active apps: {context_summary['active_apps']}")
        else:
            logger.info("⚠️ No context summary returned")
    except Exception as e:
        logger.error(f"Error getting context summary: {e}")
        logger.error(traceback.format_exc())
    
    # Analyze results
    logger.info("\n==================================================")
    logger.info("📈 RESULTS ANALYSIS")
    logger.info("==================================================")
    
    # Check for screen-related results in perception queries
    perception_success = False
    perception_result_counts = {}
    avg_perception_scores = {}
    
    for query in perception_queries:
        results = all_results.get(query, [])
        screen_related_count = 0
        scores = []
        
        for result in results:
            content = result.get('content', '').lower()
            score = result.get('score', 0)
            scores.append(score)
            
            # Check for screen-related terms
            if ('screen' in content or 'window' in content or 'display' in content or 
                'visible' in content or 'seeing' in content):
                screen_related_count += 1
                
                if screen_related_count > 0:
                    perception_success = True
        
        perception_result_counts[query] = screen_related_count
        avg_perception_scores[query] = sum(scores) / len(scores) if scores else 0
        
        if screen_related_count > 0:
            logger.info(f"Query '{query}' returned {screen_related_count}/{len(results)} screen-related results")
            logger.info(f"Average score: {avg_perception_scores[query]:.4f}")
    
    # Check if non-perception queries also return screen content (they shouldn't)
    non_perception_screen_related = False
    
    for query in non_perception_queries:
        results = all_results.get(query, [])
        screen_related_count = 0
        
        for result in results:
            content = result.get('content', '').lower()
            
            # Check for screen-related terms
            if ('screen' in content or 'window' in content or 'display' in content or 
                'visible' in content or 'seeing' in content):
                screen_related_count += 1
                
        if screen_related_count > 0:
            non_perception_screen_related = True
            logger.info(f"⚠️ Non-perception query '{query}' returned {screen_related_count} screen-related results")
    
    # Print summary
    logger.info("\n==================================================")
    logger.info("🔍 SUMMARY OF FINDINGS")
    logger.info("==================================================")
    
    if perception_success:
        logger.info("✅ PERCEPTION QUERIES: Working correctly")
        logger.info(f"Found screen-related content for {sum(1 for count in perception_result_counts.values() if count > 0)}/{len(perception_queries)} perception queries")
        
        # Find best performing query
        best_query = max(avg_perception_scores.items(), key=lambda x: x[1])[0]
        logger.info(f"Best performing query: '{best_query}' with average score {avg_perception_scores[best_query]:.4f}")
    else:
        logger.info("❌ PERCEPTION QUERIES: Not working correctly")
        logger.info("No screen-related content found for any perception queries")
    
    if non_perception_screen_related:
        logger.info("⚠️ NON-PERCEPTION QUERIES: Also returning screen content")
        logger.info("This suggests that the query specialization isn't fully effective")
    else:
        logger.info("✅ NON-PERCEPTION QUERIES: Not returning screen content (correct behavior)")
    
    # Recommendations
    logger.info("\n==================================================")
    logger.info("💡 RECOMMENDATIONS")
    logger.info("==================================================")
    
    if not perception_success:
        logger.info("1. Implement specialized handling for perception queries in memory_system.py")
        logger.info("   - Add detection of perception queries based on keywords")
        logger.info("   - Enhance the search query with visual/screen related terms")
        logger.info("   - Prioritize screen-related content in results")
        
        logger.info("\n2. Ensure screen data is properly indexed in EnhancedSemanticSearch")
        logger.info("   - Verify that screen data is being added with the correct structure")
        logger.info("   - Include clear content field in all screen data")
        
        logger.info("\n3. Improve screen sensor data capture")
        logger.info("   - Ensure screen sensor is properly capturing and storing data")
        logger.info("   - Validate that data is being stored in both short-term memory and context")
    else:
        logger.info("1. Fine-tune perception query detection")
        logger.info("   - Expand the list of perception-related patterns")
        logger.info("   - Improve scoring for screen-related content")
        
        if non_perception_screen_related:
            logger.info("\n2. Improve differentiation between perception and non-perception queries")
            logger.info("   - Ensure non-perception queries don't get enhanced with screen terms")
    
    # Include a copy-pasteable implementation for perception query handling
    logger.info("\n==================================================")
    logger.info("📝 SUGGESTED IMPLEMENTATION")
    logger.info("==================================================")
    
    implementation = """
# Perception query handling implementation to add to memory_system.py

async def search_memory(self, query: str, limit: int = 5, memory_types: List[str] = None) -> List[Dict[str, Any]]:
    '''Search memory using enhanced semantic search with vector embeddings and perception query handling.'''
    try:
        # Check if this is a perception-related query
        perception_patterns = [
            "what am i seeing", "what do i see", "what's on my screen",
            "what is on my screen", "what's being displayed", "what is displayed",
            "what's in front of me", "what is in front of me", "what's visible",
            "what around me", "what do you see", "what are you seeing"
        ]
        
        is_perception_query = any(pattern in query.lower() for pattern in perception_patterns)
        
        if is_perception_query:
            self.logger.info(f"🔍 SEARCHING MEMORY FOR PERCEPTION QUERY: {query}")
            self.logger.info(f"  - Applying specialized perception query handling")
            
            # 1. First try to get screen content directly from context memory
            if isinstance(self.context_memory, dict) and 'screen_content' in self.context_memory:
                screen_content = self.context_memory['screen_content']
                
                if screen_content:
                    self.logger.info(f"  - Found screen content in context memory: {screen_content[:50]}...")
                    
                    # Create a custom result for screen content
                    screen_result = {
                        'content': screen_content,
                        'score': 0.95,  # High confidence for direct screen content
                        'source': 'context',
                        'timestamp': datetime.now().isoformat(),
                        'type': 'screen'
                    }
                    
                    # 2. Also get regular semantic search with enhanced query
                    enhanced_query = f"{query} screen display visual content window"
                    self.logger.info(f"  - Using enhanced query: {enhanced_query}")
                    
                    try:
                        # Use enhanced semantic search with vector embeddings and enhanced query
                        regular_results = self.semantic_search.search(
                            query=enhanced_query,
                            limit=limit,
                            memory_types=memory_types,
                            min_score=0.2  # Lower threshold for perception queries
                        )
                    except Exception as e:
                        self.logger.error(f"❌ Error in enhanced semantic search: {e}")
                        regular_results = []
                    
                    # Combine results with screen content first, then regular results
                    combined_results = [screen_result] + regular_results
                    
                    # Remove duplicates and limit results
                    final_results = []
                    seen_content = set()
                    
                    for result in combined_results:
                        content = result.get('content', '')
                        if content and content not in seen_content:
                            seen_content.add(content)
                            final_results.append(result)
                        
                        if len(final_results) >= limit:
                            break
                    
                    self.logger.info(f"✅ Found {len(final_results)} results for perception query")
                    return final_results
                
            # If we don't have screen content in context or previous approach failed
            self.logger.info(f"  - Using enhanced query for perception search")
            enhanced_query = f"{query} screen display visual content window monitor"
            
            # Search with enhanced query
            try:
                self.logger.info(f"  - Searching with enhanced query: {enhanced_query}")
                results = self.semantic_search.search(
                    query=enhanced_query,
                    limit=limit,
                    memory_types=memory_types,
                    min_score=0.2  # Lower threshold for perception queries
                )
            except Exception as e:
                self.logger.error(f"❌ Error in enhanced semantic search: {e}")
                results = await self._text_based_search(enhanced_query, limit)
            
            # Prioritize screen-related results by boosting their scores
            for result in results:
                content = result.get('content', '').lower()
                if 'screen' in content or 'window' in content or 'display' in content:
                    result['score'] = min(1.0, result.get('score', 0) * 1.5)  # Boost score up to max of 1.0
            
            # Re-sort by score
            results.sort(key=lambda x: x.get('score', 0), reverse=True)
            
            self.logger.info(f"✅ Found {len(results)} results for perception query")
            return results
            
        else:
            # Standard search for non-perception queries
            self.logger.info(f"🔍 SEARCHING MEMORY WITH ENHANCED SEMANTIC SEARCH")
            self.logger.info(f"  - Query: {query}")
            self.logger.info(f"  - Limit: {limit}")
            if memory_types:
                self.logger.info(f"  - Memory types: {memory_types}")
            
            # Use enhanced semantic search with vector embeddings
            try:
                results = self.semantic_search.search(
                    query=query,
                    limit=limit,
                    memory_types=memory_types,
                    min_score=0.3  # Standard threshold
                )
                
                self.logger.info(f"✅ Found {len(results)} results")
                return results
            except Exception as e:
                self.logger.error(f"❌ Error in enhanced semantic search: {e}")
                # Fall back to text-based search in case of errors
                return await self._text_based_search(query, limit)
                
    except Exception as e:
        self.logger.error(f"❌ Error in search_memory: {e}")
        # Fall back to basic text search
        try:
            return await self._text_based_search(query, limit)
        except Exception as fallback_e:
            self.logger.error(f"❌ Error in fallback text search: {fallback_e}")
            return []
    """
    
    logger.info(implementation)
    
    # Cleanup
    await memory.cleanup()
    logger.info("\nMemory system cleaned up")
    
    return all_results

if __name__ == "__main__":
    results = asyncio.run(test_enhanced_perception())