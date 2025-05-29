#!/usr/bin/env python3
"""
Debug Memory Integration in Ask/Suggest Modes
Test to see what's actually happening with memory integration
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# Add paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_ask_mode_memory_integration():
    """Test if ask mode is actually using memory integration"""
    print("🔍 Testing Ask Mode Memory Integration...")
    
    try:
        # Test the ask mode handler directly
        from brain.handlers.ask_mode_handler import handle_ask_mode
        from brain.core.brain_router import ChatRequest, ChatMode, Priority
        
        # Create a test request
        request = ChatRequest(
            mode=ChatMode.ASK,
            query="what have I been working on recently?",
            user_id="test_user",
            session_id="test_session",
            timestamp=time.time(),
            context={"source": "memory_debug_test"}
        )
        
        print(f"📤 Sending request: {request.query}")
        
        # Call the ask handler
        response = await handle_ask_mode(request)
        
        print(f"📥 Response success: {response.success}")
        print(f"📝 Response: {response.response}")
        print(f"🕐 Processing time: {response.processing_time:.2f}s")
        print(f"🎯 Confidence: {response.confidence}")
        print(f"🔧 Resources used: {response.resources_used}")
        print(f"✅ Verification status: {response.verification_status}")
        
        if response.metadata:
            print("📊 Metadata:")
            for key, value in response.metadata.items():
                print(f"  - {key}: {value}")
        
        return response
        
    except Exception as e:
        print(f"❌ Error testing ask mode: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_memory_file_access():
    """Test if memory files exist and are accessible"""
    print("\n🗄️ Testing Memory File Access...")
    
    memory_files = [
        "memory/memory_state.json",
        "memory/conversation_history.json", 
        "memory/last_context.json",
        "memory/conscious.json"
    ]
    
    for file_path in memory_files:
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r') as f:
                    data = json.load(f)
                print(f"✅ {file_path}: {len(str(data))} chars")
                
                # Show structure for memory_state.json
                if file_path.endswith("memory_state.json"):
                    if isinstance(data, dict):
                        print(f"   Keys: {list(data.keys())}")
                        if "short_term" in data:
                            print(f"   Short-term memories: {len(data['short_term'])}")
                        if "long_term" in data:
                            print(f"   Long-term memories: {len(data['long_term'])}")
                            
            except Exception as e:
                print(f"❌ {file_path}: Error reading - {e}")
        else:
            print(f"❌ {file_path}: File not found")

async def test_semantic_search_availability():
    """Test if semantic search is available"""
    print("\n🔎 Testing Semantic Search Availability...")
    
    try:
        from memory.enhanced_semantic_search import EnhancedSemanticSearch
        
        search = EnhancedSemanticSearch()
        print("✅ Enhanced Semantic Search module loaded")
        print(f"   Embedding dim: {search.embedding_dim}")
        print(f"   Hybrid search: {search.use_hybrid}")
        
        # Test a simple search
        test_query = "what am I working on"
        test_memory = [
            {"content": "User was coding in Python", "timestamp": "2024-01-01"},
            {"content": "User opened VSCode", "timestamp": "2024-01-02"}
        ]
        
        # This would need memory to be indexed first
        print("   Semantic search module available but not integrated into ask handler")
        
        return True
        
    except ImportError as e:
        print(f"❌ Semantic search not available: {e}")
        return False
    except Exception as e:
        print(f"❌ Error with semantic search: {e}")
        return False

async def test_llm_service_memory_context():
    """Test if LLM service receives memory context"""
    print("\n🤖 Testing LLM Service Memory Context...")
    
    try:
        from llm.llm_service import LLMService
        
        llm = LLMService()
        
        # Test if it loads context from file
        context_file = os.path.join(os.path.dirname(__file__), 'memory', 'last_context.json')
        if os.path.exists(context_file):
            with open(context_file, 'r') as f:
                context = json.load(f)
            print(f"✅ Context file exists: {len(str(context))} chars")
            if context:
                print(f"   Context keys: {list(context.keys())}")
        else:
            print("❌ Context file not found")
        
        # Test generate_response with context
        test_query = "what am I seeing?"
        response = await llm.generate_response(test_query)
        
        print(f"📝 LLM Response: {response[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing LLM service: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import time
    
    async def main():
        print("🚀 Starting Memory Integration Debug Test")
        print("=" * 50)
        
        # Test memory file access first
        await test_memory_file_access()
        
        # Test semantic search availability  
        await test_semantic_search_availability()
        
        # Test LLM service memory context
        await test_llm_service_memory_context()
        
        # Test ask mode handler
        await test_ask_mode_memory_integration()
        
        print("\n" + "=" * 50)
        print("🏁 Debug test completed")
    
    asyncio.run(main())