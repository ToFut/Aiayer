#!/usr/bin/env python3
"""
Debug Mode Responses - Deep dive test for each chat mode
Tests each mode to understand why responses are not working properly
"""

import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_mode_response(mode: str, message: str):
    """Test a specific mode with a message"""
    print(f"\n🧪 Testing {mode} mode with: '{message}'")
    print("="*60)
    
    try:
        uri = "ws://localhost:8767"
        async with websockets.connect(uri) as websocket:
            # Wait for welcome message
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            print(f"📥 Welcome: {welcome_data.get('message', 'Connected')}")
            
            # Send chat request
            request = {
                "type": "chat_request",
                "mode": mode,
                "message": message,
                "session_id": f"debug_session_{mode.lower()}"
            }
            
            print(f"📤 Sending: {json.dumps(request, indent=2)}")
            await websocket.send(json.dumps(request))
            
            # Receive response
            response = await websocket.recv()
            response_data = json.loads(response)
            
            print(f"📥 Response Type: {response_data.get('type')}")
            print(f"📥 Success: {response_data.get('success')}")
            print(f"📥 Mode: {response_data.get('mode')}")
            print(f"📥 Processing Time: {response_data.get('processing_time')}s")
            
            # Print the actual response content
            payload = response_data.get('payload', {})
            actual_response = payload.get('response') or response_data.get('response')
            
            print(f"💬 ACTUAL RESPONSE:")
            print(f"   {actual_response}")
            
            # Print metadata
            print(f"🔍 Metadata:")
            print(f"   Ollama Used: {payload.get('ollama_used')}")
            print(f"   AI Powered: {payload.get('ai_powered')}")
            print(f"   Contextual: {payload.get('contextual')}")
            
            return response_data
            
    except Exception as e:
        print(f"❌ Error testing {mode} mode: {e}")
        return None

async def test_all_modes():
    """Test all chat modes comprehensively"""
    print("🚀 Deep Dive Mode Response Testing")
    print("="*60)
    
    test_cases = [
        ("Ask", "what am i seeing?"),
        ("Ask", "what is the system status?"),
        ("Agent", "click on the search button"),
        ("Agent", "search in google 'SEGEV HALFON'"),
        ("Suggest", "how can I improve my workflow?"),
        ("General", "hello, how are you?")
    ]
    
    results = {}
    
    for mode, message in test_cases:
        result = await test_mode_response(mode, message)
        results[f"{mode}_{message[:20]}"] = result
        await asyncio.sleep(1)  # Small delay between tests
    
    print("\n" + "="*60)
    print("📊 SUMMARY OF RESULTS")
    print("="*60)
    
    for test_name, result in results.items():
        if result:
            success = result.get('success', False)
            response_text = result.get('payload', {}).get('response') or result.get('response', 'No response')
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"{status} {test_name}")
            print(f"    Response: {response_text[:100]}...")
        else:
            print(f"❌ FAILED {test_name} - Connection error")

async def test_status_endpoint():
    """Test the system status endpoint"""
    print("\n🔍 Testing System Status Endpoint")
    print("="*40)
    
    try:
        uri = "ws://localhost:8767"
        async with websockets.connect(uri) as websocket:
            # Wait for welcome
            await websocket.recv()
            
            # Request status
            status_request = {
                "type": "system_status"
            }
            
            await websocket.send(json.dumps(status_request))
            response = await websocket.recv()
            status_data = json.loads(response)
            
            print(f"📊 System Status:")
            print(json.dumps(status_data, indent=2))
            
            return status_data
            
    except Exception as e:
        print(f"❌ Error getting system status: {e}")
        return None

if __name__ == "__main__":
    async def main():
        # Test system status first
        await test_status_endpoint()
        
        # Test all modes
        await test_all_modes()
        
        print("\n🎯 Deep dive analysis complete!")
    
    asyncio.run(main())