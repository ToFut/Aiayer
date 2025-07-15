#!/usr/bin/env python3
import asyncio
import websockets
import json
import time

async def debug_backend():
    print("🔍 Debugging backend connection...")
    
    uri = "ws://localhost:8767"
    async with websockets.connect(uri) as ws:
        print("✅ Connected to backend")
        
        # Register
        client_id = f"debug_{int(time.time())}"
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
        
        # Send chat request
        chat_msg = {
            "type": "chat_request",
            "mode": "Agent",
            "message": "Open Safari and search for SEGEV",
            "client_id": client_id,
            "timestamp": time.time()
        }
        print(f"📤 Sending chat request: {chat_msg}")
        await ws.send(json.dumps(chat_msg))
        
        # Wait for responses
        print("⏳ Waiting for responses...")
        for i in range(10):
            try:
                resp = await asyncio.wait_for(ws.recv(), timeout=3)
                print(f"📥 Response {i+1}: {resp}")
                
                # Try to parse as JSON
                try:
                    data = json.loads(resp)
                    if data.get("type") == "plan_generated":
                        print("🎯 Found plan_generated response!")
                        plan_id = data.get("plan_id")
                        plan = data.get("plan", {})
                        steps = plan.get("steps", [])
                        print(f"📋 Plan ID: {plan_id}")
                        print(f"📝 Steps: {len(steps)}")
                        for j, step in enumerate(steps):
                            print(f"  {j+1}. {step.get('description', 'Unknown step')}")
                        return
                except:
                    pass
                    
            except asyncio.TimeoutError:
                print(f"⏰ Timeout waiting for response {i+1}")
                break
            except Exception as e:
                print(f"❌ Error receiving response {i+1}: {e}")
                break
        
        print("❌ No plan_generated response received")

if __name__ == "__main__":
    asyncio.run(debug_backend()) 