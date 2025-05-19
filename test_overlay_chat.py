#!/usr/bin/env python3
import asyncio
import websockets
import json
import time
from datetime import datetime

async def test_overlay_chat():
    """
    Test the overlay chat interface by simulating a client connecting,
    sending a message, and receiving an LLM response.
    """
    print("Connecting to WebSocket server at ws://localhost:8765...")
    
    async with websockets.connect("ws://localhost:8765") as websocket:
        # Send connection message
        await websocket.send(json.dumps({
            "type": "connection_established",
            "payload": {
                "client": "test_overlay_chat",
                "version": "1.0.0"
            }
        }))
        
        # Wait for server response
        response = await websocket.recv()
        print(f"Server response: {response}\n")
        
        # Simulate user typing in chat interface
        print("Simulating user sending a message...")
        user_message = "Tell me about the capabilities of this AI assistant system"
        
        # Send LLM request (like the overlay would)
        await websocket.send(json.dumps({
            "type": "llm_request",
            "payload": {
                "query": user_message,
                "timestamp": datetime.now().isoformat()
            }
        }))
        
        print(f"Sent message: '{user_message}'")
        print("\nWaiting for LLM response (may take up to 30 seconds)...")
        
        # Wait for response with timeout
        try:
            start_time = time.time()
            response = await asyncio.wait_for(websocket.recv(), timeout=30)
            
            # Process response
            data = json.loads(response)
            
            if data.get("type") == "llm_response":
                print("\n✅ Received LLM response successfully!")
                print(f"Time taken: {time.time() - start_time:.2f} seconds")
                
                payload = data.get("payload", {})
                model = payload.get("model", "unknown")
                response_text = payload.get("response", "No response received")
                
                print(f"\nModel: {model}")
                print(f"Response:\n{response_text}")
                
                # Check if the response seems like a real LLM response
                if len(response_text) > 50 and "error" not in response_text.lower():
                    print("\n✅ The overlay chat integration with LLM is working correctly")
                    return True
                else:
                    print("\n⚠️ Response seems too short or contains errors")
                    return False
            else:
                print(f"\n⚠️ Unexpected response type: {data.get('type')}")
                return False
                
        except asyncio.TimeoutError:
            print("\n❌ Timeout waiting for LLM response")
            return False
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return False

if __name__ == "__main__":
    result = asyncio.run(test_overlay_chat())
    print("\nTest result:", "Success" if result else "Failed")