#!/usr/bin/env python3
"""
Test which backend is actually responding
"""

import asyncio
import json
import websockets

async def test_backend(port):
    """Test a specific backend port"""
    print(f"\n🧪 Testing Backend on Port {port}")
    print("="*50)
    
    try:
        uri = f"ws://localhost:{port}"
        async with websockets.connect(uri) as websocket:
            # Wait for welcome message
            welcome = await asyncio.wait_for(websocket.recv(), timeout=5)
            welcome_data = json.loads(welcome)
            
            print(f"📥 Welcome Message:")
            print(f"   Type: {welcome_data.get('type')}")
            print(f"   Message: {welcome_data.get('message', 'No message')}")
            print(f"   Backend: {welcome_data.get('backend', 'Unknown')}")
            print(f"   Version: {welcome_data.get('version', 'Unknown')}")
            
            # Send test Ask mode request
            request = {
                "type": "chat_request",
                "mode": "Ask",
                "message": "what is nye?",
                "session_id": "test_session"
            }
            
            await websocket.send(json.dumps(request))
            print(f"\n📤 Sent test request")
            
            # Get response with timeout
            response = await asyncio.wait_for(websocket.recv(), timeout=60)
            response_data = json.loads(response)
            
            print(f"\n📥 Response:")
            print(f"   Type: {response_data.get('type')}")
            print(f"   Success: {response_data.get('success')}")
            
            actual_response = response_data.get('payload', {}).get('response') or response_data.get('response')
            print(f"   Content: {actual_response[:100]}...")
            
            # Check if it's a mock response
            is_mock = "help you understand" in actual_response or "Based on the system's knowledge base" in actual_response
            print(f"   Is Mock: {'🚨 YES' if is_mock else '✅ NO'}")
            
            return {
                "port": port,
                "connected": True,
                "is_mock": is_mock,
                "backend": welcome_data.get('backend', 'Unknown'),
                "response": actual_response
            }
            
    except Exception as e:
        print(f"❌ Error connecting to port {port}: {e}")
        return {
            "port": port,
            "connected": False,
            "error": str(e)
        }

async def main():
    """Test both backends"""
    print("🔍 Testing Backend Identity and Response Sources")
    print("="*60)
    
    # Test both ports
    results = await asyncio.gather(
        test_backend(8765),
        test_backend(8767),
        return_exceptions=True
    )
    
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    for result in results:
        if isinstance(result, dict):
            if result["connected"]:
                status = "🚨 MOCK RESPONSES" if result["is_mock"] else "✅ REAL RESPONSES"
                print(f"Port {result['port']}: {status}")
                print(f"   Backend: {result.get('backend', 'Unknown')}")
            else:
                print(f"Port {result['port']}: ❌ Not accessible")
        else:
            print(f"Error: {result}")
    
    print("\n🎯 Action needed: Use the port with REAL RESPONSES")

if __name__ == "__main__":
    asyncio.run(main())