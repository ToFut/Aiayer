#!/usr/bin/env python3
"""
Test script to test agent mode directly and see what response we get
"""

import asyncio
import websockets
import json
import time
import sys

async def test_agent_mode():
    """Test agent mode directly"""
    print("🧪 Testing agent mode direct response...")
    
    try:
        # Connect to the backend
        uri = "ws://localhost:8767"
        print(f"📡 Connecting to {uri}...")
        
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to backend")
            
            # Register first
            register_msg = {
                "type": "register",
                "client_type": "test_client",
                "version": "1.0.0",
                "capabilities": ["testing"],
                "timestamp": int(time.time() * 1000)
            }
            
            await websocket.send(json.dumps(register_msg))
            response = await websocket.recv()
            print(f"📝 Registration response: {json.loads(response)['type']}")
            
            # Send agent mode request
            agent_msg = {
                "type": "chat_request",
                "mode": "Agent",
                "message": "open Safari and search for flights",
                "session_id": "test_session_agent"
            }
            
            print("🎯 Sending agent request...")
            await websocket.send(json.dumps(agent_msg))
            
            # Collect all responses
            responses = []
            timeout = 30  # 30 second timeout
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    data = json.loads(response)
                    responses.append(data)
                    
                    print(f"📨 Received: {data.get('type', 'unknown')} - {data.get('text', '')[:50]}...")
                    
                    # Stop if we get a final response
                    if data.get("type") == "final_response":
                        print("✅ Got final response!")
                        break
                        
                    # Stop if we get agent plan ready
                    if data.get("type") == "agent_plan_ready":
                        print("✅ Got agent plan ready!")
                        break
                        
                except asyncio.TimeoutError:
                    print("⏱️  Timeout waiting for more responses")
                    break
                except Exception as e:
                    print(f"⚠️  Error reading response: {e}")
                    break
            
            print(f"\n📊 Total responses received: {len(responses)}")
            for i, resp in enumerate(responses):
                print(f"  {i+1}. {resp.get('type', 'unknown')}: {str(resp)[:100]}...")
                
            return len(responses) > 0
                
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Starting agent mode direct test...")
    
    success = await test_agent_mode()
    
    if success:
        print("\n✅ Test completed - check responses above")
    else:
        print("\n❌ Test failed")

if __name__ == "__main__":
    asyncio.run(main())