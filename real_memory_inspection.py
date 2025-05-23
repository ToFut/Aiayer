#!/usr/bin/env python3
"""
Real Memory Inspection - NO MOCK DATA
Shows actual memory content and semantic search data
"""

import sys
import os
import json
import asyncio
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory.memory_system import MemorySystem

async def inspect_real_memory():
    """Inspect actual memory content and search data"""
    print("\n" + "="*100)
    print("🔍 REAL MEMORY CONTENT INSPECTION - NO MOCK DATA")
    print("="*100)
    
    try:
        # Initialize memory system
        memory = MemorySystem()
        
        # ===========================================
        # PART 1: RAW MEMORY CONTENT
        # ===========================================
        print("\n📊 RAW MEMORY CONTENT")
        print("="*80)
        
        # Short-term Memory - Show actual content
        print(f"\n📋 SHORT-TERM MEMORY - RAW DATA ({len(memory.short_term_memory)} items)")
        print("-" * 70)
        
        if memory.short_term_memory:
            for i, item in enumerate(list(memory.short_term_memory)[:5], 1):
                print(f"\n   Item {i}:")
                if isinstance(item, dict):
                    # Pretty print the actual JSON content
                    print(json.dumps(item, indent=6, sort_keys=True)[:500] + "...")
                else:
                    print(f"      {repr(item)}")
        else:
            print("   No short-term memories found")
        
        # Long-term Memory
        print(f"\n📚 LONG-TERM MEMORY - RAW DATA ({len(memory.long_term_memory)} items)")
        print("-" * 70)
        
        if memory.long_term_memory:
            for i, item in enumerate(list(memory.long_term_memory)[:3], 1):
                print(f"\n   Item {i}:")
                if isinstance(item, dict):
                    print(json.dumps(item, indent=6, sort_keys=True)[:400] + "...")
                else:
                    print(f"      {repr(item)}")
        else:
            print("   No long-term memories found")
        
        # Context Memory
        print(f"\n🎯 CONTEXT MEMORY - RAW DATA ({len(memory.context_memory)} items)")
        print("-" * 70)
        
        if memory.context_memory:
            for i, item in enumerate(list(memory.context_memory)[:3], 1):
                print(f"\n   Item {i}:")
                if isinstance(item, dict):
                    print(json.dumps(item, indent=6, sort_keys=True)[:400] + "...")
                else:
                    print(f"      {repr(item)}")
        else:
            print("   No context memories found")
        
        # ===========================================
        # PART 2: SEMANTIC SEARCH ENGINE INSPECTION
        # ===========================================
        print("\n" + "🔍 SEMANTIC SEARCH ENGINE INSPECTION")
        print("="*80)
        
        if hasattr(memory, 'semantic_search') and memory.semantic_search:
            search_engine = memory.semantic_search
            
            print(f"\n📊 SEARCH ENGINE STATE")
            print("-" * 50)
            
            # Check available attributes
            search_attrs = [attr for attr in dir(search_engine) if not attr.startswith('_')]
            print(f"   Available attributes: {', '.join(search_attrs[:10])}")
            
            # Try to get indexed data
            try:
                if hasattr(search_engine, 'documents'):
                    docs = search_engine.documents
                    print(f"\n   📚 Indexed Documents: {len(docs) if docs else 0}")
                    if docs:
                        for i, doc in enumerate(docs[:3], 1):
                            print(f"      Doc {i}: {str(doc)[:80]}...")
                
                if hasattr(search_engine, 'index'):
                    index_info = search_engine.index
                    print(f"\n   🗂️ Search Index: {type(index_info)}")
                    print(f"      Index content: {str(index_info)[:100]}...")
                
                if hasattr(search_engine, 'vectorizer'):
                    vectorizer = search_engine.vectorizer
                    print(f"\n   🔢 Vectorizer: {type(vectorizer)}")
                    if hasattr(vectorizer, 'vocabulary_'):
                        vocab_size = len(vectorizer.vocabulary_) if vectorizer.vocabulary_ else 0
                        print(f"      Vocabulary size: {vocab_size}")
                        if vocab_size > 0:
                            sample_words = list(vectorizer.vocabulary_.keys())[:10]
                            print(f"      Sample words: {sample_words}")
            
            except Exception as e:
                print(f"   ⚠️ Could not access search engine internals: {e}")
        
        else:
            print("   ❌ Semantic search engine not available")
        
        # ===========================================
        # PART 3: ACTUAL MEMORY FILES INSPECTION
        # ===========================================
        print("\n" + "📁 MEMORY FILES INSPECTION")
        print("="*80)
        
        memory_files = [
            "/Users/segevbin/Desktop/SensAI/Aiayer/memory/memory_state.json",
            "/Users/segevbin/Desktop/SensAI/Aiayer/memory/conscious.json",
            "/Users/segevbin/Desktop/SensAI/Aiayer/memory/conversation_history.json",
            "/Users/segevbin/Desktop/SensAI/Aiayer/memory/last_context.json"
        ]
        
        for file_path in memory_files:
            print(f"\n📄 {os.path.basename(file_path)}")
            print("-" * 50)
            
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    print(f"   File size: {os.path.getsize(file_path)} bytes")
                    print(f"   Data type: {type(data)}")
                    
                    if isinstance(data, dict):
                        print(f"   Keys: {list(data.keys())}")
                        for key, value in list(data.items())[:3]:
                            print(f"   {key}: {str(value)[:100]}...")
                    elif isinstance(data, list):
                        print(f"   List length: {len(data)}")
                        for i, item in enumerate(data[:2], 1):
                            print(f"   Item {i}: {str(item)[:100]}...")
                    else:
                        print(f"   Content: {str(data)[:200]}...")
                        
                except Exception as e:
                    print(f"   ❌ Error reading file: {e}")
            else:
                print("   📭 File does not exist")
        
        # ===========================================
        # PART 4: REAL SEMANTIC SEARCH TEST
        # ===========================================
        print("\n" + "🔬 REAL SEMANTIC SEARCH TEST")
        print("="*80)
        
        test_queries = [
            "Visual Studio Code programming",
            "user interface design",
            "data analysis"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n🔍 Test Search {i}: '{query}'")
            print("-" * 40)
            
            try:
                results = await memory.search_memory(query, limit=5)
                
                print(f"   ✅ Search completed")
                print(f"   📊 Results found: {len(results) if results else 0}")
                
                if results:
                    for j, result in enumerate(results, 1):
                        print(f"\n   Result {j}:")
                        if isinstance(result, dict):
                            for key, value in result.items():
                                print(f"      {key}: {str(value)[:80]}...")
                        else:
                            print(f"      {str(result)[:100]}...")
                else:
                    print("   📝 No results - empty search index")
            
            except Exception as e:
                print(f"   ❌ Search error: {e}")
        
        # ===========================================
        # PART 5: VECTOR STORE INSPECTION
        # ===========================================
        print("\n" + "🗃️ VECTOR STORE INSPECTION")
        print("="*80)
        
        vector_db_path = "/Users/segevbin/Desktop/SensAI/Aiayer/memory/vector_store.db"
        
        if os.path.exists(vector_db_path):
            file_size = os.path.getsize(vector_db_path)
            print(f"   📊 Vector store file size: {file_size} bytes")
            print(f"   📅 Last modified: {datetime.fromtimestamp(os.path.getmtime(vector_db_path))}")
            
            try:
                # Try to inspect SQLite database if it's a database file
                import sqlite3
                conn = sqlite3.connect(vector_db_path)
                cursor = conn.cursor()
                
                # Get table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                print(f"   📋 Tables: {[table[0] for table in tables]}")
                
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    print(f"   📊 {table_name}: {count} records")
                
                conn.close()
                
            except Exception as e:
                print(f"   ⚠️ Could not inspect vector store: {e}")
        else:
            print("   📭 Vector store file does not exist")
        
        print("\n" + "="*100)
        print("✅ REAL MEMORY INSPECTION COMPLETED")
        print("="*100)
        print("🎯 Summary:")
        print(f"   • Short-term memories: {len(memory.short_term_memory)}")
        print(f"   • Long-term memories: {len(memory.long_term_memory)}")
        print(f"   • Context memories: {len(memory.context_memory)}")
        print(f"   • Search engine: {'Available' if hasattr(memory, 'semantic_search') and memory.semantic_search else 'Not available'}")
        print("   • All data shown above is REAL system data, no mock content")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Inspection failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(inspect_real_memory())
    if success:
        print("\n🎉 Real memory inspection completed!")
    else:
        print("\n⚠️ Issues encountered during inspection.")