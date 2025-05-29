#!/usr/bin/env python3
import asyncio
import websockets
import json
import time

async def test_direct_websocket():
    """Test direct WebSocket connection with simple message"""
    uri = "ws://localhost:8767"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket")
            
            # Register client
            register_msg = {
                "type": "register",
                "client_id": "direct_test",
                "timestamp": int(time.time() * 1000)
            }
            print("📤 Sending register message...")
            await websocket.send(json.dumps(register_msg))
            
            # Wait a moment
            await asyncio.sleep(0.5)
            
            # Send agent request
            start_time = time.time()
            agent_msg = {
                "type": "agent_mode",
                "message": "open YouTube and search SEGEV",
                "client_id": "direct_test",
                "timestamp": int(time.time() * 1000)
            }
            
            print("📤 Sending agent_mode request...")
            await websocket.send(json.dumps(agent_msg))
            
            print("⏳ Waiting for response...")
            
            # Listen for response with longer timeout
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                response_time = time.time() - start_time
                
                print(f"📥 Response received in {response_time:.2f}s")
                print(f"Response length: {len(response)} chars")
                print(f"Response preview: {response[:500]}...")
                
                # Try to parse as JSON
                try:
                    data = json.loads(response)
                    print(f"✅ Valid JSON response")
                    print(f"Type: {data.get('type')}")
                    print(f"Success: {data.get('success')}")
                    if 'buttons' in data:
                        print(f"Buttons: {len(data['buttons'])}")
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON: {e}")
                    
            except asyncio.TimeoutError:
                print("⏰ Timeout - no response received")
            except websockets.exceptions.ConnectionClosed as e:
                print(f"❌ Connection closed: {e}")
                
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    print("🧪 Testing Direct WebSocket Connection")
    print("=" * 50)
    asyncio.run(test_direct_websocket())