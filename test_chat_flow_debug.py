#!/usr/bin/env python3

import asyncio
import websockets
import json
import uuid
from datetime import datetime

async def test_chat_request():
    """Test direct chat request to backend to debug response flow"""
    
    try:
        # Connect to backend
        uri = "ws://localhost:8767"
        print(f"Connecting to {uri}...")
        
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to backend")
            
            # Send registration first (like overlay does)
            register_payload = {
                "type": "register",
                "payload": {
                    "client_type": "test_client",
                    "version": "1.0.0",
                    "capabilities": ["chat", "streaming"]
                }
            }
            
            await websocket.send(json.dumps(register_payload))
            print("📝 Sent registration")
            
            # Wait for registration response
            response = await websocket.recv()
            reg_data = json.loads(response)
            print(f"📨 Registration response: {reg_data}")
            
            # Send chat request (same format as overlay)
            chat_payload = {
                "type": "chat_request",
                "mode": "ask",
                "message": "What is Python?",
                "session_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "mode_context": {
                    "mode": "ask",
                    "description": "Question answering mode for direct queries"
                },
                "user_intent": "question",
                "mode_instructions": "Provide a clear and informative answer to the user's question."
            }
            
            print(f"🚀 Sending chat request: {chat_payload['message']}")
            await websocket.send(json.dumps(chat_payload))
            
            # Listen for streaming response
            print("🔄 Listening for response chunks...")
            response_chunks = []
            
            while True:
                try:
                    # Set timeout to avoid hanging
                    response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    data = json.loads(response)
                    
                    print(f"📦 Received: {data}")
                    
                    if data.get("type") == "chat_chunk":
                        chunk = data.get("chunk", "")
                        response_chunks.append(chunk)
                        print(f"💬 Chunk: '{chunk}'")
                    
                    elif data.get("type") == "chat_complete":
                        print("✅ Chat complete received")
                        break
                    
                    elif data.get("type") == "error":
                        print(f"❌ Error received: {data}")
                        break
                        
                except asyncio.TimeoutError:
                    print("⏰ Timeout waiting for response")
                    break
                except Exception as e:
                    print(f"❌ Error receiving message: {e}")
                    break
            
            full_response = "".join(response_chunks)
            print(f"\n📋 Full response: '{full_response}'")
            print(f"📊 Total chunks received: {len(response_chunks)}")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    print("🧪 Testing chat request flow...")
    asyncio.run(test_chat_request())