#!/usr/bin/env python3
"""
Test Enhanced Backend Comparison
Compare responses between old and new backends
"""

import asyncio
import json
import websockets
from datetime import datetime

async def test_backend_comparison():
    """Compare responses between original and enhanced backends"""
    print("🔍 Comparing Original vs Enhanced Backend Responses...")
    
    test_queries = [
        {
            "query": "what is nyc?",
            "mode": "Ask",
            "description": "General knowledge query (problematic for original)"
        },
        {
            "query": "what running in my background?",
            "mode": "Ask", 
            "description": "System query (generic responses in original)"
        },
        {
            "query": "what am I seeing?",
            "mode": "Ask",
            "description": "Visual query (should work well in both)"
        },
        {
            "query": "improve my workflow",
            "mode": "Suggest",
            "description": "Workflow suggestion query"
        }
    ]
    
    # Test both backends
    backends = [
        {"name": "Original", "port": 8767, "uri": "ws://localhost:8767"},
        {"name": "Enhanced", "port": 8768, "uri": "ws://localhost:8768"}
    ]
    
    results = {}
    
    for backend in backends:
        print(f"\n🔧 Testing {backend['name']} Backend (Port {backend['port']}):")
        print("=" * 60)
        
        results[backend['name']] = {}
        
        try:
            async with websockets.connect(backend['uri']) as websocket:
                # Wait for connection
                connection_msg = await websocket.recv()
                connection_data = json.loads(connection_msg)
                print(f"✅ Connected: {connection_data.get('message', 'Connected')}")
                
                for i, test in enumerate(test_queries):
                    print(f"\n📝 Test {i+1}: {test['description']}")
                    print(f"   Query: '{test['query']}' (Mode: {test['mode']})")
                    
                    # Send request
                    request = {
                        "type": "chat_request",
                        "mode": test['mode'],
                        "message": test['query'],
                        "session_id": f"comparison_test_{i}",
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
                        
                        # Store result for comparison
                        results[backend['name']][test['query']] = {
                            "response": response_text,
                            "processing_time": processing_time,
                            "success": True
                        }
                        
                    else:
                        error = response_data.get("error", "Unknown error")
                        print(f"   ❌ Failed: {error}")
                        results[backend['name']][test['query']] = {
                            "error": error,
                            "success": False
                        }
                    
                    await asyncio.sleep(0.3)
                
        except ConnectionRefusedError:
            print(f"❌ Could not connect to {backend['name']} backend on port {backend['port']}")
            results[backend['name']] = {"connection_error": True}
        except Exception as e:
            print(f"❌ Error testing {backend['name']} backend: {e}")
            results[backend['name']] = {"error": str(e)}
    
    # Compare results
    print(f"\n📊 COMPARISON RESULTS:")
    print("=" * 70)
    
    for query in [test['query'] for test in test_queries]:
        print(f"\n🔍 Query: '{query}'")
        
        for backend_name in ["Original", "Enhanced"]:
            if backend_name in results and query in results[backend_name]:
                result = results[backend_name][query]
                if result.get("success"):
                    response = result["response"]
                    print(f"   {backend_name:>10}: {response[:80]}...")
                else:
                    print(f"   {backend_name:>10}: ❌ {result.get('error', 'Failed')}")
            else:
                print(f"   {backend_name:>10}: ❌ No result")
    
    # Summary
    print(f"\n🎯 IMPROVEMENT SUMMARY:")
    print("=" * 50)
    
    if "Enhanced" in results and "Original" in results:
        # Check specific improvements
        nyc_query = "what is nyc?"
        if nyc_query in results["Enhanced"] and nyc_query in results["Original"]:
            enhanced_resp = results["Enhanced"][nyc_query].get("response", "")
            original_resp = results["Original"][nyc_query].get("response", "")
            
            if "new york" in enhanced_resp.lower() and "new york" not in original_resp.lower():
                print("✅ NYC Query: Enhanced backend provides actual information vs generic response")
            
        background_query = "what running in my background?"
        if background_query in results["Enhanced"] and background_query in results["Original"]:
            enhanced_resp = results["Enhanced"][background_query].get("response", "")
            original_resp = results["Original"][background_query].get("response", "")
            
            if any(term in enhanced_resp.lower() for term in ["process", "system", "backend"]):
                print("✅ Background Query: Enhanced backend provides system context")
        
        visual_query = "what am I seeing?"
        if visual_query in results["Enhanced"] and visual_query in results["Original"]:
            enhanced_resp = results["Enhanced"][visual_query].get("response", "")
            original_resp = results["Original"][visual_query].get("response", "")
            
            if "cursor" in enhanced_resp.lower() and "cursor" in original_resp.lower():
                print("✅ Visual Query: Both backends maintain visual context quality")
    
    print(f"\n💡 RECOMMENDATION:")
    print("Use the Enhanced Backend (port 8768) for better general knowledge and system query handling!")

if __name__ == "__main__":
    asyncio.run(test_backend_comparison())