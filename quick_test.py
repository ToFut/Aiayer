#!/usr/bin/env python3
import asyncio
import websockets
import json

async def quick_test():
    try:
        async with websockets.connect("ws://localhost:8767") as websocket:
            # Wait for connection
            connection_msg = await websocket.recv()
            print("Connected")
            
            # Send simple request
            request = {
                "type": "chat_request",
                "mode": "ask",
                "message": "What is 1+1?",
                "timestamp": "2025-05-23T15:58:00.000Z"
            }
            
            await websocket.send(json.dumps(request))
            print("Request sent")
            
            # Collect all responses
            response_count = 0
            full_text = ""
            
            while response_count < 30:  # Limit to prevent infinite loop
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    response_data = json.loads(response)
                    response_type = response_data.get("type")
                    response_count += 1
                    
                    if response_type == "chat_response_chunk":
                        chunk = response_data.get("chunk", "")
                        full_text += chunk
                        print(chunk, end="", flush=True)
                    elif response_type == "chat_response_complete":
                        final_response = response_data.get("full_response", "")
                        print(f"\n\n✅ COMPLETED: {final_response}")
                        return True
                        
                except asyncio.TimeoutError:
                    print(f"\n\n⏱️ Timeout after {response_count} responses")
                    print(f"Collected text: {full_text}")
                    return False
            
            print(f"\n\n⚠️ Hit response limit")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(quick_test())
    print(f"Result: {result}")