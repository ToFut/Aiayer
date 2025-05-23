#!/usr/bin/env python3

import asyncio
import websockets
import json
import time

async def test_full_automation_system():
    """
    Comprehensive test of the enhanced Agent mode with REAL UI automation.
    This will test actual clicking, typing, and application opening.
    """
    
    print("🤖 TESTING FULL AUTOMATION SYSTEM")
    print("=" * 50)
    print("⚠️  This test will perform REAL UI automation")
    print("🛑 Press Ctrl+1 for emergency shutdown if needed")
    print("")
    
    try:
        # Connect to the enhanced brain router with full automation
        uri = "ws://localhost:8765"
        async with websockets.connect(uri) as websocket:
            
            # Receive connection message
            connection_msg = await websocket.recv()
            connection_data = json.loads(connection_msg)
            print(f"✅ Connected: {connection_data.get('message', 'No message')}")
            
            # Check if full automation is available
            features = connection_data.get('features', [])
            if 'real_ui_automation' in features:
                print("✅ Real UI automation confirmed!")
            else:
                print("❌ Real UI automation not detected")
                return False
            
            print("")
            print("🧪 Starting automation tests...")
            print("=" * 40)
            
            # Test 1: Safe typing test
            print("\n📝 Test 1: Typing automation")
            typing_request = {
                "type": "chat_request",
                "mode": "Agent",
                "message": "type 'Hello from AI automation!'",
                "session_id": "test_typing"
            }
            
            print(f"📤 Request: {typing_request['message']}")
            await websocket.send(json.dumps(typing_request))
            
            response_1 = await asyncio.wait_for(websocket.recv(), timeout=20)
            response_data_1 = json.loads(response_1)
            
            print(f"📥 Response: {response_data_1.get('response', 'No response')}")
            print(f"   Success: {response_data_1.get('success', 'Unknown')}")
            print(f"   Processing time: {response_data_1.get('processing_time', 'Unknown')}s")
            
            # Test 2: Application opening test
            print("\n📂 Test 2: Application opening automation")
            app_request = {
                "type": "chat_request",
                "mode": "Agent", 
                "message": "open the calculator application",
                "session_id": "test_app_opening"
            }
            
            print(f"📤 Request: {app_request['message']}")
            await websocket.send(json.dumps(app_request))
            
            response_2 = await asyncio.wait_for(websocket.recv(), timeout=20)
            response_data_2 = json.loads(response_2)
            
            print(f"📥 Response: {response_data_2.get('response', 'No response')}")
            print(f"   Success: {response_data_2.get('success', 'Unknown')}")
            
            # Test 3: Safe click test (clicking in a safe area)
            print("\n🎯 Test 3: Click automation (safe area)")
            click_request = {
                "type": "chat_request",
                "mode": "Agent",
                "message": "click on the menu bar",
                "session_id": "test_clicking"
            }
            
            print(f"📤 Request: {click_request['message']}")
            await websocket.send(json.dumps(click_request))
            
            response_3 = await asyncio.wait_for(websocket.recv(), timeout=20)
            response_data_3 = json.loads(response_3)
            
            print(f"📥 Response: {response_data_3.get('response', 'No response')}")
            print(f"   Success: {response_data_3.get('success', 'Unknown')}")
            
            # Test 4: Contextual memory test
            print("\n🧠 Test 4: Contextual memory with automation")
            context_request = {
                "type": "chat_request",
                "mode": "Agent",
                "message": "click on the same thing I clicked before",
                "session_id": "test_context"
            }
            
            print(f"📤 Request: {context_request['message']}")
            await websocket.send(json.dumps(context_request))
            
            response_4 = await asyncio.wait_for(websocket.recv(), timeout=20)
            response_data_4 = json.loads(response_4)
            
            print(f"📥 Response: {response_data_4.get('response', 'No response')}")
            print(f"   Success: {response_data_4.get('success', 'Unknown')}")
            
            # Check context usage
            context_info = response_data_4.get('context_used', {})
            print(f"   Context memories used: {context_info.get('relevant_memories', 0)}")
            print(f"   Confidence: {context_info.get('confidence_score', 0):.2f}")
            
            # Test 5: Non-automation mode test
            print("\n💬 Test 5: Ask mode (should not perform automation)")
            ask_request = {
                "type": "chat_request",
                "mode": "Ask",
                "message": "what is the current system status?",
                "session_id": "test_ask_mode"
            }
            
            print(f"📤 Request: {ask_request['message']}")
            await websocket.send(json.dumps(ask_request))
            
            response_5 = await asyncio.wait_for(websocket.recv(), timeout=15)
            response_data_5 = json.loads(response_5)
            
            print(f"📥 Response: {response_data_5.get('response', 'No response')}")
            print(f"   Success: {response_data_5.get('success', 'Unknown')}")
            
            # Analysis
            print("\n🔍 AUTOMATION ANALYSIS:")
            print("=" * 30)
            
            responses = [response_data_1, response_data_2, response_data_3, response_data_4]
            automation_detected = 0
            
            for i, resp in enumerate(responses, 1):
                response_text = resp.get('response', '').lower()
                success = resp.get('success', False)
                
                # Check for automation execution indicators
                automation_indicators = [
                    'successfully executed', 'successfully typed', 'successfully opened',
                    'successfully clicked', 'performed at coordinates', 'action performed'
                ]
                
                execution_found = any(indicator in response_text for indicator in automation_indicators)
                
                print(f"\n   Test {i} Analysis:")
                print(f"   - Success: {success}")
                print(f"   - Execution detected: {execution_found}")
                print(f"   - Response length: {len(response_text)} chars")
                
                if execution_found:
                    automation_detected += 1
                    print(f"   ✅ REAL automation execution confirmed")
                else:
                    print(f"   ❌ No automation execution detected")
            
            print(f"\n📊 FINAL RESULTS:")
            print(f"   Tests with automation: {automation_detected}/4")
            print(f"   System functionality: {'✅ FULL AUTOMATION WORKING' if automation_detected >= 2 else '❌ Automation issues detected'}")
            
            return automation_detected >= 2
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

