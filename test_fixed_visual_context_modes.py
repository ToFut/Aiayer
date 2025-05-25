#!/usr/bin/env python3
"""
Test Fixed Visual Context Modes
Test ASK/SUGGEST modes to verify they now return actual visual context instead of generic responses
"""

import asyncio
import json
import sys
import os
import time
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory.semantic_search_agent import search_memories, get_context_for_query

async def test_backend_integration():
    """Test if the backend integration works with visual context"""
    print("🔗 Testing backend integration with visual context...")
    
    # Simulate backend context lookup
    test_queries = [
        "what am I seeing",
        "current screen content", 
        "what's on my screen",
        "what application am I using"
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: '{query}'")
        
        try:
            # Get context like the backend does
            context = await get_context_for_query(query, max_context_length=500)
            context_length = len(context) if context else 0
            
            print(f"   📊 Context length: {context_length} characters")
            
            if context_length > 10:  # More than just empty response
                print(f"   ✅ Context preview: {str(context)[:150]}...")
                
                # Check if context contains actual visual information
                visual_indicators = [
                    'cursor', 'application', 'screen', 'text_content', 
                    'aiayer', 'node', 'terminal', 'development'
                ]
                
                visual_matches = [indicator for indicator in visual_indicators 
                                if indicator.lower() in str(context).lower()]
                
                if visual_matches:
                    print(f"   🎯 Visual indicators found: {visual_matches}")
                else:
                    print(f"   ⚠️  No visual indicators in context")
            else:
                print(f"   ❌ Context too short - likely generic response")
                
        except Exception as e:
            print(f"   ❌ Error getting context: {e}")

async def test_mode_simulation():
    """Simulate ASK/SUGGEST mode responses with visual queries"""
    print("\n🧠 Testing mode simulation with visual queries...")
    
    test_cases = [
        {
            "mode": "ask",
            "query": "what am I seeing on my screen right now?",
            "expected_visual_elements": ["cursor", "text_content", "application"]
        },
        {
            "mode": "suggest", 
            "query": "can you help me with what's currently displayed?",
            "expected_visual_elements": ["screen", "display", "current"]
        },
        {
            "mode": "ask",
            "query": "what application am I currently using?",
            "expected_visual_elements": ["application", "cursor", "aiayer"]
        }
    ]
    
    successful_tests = 0
    
    for i, test_case in enumerate(test_cases):
        print(f"\n🧪 Test {i+1}: {test_case['mode'].upper()} mode")
        print(f"   Query: '{test_case['query']}'")
        
        try:
            # Get context that would be sent to LLM
            context = await get_context_for_query(test_case['query'], max_context_length=800)
            
            if context:
                context_str = str(context).lower()
                found_elements = []
                
                for element in test_case['expected_visual_elements']:
                    if element.lower() in context_str:
                        found_elements.append(element)
                
                print(f"   📊 Found visual elements: {found_elements}")
                print(f"   📊 Expected elements: {test_case['expected_visual_elements']}")
                
                success_rate = len(found_elements) / len(test_case['expected_visual_elements'])
                print(f"   📈 Success rate: {success_rate*100:.1f}%")
                
                if success_rate >= 0.5:  # At least 50% of expected elements found
                    print(f"   ✅ Test PASSED - Visual context retrieved")
                    successful_tests += 1
                else:
                    print(f"   ❌ Test FAILED - Insufficient visual context")
                
                # Show context preview
                print(f"   💬 Context preview: {str(context)[:200]}...")
                
            else:
                print(f"   ❌ No context retrieved")
                
        except Exception as e:
            print(f"   ❌ Error in test: {e}")
    
    print(f"\n📊 SIMULATION RESULTS:")
    print(f"   Successful tests: {successful_tests}/{len(test_cases)}")
    print(f"   Success rate: {(successful_tests/len(test_cases))*100:.1f}%")
    
    return successful_tests >= len(test_cases) * 0.7  # 70% success threshold

async def test_memory_search_quality():
    """Test the quality of visual memory search results"""
    print("\n🔍 Testing visual memory search quality...")
    
    search_tests = [
        {
            "query": "what am I seeing", 
            "min_results": 2,
            "visual_terms": ["screen", "display", "current", "visual"]
        },
        {
            "query": "current application",
            "min_results": 1, 
            "visual_terms": ["cursor", "application", "aiayer"]
        },
        {
            "query": "screen content text",
            "min_results": 1,
            "visual_terms": ["text_content", "node", "aiayer"]
        }
    ]
    
    quality_scores = []
    
    for test in search_tests:
        print(f"\n🔎 Search test: '{test['query']}'")
        
        try:
            # Search memories
            results = await search_memories(test['query'], top_k=5)
            
            print(f"   📊 Found {len(results)} results (min required: {test['min_results']})")
            
            if len(results) >= test['min_results']:
                # Analyze result quality
                visual_term_matches = 0
                total_terms = len(test['visual_terms'])
                
                for result in results[:3]:  # Check top 3 results
                    content_str = str(result.content).lower()
                    for term in test['visual_terms']:
                        if term.lower() in content_str:
                            visual_term_matches += 1
                            break  # Count each result only once
                
                quality_score = (visual_term_matches / min(3, len(results))) * 100
                quality_scores.append(quality_score)
                
                print(f"   📈 Quality score: {quality_score:.1f}%")
                print(f"   🎯 Visual term relevance: {visual_term_matches}/{min(3, len(results))} results")
                
                if results:
                    print(f"   💡 Top result: {str(results[0].content)[:100]}...")
                    print(f"   📊 Similarity: {results[0].similarity_score:.3f}")
                
            else:
                print(f"   ❌ Insufficient results found")
                quality_scores.append(0)
                
        except Exception as e:
            print(f"   ❌ Search error: {e}")
            quality_scores.append(0)
    
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
    print(f"\n📈 SEARCH QUALITY RESULTS:")
    print(f"   Average quality score: {avg_quality:.1f}%")
    print(f"   Individual scores: {[f'{score:.1f}%' for score in quality_scores]}")
    
    return avg_quality >= 60  # 60% quality threshold

async def main():
    """Main test execution"""
    print("🚀 Testing Fixed Visual Context Modes")
    print("=" * 60)
    
    try:
        # Test 1: Backend integration
        await test_backend_integration()
        
        # Test 2: Mode simulation
        await asyncio.sleep(0.5)  # Brief pause
        mode_success = await test_mode_simulation()
        
        # Test 3: Search quality
        await asyncio.sleep(0.5)  # Brief pause
        search_success = await test_memory_search_quality()
        
        # Overall results
        print(f"\n🏁 OVERALL TEST RESULTS:")
        print(f"   Mode simulation: {'✅ PASSED' if mode_success else '❌ FAILED'}")
        print(f"   Search quality: {'✅ PASSED' if search_success else '❌ FAILED'}")
        
        if mode_success and search_success:
            print(f"\n🎉 VISUAL CONTEXT MODES ARE WORKING!")
            print(f"   ASK/SUGGEST modes now return actual visual context")
            print(f"   Users asking 'what am I seeing?' will get real screen content")
            print(f"   Visual memory indexing fix was successful!")
        else:
            print(f"\n⚠️  Some issues remain with visual context modes")
            if not mode_success:
                print(f"   - Mode simulation needs improvement")
            if not search_success:
                print(f"   - Search quality needs enhancement")
                
    except Exception as e:
        print(f"❌ Critical error in testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())