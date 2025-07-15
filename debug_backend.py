#!/usr/bin/env python3
"""
Debug Backend - Test backend message handling step by step
"""
import asyncio
import json
import websockets
from datetime import datetime

async def debug_backend():
    """Debug backend message handling"""
    print("🔍 Debugging Backend Message Handling...")
    
    try:
        # Connect to backend
        uri = "ws://localhost:8767"
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to backend")
            
            # Step 1: Register
            print("\n1️⃣ Sending registration...")
            register_message = {
                "type": "register",
                "client_id": "debug_client",
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(register_message))
            
            # Wait for registration response
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"✅ Registration response: {response_data.get('type')}")
            
            # Step 2: Send chat request to generate a plan
            print("\n2️⃣ Sending chat request to generate plan...")
            chat_message = {
                "type": "chat_request",
                "message": "Open Safari and search for SEGEV",
                "mode": "Agent",
                "client_id": "debug_client",
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(chat_message))
            
            # Wait for response
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"✅ Chat response type: {response_data.get('type')}")
            print(f"✅ Chat response: {response_data}")
            
            # Step 3: Execute the generated plan
            print("\n3️⃣ Executing generated plan...")
            
            if response_data.get("type") == "plan_generated":
                plan = response_data.get("plan", {})
                plan_id = response_data.get("plan_id", "")
                print(f"✅ Plan generated with ID: {plan_id}")
                
                # Execute the plan
                execute_message = {
                    "type": "execute_plan",
                    "plan_id": plan_id,
                    "client_id": "debug_client",
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send(json.dumps(execute_message))
                
                # Wait for execution responses
                print("⏳ Waiting for execution responses...")
                execution_completed = False
                timeout_count = 0
                
                while not execution_completed and timeout_count < 30:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        response_data = json.loads(response)
                        print(f"✅ Execution response: {response_data.get('type')}")
                        
                        if response_data.get("type") == "execution_completed":
                            print("✅ Execution completed!")
                            print(f"📊 Results: {response_data.get('steps_completed', 0)}/{response_data.get('total_steps', 0)} steps")
                            print(f"📈 Success rate: {response_data.get('success_rate', 0):.1%}")
                            print(f"⏱️ Total time: {response_data.get('total_execution_time', 0):.2f}s")
                            
                            # Print detailed reasoning if available
                            if response_data.get("detailed_reasoning"):
                                print("\n📋 Detailed Reasoning:")
                                print(response_data.get("detailed_reasoning"))
                            
                            execution_completed = True
                            break
                        elif response_data.get("type") == "execution_error":
                            print(f"❌ Execution error: {response_data.get('error')}")
                            break
                        elif response_data.get("type") == "execution_started":
                            print("🚀 Execution started...")
                        elif response_data.get("type") == "execution_progress":
                            print(f"🔄 Progress: Step {response_data.get('step', 0)}/{response_data.get('total_steps', 0)}")
                            
                    except asyncio.TimeoutError:
                        timeout_count += 1
                        print(f"⏰ Timeout waiting for execution response ({timeout_count}/30)")
                        
                if not execution_completed:
                    print("⏰ Execution timed out")
            else:
                print(f"❌ Expected plan_generated, got: {response_data.get('type')}")
                print(f"❌ Full response: {response_data}")
                
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Backend Debug...")
    asyncio.run(debug_backend()) 