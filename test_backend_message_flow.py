#!/usr/bin/env python3
import asyncio
import websockets
import json
import time

async def test_message_flow():
    """Test the complete message flow to backend server"""
    try:
        uri = "ws://localhost:8767"
        print(f"🔌 Connecting to {uri}...")
        
        async with websockets.connect(uri) as websocket:
            print("✅ Connected")
            
            # Wait for connection_established message
            print("⏳ Waiting for connection_established...")
            initial_msg = await websocket.recv()
            print(f"📨 Initial: {initial_msg}")
            
            # Wait a bit
            await asyncio.sleep(1)
            
            # Send proper agent request
            agent_request = {
                "type": "agent_request",
                "query": "click at position 100 100",
                "mode": "agent",
                "timestamp": str(int(time.time()))
            }
            
            print(f"\n🚀 Sending: {json.dumps(agent_request, indent=2)}")
            await websocket.send(json.dumps(agent_request))
            
            # Wait for response with timeout
            print("⏳ Waiting for agent response...")
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                print(f"\n📨 Agent Response: {response}")
                
                # Parse and analyze
                try:
                    resp_data = json.loads(response)
                    print(f"\n🔍 Analysis:")
                    print(f"  Type: {resp_data.get('type')}")
                    print(f"  Status: {resp_data.get('status')}")
                    print(f"  Content length: {len(str(resp_data.get('content', '')))}")
                    
                    if "UI Automation Executed" in str(resp_data):
                        print("✅ UI AUTOMATION WORKING!")
                    elif "error" in resp_data.get('type', '').lower():
                        print(f"❌ Error response: {resp_data}")
                    else:
                        print("🤔 Unexpected response format")
                        
                except json.JSONDecodeError:
                    print(f"📝 Raw response (not JSON): {response}")
                    
            except asyncio.TimeoutError:
                print("⏰ Timeout - no response received")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🔍 Testing Backend Message Flow")
    print("="*40)
    asyncio.run(test_message_flow())