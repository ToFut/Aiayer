#!/usr/bin/env python3

import asyncio
import websockets
import json
import time

async def debug_agent_response():
    """Debug the actual response from AGENT mode"""
    
    uri = "ws://localhost:8767"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔗 Connected to backend server")
            
            # Register client
            register_msg = {
                "type": "register",
                "client_id": f"debug_client_{int(time.time())}"
            }
            await websocket.send(json.dumps(register_msg))
            response = await websocket.recv()
            print(f"✅ Registration response: {json.loads(response)}")
            
            # Test AGENT mode request with exact debugging
            agent_request = {
                "type": "chat_request",
                "mode": "Agent",  # Ensure proper case
                "message": "write SEGEV in notepad",
                "timestamp": int(time.time() * 1000)
            }
            
            print(f"\n🤖 Sending AGENT mode request:")
            print(f"   Mode: '{agent_request['mode']}'")
            print(f"   Message: '{agent_request['message']}'")
            print(f"   Full request: {json.dumps(agent_request, indent=2)}")
            
            await websocket.send(json.dumps(agent_request))
            
            # Wait for response with detailed analysis
            print("\n⏳ Waiting for response...")
            response = await websocket.recv()
            response_data = json.loads(response)
            
            print(f"\n📦 Full Response Analysis:")
            print(f"Raw response: {json.dumps(response_data, indent=2)}")
            
            print(f"\n🔍 Key Fields:")
            print(f"  Type: {response_data.get('type')}")
            print(f"  Mode: {response_data.get('mode')}")
            print(f"  Interactive: {response_data.get('interactive')}")
            print(f"  Buttons: {response_data.get('buttons')}")
            print(f"  Real Automation Used: {response_data.get('real_automation_used')}")
            print(f"  Brain Router Used: {response_data.get('brain_router_used')}")
            print(f"  AI Powered: {response_data.get('ai_powered')}")
            
            # Show response message preview
            message = response_data.get('message', '') or response_data.get('response', '')
            print(f"\n📝 Response Message Preview:")
            print(f"  Length: {len(message)} characters")
            print(f"  First 200 chars: {message[:200]}...")
            if len(message) > 200:
                print(f"  Last 200 chars: ...{message[-200:]}")
                
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_agent_response())