#!/usr/bin/env python3
import asyncio
import websockets
import json
import sys

async def test_agent_ui_automation():
    """Test Agent mode UI automation with real execution"""
    try:
        # Connect to enterprise backend server
        uri = "ws://localhost:8767"
        print(f"🔌 Connecting to {uri}...")
        
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to backend server")
            
            # Test 1: Simple click command
            test_request = {
                "type": "agent_request",
                "query": "click at position 150 150",
                "mode": "agent",
                "timestamp": "2025-01-22T15:30:00Z"
            }
            
            print(f"\n🚀 Sending Agent UI automation request: {test_request['query']}")
            await websocket.send(json.dumps(test_request))
            
            # Wait for response
            print("⏳ Waiting for response...")
            response = await websocket.recv()
            response_data = json.loads(response)
            
            print(f"\n📨 Response received:")
            print(f"Type: {response_data.get('type', 'unknown')}")
            print(f"Content: {response_data.get('content', 'No content')}")
            
            # Check if it shows UI automation execution
            content = response_data.get('content', '')
            if "UI Automation Executed Successfully" in content:
                print("\n✅ SUCCESS: Agent mode is executing real UI automation!")
                print("🖱️ Mouse click was actually performed")
            elif "Do/Dismiss/Adjust" in content or "action_buttons" in str(response_data):
                print("\n❌ FAILURE: Agent mode is still showing planning buttons")
                print("🔧 UI automation is not executing properly")
            else:
                print(f"\n⚠️  UNKNOWN: Response doesn't match expected patterns")
                print(f"Full response: {response_data}")
            
            # Test 2: Type command
            print("\n" + "="*50)
            test_request2 = {
                "type": "agent_request", 
                "query": "type hello world",
                "mode": "agent",
                "timestamp": "2025-01-22T15:31:00Z"
            }
            
            print(f"🚀 Sending second test: {test_request2['query']}")
            await websocket.send(json.dumps(test_request2))
            
            response2 = await websocket.recv()
            response_data2 = json.loads(response2)
            
            print(f"\n📨 Second response:")
            print(f"Type: {response_data2.get('type', 'unknown')}")
            print(f"Content: {response_data2.get('content', 'No content')}")
            
            content2 = response_data2.get('content', '')
            if "UI Automation Executed Successfully" in content2:
                print("\n✅ SUCCESS: Typing automation also working!")
                print("⌨️ Keyboard input was actually performed")
            else:
                print("\n⚠️ Typing test result unclear")
                
    except Exception as e:
        print(f"\n❌ Connection error: {e}")
        print("🔧 Backend server might not be running on port 8767")
        return False
    
    return True

if __name__ == "__main__":
    print("🧪 Testing Agent Mode UI Automation Execution")
    print("🎯 Goal: Verify Agent mode executes real mouse/keyboard actions")
    print("" + "="*60)
    
    try:
        asyncio.run(test_agent_ui_automation())
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
