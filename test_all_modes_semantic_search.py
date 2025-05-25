#!/usr/bin/env python3
"""
Test All Modes Semantic Search
Verify that ALL modes (Ask, Agent, Suggest, General) use semantic search agent
"""

import asyncio
import websockets
import json
import time
from datetime import datetime

async def test_all_modes_semantic_search():
    """Test that all modes use semantic search for contextual responses"""
    
    print("🧪 Testing Semantic Search Integration Across ALL Modes")
    print("=" * 70)
    
    # Test cases for each mode
    test_cases = [
        {
            "mode": "ask",
            "message": "What tools do I use for coding?",
            "expected_semantic": ["development", "cursor", "tools"],
            "description": "Ask mode should retrieve development context"
        },
        {
            "mode": "agent", 
            "message": "Help me open a new application",
            "expected_semantic": ["automation", "agent", "application"],
            "description": "Agent mode should use context for automation planning"
        },
        {
            "mode": "suggest",
            "message": "How can I be more productive?",
            "expected_semantic": ["productivity", "workflow", "improve"],
            "description": "Suggest mode should analyze patterns for recommendations"
        },
        {
            "mode": "general",
            "message": "Hello, how are you?",
            "expected_semantic": ["conversation", "interaction", "general"],
            "description": "General mode should maintain conversation context"
        }
    ]
    
    try:
        # Connect to the contextual backend
        uri = "ws://localhost:8767"
        print(f"🔗 Connecting to {uri}...")
        
        async with websockets.connect(uri, ping_timeout=15) as websocket:
            # Wait for connection message
            connection_msg = await websocket.recv()
            connection_data = json.loads(connection_msg)
            print(f"✅ Connected: {connection_data.get('message', 'No message')}")
            
            semantic_results = {}
            
            for i, test in enumerate(test_cases, 1):
                print(f"\n{i}. Testing {test['mode'].upper()} Mode Semantic Search")
                print(f"   Description: {test['description']}")
                print(f"   Query: {test['message']}")
                print("   " + "-" * 60)
                
                # Send chat request
                request = {
                    "type": "chat_request",
                    "mode": test['mode'],
                    "message": test['message'],
                    "client_id": f"semantic_test_{i}",
                    "timestamp": datetime.now().isoformat()
                }
                
                await websocket.send(json.dumps(request))
                print("   📤 Request sent")
                
                # Collect response and metadata
                full_response = ""
                context_metrics = {}
                ai_powered = False
                contextual = False
                
                start_time = time.time()
                timeout = 25  # Give agent mode more time for automation
                
                while time.time() - start_time < timeout:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                        data = json.loads(response)
                        
                        if data.get('type') == 'final_response':
                            full_response = data.get('response', '')
                            contextual = data.get('contextual', False)
                            ai_powered = data.get('ai_powered', False)
                            confidence = data.get('confidence', 0)
                            
                            context_metrics = {
                                'contextual': contextual,
                                'confidence': confidence,
                                'ai_powered': ai_powered
                            }
                            break
                            
                        elif data.get('type') == 'chat_response_metadata':
                            context_metrics.update(data.get('context_metrics', {}))
                            
                        elif data.get('type') == 'progress_update':
                            print(f"   📊 {data.get('stage', 'Processing...')}")
                        
                    except asyncio.TimeoutError:
                        print("   ⏰ Waiting for response...")
                        continue
                    except Exception as e:
                        print(f"   ❌ Error receiving response: {e}")
                        break
                
                # Analyze semantic search usage
                print(f"   📝 Response Length: {len(full_response)} chars")
                print(f"   🧠 Contextual: {context_metrics.get('contextual', False)}")
                print(f"   📊 Confidence: {context_metrics.get('confidence', 0):.3f}")
                print(f"   🤖 AI Powered: {context_metrics.get('ai_powered', False)}")
                print(f"   🔍 Memories Used: {context_metrics.get('memories_used', 0)}")
                
                # Check for semantic search indicators
                semantic_indicators = []
                
                # Check for context indicators in response
                if "[Using high-confidence context]" in full_response:
                    semantic_indicators.append("HIGH_CONFIDENCE_CONTEXT")
                elif "[Using available context]" in full_response:
                    semantic_indicators.append("AVAILABLE_CONTEXT")
                
                # Check for contextual language
                response_lower = full_response.lower()
                contextual_phrases = [
                    "based on our conversation",
                    "i recall", "i remember", "you mentioned",
                    "relevant information", "context",
                    "interaction patterns", "conversation history"
                ]
                
                for phrase in contextual_phrases:
                    if phrase in response_lower:
                        semantic_indicators.append(f"CONTEXTUAL_PHRASE: {phrase}")
                
                # Store results
                semantic_results[test['mode']] = {
                    'has_semantic_search': context_metrics.get('contextual', False),
                    'confidence_score': context_metrics.get('confidence', 0),
                    'memories_used': context_metrics.get('memories_used', 0),
                    'semantic_indicators': semantic_indicators,
                    'ai_powered': context_metrics.get('ai_powered', False),
                    'response_sample': full_response[:200] + "..." if len(full_response) > 200 else full_response
                }
                
                # Evaluate semantic search usage
                if context_metrics.get('contextual', False) and context_metrics.get('confidence', 0) > 0.3:
                    print("   ✅ SEMANTIC SEARCH ACTIVE - High quality contextual response")
                elif context_metrics.get('contextual', False):
                    print("   ⚠️  SEMANTIC SEARCH WEAK - Low confidence context")
                else:
                    print("   ❌ NO SEMANTIC SEARCH - Missing contextual integration")
                
                if semantic_indicators:
                    print(f"   🎯 Semantic Indicators: {len(semantic_indicators)} found")
                    for indicator in semantic_indicators[:2]:  # Show first 2
                        print(f"      - {indicator}")
                
                # Wait between requests
                time.sleep(3)
    
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("Make sure the enhanced enterprise backend is running on port 8767")
        return None
    
    return semantic_results

