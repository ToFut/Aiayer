#!/usr/bin/env python3
"""
Debug app extraction from memory context
"""

import asyncio
import sys
import os
sys.path.append('/Users/segevbin/Desktop/SensAI/Aiayer')

from brain.handlers.enhanced_ask_mode_handler import EnhancedMemoryRetriever, EnhancedLLMContextBuilder
from brain.core.brain_router import ChatRequest, ChatMode
from datetime import datetime

async def debug_app_extraction():
    """Debug the app extraction process"""
    
    retriever = EnhancedMemoryRetriever()
    builder = EnhancedLLMContextBuilder()
    
    query = "what apps are open?"
    
    # Get memory context
    memory_context = await retriever.retrieve_enhanced_context(query, "test", "test")
    
    print("=== MEMORY CONTEXT DEBUG ===")
    print(f"Semantic Results Count: {len(memory_context.semantic_results)}")
    
    for i, result in enumerate(memory_context.semantic_results):
        print(f"\nResult {i+1}:")
        print(f"Type: {result.get('type')}")
        print(f"Relevance: {result.get('relevance_score')}")
        
        content = result.get('content', {})
        print(f"Content type: {type(content)}")
        print(f"Content keys: {list(content.keys()) if isinstance(content, dict) else 'Not a dict'}")
        
        if isinstance(content, dict) and 'user_activity' in content:
            user_activity = content['user_activity']
            print(f"User activity type: {type(user_activity)}")
            print(f"User activity keys: {list(user_activity.keys()) if isinstance(user_activity, dict) else 'Not a dict'}")
            
            if isinstance(user_activity, dict) and 'current_applications' in user_activity:
                current_apps = user_activity['current_applications']
                print(f"Current applications: {current_apps}")
                print(f"Apps count: {len(current_apps) if isinstance(current_apps, list) else 'Not a list'}")
            else:
                print("No current_applications in user_activity")
        else:
            print("No user_activity in content")
    
    # Test the extraction method directly
    print("\n=== EXTRACTION TEST ===")
    apps_info = builder._extract_apps_from_memory_context(memory_context)
    print(f"Extracted apps info: {apps_info}")

if __name__ == "__main__":
    asyncio.run(debug_app_extraction())