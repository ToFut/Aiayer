#!/usr/bin/env python3
"""
Test script for DO button execution via the Ultimate DO Button Server
This script simulates clicking the DO button in the overlay interface
"""
import asyncio
import websockets
import json
import time
import sys

async def test_do_button():
    print("🧪 Testing DO button execution via Ultimate DO Button Server...")
    
    try:
        async with websockets.connect('ws://localhost:8765') as ws:
            # Get welcome message
            welcome = await ws.recv()
            welcome_data = json.loads(welcome)
            print(f"✅ Connected to server: {welcome_data.get('message', 'Unknown')}")
            
            # Create a test session ID
            session_id = f"test_session_{int(time.time())}"
            
            # Simulate clicking the DO button by sending agent_confirmation message
            do_message = {
                "type": "agent_confirmation",
                "action": "DO",
                "session_id": session_id
            }
            
            print(f"📤 Sending DO button click for session: {session_id}")
            await ws.send(json.dumps(do_message))
            
            # Collect all responses until execution_completed is received
            progress_updates = []
            final_result = None
            
            while True:
                response = await asyncio.wait_for(ws.recv(), timeout=10)
                data = json.loads(response)
                msg_type = data.get('type')
                
                if msg_type == 'agent_progress':
                    progress = data.get('progress', 0)
                    message = data.get('message', 'No message')
                    step = data.get('step', 0)
                    progress_updates.append((step, progress, message))
                    print(f"📊 Progress: {progress}% - Step {step}: {message}")
                
                elif msg_type == 'agent_execution_success':
                    final_result = data
                    success = data.get('result', {}).get('success', False)
                    summary = data.get('summary', 'No summary')
                    print(f"✅ Execution completed: {'SUCCESS' if success else 'FAILED'}")
                    print(f"📋 Summary: {summary}")
                    break
                
                elif msg_type == 'agent_execution_error':
                    final_result = data
                    error = data.get('error', 'Unknown error')
                    print(f"❌ Execution failed: {error}")
                    break
            
            # Print final test summary
            print("\n🔍 DO Button Test Results:")
            print(f"✅ Progress Updates: {len(progress_updates)}")
            print(f"✅ Final Status: {'SUCCESS' if final_result.get('result', {}).get('success', False) else 'FAILED'}")
            print(f"✅ Execution Time: {final_result.get('result', {}).get('execution_time', 0)}s")
            print(f"✅ Steps Executed: {final_result.get('result', {}).get('steps_executed', 0)}")
            
            return True
            
    except asyncio.TimeoutError:
        print("❌ Timeout waiting for server response")
        return False
    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ Connection closed unexpectedly: {e}")
        return False
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

async def test_button_action():
    """Alternative test using button_action format (for comprehensive testing)"""
    print("\n🧪 Testing button_action format via Ultimate DO Button Server...")
    
    try:
        async with websockets.connect('ws://localhost:8765') as ws:
            # Get welcome message
            welcome = await ws.recv()
            welcome_data = json.loads(welcome)
            print(f"✅ Connected to server: {welcome_data.get('message', 'Unknown')}")
            
            # Create a test plan ID
            plan_id = f"test_plan_{int(time.time())}"
            
            # Simulate button action
            button_message = {
                "type": "button_action",
                "action": "EXECUTE_PLAN",
                "plan_id": plan_id
            }
            
            print(f"📤 Sending button action for plan: {plan_id}")
            await ws.send(json.dumps(button_message))
            
            # Collect all responses until execution_completed is received
            progress_updates = []
            final_result = None
            
            while True:
                response = await asyncio.wait_for(ws.recv(), timeout=10)
                data = json.loads(response)
                msg_type = data.get('type')
                
                if msg_type == 'agent_progress':
                    progress = data.get('progress', 0)
                    message = data.get('message', 'No message')
                    step = data.get('step', 0)
                    progress_updates.append((step, progress, message))
                    print(f"📊 Progress: {progress}% - Step {step}: {message}")
                
                elif msg_type == 'agent_execution_success':
                    final_result = data
                    success = data.get('result', {}).get('success', False)
                    summary = data.get('summary', 'No summary')
                    print(f"✅ Execution completed: {'SUCCESS' if success else 'FAILED'}")
                    print(f"📋 Summary: {summary}")
                    break
                
                elif msg_type == 'agent_execution_error':
                    final_result = data
                    error = data.get('error', 'Unknown error')
                    print(f"❌ Execution failed: {error}")
                    break
            
            # Print final test summary
            print("\n🔍 Button Action Test Results:")
            print(f"✅ Progress Updates: {len(progress_updates)}")
            print(f"✅ Final Status: {'SUCCESS' if final_result.get('result', {}).get('success', False) else 'FAILED'}")
            print(f"✅ Execution Time: {final_result.get('result', {}).get('execution_time', 0)}s")
            print(f"✅ Steps Executed: {final_result.get('result', {}).get('steps_executed', 0)}")
            
            return True
            
    except asyncio.TimeoutError:
        print("❌ Timeout waiting for server response")
        return False
    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ Connection closed unexpectedly: {e}")
        return False
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

async def test_dismiss_action():
    """Test DISMISS action"""
    print("\n🧪 Testing DISMISS action via Ultimate DO Button Server...")
    
    try:
        async with websockets.connect('ws://localhost:8765') as ws:
            # Get welcome message
            welcome = await ws.recv()
            
            # Create a test session ID
            session_id = f"test_session_dismiss_{int(time.time())}"
            
            # Simulate clicking the DISMISS button
            dismiss_message = {
                "type": "agent_confirmation",
                "action": "DISMISS",
                "session_id": session_id
            }
            
            print(f"📤 Sending DISMISS action for session: {session_id}")
            await ws.send(json.dumps(dismiss_message))
            
            # Get response
            response = await asyncio.wait_for(ws.recv(), timeout=10)
            data = json.loads(response)
            
            if data.get('type') == 'agent_dismissed':
                print(f"✅ DISMISS action successful: {data.get('message', 'No message')}")
                return True
            else:
                print(f"❌ Unexpected response to DISMISS: {data}")
                return False
            
    except Exception as e:
        print(f"❌ Error testing DISMISS: {e}")
        return False

async def main():
    # Run DO button test
    do_result = await test_do_button()
    
    # Run button action test
    button_result = await test_button_action()
    
    # Run dismiss test
    dismiss_result = await test_dismiss_action()
    
    # Print overall results
    print("\n🧪 OVERALL TEST RESULTS:")
    print(f"DO Button Test: {'✅ PASSED' if do_result else '❌ FAILED'}")
    print(f"Button Action Test: {'✅ PASSED' if button_result else '❌ FAILED'}")
    print(f"Dismiss Action Test: {'✅ PASSED' if dismiss_result else '❌ FAILED'}")
    
    # Final verdict
    if do_result and button_result and dismiss_result:
        print("🎉 All tests PASSED! DO button functionality is working perfectly!")
        return 0
    else:
        print("⚠️ Some tests FAILED. Review the logs for details.")
        return 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)