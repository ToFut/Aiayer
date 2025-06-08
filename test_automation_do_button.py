#!/usr/bin/env python3
"""
Test script for the Ultimate DO Button server automation capabilities
This script connects to the WebSocket server and sends various automation commands
"""
import asyncio
import websockets
import json
import sys
import time
import traceback
import platform
from datetime import datetime

# Configure connection parameters
WS_SERVER = "ws://localhost:8765"  # Change if server is on a different host/port

# Platform detection for better test instructions
IS_MAC = platform.system() == 'Darwin'
IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'

# Platform-specific hotkey combinations
SELECT_ALL_KEYS = ["command", "a"] if IS_MAC else ["ctrl", "a"]
COPY_KEYS = ["command", "c"] if IS_MAC else ["ctrl", "c"]

# Define test actions
TEST_ACTIONS = [
    # Before running these tests, make sure to:
    # 1. Open a text editor (like TextEdit, Notepad, etc.)
    # 2. Position it so it's visible on screen
    # 3. Make sure the cursor is in the text area
    
    # Wait a moment for the user to read instructions
    {
        "name": "Preparation Wait",
        "message": {
            "type": "agent_confirmation",
            "session_id": f"test_{int(time.time())}",
            "action": "DO",
            "action_plan": []  # Empty plan just to wait
        }
    },
    
    # Mouse movement to a visible part of the screen
    {
        "name": "Move Mouse (Top-Left)",
        "message": {
            "type": "agent_confirmation",
            "session_id": f"test_{int(time.time())}",
            "action": "DO",
            "action_plan": [
                {
                    "type": "click",
                    "x": 100,   # Move to visible top-left area
                    "y": 100,
                    "clicks": 0  # 0 clicks = just move the mouse
                }
            ]
        }
    },
    
    # Mouse movement to another visible part of the screen
    {
        "name": "Move Mouse (Bottom-Right)",
        "message": {
            "type": "agent_confirmation",
            "session_id": f"test_{int(time.time())}",
            "action": "DO",
            "action_plan": [
                {
                    "type": "click",
                    "x": 800,   # Move to visible bottom-right area
                    "y": 600,
                    "clicks": 0  # 0 clicks = just move the mouse
                }
            ]
        }
    },
    
    # Click test - click in a visible position
    {
        "name": "Visible Mouse Click",
        "message": {
            "type": "agent_confirmation",
            "session_id": f"test_{int(time.time())}",
            "action": "DO",
            "action_plan": [
                {
                    "type": "click",
                    "x": 400,   # Click in a more visible area
                    "y": 300
                }
            ]
        }
    },
    
    # Type test - type visible text
    {
        "name": "Type Very Visible Text",
        "message": {
            "type": "button_action",
            "plan_id": f"test_{int(time.time())}",
            "action": "EXECUTE_PLAN",
            "actions": [
                {
                    "type": "text",
                    "value": "THIS IS AN AUTOMATION TEST! 🤖"
                }
            ]
        }
    },
    
    # Key press test - press Enter (should be visible in text editor)
    {
        "name": "Press Enter Key",
        "message": {
            "type": "do_button",
            "session_id": f"test_{int(time.time())}",
            "action_data": {
                "type": "key",
                "key": "enter"
            }
        }
    },
    
    # Type more text after the enter key
    {
        "name": "Type More Text",
        "message": {
            "type": "button_action",
            "plan_id": f"test_{int(time.time())}",
            "action": "EXECUTE_PLAN",
            "actions": [
                {
                    "type": "text",
                    "value": "Second line - automation working! 👍"
                }
            ]
        }
    },
    
    # Hotkey test - Select All (using platform-specific key combination)
    {
        "name": f"Hotkey Select All ({'+'.join(SELECT_ALL_KEYS)})",
        "message": {
            "type": "agent_confirmation",
            "session_id": f"test_{int(time.time())}",
            "action": "DO",
            "action_plan": [
                {
                    "type": "hotkey",
                    "keys": SELECT_ALL_KEYS
                }
            ]
        }
    },
    
    # Type final test after selection
    {
        "name": "Final Text After Selection",
        "message": {
            "type": "do_button",
            "session_id": f"test_{int(time.time())}",
            "action_data": {
                "type": "text",
                "value": "Automation test complete! The DO button is now executing real actions! 🎉"
            }
        }
    }
]

