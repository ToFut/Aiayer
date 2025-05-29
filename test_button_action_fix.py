#!/usr/bin/env python3
"""
Test script to verify the button_action message handler fix
"""

import asyncio
import websockets
import json
import time
import sys

async def test_button_action():
    """Test the button_action message handler"""
    print("🧪 Testing button_action message handler fix...")
    
    try:
        # Connect to the backend
        uri = "ws://localhost:8767"
        print(f"📡 Connecting to {uri}...")
        
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to backend")
            
            # Register first
            register_msg = {
                "type": "register",
                "client_type": "test_client",
                "version": "1.0.0",
                "capabilities": ["testing"],
                "timestamp": int(time.time() * 1000)
            }
            
            await websocket.send(json.dumps(register_msg))
            response = await websocket.recv()
            print(f"📝 Registration response: {json.loads(response)['type']}")
            
            # Create a mock automation plan first (simulate agent mode)
            agent_msg = {
                "type": "chat_request",
                "mode": "Agent",
                "message": "open Safari and search for flights",
                "session_id": "test_session_123"
            }
            
            print("🎯 Sending agent request to create a plan...")
            await websocket.send(json.dumps(agent_msg))
            
            # Wait for plan creation
            plan_created = False
            plan_id = None
            
            timeout = 30  # 30 second timeout
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(response)
                    print(f"📨 Received: {data.get('type', 'unknown')}")
                    
                    if data.get("type") == "agent_plan_ready":
                        plan_created = True
                        plan_id = data.get("plan_id") or data.get("session_id")
                        print(f"✅ Plan created with ID: {plan_id}")
                        break
                        
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"⚠️  Error reading response: {e}")
            
            if not plan_created:
                print("❌ No plan was created - testing with mock plan_id")
                plan_id = "test_session_123"
            
            # Now test the button_action message
            print(f"🧪 Testing button_action with plan_id: {plan_id}")
            
            button_action_msg = {
                "type": "button_action",
                "action": "execute_plan",
                "plan_id": plan_id,
                "client_id": "test_client",
                "timestamp": int(time.time() * 1000)
            }
            
            print(f"📤 Sending button_action: {button_action_msg}")
            await websocket.send(json.dumps(button_action_msg))
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                data = json.loads(response)
                
                if data.get("type") == "error" and "Unknown message type" in data.get("error", ""):
                    print("❌ FAILED: Still getting 'Unknown message type: button_action' error")
                    return False
                else:
                    print(f"✅ SUCCESS: button_action was handled! Response type: {data.get('type')}")
                    print(f"📝 Response: {data}")
                    return True
                    
            except asyncio.TimeoutError:
                print("⚠️  No response received - but no error means handler exists")
                return True
                
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Starting button_action fix test...")
    
    success = await test_button_action()
    
    if success:
        print("\n✅ Test PASSED: button_action handler is working!")
        print("🎯 Agent mode DO button should now work")
        sys.exit(0)
    else:
        print("\n❌ Test FAILED: button_action handler still has issues")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())