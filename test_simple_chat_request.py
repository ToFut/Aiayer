#!/usr/bin/env python3
import asyncio
import websockets
import json
import time

async def test_simple_chat_request():
    print("🔍 Testing simple chat_request...")
    
    uri = "ws://localhost:8767"
    async with websockets.connect(uri) as ws:
        print("✅ Connected to backend")
        
        # Register
        client_id = f"simple_test_{int(time.time())}"
        register_msg = {"type": "register", "client_id": client_id}
        print(f"📤 Sending register: {register_msg}")
        await ws.send(json.dumps(register_msg))
        
        # Wait for registration response
        try:
            reg_resp = await asyncio.wait_for(ws.recv(), timeout=5)
            print(f"📥 Registration response: {reg_resp}")
        except Exception as e:
            print(f"❌ No registration response: {e}")
            return
        
        # Send simple chat request
        chat_msg = {
            "type": "chat_request",
            "mode": "Agent",
            "message": "Open Safari",
            "client_id": client_id,
            "timestamp": time.time()
        }
        print(f"📤 Sending chat request: {chat_msg}")
        await ws.send(json.dumps(chat_msg))
        
        # Wait for ANY response
        print("⏳ Waiting for ANY response...")
        for i in range(15):  # Wait longer
            try:
                resp = await asyncio.wait_for(ws.recv(), timeout=2)
                print(f"📥 Response {i+1}: {resp}")
                
                # Try to parse as JSON
                try:
                    data = json.loads(resp)
                    msg_type = data.get("type", "")
                    print(f"📋 Message type: {msg_type}")
                    
                    if msg_type == "plan_generated":
                        print("🎯 SUCCESS: Found plan_generated response!")
                        return True
                    elif msg_type == "plan_error":
                        print("⚠️ Plan creation failed:")
                        print(f"   Error: {data.get('error', 'Unknown error')}")
                        return False
                    elif msg_type == "error":
                        print("❌ Backend error:")
                        print(f"   Error: {data.get('error', 'Unknown error')}")
                        return False
                        
                except Exception as parse_error:
                    print(f"⚠️ Could not parse response as JSON: {parse_error}")
                    
            except asyncio.TimeoutError:
                print(f"⏰ Timeout waiting for response {i+1}")
                if i > 5:  # After 10 seconds, give up
                    break
            except Exception as e:
                print(f"❌ Error receiving response {i+1}: {e}")
                break
        
        print("❌ No meaningful response received")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_simple_chat_request())
    if result:
        print("✅ Test PASSED - Plan generation working!")
    else:
        print("❌ Test FAILED - Plan generation not working!") 