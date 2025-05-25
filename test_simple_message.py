#!/usr/bin/env python3
"""
Simple test to see what response we get from the backend
"""

import asyncio
import websockets
import json
from datetime import datetime

async def test_simple_message():
    print("Testing simple message to backend...")
    
    try:
        async with websockets.connect("ws://localhost:8767") as websocket:
            # Wait for connection
            connection_msg = await websocket.recv()
            print(f"Connection: {json.loads(connection_msg)}")
            
            # Send simple ask request
            request = {
                "type": "chat_request",
                "mode": "ask",
                "message": "what am i seeing?",
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"Sending: {request}")
            await websocket.send(json.dumps(request))
            
            # Wait for response(s)
            response_count = 0
            while response_count < 5:  # Limit to prevent infinite loop
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    response_data = json.loads(response)
                    response_count += 1
                    
                    print(f"Response {response_count}: {response_data}")
                    
                    # Check if this is the final response
                    if response_data.get("type") in ["chat_response_complete", "chat_response", "error"]:
                        print(f"\nFinal response text: {response_data.get('response', response_data.get('full_response', 'NO RESPONSE'))}")
                        break
                        
                except asyncio.TimeoutError:
                    print("Timeout waiting for response")
                    break
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple_message())