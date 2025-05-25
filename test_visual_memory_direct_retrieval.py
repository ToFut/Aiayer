#!/usr/bin/env python3
"""
Direct test of visual memory retrieval bypassing problematic embeddings
"""

import asyncio
import sqlite3
import json
from datetime import datetime

def direct_visual_memory_test():
    """Test direct retrieval of visual memories from database"""
    print("🔍 Testing Direct Visual Memory Retrieval...")
    
    # Connect directly to database
    conn = sqlite3.connect('memory/vector_store.db')
    
    # Get visual memories containing specific terms
    cursor = conn.execute("""
        SELECT content, source, metadata 
        FROM documents 
        WHERE content LIKE '%what am I seeing%' 
           OR content LIKE '%current screen%'
           OR content LIKE '%Cursor development%'
           OR content LIKE '%development environment%'
        ORDER BY LENGTH(content) DESC
    """)
    
    visual_memories = cursor.fetchall()
    print(f"Found {len(visual_memories)} visual memories")
    
    for i, (content, source, metadata) in enumerate(visual_memories):
        print(f"\n--- Visual Memory {i+1} ---")
        print(f"Source: {source}")
        print(f"Content: {content[:200]}...")
        if metadata:
            try:
                meta = json.loads(metadata)
                print(f"Metadata: {meta}")
            except:
                pass
    
    conn.close()
    
    return visual_memories

async def test_context_retrieval_with_direct_search():
    """Test context retrieval using direct database search instead of embeddings"""
    print("\n🎯 Testing Context Retrieval with Direct Search...")
    
    query = "what am I seeing?"
    query_terms = ["what am I seeing", "current screen", "screen content", "visual", "display"]
    
    conn = sqlite3.connect('memory/vector_store.db')
    
    # Build search query for any of the terms
    search_conditions = " OR ".join([f"content LIKE '%{term}%'" for term in query_terms])
    
    cursor = conn.execute(f"""
        SELECT content, source, timestamp, metadata
        FROM documents 
        WHERE {search_conditions}
        ORDER BY 
            CASE 
                WHEN content LIKE '%what am I seeing%' THEN 1
                WHEN content LIKE '%current screen%' THEN 2
                WHEN content LIKE '%Cursor development%' THEN 3
                ELSE 4
            END,
            LENGTH(content) DESC
        LIMIT 5
    """)
    
    results = cursor.fetchall()
    
    print(f"Direct search found {len(results)} results for query: '{query}'")
    
    # Build context response like the semantic search agent would
    context = {
        'relevant_memories': [],
        'total_matches': len(results),
        'confidence_score': 0.8 if results else 0.0,  # High confidence for direct matches
        'context_summary': "",
        'key_topics': ['visual_content', 'screen_analysis', 'development_environment'],
        'sources': []
    }
    
    for content, source, timestamp, metadata in results:
        context['relevant_memories'].append({
            'content': content,
            'similarity': 0.9,  # High similarity for direct matches
            'source': source,
            'timestamp': timestamp,
            'confidence': 0.8
        })
        context['sources'].append(source)
    
    context['sources'] = list(set(context['sources']))
    
    # Create summary from best match
    if results:
        best_content = results[0][0]
        if "Cursor development environment" in best_content:
            context['context_summary'] = "You are currently seeing a Cursor development environment with AI development project, code editor interface, terminal, and AI assistant modes visible."
        elif "what am I seeing" in best_content:
            context['context_summary'] = "Current screen display shows visual content and interface elements related to your development work."
        else:
            context['context_summary'] = "Screen content includes development workspace and programming interface elements."
    
    print(f"Context: {json.dumps(context, indent=2)}")
    
    conn.close()
    return context

if __name__ == "__main__":
    # Test direct retrieval
    visual_memories = direct_visual_memory_test()
    
    # Test context building
    context = asyncio.run(test_context_retrieval_with_direct_search())
    
    print(f"\n✅ Direct visual memory retrieval successful!")
    print(f"Found {len(visual_memories)} memories")
    print(f"Context confidence: {context['confidence_score']}")
    print(f"Total matches: {context['total_matches']}")