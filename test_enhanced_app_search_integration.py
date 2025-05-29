#!/usr/bin/env python3
"""
Test Enhanced App Semantic Search Integration
Tests the integration between enhanced app semantic search and the Ask mode handler
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

async def test_app_queries():
    """Test app-related queries with the enhanced system"""
    print("🧪 Testing Enhanced App Semantic Search Integration")
    print("=" * 60)
    
    # Initialize the enhanced ask mode handler
    handler = EnhancedAskModeHandler()
    
    # Test queries that should trigger app-specific responses
    test_queries = [
        "what apps are open?",
        "what applications are currently running?",
        "is spotify opened?",
        "is cursor running?",
        "show me current apps",
        "list open programs",
        "what software is active?",
        "current applications"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}: '{query}'")
        print("-" * 40)
        
        try:
            # Create a test request
            request = ChatRequest(
                mode=ChatMode.ASK,
                query=query,
                user_id="test_user",
                session_id=f"test_session_{i}",
                timestamp=datetime.now().timestamp(),
                priority=Priority.MEDIUM
            )
            
            # Process the request
            start_time = datetime.now()
            response = await handler.handle_request(request)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            print(f"✅ Success: {response.success}")
            print(f"🎯 Mode Used: {response.mode_used.value}")
            print(f"⏱️  Processing Time: {processing_time:.3f}s")
            print(f"🔍 Confidence: {response.confidence:.2f}")
            print(f"📊 Metadata Keys: {list(response.metadata.keys())}")
            
            # Check if app semantic search was used
            app_search_used = response.metadata.get("app_semantic_search_used", False)
            semantic_results = response.metadata.get("semantic_results_count", 0)
            
            print(f"🔧 App Search Used: {app_search_used}")
            print(f"📋 Semantic Results: {semantic_results}")
            
            # Show response preview
            response_preview = response.response[:200] + "..." if len(response.response) > 200 else response.response
            print(f"💬 Response Preview:\n{response_preview}")
            
            if app_search_used:
                print("✅ App semantic search was triggered correctly!")
            else:
                print("⚠️  App semantic search was NOT triggered")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            logger.error(f"Test failed for query '{query}': {e}")
    
    print("\n" + "=" * 60)
    print("🏁 Enhanced App Semantic Search Integration Test Complete")

async def test_memory_context():
    """Test that the system can read current applications from memory"""
    print("\n🧠 Testing Memory Context for Applications")
    print("-" * 40)
    
    # Check if memory state contains application data
    memory_file = "/Users/segevbin/Desktop/SensAI/Aiayer/memory/memory_state.json"
    
    if os.path.exists(memory_file):
        with open(memory_file, 'r') as f:
            memory_data = json.load(f)
        
        # Look for current applications in memory
        apps_found = []
        
        # Check short-term memory
        for item in memory_data.get("short_term", []):
            if "user_activity" in item and "current_applications" in item["user_activity"]:
                current_apps = item["user_activity"]["current_applications"]
                if current_apps:
                    apps_found = current_apps
                    break
        
        if apps_found:
            print(f"✅ Found {len(apps_found)} applications in memory:")
            for i, app in enumerate(apps_found[:10], 1):  # Show first 10
                print(f"  {i}. {app}")
            if len(apps_found) > 10:
                print(f"  ... and {len(apps_found) - 10} more")
        else:
            print("⚠️  No current applications found in memory")
            print("Memory structure:")
            print(f"  - Short-term memories: {len(memory_data.get('short_term', []))}")
            print(f"  - Long-term memories: {len(memory_data.get('long_term', []))}")
    else:
        print("❌ Memory file not found")

async def test_enhanced_app_search_direct():
    """Test the enhanced app semantic search directly"""
    print("\n🔧 Testing Enhanced App Semantic Search Directly")
    print("-" * 40)
    
    try:
        from enhanced_app_semantic_search import EnhancedAppSemanticSearch
        
        memory_file = "/Users/segevbin/Desktop/SensAI/Aiayer/memory/memory_state.json"
        search = EnhancedAppSemanticSearch(memory_file)
        
        test_queries = [
            "what apps are open?",
            "is spotify opened?",
            "current applications"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Testing: '{query}'")
            
            # Test query detection
            is_app_related = search.is_app_related_query(query)
            print(f"  App-related: {is_app_related}")
            
            if is_app_related:
                # Test context generation
                context = search.generate_app_response_context(query)
                if context:
                    print(f"  Context generated: {len(context)} characters")
                    preview = context[:150] + "..." if len(context) > 150 else context
                    print(f"  Preview: {preview}")
                else:
                    print("  No context generated")
    
    except ImportError as e:
        print(f"❌ Could not import enhanced app semantic search: {e}")
    except Exception as e:
        print(f"❌ Error testing direct search: {e}")

async def main():
    """Run all tests"""
    await test_memory_context()
    await test_enhanced_app_search_direct()
    await test_app_queries()

if __name__ == "__main__":
    asyncio.run(main())