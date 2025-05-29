#!/usr/bin/env python3
"""
Test Enhanced Generic Semantic Search
Tests the improved semantic search that can handle ANY question with proper memory retrieval
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime

# Add paths for imports
sys.path.append('/Users/segevbin/Desktop/SensAI/Aiayer')
sys.path.append('/Users/segevbin/Desktop/SensAI/Aiayer/brain/handlers')

from brain.handlers.enhanced_ask_mode_handler import EnhancedMemoryRetriever, EnhancedLLMContextBuilder
from brain.core.brain_router import ChatRequest, ChatMode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_enhanced_semantic_search():
    """Test the enhanced semantic search with various question types"""
    
    print("Testing Enhanced Generic Semantic Search")
    print("=" * 60)
    
    # Initialize components
    memory_retriever = EnhancedMemoryRetriever()
    context_builder = EnhancedLLMContextBuilder()
    
    # Test queries covering different types of questions
    test_queries = [
        # App-related queries
        "what apps are open?",
        "is spotify running?",
        "what applications do I have opened?",
        
        # Activity queries  
        "what am I working on?",
        "what am I currently doing?",
        "what's my current activity?",
        
        # General questions
        "what happened recently?",
        "what was I doing an hour ago?",
        "show me my recent work",
        
        # Screen/context queries
        "what am I seeing?",
        "what's on my screen?",
        "current context",
        
        # Specific activity queries
        "am I being productive?",
        "what work have I done today?",
        "what files have I been working with?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Testing Query: '{query}'")
        print("-" * 50)
        
        try:
            # Create a mock chat request
            request = ChatRequest(
                query=query,
                mode=ChatMode.ASK,
                user_id="test_user",
                session_id="test_session",
                timestamp=datetime.now()
            )
            
            # Retrieve enhanced memory context
            memory_context = await memory_retriever.retrieve_enhanced_context(
                query, request.user_id, request.session_id
            )
            
            # Build enriched context
            enriched_context = await context_builder.build_enriched_context(
                query, memory_context
            )
            
            # Print results
            print(f"Confidence Score: {memory_context.confidence_score:.2f}")
            print(f"Semantic Results Count: {len(memory_context.semantic_results)}")
            print(f"Search Metadata: {memory_context.search_metadata}")
            
            if memory_context.semantic_results:
                print("\nTop Search Results:")
                for j, result in enumerate(memory_context.semantic_results[:3], 1):
                    relevance = result.get('relevance_score', 0)
                    result_type = result.get('type', 'unknown')
                    print(f"  {j}. Type: {result_type}, Relevance: {relevance:.2f}")
                    
                    # Show preview of content
                    content = result.get('content', {})
                    if isinstance(content, dict):
                        if 'enriched_context' in content:
                            # App context
                            app_context = content['enriched_context'][:200]
                            print(f"     App Context: {app_context}...")
                        elif 'user_activity' in content:
                            # Activity context
                            activity = content['user_activity']
                            print(f"     Activity: {str(activity)[:150]}...")
                        else:
                            # Other content
                            print(f"     Content keys: {list(content.keys())}")
            
            print(f"\nEnriched Context Preview:")
            context_preview = enriched_context[:400]
            print(f"{context_preview}...")
            
            # Try to get a response (fallback mode since LLM might not be running)
            try:
                response = await context_builder.call_llm_with_context(query, enriched_context)
                print(f"\nGenerated Response Preview:")
                response_preview = response[:300]
                print(f"{response_preview}...")
            except Exception as e:
                print(f"\nLLM Response Error: {e}")
            
        except Exception as e:
            print(f"Error testing query '{query}': {e}")
            logger.error(f"Error details: {e}", exc_info=True)
        
        print("\n" + "=" * 60)

async def test_memory_data_availability():
    """Test what memory data is actually available"""
    print("\nTesting Memory Data Availability")
    print("-" * 40)
    
    memory_retriever = EnhancedMemoryRetriever()
    
    # Load memory data directly
    memory_data = await memory_retriever._load_memory_state()
    conscious_data = await memory_retriever._load_conscious_memory()
    visual_context = await memory_retriever._load_visual_context()
    
    print(f"Memory data keys: {list(memory_data.keys()) if memory_data else 'No memory data'}")
    print(f"Short-term memories: {len(memory_data.get('short_term', []))}")
    print(f"Long-term memories: {len(memory_data.get('long_term', []))}")
    print(f"Conscious entries: {len(conscious_data.get('entries', []))}")
    print(f"Visual context available: {bool(visual_context)}")
    
    # Show sample data
    if memory_data.get('short_term'):
        latest = memory_data['short_term'][0]
        print(f"\nLatest short-term memory keys: {list(latest.keys()) if isinstance(latest, dict) else 'Not a dict'}")
        if isinstance(latest, dict) and 'user_activity' in latest:
            user_activity = latest['user_activity']
            print(f"User activity keys: {list(user_activity.keys()) if isinstance(user_activity, dict) else 'Not a dict'}")
            if isinstance(user_activity, dict) and 'current_applications' in user_activity:
                apps = user_activity['current_applications']
                print(f"Current applications ({len(apps)}): {apps[:5] if len(apps) > 5 else apps}")

if __name__ == "__main__":
    asyncio.run(test_memory_data_availability())
    print("\n" + "=" * 80)
    asyncio.run(test_enhanced_semantic_search())