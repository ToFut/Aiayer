#!/usr/bin/env python3
"""
Test "What am I seeing?" Context Retrieval
Check what contextual information ASK and SUGGEST modes retrieve from memory 
when user asks about what they're currently seeing on screen
"""

import asyncio
import websockets
import json
import time
import sys
import os
from datetime import datetime

# Add project paths for direct memory testing
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory.semantic_search_agent import get_context_for_query

async def test_direct_memory_context():
    """Test what memory system returns for 'what am I seeing' queries"""
    
    print("🔍 TESTING DIRECT MEMORY CONTEXT RETRIEVAL")
    print("=" * 60)
    
    # Test queries about current screen/visual content
    visual_queries = [
        "What am I seeing on my screen?",
        "What's currently displayed?", 
        "What application am I using right now?",
        "What content is on my screen?",
        "What am I looking at?",
        "Describe what I'm viewing"
    ]
    
    for i, query in enumerate(visual_queries, 1):
        print(f"\n{i}. Query: {query}")
        print("   " + "-" * 50)
        
        try:
            # Get context directly from memory system
            context = await get_context_for_query(query, max_context_length=1500)
            
            print(f"   📊 Confidence Score: {context.get('confidence_score', 0):.3f}")
            print(f"   🧠 Relevant Memories: {len(context.get('relevant_memories', []))}")
            
            # Show actual memory content
            memories = context.get('relevant_memories', [])
            if memories:
                print(f"   📝 Top Memory Entries:")
                for j, memory in enumerate(memories[:3], 1):
                    content = memory.get('content', 'No content')
                    score = memory.get('similarity_score', 0)
                    source = memory.get('source', 'unknown')
                    print(f"      {j}. Score: {score:.3f} | Source: {source}")
                    print(f"         Content: {content[:150]}...")
                    
                    # Check for visual/screen content
                    if any(term in content.lower() for term in ['screen', 'cursor', 'application', 'visual', 'display', 'ui']):
                        print(f"         ✅ Contains visual context!")
                    else:
                        print(f"         ⚠️  No visual context detected")
            else:
                print("   ❌ No relevant memories found!")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

async def test_ask_suggest_visual_context():
    """Test ASK and SUGGEST modes with visual context queries via WebSocket"""
    
    print(f"\n🔗 TESTING ASK/SUGGEST MODES WITH VISUAL QUERIES")
    print("=" * 60)
    
    visual_test_cases = [
        {
            "mode": "ask",
            "query": "What am I seeing on my screen right now?",
            "expected_content": ["cursor", "screen", "application", "visual", "content"]
        },
        {
            "mode": "ask", 
            "query": "What application am I currently using?",
            "expected_content": ["cursor", "application", "development", "using"]
        },
        {
            "mode": "suggest",
            "query": "Based on what I'm seeing, what should I do next?",
            "expected_content": ["screen", "next", "workflow", "suggest"]
        }
    ]
    
    try:
        uri = "ws://localhost:8767"
        async with websockets.connect(uri, ping_timeout=20) as websocket:
            # Wait for connection
            connection_msg = await websocket.recv()
            print(f"✅ Connected to backend for visual context testing")
            
            for i, test_case in enumerate(visual_test_cases, 1):
                print(f"\n{i}. {test_case['mode'].upper()} Mode: {test_case['query']}")
                print("   " + "-" * 60)
                
                # Send request
                request = {
                    "type": "chat_request",
                    "mode": test_case['mode'],
                    "message": test_case['query'],
                    "client_id": f"visual_test_{i}",
                    "timestamp": datetime.now().isoformat()
                }
                
                await websocket.send(json.dumps(request))
                print("   📤 Request sent")
                
                # Collect response and context metadata
                full_response = ""
                context_metrics = {}
                
                start_time = time.time()
                timeout = 20
                
                while time.time() - start_time < timeout:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                        data = json.loads(response)
                        
                        if data.get('type') == 'final_response':
                            full_response = data.get('response', '')
                            context_metrics = {
                                'contextual': data.get('contextual', False),
                                'confidence': data.get('confidence', 0)
                            }
                            break
                            
                        elif data.get('type') == 'chat_response_metadata':
                            context_metrics.update(data.get('context_metrics', {}))
                            
                        elif data.get('type') == 'progress_update':
                            print(f"   📊 {data.get('stage', 'Processing...')}")
                        
                    except asyncio.TimeoutError:
                        print("   ⏰ Waiting...")
                        continue
                    except Exception as e:
                        print(f"   ❌ Error: {e}")
                        break
                
                # Analyze what visual context was retrieved
                print(f"   📝 Response Length: {len(full_response)} characters")
                print(f"   🧠 Contextual: {context_metrics.get('contextual', False)}")
                print(f"   📊 Confidence: {context_metrics.get('confidence', 0):.3f}")
                print(f"   🔍 Memories Used: {context_metrics.get('memories_used', 0)}")
                
                # Check for visual content in response
                response_lower = full_response.lower()
                visual_terms_found = []
                for term in ['cursor', 'screen', 'application', 'development', 'code', 'editor', 'ui', 'interface', 'visual', 'display']:
                    if term in response_lower:
                        visual_terms_found.append(term)
                
                print(f"   🎯 Visual Terms Found: {visual_terms_found}")
                
                # Check for specific screen content references
                screen_content_indicators = []
                screen_patterns = [
                    'currently using', 'on your screen', 'what you\'re seeing',
                    'displayed', 'viewing', 'looking at', 'screen shows',
                    'application', 'cursor', 'development'
                ]
                
                for pattern in screen_patterns:
                    if pattern in response_lower:
                        screen_content_indicators.append(pattern)
                
                print(f"   📺 Screen Content Indicators: {screen_content_indicators}")
                
                # Show response preview
                print(f"   📄 Response Preview:")
                print(f"      {full_response[:200]}...")
                
                # Evaluate visual context quality
                if len(visual_terms_found) >= 2 and len(screen_content_indicators) >= 1:
                    print("   ✅ STRONG visual context retrieved")
                elif len(visual_terms_found) >= 1 or len(screen_content_indicators) >= 1:
                    print("   ⚠️  WEAK visual context retrieved")
                else:
                    print("   ❌ NO visual context retrieved")
                
                time.sleep(2)
    
    except Exception as e:
        print(f"❌ Connection error: {e}")

