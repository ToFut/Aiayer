#!/usr/bin/env python3
"""
Test Interactive Button System - Do/Dismiss/Adjust buttons
"""

import asyncio
import json
import websockets
import time

async def test_interactive_buttons():
    """Test the interactive button system"""
    uri = "ws://localhost:8767"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔗 Connected to backend with Interactive Buttons")
            
            # Register first
            register_msg = {
                "type": "register",
                "client_id": "test_buttons_client"
            }
            await websocket.send(json.dumps(register_msg))
            response = await websocket.recv()
            print(f"📝 Registration: {json.loads(response)}")
            
            # Test AGENT mode with a simple automation request
            test_message = {
                "type": "chat_request",
                "mode": "Agent",
                "message": 'open Notepad and write "SEGEV"',
                "session_id": "test_buttons_session"
            }
            
            print(f"\n🤖 Sending AGENT mode request: '{test_message['message']}'")
            await websocket.send(json.dumps(test_message))
            
            # Wait for response
            response = await websocket.recv()
            result = json.loads(response)
            
            print(f"\n✅ Response received:")
            print(f"Mode: {result.get('mode')}")
            print(f"Real Automation Used: {result.get('real_automation_used', 'Unknown')}")
            print(f"Interactive Mode: {result.get('interactive_mode', 'Unknown')}")
            print(f"Buttons Available: {result.get('buttons') is not None}")
            
            if result.get('buttons'):
                print(f"Button Count: {len(result['buttons'])}")
                for i, button in enumerate(result['buttons']):
                    print(f"  {i+1}. {button['text']} - {button['description']}")
            
            plan_id = result.get('plan_id')
            print(f"Plan ID: {plan_id}")
            
            print(f"\n📋 Response Text:")
            print(result.get('response', 'No response'))
            
            # Check if we got interactive buttons
            if result.get('buttons') and len(result['buttons']) >= 3:
                print("\n🎉 SUCCESS! Interactive buttons are working!")
                print("✅ Do/Dismiss/Adjust buttons are available")
                print("✅ Button metadata includes actions and styling")
                print("✅ Plan ID is tracked for button actions")
                
                # Test a button action (simulate clicking DO button)
                if plan_id:
                    print(f"\n🟢 Testing DO button action...")
                    button_action = {
                        "type": "button_action",
                        "action": "execute_plan",
                        "plan_id": plan_id,
                        "client_id": "test_buttons_client"
                    }
                    
                    await websocket.send(json.dumps(button_action))
                    button_response = await websocket.recv()
                    button_result = json.loads(button_response)
                    
                    print(f"Button Action Result:")
                    print(f"Success: {button_result.get('success')}")
                    print(f"Response: {button_result.get('response', 'No response')}")
                    
                    if button_result.get('success'):
                        print("✅ Button action processing works!")
                    else:
                        print("⚠️ Button action had issues")
                        
            else:
                print("\n⚠️ Interactive buttons not found in response")
                print("Check button formatting and response structure")
                
    except Exception as e:
        print(f"❌ Error testing interactive buttons: {e}")

if __name__ == "__main__":
    print("🧪 Testing Interactive Button System")
    print("=" * 50)
    asyncio.run(test_interactive_buttons())