#!/usr/bin/env python3
"""
Simple test for Agent Mode - just print all responses
"""
import asyncio
import websockets
import json

async def test_agent():
    uri = "ws://localhost:8767"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to backend")
            
            # Send Agent mode message
            message = {
                "type": "chat_message",
                "data": {
                    "message": "open Safari",
                    "mode": "agent",
                    "session_id": "test_123"
                }
            }
            
            print(f"📤 Sending: {message}")
            await websocket.send(json.dumps(message))
            
            # Wait for ALL responses for 10 seconds
            import time
            start_time = time.time()
            response_count = 0
            
            while time.time() - start_time < 10:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    response_count += 1
                    response_data = json.loads(response)
                    print(f"📥 Response {response_count}: {response_data.get('type', 'unknown')}")
                    
                    if response_data.get('type') == 'streaming_response':
                        print(f"   ✅ FOUND AGENT RESPONSE!")
                        print(f"   📝 Text: {response_data.get('data', {}).get('response', 'No text')}")
                        buttons = response_data.get('data', {}).get('buttons', [])
                        print(f"   🔘 Buttons: {len(buttons)} found")
                        for i, btn in enumerate(buttons):
                            print(f"      {i+1}. {btn.get('text', 'No text')}")
                        break
                    elif response_data.get('type') == 'error':
                        print(f"   ❌ ERROR: {response_data.get('error', response_data.get('message', 'Unknown'))}")
                        break
                    else:
                        print(f"   📄 Data: {str(response_data)[:200]}...")
                        
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"   ⚠️ Parse error: {e}")
                    break
            
            print(f"📊 Total responses received: {response_count}")
                
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_agent())