#!/usr/bin/env python3
"""
Debug what the enriched context looks like
"""

import asyncio
import sys
import os
sys.path.append('/Users/segevbin/Desktop/SensAI/Aiayer')

from brain.handlers.enhanced_ask_mode_handler import EnhancedMemoryRetriever, EnhancedLLMContextBuilder
from brain.core.brain_router import ChatRequest, ChatMode
from datetime import datetime

async def debug_context():
    """Debug the enriched context content"""
    
    retriever = EnhancedMemoryRetriever()
    builder = EnhancedLLMContextBuilder()
    
    query = "what apps are open?"
    
    # Get memory context
    memory_context = await retriever.retrieve_enhanced_context(query, "test", "test")
    
    # Build enriched context
    enriched_context = await builder.build_enriched_context(query, memory_context)
    
    print("=== ENRICHED CONTEXT DEBUG ===")
    print(enriched_context)
    print("\n=== SEMANTIC RESULTS ===")
    
    for i, result in enumerate(memory_context.semantic_results):
        print(f"\nResult {i+1}:")
        print(f"Type: {result.get('type')}")
        print(f"Relevance: {result.get('relevance_score')}")
        content = result.get('content', {})
        if isinstance(content, dict):
            print(f"Content keys: {list(content.keys())}")
            if 'user_activity' in content:
                user_activity = content['user_activity']
                print(f"User activity: {user_activity}")
        print(f"Searchable text preview: {result.get('searchable_text', '')[:200]}...")

if __name__ == "__main__":
    asyncio.run(debug_context())