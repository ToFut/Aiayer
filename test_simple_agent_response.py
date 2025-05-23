#!/usr/bin/env python3
"""
Simple test to see the actual response format from the enhanced enterprise backend
"""
import asyncio
import websockets
import json

async def test_simple_response():
    uri = "ws://localhost:8765"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to enhanced enterprise backend")
            
            # Register first
            register_msg = {
                "type": "register",
                "client_type": "test_client"
            }
            await websocket.send(json.dumps(register_msg))
            response = await websocket.recv()
            print(f"Registration: {response[:100]}...")
            
            # Test Agent mode
            test_msg = {
                "type": "agent_request",
                "message": "click on the Documents folder"
            }
            
            print(f"\n📤 Sending: {test_msg}")
            await websocket.send(json.dumps(test_msg))
            
            # Wait for response
            response = await websocket.recv()
            print(f"\n📥 Raw response:")
            print(response)
            
            # Parse and analyze
            try:
                response_data = json.loads(response)
                print(f"\n📊 Parsed response type: {response_data.get('type')}")
                print(f"Keys in response: {list(response_data.keys())}")
                
                if 'execution_plan' in response_data:
                    exec_plan = response_data['execution_plan']
                    print(f"Execution plan response: {exec_plan.get('response', 'No response in execution plan')}")
                
            except Exception as e:
                print(f"Error parsing response: {e}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple_response())