async def analyze_semantic_integration_results(results):
    """Analyze the semantic search integration across all modes"""
    
    if not results:
        print("\n❌ No results to analyze")
        return
    
    print(f"\n📊 SEMANTIC SEARCH INTEGRATION ANALYSIS")
    print("=" * 70)
    
    total_modes = len(results)
    semantic_active_modes = 0
    high_confidence_modes = 0
    ai_powered_modes = 0
    
    for mode, data in results.items():
        print(f"\n🔍 {mode.upper()} Mode Analysis:")
        print(f"   Semantic Search: {'✅ Active' if data['has_semantic_search'] else '❌ Inactive'}")
        print(f"   Confidence Score: {data['confidence_score']:.3f}")
        print(f"   Memories Used: {data['memories_used']}")
        print(f"   AI Powered: {'✅ Yes' if data['ai_powered'] else '❌ No'}")
        print(f"   Indicators: {len(data['semantic_indicators'])}")
        
        if data['has_semantic_search']:
            semantic_active_modes += 1
        if data['confidence_score'] > 0.6:
            high_confidence_modes += 1
        if data['ai_powered']:
            ai_powered_modes += 1
    
    # Summary
    print(f"\n🎯 SUMMARY:")
    print(f"   Modes with Semantic Search: {semantic_active_modes}/{total_modes} ({semantic_active_modes/total_modes*100:.1f}%)")
    print(f"   High Confidence Modes: {high_confidence_modes}/{total_modes} ({high_confidence_modes/total_modes*100:.1f}%)")
    print(f"   AI-Powered Modes: {ai_powered_modes}/{total_modes} ({ai_powered_modes/total_modes*100:.1f}%)")
    
    if semantic_active_modes == total_modes:
        print(f"   ✅ ALL MODES HAVE SEMANTIC SEARCH INTEGRATION!")
    elif semantic_active_modes > total_modes * 0.75:
        print(f"   ⚠️  MOST modes have semantic search ({semantic_active_modes}/{total_modes})")
    else:
        print(f"   ❌ INSUFFICIENT semantic search integration ({semantic_active_modes}/{total_modes})")

async def main():
    """Main test function"""
    print("Testing semantic search agent attachment to all modes...")
    
    results = await test_all_modes_semantic_search()
    await analyze_semantic_integration_results(results)
    
    print(f"\n💡 Expected Results:")
    print("✅ All 4 modes should show 'Contextual: True'")
    print("✅ All modes should have confidence scores > 0.3")  
    print("✅ All modes should use memories from semantic search")
    print("✅ Responses should include contextual indicators")

if __name__ == "__main__":
    asyncio.run(main())