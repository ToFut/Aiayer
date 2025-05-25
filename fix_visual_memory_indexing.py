#!/usr/bin/env python3
"""
Fix Visual Memory Indexing - Specialized indexer for visual analysis memories
Addresses the issue where semantic search returns 0 results for visual queries like "what am I seeing?"
Re-indexes visual analysis data with proper search terms.
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory.semantic_search_agent import add_memory, search_memories, get_context_for_query

async def read_existing_visual_memories():
    """Read existing visual analysis data from memory files"""
    visual_memories = []
    
    try:
        # Check conscious memory for visual data
        conscious_file = "memory/conscious.json"
        if os.path.exists(conscious_file):
            with open(conscious_file, 'r') as f:
                conscious_data = json.load(f)
                print(f"📖 Found conscious memory with {len(conscious_data)} entries")
                
                for entry in conscious_data.get("insights", []):
                    if any(keyword in str(entry).lower() for keyword in [
                        'screen', 'visual', 'cursor', 'application', 'ui', 'display', 
                        'window', 'interface', 'ocr', 'text_detected', 'app_detected',
                        'comprehensive_visual_analysis', 'text_content', 'content_analysis'
                    ]):
                        visual_memories.append({
                            "source": "conscious_memory",
                            "data": entry,
                            "timestamp": entry.get("timestamp", datetime.now().isoformat())
                        })
        
        # Check memory state for visual context
        memory_state_file = "memory/memory_state.json"
        if os.path.exists(memory_state_file):
            with open(memory_state_file, 'r') as f:
                memory_state = json.load(f)
                print(f"📖 Found memory state with {len(memory_state.get('memories', []))} memories")
                
                for memory in memory_state.get("memories", []):
                    if any(keyword in str(memory).lower() for keyword in [
                        'screen', 'visual', 'cursor', 'application', 'ui', 'display'
                    ]):
                        visual_memories.append({
                            "source": "memory_state",
                            "data": memory,
                            "timestamp": memory.get("timestamp", datetime.now().isoformat())
                        })
        
        # Check last context for recent visual data
        last_context_file = "memory/last_context.json"
        if os.path.exists(last_context_file):
            with open(last_context_file, 'r') as f:
                last_context = json.load(f)
                print(f"📖 Found last context data")
                
                if any(keyword in str(last_context).lower() for keyword in [
                    'screen', 'visual', 'cursor', 'application', 'ui', 'display'
                ]):
                    visual_memories.append({
                        "source": "last_context",
                        "data": last_context,
                        "timestamp": datetime.now().isoformat()
                    })
    
    except Exception as e:
        print(f"❌ Error reading visual memories: {e}")
    
    print(f"🔍 Found {len(visual_memories)} visual memory entries to re-index")
    return visual_memories

def create_visual_search_content(memory_data):
    """Create searchable content specifically for visual queries"""
    
    # Extract key visual information
    content_parts = []
    
    # Add screen/display related terms
    base_terms = [
        "current screen content",
        "what I'm seeing",
        "visual display",
        "screen analysis",
        "current application",
        "display content"
    ]
    content_parts.extend(base_terms)
    
    # Extract application information
    data_str = str(memory_data).lower()
    if 'cursor' in data_str:
        content_parts.extend([
            "Cursor application active",
            "development environment",
            "code editor visible",
            "programming interface"
        ])
    
    if 'terminal' in data_str or 'command' in data_str:
        content_parts.extend([
            "terminal window open",
            "command line interface",
            "console visible"
        ])
    
    if 'aiayer' in data_str:
        content_parts.extend([
            "Aiayer project active",
            "AI system interface",
            "agent system running"
        ])
    
    # Extract UI elements
    if any(ui_term in data_str for ui_term in ['button', 'menu', 'dialog', 'window']):
        content_parts.append("interactive UI elements visible")
    
    # Extract text content if available
    if isinstance(memory_data, dict):
        # Look for OCR text or screen content
        for key in ['text_detected', 'ocr_content', 'screen_content', 'extracted_text']:
            if key in memory_data and memory_data[key]:
                content_parts.append(f"screen text: {memory_data[key][:200]}")
        
        # Look for application detection
        for key in ['app_detected', 'current_app', 'active_application']:
            if key in memory_data and memory_data[key]:
                content_parts.append(f"using {memory_data[key]} application")
    
    # Create comprehensive searchable content
    searchable_content = " | ".join(content_parts)
    
    return searchable_content

async def reindex_visual_memories():
    """Re-index all visual memories with proper search terms"""
    print("🔄 Starting visual memory re-indexing...")
    
    # Read existing visual memories
    visual_memories = await read_existing_visual_memories()
    
    if not visual_memories:
        print("❌ No visual memories found to re-index")
        return False
    
    reindexed_count = 0
    
    for i, memory_entry in enumerate(visual_memories):
        try:
            # Create visual-specific searchable content
            searchable_content = create_visual_search_content(memory_entry["data"])
            
            # Add visual-specific tags
            visual_tags = {
                "visual_query", "screen_content", "what_am_i_seeing", 
                "current_display", "visual_analysis", "screen_analysis"
            }
            
            # Add memory with visual search optimization
            await add_memory(
                content=searchable_content,
                source=f"visual_reindex_{memory_entry['source']}",
                tags=visual_tags,
                metadata={
                    "original_timestamp": memory_entry["timestamp"],
                    "reindexed_at": datetime.now().isoformat(),
                    "visual_optimized": True,
                    "query_types": ["what am I seeing", "current screen", "visual content"]
                }
            )
            
            reindexed_count += 1
            print(f"✅ Re-indexed visual memory {i+1}/{len(visual_memories)}")
            
        except Exception as e:
            print(f"❌ Error re-indexing memory {i+1}: {e}")
    
    print(f"🎯 Successfully re-indexed {reindexed_count} visual memories")
    return reindexed_count > 0

async def test_visual_query_search():
    """Test if visual queries now return results"""
    print("\n🧪 Testing visual query search...")
    
    test_queries = [
        "what am I seeing",
        "current screen content",
        "what's on my screen",
        "visual display",
        "what application am I using",
        "screen analysis"
    ]
    
    results_summary = {}
    
    for query in test_queries:
        try:
            print(f"\n🔍 Testing query: '{query}'")
            
            # Search for memories
            memories = await search_memories(query, top_k=3)
            print(f"   📊 Found {len(memories)} memories")
            
            # Get context
            context = await get_context_for_query(query, max_context_length=500)
            context_length = len(context) if context else 0
            print(f"   📝 Context length: {context_length} characters")
            
            results_summary[query] = {
                "memories_found": len(memories),
                "context_length": context_length,
                "success": len(memories) > 0 and context_length > 0
            }
            
            if memories:
                print(f"   ✅ Sample memory: {str(memories[0])[:100]}...")
            else:
                print(f"   ❌ No memories found for visual query")
                
        except Exception as e:
            print(f"   ❌ Error testing query '{query}': {e}")
            results_summary[query] = {"error": str(e)}
    
    # Summary
    successful_queries = sum(1 for result in results_summary.values() 
                           if isinstance(result, dict) and result.get("success", False))
    
    print(f"\n📊 VISUAL QUERY TEST RESULTS:")
    print(f"   Successful queries: {successful_queries}/{len(test_queries)}")
    print(f"   Success rate: {(successful_queries/len(test_queries))*100:.1f}%")
    
    if successful_queries > 0:
        print("   ✅ Visual memory indexing FIXED!")
    else:
        print("   ❌ Visual memory indexing still needs work")
    
    return successful_queries > 0

async def main():
    """Main execution function"""
    print("🚀 Visual Memory Indexing Fix")
    print("=" * 50)
    
    try:
        # Step 1: Re-index visual memories
        reindex_success = await reindex_visual_memories()
        
        if not reindex_success:
            print("❌ Failed to re-index visual memories")
            return
        
        # Step 2: Test visual query search
        await asyncio.sleep(1)  # Give indexing time to complete
        test_success = await test_visual_query_search()
        
        # Summary
        print(f"\n🏁 FINAL RESULTS:")
        print(f"   Re-indexing: {'✅ SUCCESS' if reindex_success else '❌ FAILED'}")
        print(f"   Query Testing: {'✅ SUCCESS' if test_success else '❌ FAILED'}")
        
        if reindex_success and test_success:
            print("\n🎉 Visual memory indexing has been FIXED!")
            print("   ASK/SUGGEST modes should now return actual visual context")
            print("   for queries like 'what am I seeing?'")
        else:
            print("\n⚠️  Issues remain with visual memory indexing")
            
    except Exception as e:
        print(f"❌ Critical error in visual memory indexing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())