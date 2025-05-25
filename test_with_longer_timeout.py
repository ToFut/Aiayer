#!/usr/bin/env python3
"""
Test with longer timeout to see if completion eventually comes
"""

import asyncio
import websockets
import json
from datetime import datetime

async def test_completion():
    print("Testing with longer timeout...")
    
    try:
        async with websockets.connect("ws://localhost:8767") as websocket:
            # Wait for connection
            connection_msg = await websocket.recv()
            print("Connected to backend")
            
            # Send request
            request = {
                "type": "chat_request",
                "mode": "ask",
                "message": "What is 2+2?",
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send(json.dumps(request))
            print("Request sent, waiting up to 2 minutes...")
            
            # Wait for responses with longer timeout
            response_count = 0
            while response_count < 50:  # Increase limit
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=120.0)  # 2 minutes
                    response_data = json.loads(response)
                    response_type = response_data.get("type")
                    response_count += 1
                    
                    print(f"Response {response_count}: {response_type}")
                    
                    if response_type == "chat_response_chunk":
                        chunk = response_data.get("chunk", "")
                        print(f"  Chunk: '{chunk}'")
                    elif response_type == "chat_response_complete":
                        full_response = response_data.get("full_response", "")
                        print(f"  ✅ COMPLETE: {full_response}")
                        return True
                    elif response_type == "chat_response_error":
                        error = response_data.get("error", "Unknown error")
                        print(f"  ❌ ERROR: {error}")
                        return False
                        
                except asyncio.TimeoutError:
                    print("  ⏱️ Final timeout after 2 minutes")
                    break
            
            print("❌ No completion after 50 responses")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_completion())