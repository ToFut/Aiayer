#!/usr/bin/env python3
"""
Test Visual Context Integration
Test if the enhanced handlers now include visual screen context
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime

# Add paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_visual_context_loading():
    """Test if visual context is being loaded"""
    print("📺 Testing Visual Context Loading...")
    
    try:
        from brain.handlers.enhanced_ask_mode_handler import EnhancedMemoryRetriever
        
        retriever = EnhancedMemoryRetriever()
        
        # Test loading visual context directly
        visual_context = await retriever._load_visual_context()
        
        print(f"Visual context loaded: {bool(visual_context)}")
        if visual_context:
            print(f"  Timestamp: {visual_context.get('timestamp', 'unknown')}")
            
            memory_summary = visual_context.get('memory_summary', {})
            if memory_summary:
                app = memory_summary.get('application', {})
                print(f"  Application: {app.get('name', 'unknown')}")
                print(f"  App Type: {app.get('detected_type', 'unknown')}")
                
                content = memory_summary.get('content', {})
                print(f"  Content Type: {content.get('type', 'unknown')}")
                print(f"  Word Count: {content.get('word_count', 0)}")
                
                user_activity = memory_summary.get('user_activity', {})
                print(f"  Current Activity: {user_activity.get('current_activity', 'unknown')}")
                
                insights = memory_summary.get('key_insights', [])
                print(f"  Insights: {insights}")
                
                text_sample = memory_summary.get('text_sample', '')
                if text_sample:
                    print(f"  Text Sample: {text_sample[:100]}...")
        
        return visual_context
        
    except Exception as e:
        print(f"❌ Error testing visual context loading: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_enhanced_ask_with_visual():
    """Test enhanced ask mode with visual context integration"""
    print("\n🔍 Testing Enhanced Ask Mode with Visual Context...")
    
    try:
        from brain.handlers.enhanced_ask_mode_handler import handle_enhanced_ask_mode
        from brain.core.brain_router import ChatRequest, ChatMode
        
        # Test "what am I seeing" query
        request = ChatRequest(
            mode=ChatMode.ASK,
            query="what am I seeing on my screen?",
            user_id="test_user",
            session_id="test_session",
            timestamp=time.time(),
            context={"source": "visual_context_test"}
        )
        
        print(f"📤 Asking: {request.query}")
        
        # Call the enhanced ask handler
        response = await handle_enhanced_ask_mode(request)
        
        print(f"📥 Visual Context Response:")
        print(f"  Success: {response.success}")
        print(f"  Response: {response.response}")
        print(f"  Confidence: {response.confidence}")
        print(f"  Resources: {response.resources_used}")
        
        if response.metadata:
            print("  📊 Metadata:")
            for key, value in response.metadata.items():
                print(f"    {key}: {value}")
        
        return response
        
    except Exception as e:
        print(f"❌ Error testing enhanced ask with visual: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_visual_searchable_text():
    """Test visual context searchable text extraction"""
    print("\n🔎 Testing Visual Context Searchable Text...")
    
    try:
        from brain.handlers.enhanced_ask_mode_handler import EnhancedMemoryRetriever
        
        retriever = EnhancedMemoryRetriever()
        
        # Load visual context
        visual_context = await retriever._load_visual_context()
        
        if visual_context:
            # Extract searchable text
            searchable_text = retriever._extract_visual_searchable_text(visual_context)
            
            print(f"Searchable text extracted: {len(searchable_text)} chars")
            print(f"Content preview: {searchable_text[:300]}...")
            
            return searchable_text
        else:
            print("No visual context available for text extraction")
            return None
        
    except Exception as e:
        print(f"❌ Error testing visual searchable text: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_semantic_search_with_visual():
    """Test semantic search including visual context"""
    print("\n🔍 Testing Semantic Search with Visual Context...")
    
    try:
        from brain.handlers.enhanced_ask_mode_handler import EnhancedMemoryRetriever
        
        retriever = EnhancedMemoryRetriever()
        
        # Test enhanced context retrieval for "what am I seeing" query
        context = await retriever.retrieve_enhanced_context(
            "what am I seeing on my screen cursor development",
            "test_user",
            "test_session"
        )
        
        print(f"Enhanced context retrieved:")
        print(f"  Semantic results: {len(context.semantic_results)}")
        print(f"  Confidence: {context.confidence_score}")
        print(f"  Search metadata: {context.search_metadata}")
        
        # Check for visual context results
        visual_results = [r for r in context.semantic_results if r.get('type') == 'visual_context']
        print(f"  Visual context results: {len(visual_results)}")
        
        if visual_results:
            visual_result = visual_results[0]
            print(f"  Visual result relevance: {visual_result.get('relevance_score', 0)}")
            print(f"  Visual content preview: {visual_result.get('searchable_text', '')[:200]}...")
        
        return context
        
    except Exception as e:
        print(f"❌ Error testing semantic search with visual: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    async def main():
        print("🚀 Starting Visual Context Integration Test")
        print("=" * 60)
        
        # Test visual context loading
        await test_visual_context_loading()
        
        # Test visual searchable text extraction
        await test_visual_searchable_text()
        
        # Test semantic search with visual context
        await test_semantic_search_with_visual()
        
        # Test enhanced ask mode with visual context
        await test_enhanced_ask_with_visual()
        
        print("\n" + "=" * 60)
        print("🏁 Visual Context Integration Test Completed")
    
    asyncio.run(main())