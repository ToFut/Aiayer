#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced UI for DO buttons.
This sends a sample automation plan to verify that the UI displays the plan properly.
"""
import asyncio
import websockets
import json
import time
import uuid

async def test_do_button_ui():
    """Send a sample automation plan to test the UI enhancements"""
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
            
            # Wait for a response to registration
            print("Waiting for registration response...")
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"Received response: {response}")
            except asyncio.TimeoutError:
                print("No response received to registration (this might be normal)")
            
            # Create a test plan with a more realistic format for a Google search
            plan_id = f"plan_{int(time.time())}"
            test_plan = {
                "type": "response",
                "mode": "Agent",
                "success": True,
                "response": f"""I'll help you search for information about the weather in New York.

🎯 **AUTOMATION EXECUTION PLAN**

**🔍 Task Type:** Google Search
**📋 Task:** Search for weather in New York
**⏱️ Estimated Duration:** 5.0 seconds
**🎯 Success Probability:** 95%
**🔧 Complexity:** Low
**📝 Steps:** 3 actions

**🚀 Automation Steps:**
1. 🟢 Open Google in the browser
2. 🟢 Type "weather in New York" in the search box
3. 🟢 Press Enter to perform the search

**🆔 Plan ID:** `{plan_id}`
**🧠 Planning:** Universal Intelligence System

*Automation System: ✅ Ready for Execution*"""
            }
            
            # Send the test plan
            print(f"Sending test plan with ID {plan_id}...")
            await websocket.send(json.dumps(test_plan))
            
            # Now send a typical unstructured plan that should also be formatted nicely
            await asyncio.sleep(3)
            
            unstructured_plan_id = f"plan_{int(time.time())}"
            unstructured_plan = {
                "type": "response",
                "mode": "Agent",
                "success": True,
                "response": f"""I'll help you open the Calculator application.

To do this, I'll:

1. Look for the Calculator application on your system
2. Click on the Calculator icon to open it
3. Verify the Calculator has opened successfully

This task should be straightforward and quick to execute. The plan ID is {unstructured_plan_id}.

Would you like me to proceed with opening the Calculator?"""
            }
            
            print(f"Sending unstructured plan with ID {unstructured_plan_id}...")
            await websocket.send(json.dumps(unstructured_plan))
            
            # Wait for a while to keep the connection open so the user can see the UI
            print("Plans sent. Check the overlay UI to see the formatted cards with DO buttons.")
            print("Waiting for 30 seconds before closing connection...")
            await asyncio.sleep(30)
            
            print("Test completed")
    
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    print("Running DO button UI test...")
    asyncio.run(test_do_button_ui())