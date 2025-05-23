#!/usr/bin/env python3
import asyncio
import websockets
import json
import time

async def test_correct_agent_request():
    """Test with correct message format for agent mode"""
    try:
        uri = "ws://localhost:8767"
        print(f"🔌 Connecting to {uri}...")
        
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to backend server")
            
            # Wait for initial connection message
            initial_msg = await websocket.recv()
            initial_data = json.loads(initial_msg)
            print(f"📨 Initial: {initial_data.get('type')} - {initial_data.get('message')}")
            
            # Send correct chat_request format for agent mode
            chat_request = {
                "type": "chat_request",
                "query": "click at position 100 100",
                "mode": "agent",  # This should trigger UI automation
                "timestamp": str(int(time.time()))
            }
            
            print(f"\n🚀 Sending CORRECT format:")
            print(f"   Type: {chat_request['type']}")
            print(f"   Mode: {chat_request['mode']}")
            print(f"   Query: {chat_request['query']}")
            
            await websocket.send(json.dumps(chat_request))
            
            # Wait for response
            print("\n⏳ Waiting for agent mode response...")
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                print(f"\n📨 RESPONSE RECEIVED!")
                print(f"Raw: {response}")
                
                # Parse response
                try:
                    resp_data = json.loads(response)
                    print(f"\n🔍 PARSED RESPONSE:")
                    print(f"  Type: {resp_data.get('type')}")
                    print(f"  Status: {resp_data.get('status')}")
                    print(f"  Mode: {resp_data.get('mode')}")
                    
                    # Get content from payload
                    payload = resp_data.get('payload', {})
                    content = payload.get('response', '')
                    success = payload.get('success', False)
                    print(f"  Content preview: {content[:200]}...")
                    print(f"  Success: {success}")
                    
                    # Check for success indicators
                    if "UI Automation Executed Successfully" in content and success:
                        print("\n✅ 🎉 SUCCESS! UI AUTOMATION IS WORKING!")
                        print("🖱️ Agent mode executed real mouse click!")
                        return True
                    elif "Do" in content and "Dismiss" in content:
                        print("\n❌ STILL PLANNING MODE - Not executing UI automation")
                        print("🔧 Need to fix workflow execution")
                        return False
                    elif "error" in resp_data.get('type', '').lower():
                        print(f"\n❌ ERROR RESPONSE: {resp_data}")
                        return False
                    else:
                        print(f"\n🤔 UNCLEAR RESULT:")
                        print(f"Full response: {resp_data}")
                        return False
                        
                except json.JSONDecodeError:
                    print(f"\n📝 Raw non-JSON response: {response}")
                    return False
                    
            except asyncio.TimeoutError:
                print("\n⏰ TIMEOUT - No response from backend")
                print("🔧 Backend may not be processing agent requests")
                return False
                
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 TESTING AGENT MODE UI AUTOMATION")
    print("🎯 Goal: Verify real mouse clicks are executed")
    print("="*50)
    
    success = asyncio.run(test_correct_agent_request())
    
    if success:
        print("\n🎆 AGENT MODE IS WORKING - Real UI automation!")
    else:
        print("\n🚨 AGENT MODE NEEDS FIXING - Still in planning mode")
    
    print("\n" + "="*50)