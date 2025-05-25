#!/usr/bin/env python3
"""
Test Fixed Backend Visual Integration
Test the enterprise backend with fixed visual memory
"""

import asyncio
import json
import websockets
from datetime import datetime

async def test_fixed_backend():
    """Test the fixed backend with visual memory integration"""
    print("🔧 Testing Fixed Backend Visual Integration...")
    
    try:
        # Connect to the fixed backend
        uri = "ws://localhost:8767"
        
        async with websockets.connect(uri) as websocket:
            # Wait for connection established message
            connection_msg = await websocket.recv()
            connection_data = json.loads(connection_msg)
            print(f"✅ Connected: {connection_data.get('message', 'Unknown')}")
            
            # Test visual queries that should now work
            test_queries = [
                {
                    "query": "what am I seeing?",
                    "mode": "Ask",
                    "expected_context": "Cursor development environment"
                },
                {
                    "query": "what's on my screen?", 
                    "mode": "Ask",
                    "expected_context": "development environment"
                },
                {
                    "query": "what application am I using?",
                    "mode": "Ask", 
                    "expected_context": "Cursor"
                },
                {
                    "query": "current screen content",
                    "mode": "Suggest",
                    "expected_context": "development"
                }
            ]
            
            for i, test in enumerate(test_queries):
                print(f"\n🔍 Test {i+1}: {test['query']} (Mode: {test['mode']})")
                
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
                    print(f"✅ Response: {response_text[:150]}...")
                    
                    # Check if expected context is present
                    if test['expected_context'].lower() in response_text.lower():
                        print(f"✅ Contains expected context: '{test['expected_context']}'")
                    else:
                        print(f"⚠️  Missing expected context: '{test['expected_context']}'")
                        print(f"   Full response: {response_text}")
                else:
                    print(f"❌ Request failed: {response_data.get('error', 'Unknown error')}")
                
                # Small delay between requests
                await asyncio.sleep(0.5)
            
            print(f"\n✅ Fixed backend visual integration test completed!")
            
    except ConnectionRefusedError:
        print("❌ Could not connect to backend on port 8767. Is the server running?")
        print("To start the fixed backend, run:")
        print("python3 enterprise_backend_8767_with_fixed_visual_memory.py")
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    asyncio.run(test_fixed_backend())