#!/usr/bin/env python3
"""
Debug Agent Mode to see what's happening with mode detection
"""
import asyncio
import websockets
import json

async def debug_agent_mode():
    uri = "ws://localhost:8767"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to backend")
            
            # Test different message formats
            test_messages = [
                {
                    "type": "chat_message", 
                    "data": {"message": "open Safari", "mode": "agent", "session_id": "test_1"}
                },
                {
                    "type": "chat_request", 
                    "data": {"message": "open Safari", "mode": "agent", "session_id": "test_2"}
                },
                {
                    "type": "chat_request", 
                    "message": "open Safari", 
                    "mode": "agent", 
                    "session_id": "test_3"
                }
            ]
            
            for i, msg in enumerate(test_messages):
                print(f"\n📤 Test {i+1}: {msg}")
                await websocket.send(json.dumps(msg))
                
                # Wait for responses
                try:
                    # Connection response
                    response1 = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data1 = json.loads(response1)
                    print(f"📥 Response 1: {data1.get('type')}")
                    
                    # Agent response
                    response2 = await asyncio.wait_for(websocket.recv(), timeout=8.0)
                    data2 = json.loads(response2)
                    print(f"📥 Response 2: {data2.get('type')}")
                    print(f"    Mode: {data2.get('mode', 'Not specified')}")
                    
                    if data2.get('type') == 'streaming_response':
                        print(f"    🎉 AGENT MODE WORKED!")
                        buttons = data2.get('data', {}).get('buttons', [])
                        print(f"    Buttons: {len(buttons)} found")
                        return
                    else:
                        print(f"    ❌ Not Agent mode: {data2.get('mode', 'unknown')}")
                        
                except asyncio.TimeoutError:
                    print(f"    ⏱️ Timeout waiting for response")
                    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_agent_mode())