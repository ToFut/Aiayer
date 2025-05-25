#!/usr/bin/env python3
"""
Test ASK Mode - What am I seeing on my PC?
"""

import asyncio
import json
import websockets
import time

async def test_ask_mode():
    """Test the ASK mode with screen context question"""
    uri = "ws://localhost:8767"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔗 Connected to backend")
            
            # Register first
            register_msg = {
                "type": "register",
                "client_id": "test_ask_client"
            }
            await websocket.send(json.dumps(register_msg))
            response = await websocket.recv()
            print(f"📝 Registration: {json.loads(response)}")
            
            # Test the ASK mode request
            test_message = {
                "type": "chat_request",
                "mode": "Ask",
                "message": "what am i seeing in my PC?",
                "session_id": "test_ask_session"
            }
            
            print(f"\n💭 Sending ASK mode request: '{test_message['message']}'")
            await websocket.send(json.dumps(test_message))
            
            # Wait for response
            response = await websocket.recv()
            result = json.loads(response)
            
            print(f"\n✅ Response received:")
            print(f"Mode: {result.get('mode')}")
            print(f"Brain Router Used: {result.get('brain_router_used', 'Unknown')}")
            print(f"Response: {result.get('response', 'No response')}")
            
            if result.get('brain_router_used'):
                print(f"Processing Time: {result.get('processing_time', 'Unknown')}s")
                print(f"Confidence: {result.get('confidence', 'Unknown')}")
                print(f"Resources Used: {result.get('resources_used', [])}")
                print(f"Verification Status: {result.get('verification_status', 'Unknown')}")
            
            # Check if we got a proper response or timeout error
            response_text = result.get('response', '').lower()
            if "timeout" in response_text or "unavailable" in response_text:
                print("\n⚠️ Still getting timeout issues with LLM service")
            else:
                print("\n✅ SUCCESS! ASK mode is working!")
                
    except Exception as e:
        print(f"❌ Error testing ASK mode: {e}")

if __name__ == "__main__":
    print("🧪 Testing ASK Mode Integration")
    print("=" * 40)
    asyncio.run(test_ask_mode())