#!/usr/bin/env python3
"""
Test ASK Mode Integration
Test if ASK mode is actually using memory + brain router
"""
import asyncio
import json
import websockets
import sys
from datetime import datetime

async def test_ask_mode():
    """Test ASK mode functionality"""
    try:
        print("🧪 Testing ASK Mode Integration")
        print("=" * 50)
        
        # Connect to the backend
        uri = "ws://localhost:8767"
        
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to backend")
            
            # Register as LLM client
            register_msg = {
                "type": "register",
                "client_type": "llm"
            }
            
            await websocket.send(json.dumps(register_msg))
            response = await websocket.recv()
            print(f"📝 Registration response: {response}")
            
            # Test ASK mode with memory-related question
            test_questions = [
                "What development activities have I been doing recently?",
                "What applications am I using for coding?", 
                "Tell me about my productivity patterns",
                "What's my current workflow?"
            ]
            
            for i, question in enumerate(test_questions, 1):
                print(f"\n🔍 Test {i}: ASK Mode Query")
                print(f"Question: {question}")
                
                chat_msg = {
                    "type": "chat_request",
                    "mode": "Ask",
                    "message": question,
                    "timestamp": datetime.now().isoformat()
                }
                
                await websocket.send(json.dumps(chat_msg))
                response = await websocket.recv()
                
                try:
                    response_data = json.loads(response)
                    
                    print(f"Mode: {response_data.get('mode', 'unknown')}")
                    print(f"Response: {response_data.get('response', 'No response')[:200]}...")
                    print(f"Brain Router Used: {response_data.get('brain_router_used', False)}")
                    print(f"Confidence: {response_data.get('confidence', 'N/A')}")
                    print(f"Resources Used: {response_data.get('resources_used', 'N/A')}")
                    
                    # Check if response contains memory/context info
                    response_text = response_data.get('response', '').lower()
                    has_memory_info = any(keyword in response_text for keyword in [
                        'recent', 'memory', 'context', 'history', 'pattern', 'workflow', 'development', 'coding'
                    ])
                    
                    print(f"Contains Memory Info: {'✅' if has_memory_info else '❌'}")
                    
                    if response_data.get('brain_router_used'):
                        print("✅ Brain Router is being used!")
                    else:
                        print("❌ Brain Router NOT being used - falling back to basic LLM")
                    
                except json.JSONDecodeError:
                    print(f"Raw response: {response}")
                
                print("-" * 40)
        
        print("\n📊 ASK Mode Test Summary:")
        print("- If 'Brain Router Used: True' → ASK mode is working correctly")
        print("- If 'Brain Router Used: False' → ASK mode is falling back to basic LLM")
        print("- Memory integration requires Brain Router to be working")
        
    except Exception as e:
        print(f"❌ Error testing ASK mode: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ask_mode())