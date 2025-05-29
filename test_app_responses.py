#!/usr/bin/env python3
"""
Test App Response Generation
Focus on testing app-specific queries to see if we get good responses
"""

import asyncio
import sys
import os
sys.path.append('/Users/segevbin/Desktop/SensAI/Aiayer')

from brain.handlers.enhanced_ask_mode_handler import EnhancedAskModeHandler
from brain.core.brain_router import ChatRequest, ChatMode
from datetime import datetime

async def test_app_queries():
    """Test app-related queries specifically"""
    
    handler = EnhancedAskModeHandler()
    
    test_queries = [
        "what apps are open?",
        "is spotify running?", 
        "what applications do I have opened?",
        "is cursor open?",
        "what's my primary app?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)
        
        request = ChatRequest(
            query=query,
            mode=ChatMode.ASK,
            user_id="test_user",
            session_id="test_session",
            timestamp=datetime.now()
        )
        
        response = await handler.handle_request(request)
        
        print(f"Success: {response.success}")
        print(f"Mode Used: {response.mode_used}")
        print(f"Confidence: {response.confidence:.2f}")
        print(f"Processing Time: {response.processing_time:.2f}s")
        print(f"Resources Used: {response.resources_used}")
        
        if response.metadata:
            print(f"App Search Used: {response.metadata.get('app_semantic_search_used', False)}")
            print(f"Semantic Results: {response.metadata.get('semantic_results_count', 0)}")
            
        print(f"\nResponse:")
        print(response.response)

if __name__ == "__main__":
    asyncio.run(test_app_queries())