#!/usr/bin/env python3
"""
Test Real ASK Mode Integration

This script tests if ASK mode now provides contextual answers
based on real memory data instead of mock responses.
"""

import asyncio
import websockets
import json
import time

async def test_real_ask_mode():
    """Test ASK mode with real memory integration"""
    
    print("🧪 Testing Real ASK Mode Integration")
    print("=" * 50)
    
    try:
        uri = "ws://localhost:8767"
        async with websockets.connect(uri) as websocket:
            
            # Register as client
            register_msg = {
                "type": "register",
                "client_type": "test_client",
                "client_id": "test_real_ask_mode"
            }
            
            await websocket.send(json.dumps(register_msg))
            response = await websocket.recv()
            registration = json.loads(response)
            print(f"✅ Connected: {registration.get('connection_id')}")
            
            # Test queries that should use real memory
            test_queries = [
                {
                    "query": "What development activities have I been doing recently?",
                    "expected_keywords": ["development", "coding", "Cursor", "software_engineering"]
                },
                {
                    "query": "What applications am I using for coding?", 
                    "expected_keywords": ["Cursor", "application", "development", "coding"]
                },
                {
                    "query": "Tell me about my productivity patterns",
                    "expected_keywords": ["productivity", "patterns", "highly_productive", "development"]
                },
                {
                    "query": "What's my current workflow?",
                    "expected_keywords": ["workflow", "active_coding", "development"]
                }
            ]
            
            results = []
            
            for i, test in enumerate(test_queries, 1):
                print(f"\n🔍 Test {i}: {test['query']}")
                
                # Send ASK mode message
                message = {
                    "type": "chat",
                    "message": test["query"],
                    "mode": "Ask"
                }
                
                await websocket.send(json.dumps(message))
                
                # Wait for response
                start_time = time.time()
                response = await websocket.recv()
                response_time = time.time() - start_time
                
                response_data = json.loads(response)
                response_text = response_data.get("response", "")
                metadata = response_data.get("metadata", {})
                
                print(f"Response ({response_time:.2f}s): {response_text}")
                print(f"Real Memory Used: {metadata.get('real_memory_used', False)}")
                print(f"Memory Items Analyzed: {metadata.get('memory_items_analyzed', 0)}")
                print(f"Confidence: {metadata.get('confidence', 0)}")
                
                # Check if response contains real memory insights
                real_memory_indicators = [
                    "Cursor", "development", "software_engineering", "coding",
                    "productivity", "activity", "workflow", "recent", "analysis"
                ]
                
                contains_real_data = any(indicator.lower() in response_text.lower() 
                                       for indicator in real_memory_indicators)
                
                is_mock_response = any(mock_phrase in response_text.lower() for mock_phrase in [
                    "processing your query about",
                    "based on my knowledge",
                    "here's what i know",
                    "medium confidence based on available context"
                ])
                
                result = {
                    "query": test["query"],
                    "response": response_text,
                    "real_memory_used": metadata.get("real_memory_used", False),
                    "memory_items": metadata.get("memory_items_analyzed", 0),
                    "confidence": metadata.get("confidence", 0),
                    "contains_real_data": contains_real_data,
                    "is_mock_response": is_mock_response,
                    "response_time": response_time
                }
                
                results.append(result)
                
                if contains_real_data and not is_mock_response:
                    print("✅ SUCCESS: Response contains real memory data!")
                elif metadata.get("real_memory_used"):
                    print("⚠️  PARTIAL: Real memory used but response needs improvement")
                else:
                    print("❌ FAILED: Still using mock responses")
                
                print("-" * 40)
            
            # Summary
            print(f"\n📊 Test Summary:")
            successful_tests = sum(1 for r in results if r["contains_real_data"] and not r["is_mock_response"])
            partial_tests = sum(1 for r in results if r["real_memory_used"] and not r["contains_real_data"])
            failed_tests = len(results) - successful_tests - partial_tests
            
            print(f"✅ Successful: {successful_tests}/{len(results)}")
            print(f"⚠️  Partial: {partial_tests}/{len(results)}")
            print(f"❌ Failed: {failed_tests}/{len(results)}")
            
            avg_memory_items = sum(r["memory_items"] for r in results) / len(results)
            avg_confidence = sum(r["confidence"] for r in results) / len(results)
            
            print(f"\n📈 Performance:")
            print(f"Average Memory Items: {avg_memory_items:.1f}")
            print(f"Average Confidence: {avg_confidence:.2f}")
            print(f"Real Memory Usage: {sum(1 for r in results if r['real_memory_used'])}/{len(results)}")
            
            if successful_tests == len(results):
                print("\n🎉 ALL TESTS PASSED! ASK mode is now using real memory data!")
            elif successful_tests + partial_tests == len(results):
                print("\n🔧 GOOD PROGRESS! ASK mode is using real memory but responses need refinement.")
            else:
                print("\n⚠️ MIXED RESULTS. Some tests still using mock data.")
                
            return results
                
    except Exception as e:
        print(f"❌ Error testing: {e}")
        return []

async def main():
    """Main execution"""
    results = await test_real_ask_mode()
    
    print("\n" + "=" * 50)
    print("🎯 Next Steps:")
    if results and all(r["real_memory_used"] for r in results):
        print("✅ ASK mode successfully integrated with real memory!")
        print("✅ You should now get contextual answers based on your actual activity!")
        print("\n🔧 Try asking these questions in your chat interface:")
        print("  • 'What have I been working on lately?'")
        print("  • 'What applications am I using?'")
        print("  • 'How productive have I been?'")
        print("  • 'What's my current workflow stage?'")
    else:
        print("⚠️ ASK mode integration needs more work.")
        print("Check the backend logs for any errors.")

if __name__ == "__main__":
    asyncio.run(main())