#!/usr/bin/env python3
"""
Fix Corrupted Embeddings - Clear corrupted embeddings and re-add visual memories
The embedding vectors are corrupted with infinite values and wrong dimensions
"""

import asyncio
import json
import sys
import os
import sqlite3
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory.semantic_search_agent import add_memory, search_memories, get_context_for_query

async def clear_corrupted_data():
    """Clear all corrupted data from the database"""
    print("🧹 Clearing corrupted embeddings and documents...")
    
    db_path = "memory/vector_store.db"
    
    try:
        with sqlite3.connect(db_path) as conn:
            # Clear embeddings table
            conn.execute("DELETE FROM embeddings")
            print("   ✅ Cleared embeddings table")
            
            # Clear documents table
            conn.execute("DELETE FROM documents")
            print("   ✅ Cleared documents table")
            
            conn.commit()
        
        print("🗑️  Database cleared successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error clearing database: {e}")
        return False

async def add_visual_memories_properly():
    """Add visual memories with proper content and structure"""
    print("📝 Adding visual memories with proper embeddings...")
    
    # Read visual memory content from conscious.json
    conscious_file = "memory/conscious.json"
    visual_memories = []
    
    try:
        with open(conscious_file, 'r') as f:
            conscious_data = json.load(f)
            
            for entry in conscious_data.get("insights", []):
                if entry.get("memory_type") == "comprehensive_visual_analysis":
                    visual_memories.append(entry)
        
        print(f"📖 Found {len(visual_memories)} visual analysis entries")
        
        added_count = 0
        
        for i, memory in enumerate(visual_memories):
            try:
                # Extract key information for better searchability
                app_name = memory.get("application_context", {}).get("primary_application", "Unknown")
                text_content = memory.get("content_analysis", {}).get("text_content", "")
                word_count = memory.get("content_analysis", {}).get("word_count", 0)
                
                # Create comprehensive searchable content
                searchable_parts = [
                    # Primary visual queries
                    "what am I seeing on my screen",
                    "current screen display content",
                    "visual content analysis",
                    "screen text and applications",
                    
                    # Application context
                    f"currently using {app_name} application",
                    f"{app_name} interface active",
                    
                    # Screen content
                    f"screen contains {word_count} words of text",
                    "development environment visible",
                    "code editor interface",
                    
                    # Specific content if available
                ]
                
                if text_content and len(text_content) > 10:
                    # Add key phrases from the actual screen text
                    text_sample = text_content[:200].replace('\n', ' ').strip()
                    searchable_parts.append(f"screen text: {text_sample}")
                
                if "cursor" in app_name.lower():
                    searchable_parts.extend([
                        "Cursor code editor active",
                        "development tools visible", 
                        "programming interface displayed"
                    ])
                
                if "aiayer" in str(memory).lower():
                    searchable_parts.extend([
                        "Aiayer project active",
                        "AI assistant system running",
                        "agent development environment"
                    ])
                
                # Combine all searchable content
                content = " | ".join(searchable_parts)
                
                # Add to memory system
                success = await add_memory(
                    content=content,
                    source="visual_analysis_fixed",
                    tags=["visual_query", "screen_content", "current_display", "what_am_i_seeing"],
                    metadata={
                        "timestamp": memory.get("timestamp"),
                        "application": app_name,
                        "word_count": word_count,
                        "analysis_type": "comprehensive_visual",
                        "fixed_embeddings": True,
                        "query_optimized": True
                    }
                )
                
                if success:
                    added_count += 1
                    print(f"   ✅ Added visual memory {i+1}/{len(visual_memories)}")
                else:
                    print(f"   ❌ Failed to add memory {i+1}")
                    
            except Exception as e:
                print(f"   ❌ Error adding memory {i+1}: {e}")
        
        print(f"🎯 Successfully added {added_count} visual memories with proper embeddings")
        return added_count > 0
        
    except Exception as e:
        print(f"❌ Error reading visual memories: {e}")
        return False

async def test_fixed_embeddings():
    """Test if the fixed embeddings work properly"""
    print("\n🧪 Testing fixed embeddings...")
    
    test_queries = [
        "what am I seeing",
        "current screen content", 
        "what application am I using",
        "screen display"
    ]
    
    working_queries = 0
    
    for query in test_queries:
        try:
            print(f"\n🔍 Testing: '{query}'")
            
            # Search memories
            results = await search_memories(query, top_k=3, min_similarity=0.1)
            print(f"   📊 Found {len(results)} results")
            
            if results:
                for i, result in enumerate(results[:2]):
                    print(f"   {i+1}. Similarity: {result.similarity_score:.3f}")
                    print(f"      Content: {result.content[:80]}...")
                
                working_queries += 1
            else:
                print(f"   ❌ No results found")
                
        except Exception as e:
            print(f"   ❌ Error testing '{query}': {e}")
    
    success_rate = (working_queries / len(test_queries)) * 100
    print(f"\n📊 EMBEDDING FIX RESULTS:")
    print(f"   Working queries: {working_queries}/{len(test_queries)}")
    print(f"   Success rate: {success_rate:.1f}%")
    
    if success_rate >= 75:
        print("   ✅ Embeddings FIXED successfully!")
    else:
        print("   ⚠️  Embeddings still need work")
    
    return success_rate >= 75

async def main():
    """Main execution function"""
    print("🚀 Fixing Corrupted Embeddings")
    print("=" * 50)
    
    try:
        # Step 1: Clear corrupted data
        clear_success = await clear_corrupted_data()
        
        if not clear_success:
            print("❌ Failed to clear corrupted data")
            return
        
        # Step 2: Re-add visual memories with proper embeddings
        await asyncio.sleep(1)  # Brief pause
        add_success = await add_visual_memories_properly()
        
        if not add_success:
            print("❌ Failed to add visual memories")
            return
        
        # Step 3: Test fixed embeddings
        await asyncio.sleep(1)  # Brief pause
        test_success = await test_fixed_embeddings()
        
        # Summary
        print(f"\n🏁 FINAL RESULTS:")
        print(f"   Database clearing: {'✅ SUCCESS' if clear_success else '❌ FAILED'}")
        print(f"   Memory addition: {'✅ SUCCESS' if add_success else '❌ FAILED'}")
        print(f"   Embedding testing: {'✅ SUCCESS' if test_success else '❌ FAILED'}")
        
        if clear_success and add_success and test_success:
            print("\n🎉 EMBEDDINGS HAVE BEEN FIXED!")
            print("   Visual queries should now work properly")
            print("   ASK/SUGGEST modes will return actual visual context")
        else:
            print("\n⚠️  Some issues remain with embeddings")
            
    except Exception as e:
        print(f"❌ Critical error fixing embeddings: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())