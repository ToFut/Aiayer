#!/usr/bin/env python3
"""
Simple connection test to debug WebSocket communication
"""

import asyncio
import json
import websockets

async def test_connection():
    """Test basic connection and message exchange"""
    try:
        print("🔗 Connecting to Brain Router...")
        async with websockets.connect("ws://localhost:8765", ping_timeout=10) as websocket:
            # Get connection message
            connection_msg = await asyncio.wait_for(websocket.recv(), timeout=5)
            print(f"📥 Connection response: {connection_msg}")
            
            # Test simple Agent request
            test_request = {
                "type": "chat_request",
                "mode": "Agent",
                "message": "test message",
                "session_id": "test_session"
            }
            
            print(f"📤 Sending: {json.dumps(test_request, indent=2)}")
            await websocket.send(json.dumps(test_request))
            
            # Get response
            response_raw = await asyncio.wait_for(websocket.recv(), timeout=15)
            print(f"📥 Raw response: {response_raw}")
            
            response = json.loads(response_raw)
            print(f"📥 Parsed response: {json.dumps(response, indent=2)}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())