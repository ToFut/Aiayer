#!/usr/bin/env python3
"""
Test script for fixed message flow in enhanced_enterprise_backend_with_context.py
This script tests all chat modes to verify that LLM responses are working correctly.
"""
import asyncio
import websockets
import json
import time
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def test_message_flow():
    """Test the message flow in the backend with all chat modes"""
    uri = "ws://localhost:8767"
    
    modes_to_test = [
        {"type": "chat_request", "mode": "General", "message": "Tell me about the system"},
        {"type": "chat_request", "mode": "Ask", "message": "What files are currently on my desktop?"},
        {"type": "chat_request", "mode": "Suggest", "message": "How can I improve my productivity?"},
        {"type": "chat_request", "mode": "Agent", "message": "Open Safari browser"}
    ]
    
    results = {}
    
    try:
        print(f"Connecting to {uri}...")
        async with websockets.connect(uri, max_size=10 * 1024 * 1024, ping_interval=None) as websocket:
            print("✅ Connected to backend")
            
            # Get connection established message
            conn_msg = await websocket.recv()
            print(f"📥 Connection: {json.loads(conn_msg).get('type')}")
            
            # Register client
            register_msg = {"type": "register", "client_type": "test_client"}
            await websocket.send(json.dumps(register_msg))
            
            try:
                reg_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📥 Registration: {json.loads(reg_response).get('type')}")
            except asyncio.TimeoutError:
                print("⚠️ No registration response received, continuing anyway")
            
            # Test each mode
            for mode_test in modes_to_test:
                mode_name = mode_test["mode"]
                print(f"\n🧪 Testing {mode_name} mode...")
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
                    
                    # Check for real LLM response
                    if "response" in response_data:
                        ai_response = response_data.get('response', '')
                        print(f"🧠 Response: {ai_response[:150]}{'...' if len(ai_response) > 150 else ''}")
                        
                        # Check if it's real AI (not fallback)
                        is_real_llm = not any(fallback in ai_response for fallback in [
                            "🎯 Agent Mode:",
                            "💭 Ask Mode:", 
                            "💡 Suggest Mode:",
                            "🤖 General Mode:"
                        ])
                        
                        if is_real_llm:
                            print("✅ REAL LLM RESPONSE!")
                            results[mode_name] = "✅ Real LLM"
                        else:
                            print("⚠️ Using fallback response")
                            results[mode_name] = "⚠️ Fallback"
                    elif "error" in response_data:
                        error_message = response_data.get("error", "Unknown error")
                        print(f"❌ Error: {error_message}")
                        results[mode_name] = f"❌ Error: {error_message[:50]}"
                    else:
                        print("❓ No response or error field found")
                        print(f"Keys in response: {', '.join(response_data.keys())}")
                        results[mode_name] = "❓ Unknown response format"
                    
                except asyncio.TimeoutError:
                    print("⏰ Timeout waiting for response")
                    results[mode_name] = "⏰ Timeout"
                except Exception as e:
                    print(f"❌ Error during test: {e}")
                    results[mode_name] = f"❌ Error: {str(e)[:50]}"
                
                # Brief pause between tests
                await asyncio.sleep(2)
            
            # Summary
            print("\n" + "="*60)
            print("🎯 TEST RESULTS:")
            print("="*60)
            
            for mode, result in results.items():
                print(f"{mode:8} mode: {result}")
            
            all_real_llm = all("✅ Real LLM" in result for result in results.values())
            
            if all_real_llm:
                print(f"\n🎉 SUCCESS! All {len(results)} modes using REAL LLM responses!")
                print("🚀 Message flow fixed successfully!")
            else:
                print(f"\n⚠️ Some modes still using fallbacks or have errors.")
                print("Check the backend logs and model.py for issues.")
                
        print(f"\n📊 Total modes tested: {len(results)}")
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("Make sure the backend server is running on port 8767")

if __name__ == "__main__":
    asyncio.run(test_message_flow())