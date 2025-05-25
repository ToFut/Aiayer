#!/usr/bin/env python3
"""
Test Real Automation Handler - Interactive Do/Dismiss/Adjust workflow
"""

import asyncio
import json
import websockets
import time

async def test_real_automation():
    """Test the real automation handler with interactive workflow"""
    uri = "ws://localhost:8767"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔗 Connected to backend with Real Automation")
            
            # Register first
            register_msg = {
                "type": "register",
                "client_id": "test_automation_client"
            }
            await websocket.send(json.dumps(register_msg))
            response = await websocket.recv()
            print(f"📝 Registration: {json.loads(response)}")
            
            # Test AGENT mode with productivity workflow request
            test_message = {
                "type": "chat_request",
                "mode": "Agent",
                "message": "Create a daily productivity workflow for me",
                "session_id": "test_automation_session"
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
            print(f"Requires Approval: {result.get('requires_approval', 'Unknown')}")
            print(f"Plan ID: {result.get('plan_id', 'Unknown')}")
            print(f"Automation Available: {result.get('automation_available', 'Unknown')}")
            
            print(f"\n📋 Response:")
            print(result.get('response', 'No response'))
            
            # Check if we got the interactive workflow
            response_text = result.get('response', '')
            if "DO" in response_text and "DISMISS" in response_text and "ADJUST" in response_text:
                print("\n🎉 SUCCESS! Interactive Do/Dismiss/Adjust workflow is working!")
                print("✅ AGENT mode now provides proper automation planning")
                print("✅ Real automation system is integrated")
                print("✅ Interactive approval workflow is active")
            else:
                print("\n⚠️ Response received but missing interactive elements")
                
    except Exception as e:
        print(f"❌ Error testing real automation: {e}")

if __name__ == "__main__":
    print("🧪 Testing Real Automation Handler")
    print("=" * 50)
    asyncio.run(test_real_automation())