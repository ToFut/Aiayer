#!/usr/bin/env python3
"""
Test Fixed AGENT Mode - Verify Brain Router Integration
"""

import asyncio
import json
import websockets
import time

async def test_agent_mode():
    """Test the fixed AGENT mode with the specific case"""
    uri = "ws://localhost:8767"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔗 Connected to backend")
            
            # Register first
            register_msg = {
                "type": "register",
                "client_id": "test_client"
            }
            await websocket.send(json.dumps(register_msg))
            response = await websocket.recv()
            print(f"📝 Registration: {json.loads(response)}")
            
            # Test the problematic AGENT mode request
            test_message = {
                "type": "chat_request",
                "mode": "Agent",
                "message": "write SEGEV in notepad",
                "session_id": "test_session"
            }
            
            print(f"\n🤖 Sending AGENT mode request: '{test_message['message']}'")
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
            
            # Check if the response is appropriate
            response_text = result.get('response', '').lower()
            if any(phrase in response_text for phrase in ['illegal', 'harmful', "can't assist"]):
                print("\n❌ STILL GETTING INAPPROPRIATE RESPONSE!")
                print("The safety issue persists.")
            else:
                print("\n✅ SUCCESS! AGENT mode is now working properly!")
                print("No inappropriate safety response detected.")
                
    except Exception as e:
        print(f"❌ Error testing AGENT mode: {e}")

if __name__ == "__main__":
    print("🧪 Testing Fixed AGENT Mode Integration")
    print("=" * 50)
    asyncio.run(test_agent_mode())