async def check_current_memory_visual_content():
    """Check what visual content is currently in memory"""
    
    print(f"\n📋 CHECKING CURRENT MEMORY FOR VISUAL CONTENT")
    print("=" * 60)
    
    try:
        # Check conscious memory
        conscious_file = "memory/conscious.json"
        if os.path.exists(conscious_file):
            with open(conscious_file, 'r') as f:
                conscious_data = json.load(f)
            
            insights = conscious_data.get('insights', [])
            print(f"📝 Conscious Memory: {len(insights)} insights")
            
            visual_insights = 0
            for insight in insights:
                # Check for visual/screen content
                if insight.get('memory_type') == 'comprehensive_visual_analysis':
                    visual_insights += 1
                    app = insight.get('application_context', {}).get('primary_application', 'unknown')
                    text_content = insight.get('content_analysis', {}).get('text_content', '')
                    activity = insight.get('user_behavior', {}).get('current_activity', 'unknown')
                    
                    print(f"   📱 Visual Insight {visual_insights}:")
                    print(f"      App: {app}")
                    print(f"      Activity: {activity}")
                    print(f"      Text Content: {len(text_content)} characters")
                    if text_content:
                        print(f"      Sample: {text_content[:100]}...")
            
            print(f"   🎯 Total Visual Insights: {visual_insights}/{len(insights)}")
        else:
            print("   ❌ No conscious memory file found")
        
        # Check memory state
        memory_state_file = "memory/memory_state.json"
        if os.path.exists(memory_state_file):
            with open(memory_state_file, 'r') as f:
                memory_state = json.load(f)
            
            short_term = memory_state.get('short_term', [])
            visual_memories = 0
            for memory in short_term:
                if memory.get('memory_type') == 'comprehensive_visual_analysis':
                    visual_memories += 1
            
            print(f"🧠 Short-term Memory: {visual_memories}/{len(short_term)} visual memories")
        else:
            print("   ❌ No memory state file found")
            
    except Exception as e:
        print(f"   ❌ Error checking memory: {e}")

async def main():
    """Main function to test visual context retrieval"""
    
    print("🧪 TESTING VISUAL CONTEXT RETRIEVAL FOR ASK/SUGGEST MODES")
    print("=" * 80)
    print("Testing what users get when asking 'What am I seeing?'")
    
    # 1. Check current memory content
    await check_current_memory_visual_content()
    
    # 2. Test direct memory retrieval
    await test_direct_memory_context()
    
    # 3. Test ASK/SUGGEST modes via WebSocket
    await test_ask_suggest_visual_context()
    
    print(f"\n💡 SUMMARY:")
    print("=" * 60)
    print("This test shows exactly what contextual information")
    print("ASK and SUGGEST modes retrieve when users ask about")
    print("what they're currently seeing on their screen.")
    print("")
    print("Expected results:")
    print("✅ Should find visual analysis memories")
    print("✅ Should reference current application (Cursor)")
    print("✅ Should mention screen content and activity")
    print("✅ Should provide context about development work")

if __name__ == "__main__":
    asyncio.run(main())