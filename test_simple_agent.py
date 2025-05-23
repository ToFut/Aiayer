#!/usr/bin/env python3
"""
Simple Agent Mode Test
"""

import asyncio
import websockets
import json

async def test_agent():
    """Test Agent mode"""
    
    try:
        async with websockets.connect("ws://127.0.0.1:8767") as websocket:
            print("✅ Connected to backend")
            
            # Test a simple UI automation command
            message = {
                "type": "chat_request",
                "mode": "Agent",
                "query": "click at position 100 100",
                "user_id": "test_user",
                "session_id": "test_session"
            }
            
            print("📤 Sending: click at position 100 100")
            await websocket.send(json.dumps(message))
            
            # Get response
            response = await websocket.recv()
            data = json.loads(response)
            
            if data.get("type") == "chat_response":
                payload = data.get("payload", {})
                success = payload.get("success", False)
                response_text = payload.get("response", "")
                
                print(f"📥 Success: {success}")
                print(f"📄 Response: {response_text[:200]}...")
                
                if "Task Completed Successfully" in response_text:
                    print("🎉 REAL UI AUTOMATION WORKING!")
                else:
                    print("⚠️ Still using planning mode")
            else:
                print(f"📄 Response: {data}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_agent())