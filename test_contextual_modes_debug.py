#!/usr/bin/env python3
"""
Quick test to verify ASK and Suggest modes are providing contextual feedback
"""

import asyncio
import websockets
import json
import time

async def test_contextual_modes():
    """Test ASK and Suggest modes for contextual responses"""
    
    uri = "ws://localhost:8767"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔗 Connected to backend")
            
            # Register
            register_msg = {
                "type": "register",
                "client_id": f"test_client_{int(time.time())}"
            }
            await websocket.send(json.dumps(register_msg))
            response = await websocket.recv()
            print(f"📝 Registration: {json.loads(response)}")
            
            # Test ASK mode
            print("\n🤔 Testing ASK mode...")
            ask_msg = {
                "type": "chat_request",
                "mode": "Ask",
                "message": "What am I working on right now?",
                "session_id": "test_session_ask"
            }
            await websocket.send(json.dumps(ask_msg))
            response = await websocket.recv()
            ask_result = json.loads(response)
            print(f"ASK Response: {ask_result.get('response', 'No response')}")
            print(f"Enhanced memory used: {ask_result.get('enhanced_memory_used', False)}")
            print(f"Semantic search used: {ask_result.get('semantic_search_used', False)}")
            
            # Test SUGGEST mode  
            print("\n💡 Testing SUGGEST mode...")
            suggest_msg = {
                "type": "chat_request", 
                "mode": "Suggest",
                "message": "What should I do next with my coding project?",
                "session_id": "test_session_suggest"
            }
            await websocket.send(json.dumps(suggest_msg))
            response = await websocket.recv()
            suggest_result = json.loads(response)
            print(f"SUGGEST Response: {suggest_result.get('response', 'No response')}")
            print(f"Memory integrated: {suggest_result.get('memory_integrated', False)}")
            print(f"Suggest mode used: {suggest_result.get('suggest_mode_used', False)}")
            
            # Check for contextual elements
            print("\n🔍 Contextual Analysis:")
            print(f"ASK brain_router_used: {ask_result.get('brain_router_used', False)}")
            print(f"SUGGEST brain_router_used: {suggest_result.get('brain_router_used', False)}")
            
            if ask_result.get('metadata'):
                print(f"ASK metadata: {ask_result['metadata']}")
            if suggest_result.get('metadata'):
                print(f"SUGGEST metadata: {suggest_result['metadata']}")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_contextual_modes())