#!/usr/bin/env python3
"""
Test script for the DO button functionality with the fixed WebSocket server
"""
import asyncio
import websockets
import json
import time
import uuid

async def test_agent_confirmation():
    """Test the DO button functionality by sending an agent_confirmation message"""
    uri = "ws://localhost:8765"
    
    print(f"Connecting to {uri}...")
    async with websockets.connect(uri) as websocket:
        # Wait for welcome message
        welcome = await websocket.recv()
        print(f"Received welcome message: {welcome}")
        
        # Create a test agent_confirmation message (DO button click)
        session_id = f"test_session_{int(time.time())}"
        message = {
            "type": "agent_confirmation",
            "session_id": session_id,
            "action": "DO",
            "modifications": {},
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
        }
        
        # Send the message
        print(f"Sending agent_confirmation message for session {session_id}...")
        await websocket.send(json.dumps(message))
        
        # Receive progress updates and completion message
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            response_type = data.get("type")
            
            print(f"Received {response_type} message: {data}")
            
            # If we receive the completion message, we're done
            if response_type == "agent_execution_success":
                print("Test completed successfully!")
                break

async def test_do_button_with_plan():
    """Test the DO button functionality by sending a plan and then executing it"""
    uri = "ws://localhost:8765"
    
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            # Register the client
            client_id = f"test_client_{uuid.uuid4()}"
            session_id = f"test_session_{uuid.uuid4()}"
            register_message = {
                "type": "register",
                "client_id": client_id,
                "session_id": session_id,
                "client_type": "nextgen_overlay",
                "capabilities": ["text", "json", "suggestions"]
            }
            
            print("Sending registration message...")
            await websocket.send(json.dumps(register_message))
            
            # Create a test plan
            plan_id = f"plan_{int(time.time())}"
            test_plan = {
                "type": "response",
                "mode": "Agent",
                "success": True,
                "response": f"""🎯 **AUTOMATION EXECUTION PLAN**

**🔍 Task Type:** Test Automation
**📋 Task:** Execute a test plan
**⏱️ Estimated Duration:** 5.0 seconds
**🎯 Success Probability:** 95%
**🔧 Complexity:** Low
**📝 Steps:** 3 actions

**🚀 Automation Steps:**
1. 🟢 Initialize test environment
2. 🟢 Run test procedure
3. 🟢 Verify test results

**🆔 Plan ID:** `{plan_id}`
**🧠 Planning:** Test System

*Automation System: ✅ Ready for Execution*"""
            }
            
            # Wait for a response to registration
            print("Waiting for registration response...")
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"Received response: {response}")
            except asyncio.TimeoutError:
                print("No response received to registration (this might be normal)")
            
            # Send the test plan
            print(f"Sending test plan with ID {plan_id}...")
            await websocket.send(json.dumps(test_plan))
            
            # Wait a moment for the plan to be processed
            await asyncio.sleep(2)
            
            # Send execute command for the plan
            execute_command = {
                "type": "query",
                "payload": {
                    "message": f"/do_execute {plan_id}",
                    "timestamp": int(time.time() * 1000)
                }
            }
            
            print(f"Sending execute command for plan {plan_id}...")
            await websocket.send(json.dumps(execute_command))
            
            # Wait for execution responses
            print("Waiting for execution responses...")
            timeout_count = 0
            while timeout_count < 3:  # Allow up to 3 timeouts
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print(f"Received response: {response}")
                    
                    # Parse the response to check for execution status
                    try:
                        data = json.loads(response)
                        if data.get("type") == "execution_complete":
                            print("Execution completed successfully!")
                            break
                    except json.JSONDecodeError:
                        print(f"Received non-JSON response: {response}")
                        
                except asyncio.TimeoutError:
                    timeout_count += 1
                    print(f"No response received within timeout ({timeout_count}/3)")
            
            print("Test completed")
    
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    print("Running DO button test with plan execution...")
    asyncio.run(test_do_button_with_plan())