#!/usr/bin/env python3
"""
Test Client for Simple Brain Router
Tests all 4 modes and connectivity
"""

import asyncio
import json
import websockets
import sys

async def test_brain_router():
    """Test all brain router modes"""
    uri = "ws://localhost:8765"
    
    try:
        print("🔗 Connecting to Brain Router...")
        async with websockets.connect(uri) as websocket:
            
            # Wait for connection confirmation
            initial_msg = await websocket.recv()
            connection_data = json.loads(initial_msg)
            print(f"✅ Connected: {connection_data.get('message')}")
            print(f"📋 Available modes: {connection_data.get('available_modes')}")
            print()
            
            # Test each mode
            test_cases = [
                {"mode": "Agent", "message": "Click on Documents folder"},
                {"mode": "Ask", "message": "What is the system status?"},
                {"mode": "Suggest", "message": "Help me optimize my workflow"},
                {"mode": "General", "message": "Hello, how are you?"}
            ]
            
            for test in test_cases:
                print(f"🧪 Testing {test['mode']} Mode...")
                
                # Send request
                request = {
                    "type": "chat_request",
                    "mode": test["mode"],
                    "message": test["message"]
                }
                
                await websocket.send(json.dumps(request))
                
                # Get response
                response = await websocket.recv()
                result = json.loads(response)
                
                if result.get("success"):
                    print(f"   ✅ {result['response']}")
                    print(f"   ⏱️ Processing time: {result['processing_time']}s")
                else:
                    print(f"   ❌ Error: {result.get('error')}")
                print()
            
            # Test system status
            print("📊 Getting system status...")
            await websocket.send(json.dumps({"type": "system_status"}))
            status_response = await websocket.recv()
            status = json.loads(status_response)
            
            print(f"   Status: {status.get('status')}")
            print(f"   Uptime: {status.get('uptime_seconds')}s")
            print(f"   Connected clients: {status.get('connected_clients')}")
            print(f"   Version: {status.get('version')}")
            
            print("\n🎉 All tests completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_brain_router())
    sys.exit(0 if success else 1)