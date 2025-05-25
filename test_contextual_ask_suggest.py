#!/usr/bin/env python3
"""
Test Contextual Ask/Suggest Modes
Test if Ask and Suggest modes now provide meaningful contextual responses
"""

import asyncio
import websockets
import json
import time
from datetime import datetime

async def test_contextual_modes():
    """Test Ask and Suggest modes with contextual responses"""
    
    print("🧪 Testing Contextual Ask/Suggest Modes")
    print("=" * 60)
    
    test_cases = [
        {
            "mode": "ask",
            "message": "What development tools am I using?",
            "expected_context": ["Cursor", "development", "coding"]
        },
        {
            "mode": "suggest", 
            "message": "How can I improve my development workflow?",
            "expected_context": ["productivity", "workflow", "development"]
        },
        {
            "mode": "ask",
            "message": "How productive have I been today?",
            "expected_context": ["productive", "activity", "score"]
        },
        {
            "mode": "suggest",
            "message": "What should I focus on next?",
            "expected_context": ["workflow", "next", "recommend"]
        }
    ]
    
    try:
        # Connect to the contextual backend
        uri = "ws://localhost:8767"
        print(f"🔗 Connecting to {uri}...")
        
        async with websockets.connect(uri, ping_timeout=10) as websocket:
            # Wait for connection message
            connection_msg = await websocket.recv()
            connection_data = json.loads(connection_msg)
            print(f"✅ Connected: {connection_data.get('message', 'No message')}")
            
            for i, test in enumerate(test_cases, 1):
                print(f"\n{i}. Testing {test['mode'].upper()} Mode")
                print(f"   Query: {test['message']}")
                print(f"   Expected Context: {test['expected_context']}")
                print("   " + "-" * 50)
                
                # Send chat request
                request = {
                    "type": "chat_request",
                    "mode": test['mode'],
                    "message": test['message'],
                    "client_id": f"test_client_{i}",
                    "timestamp": datetime.now().isoformat()
                }
                
                await websocket.send(json.dumps(request))
                print("   📤 Request sent")
                
                # Collect all response messages
                full_response = ""
                contextual_info = {}
                
                start_time = time.time()
                timeout = 30  # 30 second timeout
                
                while time.time() - start_time < timeout:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        data = json.loads(response)
                        
                        if data.get('type') == 'final_response':
                            full_response = data.get('response', '')
                            contextual_info = {
                                'contextual': data.get('contextual', False),
                                'confidence': data.get('confidence', 0),
                                'ai_powered': data.get('ai_powered', False)
                            }
                            break
                        elif data.get('type') == 'progress_update':
                            print(f"   📊 {data.get('stage', 'Processing...')}")
                        
                    except asyncio.TimeoutError:
                        print("   ⏰ Waiting for response...")
                        continue
                    except Exception as e:
                        print(f"   ❌ Error receiving response: {e}")
                        break
                
                # Analyze response
                if full_response:
                    print(f"   📝 Response: {full_response[:200]}...")
                    print(f"   🧠 Contextual: {contextual_info.get('contextual', False)}")
                    print(f"   📊 Confidence: {contextual_info.get('confidence', 0):.3f}")
                    print(f"   🤖 AI Powered: {contextual_info.get('ai_powered', False)}")
                    
                    # Check if response contains expected context
                    response_lower = full_response.lower()
                    context_found = []
                    for expected in test['expected_context']:
                        if expected.lower() in response_lower:
                            context_found.append(expected)
                    
                    if len(context_found) > 0:
                        print(f"   ✅ CONTEXTUAL: Found {context_found}")
                    else:
                        print(f"   ❌ NO CONTEXT: Expected {test['expected_context']}")
                    
                    # Check for high-confidence contextual indicator
                    if "[Using high-confidence context]" in full_response:
                        print("   🎯 HIGH-CONFIDENCE CONTEXT USED!")
                    elif "[Using available context]" in full_response:
                        print("   📈 AVAILABLE CONTEXT USED")
                    else:
                        print("   ⚠️  No context indicator in response")
                        
                else:
                    print("   ❌ No response received")
                
                # Wait between requests
                time.sleep(2)
    
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("Make sure the enhanced enterprise backend is running on port 8767")

async def main():
    """Main test function"""
    await test_contextual_modes()
    
    print(f"\n💡 Expected Results:")
    print("✅ Responses should mention 'Cursor' for development tool questions")
    print("✅ Responses should reference productivity scores and activity data")
    print("✅ Contextual indicators should show '[Using context]'")
    print("✅ Confidence scores should be > 0.3 for meaningful context")

if __name__ == "__main__":
    asyncio.run(main())