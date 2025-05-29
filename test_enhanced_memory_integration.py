#!/usr/bin/env python3
"""
Test Enhanced Memory Integration in Ask/Suggest Modes
Test the new enhanced handlers with semantic search and LLM integration
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime

# Add paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_enhanced_ask_mode():
    """Test the enhanced ask mode handler"""
    print("🔍 Testing Enhanced Ask Mode...")
    
    try:
        from brain.handlers.enhanced_ask_mode_handler import handle_enhanced_ask_mode
        from brain.core.brain_router import ChatRequest, ChatMode, Priority
        
        # Create a test request
        request = ChatRequest(
            mode=ChatMode.ASK,
            query="what have I been working on recently with my development environment?",
            user_id="test_user",
            session_id="test_session", 
            timestamp=time.time(),
            context={"source": "enhanced_memory_test"}
        )
        
        print(f"📤 Sending enhanced ask request: {request.query}")
        
        # Call the enhanced ask handler
        response = await handle_enhanced_ask_mode(request)
        
        print(f"📥 Enhanced Ask Response:")
        print(f"  Success: {response.success}")
        print(f"  Response: {response.response}")
        print(f"  Processing time: {response.processing_time:.2f}s")
        print(f"  Confidence: {response.confidence}")
        print(f"  Resources used: {response.resources_used}")
        print(f"  Verification status: {response.verification_status}")
        
        if response.metadata:
            print("  📊 Enhanced Metadata:")
            for key, value in response.metadata.items():
                print(f"    - {key}: {value}")
        
        return response
        
    except Exception as e:
        print(f"❌ Error testing enhanced ask mode: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_suggest_mode():
    """Test the suggest mode handler"""
    print("\n💡 Testing Suggest Mode...")
    
    try:
        from brain.handlers.suggest_mode_handler import handle_suggest_mode
        from brain.core.brain_router import ChatRequest, ChatMode, Priority
        
        # Create a test request
        request = ChatRequest(
            mode=ChatMode.SUGGEST,
            query="help me be more productive with my current coding work",
            user_id="test_user",
            session_id="test_session",
            timestamp=time.time(),
            context={"source": "suggest_mode_test"}
        )
        
        print(f"📤 Sending suggest request: {request.query}")
        
        # Call the suggest handler
        response = await handle_suggest_mode(request)
        
        print(f"📥 Suggest Mode Response:")
        print(f"  Success: {response.success}")
        print(f"  Response: {response.response}")
        print(f"  Processing time: {response.processing_time:.2f}s")
        print(f"  Confidence: {response.confidence}")
        print(f"  Resources used: {response.resources_used}")
        print(f"  Verification status: {response.verification_status}")
        
        if response.metadata:
            print("  📊 Suggest Metadata:")
            for key, value in response.metadata.items():
                print(f"    - {key}: {value}")
        
        return response
        
    except Exception as e:
        print(f"❌ Error testing suggest mode: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_semantic_search_integration():
    """Test semantic search integration"""
    print("\n🔎 Testing Semantic Search Integration...")
    
    try:
        from brain.handlers.enhanced_ask_mode_handler import EnhancedMemoryRetriever
        
        retriever = EnhancedMemoryRetriever()
        
        # Test memory retrieval with semantic search
        context = await retriever.retrieve_enhanced_context(
            "coding development programming python",
            "test_user",
            "test_session"
        )
        
        print(f"📊 Semantic Search Results:")
        print(f"  Semantic results: {len(context.semantic_results)}")
        print(f"  Relevant knowledge: {len(context.relevant_knowledge)}")
        print(f"  User patterns: {len(context.user_patterns)}")
        print(f"  Confidence score: {context.confidence_score}")
        print(f"  Search metadata: {context.search_metadata}")
        
        if context.semantic_results:
            print(f"  📝 First semantic result:")
            first_result = context.semantic_results[0]
            print(f"    Type: {first_result.get('type', 'unknown')}")
            print(f"    Relevance: {first_result.get('relevance_score', 0)}")
            print(f"    Preview: {first_result.get('searchable_text', '')[:100]}...")
        
        return context
        
    except Exception as e:
        print(f"❌ Error testing semantic search: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_backend_integration():
    """Test backend integration with enhanced handlers"""
    print("\n🔧 Testing Backend Integration...")
    
    try:
        # Test import of the enhanced backend
        from real_llm_backend_8767 import RealLLMBackend8767
        
        backend = RealLLMBackend8767()
        
        print(f"✅ Backend initialized")
        print(f"  Ask handler available: {backend.ask_handler is not None}")
        print(f"  Suggest handler available: {hasattr(backend, 'suggest_handler') and backend.suggest_handler is not None}")
        
        # Test the handler methods exist
        if hasattr(backend, 'suggest_handler'):
            print(f"  Suggest handler type: {type(backend.suggest_handler)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing backend integration: {e}")
        import traceback
        traceback.print_exc()
        return False

async def compare_handlers():
    """Compare original vs enhanced ask mode handlers"""
    print("\n📊 Comparing Handler Responses...")
    
    try:
        # Test original handler
        print("Testing Original Ask Handler:")
        from brain.handlers.ask_mode_handler import handle_ask_mode as original_ask
        from brain.core.brain_router import ChatRequest, ChatMode
        
        request = ChatRequest(
            mode=ChatMode.ASK,
            query="what applications am I using for development?",
            user_id="test_user",
            session_id="test_session",
            timestamp=time.time(),
            context={"source": "comparison_test"}
        )
        
        original_response = await original_ask(request)
        print(f"  Original: {original_response.response[:100]}...")
        print(f"  Confidence: {original_response.confidence}")
        print(f"  Resources: {original_response.resources_used}")
        
        # Test enhanced handler
        print("\nTesting Enhanced Ask Handler:")
        from brain.handlers.enhanced_ask_mode_handler import handle_enhanced_ask_mode as enhanced_ask
        
        enhanced_response = await enhanced_ask(request)
        print(f"  Enhanced: {enhanced_response.response[:100]}...")
        print(f"  Confidence: {enhanced_response.confidence}")
        print(f"  Resources: {enhanced_response.resources_used}")
        
        # Compare metadata
        print(f"\n  Original metadata keys: {list(original_response.metadata.keys()) if original_response.metadata else []}")
        print(f"  Enhanced metadata keys: {list(enhanced_response.metadata.keys()) if enhanced_response.metadata else []}")
        
        return {
            "original": original_response,
            "enhanced": enhanced_response
        }
        
    except Exception as e:
        print(f"❌ Error comparing handlers: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    async def main():
        print("🚀 Starting Enhanced Memory Integration Test")
        print("=" * 60)
        
        # Test semantic search integration
        await test_semantic_search_integration()
        
        # Test enhanced ask mode
        await test_enhanced_ask_mode()
        
        # Test suggest mode
        await test_suggest_mode()
        
        # Test backend integration
        await test_backend_integration()
        
        # Compare handlers
        await compare_handlers()
        
        print("\n" + "=" * 60)
        print("🏁 Enhanced Memory Integration Test Completed")
    
    asyncio.run(main())