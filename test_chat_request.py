#!/usr/bin/env python3
import asyncio
import websockets
import json

async def test_chat_request():
    try:
        async with websockets.connect("ws://localhost:8767") as websocket:
            # Wait for connection established
            connection_msg = await websocket.recv()
            print(f"✅ Connected: {json.loads(connection_msg).get('message')}")
            
            # Send chat request like the overlay does
            chat_request = {
                "type": "chat_request",
                "mode": "ask",
                "message": "Hello, how are you?",
                "session_id": "test_session_123",
                "timestamp": "2025-05-23T16:06:00.000Z"
            }
            
            print(f"📤 Sending chat request: {chat_request}")
            await websocket.send(json.dumps(chat_request))
            
            # Collect responses
            response_count = 0
            while response_count < 20:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    response_data = json.loads(response)
                    response_count += 1
                    
                    print(f"📥 Response {response_count}: {response_data.get('type')}")
                    
                    if response_data.get("type") == "chat_response_start":
                        print(f"   🚀 Started: {response_data.get('message')}")
                    elif response_data.get("type") == "chat_response_chunk":
                        chunk = response_data.get("chunk", "")
                        print(f"   📝 Chunk: '{chunk}'")
                    elif response_data.get("type") == "chat_response_complete":
                        final = response_data.get("full_response", "")
                        print(f"   ✅ Complete: {final}")
                        return True
                    elif response_data.get("type") == "error":
                        error = response_data.get("error", "Unknown")
                        print(f"   ❌ Error: {error}")
                        return False
                        
                except asyncio.TimeoutError:
                    print(f"⏱️ Timeout after {response_count} responses")
                    break
                    
            print("❌ No completion received")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_chat_request())
    print(f"Result: {result}")