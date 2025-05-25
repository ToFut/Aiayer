#!/usr/bin/env python3
import asyncio
import websockets
import json

async def test_register():
    try:
        async with websockets.connect("ws://localhost:8767") as websocket:
            # Wait for connection established
            connection_msg = await websocket.recv()
            connection_data = json.loads(connection_msg)
            print(f"✅ Connection: {connection_data.get('message')}")
            
            # Send register message like the overlay does
            register_msg = {
                "type": "register",
                "client_type": "ui",
                "version": "1.0.0",
                "capabilities": ["overlay_display", "user_interaction", "context_tracking"],
                "timestamp": 1716491234000
            }
            
            await websocket.send(json.dumps(register_msg))
            print("📤 Sent register message")
            
            # Wait for registration response
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            response_data = json.loads(response)
            print(f"📥 Registration response: {response_data.get('type')}")
            
            if response_data.get("type") == "registration_success":
                print("✅ Registration successful!")
                print(f"Server: {response_data.get('server_info', {}).get('name')}")
                print(f"AI Enabled: {response_data.get('server_info', {}).get('ai_enabled')}")
                print(f"Features: {response_data.get('server_info', {}).get('features')}")
                return True
            else:
                print(f"❌ Unexpected response: {response_data}")
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_register())
    print(f"Result: {result}")