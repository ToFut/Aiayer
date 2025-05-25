#!/usr/bin/env python3
"""
Test Memory Context Retrieval
Check if memory system is actually providing meaningful context for Ask/Suggest modes
"""

import sys
import os
import json
import asyncio
from datetime import datetime

# Add project paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory.semantic_search_agent import SemanticSearchAgent, get_context_for_query, add_memory

async def test_context_retrieval():
    """Test if memory retrieval is working properly"""
    
    print("🧪 Testing Memory Context Retrieval for Ask/Suggest Modes")
    print("=" * 60)
    
    # Test queries for different modes
    test_queries = [
        {
            "mode": "Ask", 
            "query": "What applications am I using for development?",
            "expected": "Should find Cursor, coding activities"
        },
        {
            "mode": "Suggest", 
            "query": "What can I improve in my workflow?",
            "expected": "Should suggest based on usage patterns"
        },
        {
            "mode": "Ask",
            "query": "How productive have I been today?",
            "expected": "Should find productivity scores and activity data"
        },
        {
            "mode": "Suggest",
            "query": "What should I work on next?",
            "expected": "Should suggest based on current context"
        }
    ]
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n{i}. Testing {test['mode']} Mode")
        print(f"   Query: {test['query']}")
        print(f"   Expected: {test['expected']}")
        print("   " + "-" * 50)
        
        try:
            # Retrieve context
            context = await get_context_for_query(test['query'], max_context_length=2000)
            
            print(f"   📊 Context Retrieved:")
            print(f"      - Confidence Score: {context.get('confidence_score', 0):.3f}")
            print(f"      - Relevant Memories: {len(context.get('relevant_memories', []))}")
            print(f"      - Search Query: {context.get('search_query', 'N/A')}")
            
            # Show actual memory content
            memories = context.get('relevant_memories', [])
            if memories:
                print(f"   🧠 Top Memory Entries:")
                for j, memory in enumerate(memories[:3], 1):
                    content = memory.get('content', 'No content')[:100]
                    score = memory.get('similarity_score', 0)
                    print(f"      {j}. Score: {score:.3f} | {content}...")
            else:
                print("   ❌ No relevant memories found!")
            
            # Check if context is meaningful
            if context.get('confidence_score', 0) > 0.3:
                print("   ✅ MEANINGFUL context retrieved")
            elif context.get('confidence_score', 0) > 0.1:
                print("   ⚠️  WEAK context retrieved")
            else:
                print("   ❌ NO meaningful context retrieved")
            
        except Exception as e:
            print(f"   ❌ ERROR retrieving context: {e}")
    
    # Test what's actually in memory
    print(f"\n🗃️  Memory System Status Check")
    print("=" * 60)
    
    try:
        # Check conscious memory
        conscious_file = "memory/conscious.json"
        if os.path.exists(conscious_file):
            with open(conscious_file, 'r') as f:
                conscious_data = json.load(f)
            
            insights = conscious_data.get('insights', [])
            print(f"   📝 Conscious Memory: {len(insights)} insights")
            
            if insights:
                latest = insights[-1]
                print(f"   📅 Latest Entry: {latest.get('timestamp', 'N/A')}")
                print(f"   📱 App Context: {latest.get('application_context', {}).get('primary_application', 'N/A')}")
                print(f"   🎯 Activity: {latest.get('user_behavior', {}).get('current_activity', 'N/A')}")
                print(f"   📊 Quality: {latest.get('analysis_quality', {}).get('completeness_score', 0):.2f}")
            else:
                print("   ❌ No insights in conscious memory")
        else:
            print("   ❌ Conscious memory file not found")
        
        # Check memory state
        memory_state_file = "memory/memory_state.json"
        if os.path.exists(memory_state_file):
            with open(memory_state_file, 'r') as f:
                memory_state = json.load(f)
            
            short_term = memory_state.get('short_term', [])
            print(f"   🧠 Short-term Memory: {len(short_term)} entries")
            
            if short_term:
                latest_st = short_term[-1]
                print(f"   📅 Latest Short-term: {latest_st.get('timestamp', 'N/A')}")
                print(f"   🔖 Type: {latest_st.get('memory_type', 'N/A')}")
            else:
                print("   ❌ No short-term memory entries")
        else:
            print("   ❌ Memory state file not found")
            
    except Exception as e:
        print(f"   ❌ ERROR checking memory status: {e}")

async def test_context_integration():
    """Test how context is integrated into LLM prompts"""
    
    print(f"\n🔗 Testing Context Integration into LLM Prompts")
    print("=" * 60)
    
    test_query = "What development tools am I using?"
    
    try:
        # Get context
        context = await get_context_for_query(test_query, max_context_length=1000)
        
        # Simulate how backend formats context for LLM
        def format_context_for_llm(context):
            """Simulate the backend's context formatting"""
            if not context or not context.get('relevant_memories'):
                return "No relevant context available."
            
            formatted = "Relevant Context:\n"
            for i, memory in enumerate(context['relevant_memories'][:3], 1):
                content = memory.get('content', 'No content')
                score = memory.get('similarity_score', 0)
                formatted += f"{i}. (Score: {score:.3f}) {content}\n"
            
            formatted += f"\nContext Confidence: {context.get('confidence_score', 0):.3f}"
            return formatted
        
        # Show how it would be sent to LLM
        context_info = format_context_for_llm(context)
        
        # Simulate system prompt
        system_prompt = "You are an AI assistant in Ask mode. Use the provided context about the user's activities and preferences to give personalized, relevant answers."
        
        full_prompt = f"{system_prompt}\n\nContext Information:\n{context_info}\n\nUser: {test_query}\nAssistant:"
        
        print("📝 Full LLM Prompt Preview:")
        print("=" * 50)
        print(full_prompt)
        print("=" * 50)
        
        # Check if prompt contains meaningful context
        if "Cursor" in full_prompt or "development" in full_prompt or "coding" in full_prompt:
            print("✅ MEANINGFUL context found in prompt!")
        else:
            print("❌ No meaningful context in prompt")
            
    except Exception as e:
        print(f"❌ ERROR testing context integration: {e}")

async def main():
    """Main test function"""
    await test_context_retrieval()
    await test_context_integration()
    
    print(f"\n💡 Diagnosis Summary:")
    print("=" * 60)
    print("If you're not getting contextual answers:")
    print("1. Check if memory contains meaningful entries")
    print("2. Verify context retrieval returns relevant memories")
    print("3. Ensure confidence scores are above 0.3")
    print("4. Confirm context is properly formatted for LLM")

if __name__ == "__main__":
    asyncio.run(main())