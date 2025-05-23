#!/usr/bin/env python3
"""
Test script that properly reads messages in the correct order
"""
import asyncio
import websockets
import json

async def test_correct_order():
    uri = "ws://localhost:8765"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to enhanced enterprise backend")
            
            # First, get the connection established message
            conn_msg = await websocket.recv()
            conn_data = json.loads(conn_msg)
            print(f"📥 Connection: {conn_data.get('type')}")
            
            # Register
            register_msg = {
                "type": "register",
                "client_type": "test_client"
            }
            await websocket.send(json.dumps(register_msg))
            
            # Get registration response
            reg_response = await websocket.recv()
            reg_data = json.loads(reg_response)
            print(f"📥 Registration: {reg_data.get('type')}")
            
            # Send agent request
            test_msg = {
                "type": "agent_request", 
                "message": "What are the main benefits of using artificial intelligence in business?"
            }
            
            print(f"\n📤 Sending agent request...")
            await websocket.send(json.dumps(test_msg))
            
            # Now wait for the agent response (with proper timeout)
            print("⏳ Waiting for agent response (this may take ~10 seconds due to LLM processing)...")
            
            try:
                agent_response = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                
                print(f"\n📥 Agent response received!")
                response_data = json.loads(agent_response)
                
                print(f"Type: {response_data.get('type')}")
                print(f"Mode: {response_data.get('mode')}")
                print(f"Success: {response_data.get('success')}")
                
                if 'response' in response_data:
                    ai_response = response_data['response']
                    print(f"\n🧠 AI Response: {ai_response}")
                    
                    # Check if it's real AI (not template)
                    if 'Professional agent mode response for:' in ai_response:
                        print("\n❌ Still getting template responses!")
                    else:
                        print("\n✅ SUCCESS! Getting real AI responses!")
                        print("\n🎉 The enhanced enterprise backend is now providing intelligent AI responses!")
                        
                    print(f"\nSession ID: {response_data.get('session_id')}")
                    print(f"Validation Confidence: {response_data.get('validation_confidence')}")
                    
                    if response_data.get('goal_analysis'):
                        print(f"Goal Analysis: {response_data['goal_analysis'].get('clarified_goal')}")
                        
                else:
                    print("❌ No 'response' field found")
                    print(f"Available fields: {list(response_data.keys())}")
                    
            except asyncio.TimeoutError:
                print("⏰ Timeout waiting for agent response")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_correct_order())