#!/usr/bin/env python3
"""
Test the specific PC query that was failing
"""

import asyncio
import os
import sys
import json
import logging
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from brain.handlers.enhanced_ask_mode_handler import EnhancedAskModeHandler
from brain.core.brain_router import ChatRequest, ChatMode, Priority

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_pc_query():
    """Test the specific query that was failing"""
    print("🧪 Testing PC Query: 'what's opened in my PC?'")
    print("=" * 50)
    
    # Initialize the enhanced ask mode handler
    handler = EnhancedAskModeHandler()
    
    query = "what's opened in my PC?"
    print(f"Query: {query}")
    
    try:
        # Create a test request
        request = ChatRequest(
            mode=ChatMode.ASK,
            query=query,
            user_id="test_user",
            session_id="test_session_pc",
            timestamp=datetime.now().timestamp(),
            priority=Priority.MEDIUM
        )
        
        # Process the request
        start_time = datetime.now()
        response = await handler.handle_request(request)
        processing_time = (datetime.now() - start_time).total_seconds()
        
        print(f"\n✅ Success: {response.success}")
        print(f"🎯 Mode Used: {response.mode_used.value}")
        print(f"⏱️  Processing Time: {processing_time:.3f}s")
        print(f"🔍 Confidence: {response.confidence:.2f}")
        
        # Check if app semantic search was used
        app_search_used = response.metadata.get("app_semantic_search_used", False)
        semantic_results = response.metadata.get("semantic_results_count", 0)
        
        print(f"🔧 App Search Used: {app_search_used}")
        print(f"📋 Semantic Results: {semantic_results}")
        
        print(f"\n💬 Full Response:")
        print("-" * 30)
        print(response.response)
        print("-" * 30)
        
        if app_search_used:
            print("✅ App semantic search was triggered correctly!")
        else:
            print("⚠️  App semantic search was NOT triggered")
        
        # Check current memory state
        print(f"\n🧠 Memory Check:")
        memory_file = "/Users/segevbin/Desktop/SensAI/Aiayer/memory/memory_state.json"
        if os.path.exists(memory_file):
            with open(memory_file, 'r') as f:
                memory_data = json.load(f)
            
            if 'short_term' in memory_data and memory_data['short_term']:
                latest_entry = memory_data['short_term'][0]
                if 'user_activity' in latest_entry and 'current_applications' in latest_entry['user_activity']:
                    apps = latest_entry['user_activity']['current_applications']
                    print(f"📱 {len(apps)} apps found in memory:")
                    for i, app in enumerate(apps[:5], 1):
                        print(f"  {i}. {app}")
                    if len(apps) > 5:
                        print(f"  ... and {len(apps) - 5} more")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Test failed for query '{query}': {e}")

if __name__ == "__main__":
    asyncio.run(test_pc_query())