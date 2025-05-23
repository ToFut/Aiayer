#!/usr/bin/env python3
"""
Test script to read all messages and see what's happening
"""
import asyncio
import websockets
import json

async def test_all_messages():
    uri = "ws://localhost:8765"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to enhanced enterprise backend")
            
            # Register first
            register_msg = {
                "type": "register",
                "client_type": "test_client"
            }
            await websocket.send(json.dumps(register_msg))
            
            # Send agent request immediately
            test_msg = {
                "type": "agent_request",
                "message": "What are the benefits of AI in business?"
            }
            await websocket.send(json.dumps(test_msg))
            print(f"📤 Sent both registration and agent request")
            
            # Read all messages for 10 seconds
            messages_received = []
            try:
                for i in range(5):  # Try to get up to 5 messages
                    print(f"⏳ Waiting for message {i+1}...")
                    message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    messages_received.append(message)
                    
                    response_data = json.loads(message)
                    print(f"\n📥 Message {i+1}:")
                    print(f"Type: {response_data.get('type')}")
                    
                    if response_data.get('type') == 'agent_response_with_reflection':
                        print(f"✅ Found agent response!")
                        print(f"Response: {response_data.get('response', 'No response field')}")
                        break
                    elif 'response' in response_data:
                        print(f"Response field: {response_data['response']}")
                        
            except asyncio.TimeoutError:
                print("⏰ Timeout waiting for more messages")
                
            print(f"\n📊 Total messages received: {len(messages_received)}")
            for i, msg in enumerate(messages_received):
                data = json.loads(msg)
                print(f"Message {i+1}: {data.get('type')} - {len(msg)} chars")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_all_messages())