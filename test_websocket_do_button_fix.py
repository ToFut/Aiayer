#!/usr/bin/env python3
"""
Comprehensive test for the DO button fix in final_guaranteed_ws_server_8765.py

This test script:
1. Connects to the WebSocket server on port 8765
2. Sends agent_confirmation messages (simulating DO button clicks)
3. Verifies the server responds with the expected sequence of messages
4. Tests all confirmation actions: DO, DISMISS, ADJUST
"""
import asyncio
import websockets
import json
import time
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('test_do_button_fix')

async def test_agent_confirmation():
    """Test the DO button functionality by sending agent_confirmation messages"""
    uri = "ws://localhost:8765"
    
    print(f"🔌 Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            # Wait for welcome message
            welcome = await asyncio.wait_for(websocket.recv(), timeout=5)
            welcome_data = json.loads(welcome)
            print(f"✅ Connected! Received welcome message: {welcome_data['type']}")
            
            # Test 1: DO button
            print("\n🧪 TEST 1: DO BUTTON")
            await test_do_action(websocket)
            
            # Test 2: DISMISS button
            print("\n🧪 TEST 2: DISMISS BUTTON")
            await test_dismiss_action(websocket)
            
            # Test 3: ADJUST button
            print("\n🧪 TEST 3: ADJUST BUTTON")
            await test_adjust_action(websocket)
            
            print("\n✅ All tests completed successfully!")
            return True
            
    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ Connection closed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_do_action(websocket):
    """Test the DO button action"""
    session_id = f"test_session_{int(time.time())}"
    message = {
        "type": "agent_confirmation",
        "session_id": session_id,
        "action": "DO",
        "modifications": {},
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
    }
    
    print(f"📤 Sending DO confirmation message for session {session_id}...")
    await websocket.send(json.dumps(message))
    
    # Expected responses: 3 progress updates followed by success message
    expected_types = ["agent_progress", "agent_progress", "agent_progress", "agent_execution_success"]
    expected_steps = [1, 2, 3]
    
    for i, expected_type in enumerate(expected_types):
        response = await asyncio.wait_for(websocket.recv(), timeout=5)
        data = json.loads(response)
        response_type = data.get("type")
        
        if response_type == "agent_progress":
            step = data.get("step")
            progress = data.get("progress")
            msg = data.get("message")
            print(f"✅ Received progress update {i+1}: Step {step}, Progress {progress}%, Message: {msg}")
            assert step == expected_steps[i], f"Expected step {expected_steps[i]}, got {step}"
        elif response_type == "agent_execution_success":
            result = data.get("result", {})
            success = result.get("success", False)
            steps = result.get("steps_executed", 0)
            print(f"✅ Received execution success: {success}, Steps executed: {steps}")
            assert success is True, "Expected successful execution"
            assert steps == 3, "Expected 3 steps executed"
        else:
            print(f"❌ Unexpected response type: {response_type}")
            assert False, f"Unexpected response type: {response_type}"
    
    print("✅ DO button test passed!")

async def test_dismiss_action(websocket):
    """Test the DISMISS button action"""
    session_id = f"test_session_{int(time.time())}"
    message = {
        "type": "agent_confirmation",
        "session_id": session_id,
        "action": "DISMISS",
        "modifications": {},
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
    }
    
    print(f"📤 Sending DISMISS confirmation message for session {session_id}...")
    await websocket.send(json.dumps(message))
    
    # Expected response: agent_dismissed
    response = await asyncio.wait_for(websocket.recv(), timeout=5)
    data = json.loads(response)
    response_type = data.get("type")
    
    print(f"✅ Received response: {response_type}")
    assert response_type == "agent_dismissed", f"Expected agent_dismissed, got {response_type}"
    
    print("✅ DISMISS button test passed!")

async def test_adjust_action(websocket):
    """Test the ADJUST button action"""
    session_id = f"test_session_{int(time.time())}"
    message = {
        "type": "agent_confirmation",
        "session_id": session_id,
        "action": "ADJUST",
        "modifications": {},
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
    }
    
    print(f"📤 Sending ADJUST confirmation message for session {session_id}...")
    await websocket.send(json.dumps(message))
    
    # Expected response: agent_adjustment_request
    response = await asyncio.wait_for(websocket.recv(), timeout=5)
    data = json.loads(response)
    response_type = data.get("type")
    
    print(f"✅ Received response: {response_type}")
    assert response_type == "agent_adjustment_request", f"Expected agent_adjustment_request, got {response_type}"
    
    print("✅ ADJUST button test passed!")

if __name__ == "__main__":
    print("🧪 Running comprehensive DO button fix test...")
    print("This test verifies that the DO button functionality in the overlay is working correctly.")
    print("It tests all agent confirmation actions: DO, DISMISS, and ADJUST.")
    print("Make sure the WebSocket server is running on port 8765 before running this test.")
    print("\nStarting tests in 2 seconds...")
    time.sleep(2)
    
    try:
        success = asyncio.run(test_agent_confirmation())
        if success:
            print("\n🎉 COMPREHENSIVE TEST PASSED!")
            print("✅ The DO button fix is working correctly.")
            print("✅ Your WebSocket server on port 8765 correctly handles agent_confirmation messages.")
            print("✅ The overlay should now be able to execute automation plans with the DO button.")
            sys.exit(0)
        else:
            print("\n❌ TEST FAILED!")
            print("⚠️ The DO button fix is not working correctly.")
            print("⚠️ Check logs for details.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        sys.exit(1)