#!/usr/bin/env python3
"""
Quick Mode Test - Test one mode to verify improvements
"""

import asyncio
import json
import websockets

async def test_single_mode():
    """Test Agent mode with google search"""
    print("🧪 Testing Agent mode: 'search in google 'SEGEV HALFON''")
    
    try:
        uri = "ws://localhost:8767"
        async with websockets.connect(uri) as websocket:
            # Wait for welcome message
            welcome = await websocket.recv()
            print("✅ Connected")
            
            # Send chat request
            request = {
                "type": "chat_request",
                "mode": "Agent", 
                "message": "search in google 'SEGEV HALFON'",
                "session_id": "quick_test"
            }
            
            await websocket.send(json.dumps(request))
            print("📤 Request sent, waiting for response...")
            
            # Wait for response with longer timeout
            response = await asyncio.wait_for(websocket.recv(), timeout=60)
            response_data = json.loads(response)
            
            print(f"📥 Response Type: {response_data.get('type')}")
            print(f"📥 Success: {response_data.get('success')}")
            print(f"📥 Processing Time: {response_data.get('processing_time')}s")
            
            actual_response = response_data.get('payload', {}).get('response') or response_data.get('response')
            print(f"\n💬 RESPONSE:\n{actual_response}")
            
            return response_data
            
    except asyncio.TimeoutError:
        print("❌ Response timed out - likely processing with longer Ollama timeout")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_single_mode())