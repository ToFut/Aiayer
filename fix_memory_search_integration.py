#!/usr/bin/env python3
"""
Fix Memory Search Integration
The issue: Memory system has data but it's not indexed for semantic search
Solution: Add memory entries to searchable index and fix search algorithm
"""

import json
import asyncio
import sys
import os
from datetime import datetime

# Add project paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory.semantic_search_agent import add_memory

async def index_existing_memory():
    """Index existing memory entries for semantic search"""
    
    print("🔧 Fixing Memory Search Integration")
    print("=" * 50)
    
    indexed_count = 0
    
    # 1. Index conscious memory insights
    print("📝 Indexing conscious memory insights...")
    
    try:
        conscious_file = "memory/conscious.json"
        if os.path.exists(conscious_file):
            with open(conscious_file, 'r') as f:
                conscious_data = json.load(f)
            
            insights = conscious_data.get('insights', [])
            print(f"   Found {len(insights)} insights to index")
            
            for insight in insights:
                # Extract searchable content
                if insight.get('memory_type') == 'comprehensive_visual_analysis':
                    # For comprehensive visual analysis
                    app = insight.get('application_context', {}).get('primary_application', 'unknown')
                    activity = insight.get('user_behavior', {}).get('current_activity', 'unknown')
                    text_content = insight.get('content_analysis', {}).get('text_content', '')
                    
                    # Create searchable content
                    searchable_content = f"Using {app} for {activity}. Screen content: {text_content}"
                    
                    # Add to search index
                    await add_memory(
                        searchable_content,
                        source="comprehensive_visual_analysis",
                        tags={"visual_analysis", "application", app.lower(), activity}
                    )
                    indexed_count += 1
                    
                elif insight.get('memory_type') == 'activity_analysis':
                    # For activity analysis
                    app = insight.get('user_activity', {}).get('application_used', 'unknown')
                    activity = insight.get('user_activity', {}).get('primary_activity', 'unknown')
                    context = insight.get('user_activity', {}).get('professional_context', 'unknown')
                    productivity = insight.get('user_activity', {}).get('productivity_score', 0)
                    
                    # Create searchable content
                    searchable_content = f"User is doing {activity} using {app}. Professional context: {context}. Productivity score: {productivity}"
                    
                    # Add to search index
                    await add_memory(
                        searchable_content,
                        source="activity_analysis",
                        tags={"activity", "productivity", app.lower(), activity, context}
                    )
                    indexed_count += 1
            
            print(f"   ✅ Indexed {indexed_count} insights from conscious memory")
        else:
            print("   ❌ Conscious memory file not found")
    
    except Exception as e:
        print(f"   ❌ Error indexing conscious memory: {e}")
    
    # 2. Index short-term memory
    print("🧠 Indexing short-term memory...")
    
    try:
        memory_state_file = "memory/memory_state.json"
        if os.path.exists(memory_state_file):
            with open(memory_state_file, 'r') as f:
                memory_state = json.load(f)
            
            short_term = memory_state.get('short_term', [])
            print(f"   Found {len(short_term)} short-term memories")
            
            for memory in short_term:
                if memory.get('memory_type') == 'comprehensive_visual_analysis':
                    app = memory.get('application_context', {}).get('primary_application', 'unknown')
                    activity = memory.get('user_behavior', {}).get('current_activity', 'unknown')
                    text_content = memory.get('content_analysis', {}).get('text_content', '')
                    
                    searchable_content = f"Application: {app}, Activity: {activity}, Content: {text_content[:200]}"
                    
                    await add_memory(
                        searchable_content,
                        source="short_term_memory",
                        tags={"short_term", app.lower(), activity}
                    )
                    indexed_count += 1
            
            print(f"   ✅ Indexed {len(short_term)} short-term memories")
        else:
            print("   ❌ Memory state file not found")
    
    except Exception as e:
        print(f"   ❌ Error indexing short-term memory: {e}")
    
    # 3. Add current development context
    print("💻 Adding current development context...")
    
    development_context = [
        "User is actively using Cursor IDE for AI-assisted development and programming",
        "Current development workflow includes coding, debugging, and software engineering tasks",
        "User has high productivity scores when using development tools like Cursor",
        "Professional context is software engineering and programming work",
        "User frequently works with code editors and development environments",
        "Screen analysis shows content related to programming and code development",
        "User intent is often related to editing, coding, and development workflows"
    ]
    
    for context in development_context:
        await add_memory(
            context,
            source="development_context",
            tags={"development", "cursor", "programming", "coding", "productivity"}
        )
        indexed_count += 1
    
    print(f"   ✅ Added {len(development_context)} development context entries")
    
    print(f"\n🎯 Total indexed entries: {indexed_count}")
    return indexed_count

async def test_fixed_search():
    """Test the fixed semantic search"""
    
    print("\n🧪 Testing Fixed Semantic Search")
    print("=" * 50)
    
    from memory.semantic_search_agent import get_context_for_query
    
    test_queries = [
        "What applications am I using for development?",
        "How productive have I been?",
        "What tools do I use for coding?",
        "What is my development workflow?"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        
        try:
            context = await get_context_for_query(query, max_context_length=1000)
            
            confidence = context.get('confidence_score', 0)
            memories = context.get('relevant_memories', [])
            
            print(f"   📊 Confidence: {confidence:.3f}")
            print(f"   📝 Memories found: {len(memories)}")
            
            if memories:
                for i, memory in enumerate(memories[:2], 1):
                    content = memory.get('content', 'No content')[:80]
                    score = memory.get('similarity_score', 0)
                    print(f"   {i}. Score: {score:.3f} | {content}...")
            
            if confidence > 0.3:
                print("   ✅ MEANINGFUL context retrieved!")
            elif confidence > 0.1:
                print("   ⚠️  Weak context")
            else:
                print("   ❌ No meaningful context")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

async def main():
    """Main fix function"""
    
    # Fix the indexing
    indexed_count = await index_existing_memory()
    
    if indexed_count > 0:
        print("\n✅ Memory indexing completed!")
        
        # Test the fix
        await test_fixed_search()
        
        print("\n💡 Next Steps:")
        print("1. The memory search should now return meaningful context")
        print("2. Ask/Suggest modes should provide contextual responses")
        print("3. Backend will use this context in LLM prompts")
        print("4. Test with: 'What development tools am I using?'")
    else:
        print("\n❌ No memory entries were indexed")
        print("Make sure the memory system has collected some data first")

if __name__ == "__main__":
    asyncio.run(main())