async def test_automation():
    """Test the DO button automation capabilities"""
    print("\n" + "="*80)
    print("🤖 DO BUTTON AUTOMATION TEST 🤖")
    print("="*80)
    print(f"\nDetected platform: {platform.system()} {platform.release()}")
    
    if IS_MAC:
        print("\n⚠️  IMPORTANT MAC OS REQUIREMENT ⚠️")
        print("For automation to work on Mac, you MUST grant Accessibility permissions:")
        print("1. Go to System Settings > Privacy & Security > Accessibility")
        print("2. Add Terminal (or your IDE) to the list of allowed apps")
        print("3. Make sure the checkbox is enabled")
    elif IS_WINDOWS:
        print("\n⚠️  IMPORTANT WINDOWS NOTE ⚠️")
        print("For best results, make sure the terminal has focus but isn't covering the whole screen")
    
    print("\nBefore continuing, please:")
    print("1. Open a text editor (like " + ("TextEdit" if IS_MAC else "Notepad" if IS_WINDOWS else "gedit") + ")")
    print("2. Position it so it's visible on screen")
    print("3. Click in the text area so the cursor is active")
    print("4. Come back to this terminal window")
    print("\nThe automation will move your mouse and type text in the active window.")
    print("⚠️  You should see the mouse move and text being typed automatically!")
    print("⚠️  Do not move your mouse during the test!")
    print("="*80)
    
    # 5-second countdown
    for i in range(5, 0, -1):
        print(f"Starting in {i} seconds...", end="\r")
        await asyncio.sleep(1)
    print("Starting now!                 ")
    
    print(f"\nConnecting to DO button server at {WS_SERVER}...")
    
    try:
        async with websockets.connect(WS_SERVER) as websocket:
            print(f"Connected successfully!")
            
            # Receive the welcome message
            welcome = await websocket.recv()
            print(f"Server welcome: {welcome}")
            
            # Run each test action
            for i, test in enumerate(TEST_ACTIONS):
                print(f"\n[{i+1}/{len(TEST_ACTIONS)}] Running test: {test['name']}")
                
                # Give extra time before mouse movements for better visibility
                if "Move Mouse" in test["name"] or "Click" in test["name"]:
                    print("  ⚠️  Watch your mouse cursor...")
                    await asyncio.sleep(1)
                
                # Send the message
                message = test['message']
                print(f"Sending: {json.dumps(message, indent=2)}")
                await websocket.send(json.dumps(message))
                
                # Wait for and collect all responses
                response_count = 0
                while True:
                    try:
                        # Set a timeout for each response
                        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        response_count += 1
                        
                        # Parse and print the response
                        try:
                            resp_json = json.loads(response)
                            resp_type = resp_json.get('type', 'unknown')
                            
                            # Print progress messages briefly
                            if resp_type == 'agent_progress':
                                progress = resp_json.get('progress', 0)
                                step = resp_json.get('step', 0)
                                message = resp_json.get('message', '')
                                print(f"  Progress [{progress}%] Step {step}: {message}")
                            
                            # Print final result in detail
                            elif resp_type == 'agent_execution_success':
                                print(f"\n  ✅ SUCCESS: {resp_json.get('summary', '')}")
                                result = resp_json.get('result', {})
                                print(f"  Steps executed: {result.get('steps_executed', 0)}")
                                print(f"  Execution time: {result.get('execution_time', 0)}s")
                                
                                # Print automation result if available
                                automation_result = result.get('automation_result', {})
                                if automation_result:
                                    print(f"  Automation success: {automation_result.get('success', False)}")
                                    
                                # Final response received, break the loop
                                break
                            
                            # Other response types
                            else:
                                print(f"  Received {resp_type} response")
                        
                        except json.JSONDecodeError:
                            print(f"  Received non-JSON response: {response[:100]}...")
                    
                    except asyncio.TimeoutError:
                        print("  ⚠️ Timeout waiting for response")
                        break
                
                # Longer delay between tests for better visibility
                print("\n  ⏳ Waiting before next action...")
                await asyncio.sleep(3)
            
            print("\n" + "="*80)
            print("✅ All automation tests completed!")
            print("="*80)
            print("\nResults:")
            print("- If you saw your mouse move and text being typed: Automation is working correctly! ✅")
            print("- If nothing happened: There might be an issue with pyautogui or permissions ❌")
            print("\nTroubleshooting:")
            print("1. Make sure pyautogui is installed: pip install pyautogui")
            
            if IS_MAC:
                print("2. On Mac, ensure Terminal has Accessibility permissions in System Settings > Privacy & Security")
                print("   You may need to restart Terminal after granting permissions")
                print("3. Try running with sudo if you have permission issues: sudo python3 test_automation_do_button.py")
            elif IS_WINDOWS:
                print("2. On Windows, try running as Administrator if you have permission issues")
                print("3. Make sure the application window you're testing with is not minimized")
            else:  # Linux
                print("2. On Linux, you may need to install additional dependencies:")
                print("   sudo apt-get install python3-tk python3-dev")
                print("3. Try running with sudo if you have permission issues: sudo python3 test_automation_do_button.py")
                
            print("4. Check logs for detailed errors: logs/websocket/ultimate_do_button_server.log")
            print("\nYou can also try the browser-based test: test_automation_do_button.html")
            print("="*80)
    
    except websockets.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        print("\nMake sure the DO button server is running:")
        print("./start_do_button_server.sh")
    except Exception as e:
        print(f"❌ Error: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    # Run the test function
    asyncio.run(test_automation())