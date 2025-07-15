#!/usr/bin/env python3
"""
Test Backend Execution - Verify backend can execute automation plans
"""
import asyncio
import json
import websockets
from datetime import datetime

async def test_backend_execution():
    """Test backend execution with real automation"""
    print("🚀 Testing Backend Execution...")
    
    try:
        # Connect to backend
        uri = "ws://localhost:8767"
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to backend")
            
            # Register
            register_message = {
                "type": "register",
                "client_id": "test_execution_client",
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(register_message))
            
            # Wait for registration response
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"✅ Registration response: {response_data.get('type')}")
            
            # Send a simple automation request
            automation_message = {
                "type": "chat_request",
                "message": "Type Hello World",
                "mode": "Agent",
                "client_id": "test_execution_client",
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(automation_message))
            
            # Wait for plan generation
            response = await websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get("type") == "plan_generated":
                plan = response_data.get("plan", {})
                steps = plan.get("steps", [])
                print(f"✅ Plan generated with {len(steps)} steps")
                
                # Print plan details
                for i, step in enumerate(steps):
                    action_type = step.get("action_type", "unknown")
                    description = step.get("description", "No description")
                    print(f"  Step {i+1}: {action_type} - {description}")
                
                # Execute the plan
                execute_message = {
                    "type": "execute_plan",
                    "plan_id": plan.get("plan_id", "test_plan"),
                    "client_id": "test_execution_client",
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send(json.dumps(execute_message))
                
                # Wait for execution responses
                execution_started = False
                execution_completed = False
                step_count = 0
                
                while not execution_completed:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                        response_data = json.loads(response)
                        
                        if response_data.get("type") == "execution_started":
                            execution_started = True
                            print("✅ Execution started")
                            
                        elif response_data.get("type") == "execution_progress":
                            step_count += 1
                            step_type = response_data.get("step_type", "unknown")
                            description = response_data.get("description", "No description")
                            print(f"  ✅ Step {step_count}: {step_type} - {description}")
                            
                        elif response_data.get("type") == "execution_completed":
                            execution_completed = True
                            print("✅ Execution completed")
                            
                        elif response_data.get("type") == "execution_error":
                            error = response_data.get("error", "Unknown error")
                            print(f"❌ Execution error: {error}")
                            return False
                            
                    except asyncio.TimeoutError:
                        print("⏰ Timeout waiting for execution response")
                        break
                
                return execution_started and execution_completed
            else:
                print(f"❌ Plan generation failed: {response_data}")
                return False
                
    except Exception as e:
        print(f"❌ Backend execution test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Backend Execution Test...")
    print("⚠️  This will execute real automation!")
    
    # Run test
    success = asyncio.run(test_backend_execution())
    
    if success:
        print("\n🎉 Backend execution test passed!")
    else:
        print("\n❌ Backend execution test failed.") 