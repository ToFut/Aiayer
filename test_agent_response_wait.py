#!/usr/bin/env python3
"""
Test script that waits for the actual agent response
"""
import asyncio
import websockets
import json

async def test_agent_response_wait():
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
            
            # Get registration response
            reg_response = await websocket.recv()
            print(f"📥 Registration: {json.loads(reg_response).get('type')}")
            
            # Send agent request
            test_msg = {
                "type": "agent_request",
                "message": "What are the benefits of AI in business?"
            }
            
            print(f"\n📤 Sending agent request: {test_msg['message']}")
            await websocket.send(json.dumps(test_msg))
            
            # Wait for agent response
            print("⏳ Waiting for agent response...")
            agent_response = await websocket.recv()
            
            print(f"\n📥 Agent response received:")
            response_data = json.loads(agent_response)
            print(f"Type: {response_data.get('type')}")
            print(f"Mode: {response_data.get('mode')}")
            print(f"Success: {response_data.get('success')}")
            
            if 'response' in response_data:
                print(f"AI Response: {response_data['response']}")
                
                # Check if it's real AI (not template)
                response_text = response_data['response']
                if 'Professional agent mode response for:' in response_text:
                    print("❌ Still getting template responses!")
                else:
                    print("✅ Getting real AI responses!")
            else:
                print("❌ No 'response' field found")
                print(f"Available fields: {list(response_data.keys())}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_agent_response_wait())