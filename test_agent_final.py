#!/usr/bin/env python3
"""
Final test script that properly waits for the agent response
"""
import asyncio
import websockets
import json

async def test_agent_final():
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
                "message": "What are the main benefits of using artificial intelligence in business?"
            }
            
            print(f"\n📤 Sending agent request...")
            await websocket.send(json.dumps(test_msg))
            
            # Wait for agent response (with longer timeout since LLM takes ~8 seconds)
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
                        
                    print(f"\nSession ID: {response_data.get('session_id')}")
                    print(f"Validation Confidence: {response_data.get('validation_confidence')}")
                    
                else:
                    print("❌ No 'response' field found")
                    print(f"Available fields: {list(response_data.keys())}")
                    
            except asyncio.TimeoutError:
                print("⏰ Timeout waiting for agent response - this suggests the backend may have issues")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_agent_final())