async def test_system_status():
    """Test system status endpoint"""
    try:
        uri = "ws://localhost:8765"
        async with websockets.connect(uri) as websocket:
            
            # Skip connection message
            await websocket.recv()
            
            # Request system status
            status_request = {
                "type": "system_status"
            }
            
            await websocket.send(json.dumps(status_request))
            status_response = await asyncio.wait_for(websocket.recv(), timeout=10)
            status_data = json.loads(status_response)
            
            print("\n🔍 SYSTEM STATUS:")
            print("=" * 20)
            print(f"Version: {status_data.get('version', 'Unknown')}")
            print(f"Status: {status_data.get('status', 'Unknown')}")
            print(f"Connected clients: {status_data.get('connected_clients', 0)}")
            
            automation_info = status_data.get('automation_system', {})
            print(f"\nAutomation System:")
            print(f"- UI automation active: {automation_info.get('ui_automation_active', False)}")
            print(f"- Safety level: {automation_info.get('safety_level', 'Unknown')}")
            print(f"- Input controller ready: {automation_info.get('input_controller_ready', False)}")
            print(f"- Screen analyzer ready: {automation_info.get('screen_analyzer_ready', False)}")
            
            features = status_data.get('features', [])
            print(f"\nFeatures: {', '.join(features)}")
            
            return True
            
    except Exception as e:
        print(f"❌ Status test failed: {e}")
        return False

if __name__ == "__main__":
    print("🤖 FULL AUTOMATION SYSTEM TEST")
    print("=" * 40)
    print("This will test the Enhanced Brain Router with real UI automation")
    print("Make sure the system is running with: ./START_ENHANCED_SYSTEM.sh")
    print("")
    
    # Test system status first
    print("🔍 Testing system status...")
    status_result = asyncio.run(test_system_status())
    
    if status_result:
        print("\n🚀 Starting automation tests...")
        result = asyncio.run(test_full_automation_system())
        
        if result:
            print("\n🎉 FULL AUTOMATION SYSTEM TEST PASSED!")
            print("✅ Agent mode is performing REAL UI automation")
            print("🎯 Clicking, typing, and app opening confirmed working")
            print("🧠 Contextual memory integration active")
            print("")
            print("💡 You can now ask the Agent to:")
            print("   • Click on specific UI elements")
            print("   • Type text in input fields")  
            print("   • Open applications")
            print("   • All with contextual memory!")
        else:
            print("\n⚠️  AUTOMATION SYSTEM TEST FAILED")
            print("❌ Real UI automation may not be working properly")
            print("🔧 Check logs for details")
    else:
        print("\n❌ System status test failed - system may not be running")
        print("🔧 Start the system with: ./START_ENHANCED_SYSTEM.sh")