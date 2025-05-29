#!/usr/bin/env python3
"""
Quick test for Enhanced Automation Handler
"""

import asyncio
import json
import websockets
import time

async def test_enhanced_automation():
    """Test if Enhanced automation handler is working"""
    
    print("🧪 Testing Enhanced Automation Handler...")
    
    try:
        # Connect to backend
        websocket = await websockets.connect("ws://localhost:8767")
        print("✅ Connected to backend")
        
        # Send a simple agent request
        message = {
            "type": "chat_request",
            "message": "Click on the search button",
            "session_id": f"test_{int(time.time())}",
            "mode": "agent"
        }
        
        print(f"📤 Sending message: {message['message']}")
        await websocket.send(json.dumps(message))
        
        # Wait for connection established message first
        connection_response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
        print(f"📡 Connection: {json.loads(connection_response).get('type')}")
        
        # Wait for actual response
        response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
        response_data = json.loads(response)
        
        print(f"📥 Response type: {response_data.get('type')}")
        print(f"📥 Success: {response_data.get('success')}")
        
        # Check for automation plan
        if "plan" in response_data:
            plan = response_data["plan"]
            print(f"✅ Plan found: {plan.get('title', 'No title')}")
            print(f"📊 Steps: {len(plan.get('steps', []))}")
            if plan.get('coordinates'):
                print(f"📍 Coordinates: {plan['coordinates']}")
        elif "executionPlan" in response_data:
            exec_plan = response_data["executionPlan"]
            print(f"✅ Execution plan found")
            print(f"📊 Total steps: {exec_plan.get('total_steps', 0)}")
            print(f"📊 Steps array: {len(exec_plan.get('steps', []))}")
            if exec_plan.get('coordinates'):
                print(f"📍 Coordinates: {exec_plan['coordinates']}")
        else:
            print("⚠️  No automation plan found in response")
            print(f"📄 Response keys: {list(response_data.keys())}")
        
        await websocket.close()
        print("✅ Test completed")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_enhanced_automation())