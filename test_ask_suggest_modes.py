#!/usr/bin/env python3
"""
Test ASK and SUGGEST modes with fixed backend
Send actual WebSocket requests to verify contextual responses
"""

import asyncio
import json
import websockets
from datetime import datetime

async def test_ask_and_suggest_modes():
    """Test ASK and SUGGEST modes with visual queries"""
    print("🔧 Testing ASK and SUGGEST Modes with Fixed Backend...")
    
    try:
        # Connect to the fixed backend on port 8767
        uri = "ws://localhost:8767"
        
        async with websockets.connect(uri) as websocket:
            # Wait for connection established message
            connection_msg = await websocket.recv()
            connection_data = json.loads(connection_msg)
            print(f"✅ Connected: {connection_data.get('message', 'Unknown')}")
            
            # Test cases for both ASK and SUGGEST modes
            test_cases = [
                # ASK Mode Tests
                {
                    "mode": "Ask",
                    "query": "what am I seeing?",
                    "expected_keywords": ["cursor", "development", "environment", "code", "editor"],
                    "description": "Visual query - what am I seeing"
                },
                {
                    "mode": "Ask", 
                    "query": "what application am I using?",
                    "expected_keywords": ["cursor", "development", "application"],
                    "description": "Application query"
                },
                {
                    "mode": "Ask",
                    "query": "current screen content",
                    "expected_keywords": ["screen", "development", "cursor", "visual"],
                    "description": "Screen content query"
                },
                {
                    "mode": "Ask",
                    "query": "what's on my screen?",
                    "expected_keywords": ["cursor", "development", "screen", "code"],
                    "description": "Screen visibility query"
                },
                
                # SUGGEST Mode Tests
                {
                    "mode": "Suggest",
                    "query": "what should I do next?",
                    "expected_keywords": ["development", "cursor", "project"],
                    "description": "General suggestion with context"
                },
                {
                    "mode": "Suggest",
                    "query": "improve my workflow",
                    "expected_keywords": ["development", "workflow", "cursor"],
                    "description": "Workflow improvement suggestion"
                },
                {
                    "mode": "Suggest",
                    "query": "optimize my code editor",
                    "expected_keywords": ["cursor", "code", "editor"],
                    "description": "Editor optimization suggestion"
                }
            ]
            
            results = []
            
            for i, test in enumerate(test_cases):
                print(f"\n🔍 Test {i+1}: {test['description']}")
                print(f"   Mode: {test['mode']}")
                print(f"   Query: '{test['query']}'")
                
                # Send chat request
                request = {
                    "type": "chat_request",
                    "mode": test['mode'],
                    "message": test['query'],
                    "session_id": f"test_session_{i}",
                    "timestamp": datetime.now().isoformat()
                }
                
                await websocket.send(json.dumps(request))
                
                # Get response
                response_msg = await websocket.recv()
                response_data = json.loads(response_msg)
                
                if response_data.get("success"):
                    response_text = response_data.get("response", "")
                    processing_time = response_data.get("processing_time", 0)
                    
                    print(f"   ✅ Response ({processing_time}s): {response_text[:100]}...")
                    
                    # Check for contextual keywords
                    found_keywords = []
                    for keyword in test['expected_keywords']:
                        if keyword.lower() in response_text.lower():
                            found_keywords.append(keyword)
                    
                    # Analyze response quality
                    is_contextual = len(found_keywords) >= 2
                    is_generic = any(phrase in response_text.lower() for phrase in [
                        "enterprise", "validation", "general mode", "i understand your query"
                    ])
                    
                    if is_contextual and not is_generic:
                        print(f"   ✅ CONTEXTUAL RESPONSE - Found keywords: {found_keywords}")
                        result_status = "✅ Contextual"
                    elif is_contextual:
                        print(f"   ⚠️  MIXED RESPONSE - Contextual but generic: {found_keywords}")
                        result_status = "⚠️ Mixed"
                    else:
                        print(f"   ❌ GENERIC RESPONSE - Missing context keywords")
                        result_status = "❌ Generic"
                    
                    results.append({
                        "test": test['description'],
                        "mode": test['mode'],
                        "query": test['query'],
                        "status": result_status,
                        "keywords_found": found_keywords,
                        "response_length": len(response_text),
                        "processing_time": processing_time
                    })
                    
                else:
                    print(f"   ❌ Request failed: {response_data.get('error', 'Unknown error')}")
                    results.append({
                        "test": test['description'],
                        "mode": test['mode'],
                        "query": test['query'],
                        "status": "❌ Failed",
                        "error": response_data.get('error', 'Unknown')
                    })
                
                # Small delay between requests
                await asyncio.sleep(0.5)
            
            # Print summary
            print(f"\n📊 TEST RESULTS SUMMARY:")
            print("=" * 60)
            
            contextual_count = sum(1 for r in results if "✅" in r.get('status', ''))
            mixed_count = sum(1 for r in results if "⚠️" in r.get('status', ''))
            generic_count = sum(1 for r in results if "❌" in r.get('status', ''))
            
            print(f"Total Tests: {len(results)}")
            print(f"✅ Contextual Responses: {contextual_count}")
            print(f"⚠️  Mixed Responses: {mixed_count}")
            print(f"❌ Generic/Failed Responses: {generic_count}")
            print(f"Success Rate: {(contextual_count/len(results)*100):.1f}%")
            
            # Detailed results
            print(f"\nDetailed Results:")
            for result in results:
                print(f"  {result['status']} {result['mode']} Mode: {result['test']}")
                if 'keywords_found' in result:
                    print(f"    Keywords: {result['keywords_found']}")
            
            # Conclusion
            if contextual_count >= len(results) * 0.7:
                print(f"\n🎉 SUCCESS: Visual memory integration is working!")
                print(f"   ASK/SUGGEST modes are providing contextual responses.")
            elif contextual_count > 0:
                print(f"\n⚠️  PARTIAL SUCCESS: Some contextual responses detected.")
                print(f"   System is improved but may need further tuning.")
            else:
                print(f"\n❌ FAILURE: No contextual responses detected.")
                print(f"   Visual memory integration is not working properly.")
            
    except ConnectionRefusedError:
        print("❌ Could not connect to backend on port 8767.")
        print("   Make sure the fixed backend is running:")
        print("   python3 enterprise_backend_8767_with_fixed_visual_memory.py")
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    asyncio.run(test_ask_and_suggest_modes())