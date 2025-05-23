#!/usr/bin/env python3
"""
Comprehensive test for all modes with real LLM responses
"""
import asyncio
import websockets
import json
import time

async def test_all_modes():
    uri = "ws://localhost:8765"
    
    modes_to_test = [
        {"type": "agent_request", "mode": "agent", "message": "Help me organize my files efficiently"},
        {"type": "ask_request", "mode": "ask", "message": "What is the current system status and memory usage?"},
        {"type": "suggest_request", "mode": "suggest", "message": "How can I improve my workflow productivity?"},
        {"type": "general_request", "mode": "general", "message": "What are the benefits of AI automation?"}
    ]
    
    results = {}
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to enhanced enterprise backend")
            
            # Get connection established message
            conn_msg = await websocket.recv()
            print(f"📥 Connection: {json.loads(conn_msg).get('type')}")
            
            # Register
            register_msg = {"type": "register", "client_type": "test_client"}
            await websocket.send(json.dumps(register_msg))
            
            reg_response = await websocket.recv()
            print(f"📥 Registration: {json.loads(reg_response).get('type')}")
            
            # Test each mode
            for mode_test in modes_to_test:
                print(f"\n🧪 Testing {mode_test['mode'].upper()} mode...")
                print(f"📤 Query: {mode_test['message']}")
                
                start_time = time.time()
                
                # Send request
                await websocket.send(json.dumps(mode_test))
                
                # Wait for response with longer timeout for LLM processing
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=45.0)
                    response_time = time.time() - start_time
                    
                    response_data = json.loads(response)
                    
                    print(f"📥 Response received in {response_time:.1f}s")
                    print(f"Type: {response_data.get('type')}")
                    print(f"Mode: {response_data.get('mode')}")
                    print(f"Success: {response_data.get('success')}")
                    
                    # Check for real LLM response
                    ai_response = response_data.get('response', '')
                    if ai_response:
                        print(f"🧠 AI Response: {ai_response[:150]}{'...' if len(ai_response) > 150 else ''}")
                        
                        # Check if it's real AI (not fallback)
                        is_real_llm = not any(fallback in ai_response for fallback in [
                            "🎯 I'll analyze and execute",
                            "💭 The enterprise system is",
                            "💡 For optimization, I recommend",
                            "🤖 Hello! I'm your enhanced"
                        ])
                        
                        if is_real_llm:
                            print("✅ REAL LLM RESPONSE!")
                            results[mode_test['mode']] = "✅ Real LLM"
                        else:
                            print("⚠️ Using fallback response")
                            results[mode_test['mode']] = "⚠️ Fallback"
                    else:
                        print("❌ No response field")
                        results[mode_test['mode']] = "❌ No response"
                    
                    print(f"Response size: {len(response)} characters")
                    
                except asyncio.TimeoutError:
                    print("⏰ Timeout waiting for response")
                    results[mode_test['mode']] = "⏰ Timeout"
                
                # Brief pause between tests
                await asyncio.sleep(2)
            
            # Summary
            print("\n" + "="*60)
            print("🎯 COMPREHENSIVE TEST RESULTS:")
            print("="*60)
            
            for mode, result in results.items():
                print(f"{mode.upper():8} mode: {result}")
            
            all_real_llm = all("✅ Real LLM" in result for result in results.values())
            
            if all_real_llm:
                print(f"\n🎉 SUCCESS! All {len(results)} modes using REAL LLM responses!")
                print("🚀 Enterprise system fully operational with AI intelligence!")
            else:
                print(f"\n⚠️ Some modes still using fallbacks. Check Ollama service.")
                
        print(f"\n📊 Total modes tested: {len(results)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_all_modes())