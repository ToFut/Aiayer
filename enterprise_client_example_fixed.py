#!/usr/bin/env python3
"""
Enterprise Client Example - Fixed Version
Professional Agent Interaction with Enhanced Error Handling
"""

import asyncio
import websockets
import json
import sys
from datetime import datetime

async def enterprise_demo():
    """Demonstrate enterprise agent capabilities"""
    uri = "ws://localhost:8765"
    
    try:
        print("🏢 Connecting to Enterprise Agent System...")
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully!")
            
            # Test system status first
            status_request = {"type": "system_status"}
            await websocket.send(json.dumps(status_request))
            status_response = await asyncio.wait_for(websocket.recv(), timeout=5)
            status_data = json.loads(status_response)
            
            print(f"📊 System Status: {status_data.get('status', 'Unknown')}")
            print(f"⏱️ Server Time: {status_data.get('server_time', 'Unknown')}")
            
            # Test different modes
            test_cases = [
                {"mode": "Agent", "message": "Click on Documents folder"},
                {"mode": "Ask", "message": "What is the current system status?"},
                {"mode": "Suggest", "message": "Help optimize my workflow"},
                {"mode": "General", "message": "Hello enterprise system"}
            ]
            
            for test in test_cases:
                print(f"\n🧪 Testing {test['mode']} Mode...")
                
                request = {
                    "type": "chat_request",
                    "mode": test["mode"],
                    "message": test["message"],
                    "timestamp": datetime.now().isoformat()
                }
                
                await websocket.send(json.dumps(request))
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                data = json.loads(response)
                
                if data.get("success"):
                    print(f"   ✅ {data.get('response', 'No response')}")
                    print(f"   ⏱️ Processing: {data.get('processing_time', 'N/A')}s")
                else:
                    print(f"   ❌ Error: {data.get('error', 'Unknown error')}")
            
            print("\n🎉 Enterprise demo completed successfully!")
            
    except asyncio.TimeoutError:
        print("❌ Connection timeout - enterprise system may be overloaded")
        return False
    except websockets.exceptions.ConnectionRefused:
        print("❌ Connection refused - enterprise system may not be running")
        return False
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(enterprise_demo())
    sys.exit(0 if success else 1)
