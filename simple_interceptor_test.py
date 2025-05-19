#!/usr/bin/env python3
"""
Simple test for the WebSocket interceptor service
"""
import asyncio
import websockets
import json
import sys

async def test_llm_request():
    """Simple direct test of the LLM request functionality"""
    url = "ws://localhost:8766"
    print(f"Connecting to {url}...")
    
    try:
        # Create a connection without automatic context management
        ws = await websockets.connect(url, ping_interval=None)
        success = False
        
        try:
            print("Connected successfully!")
            
            # Wait for the initial connection message
            try:
                init_response = await asyncio.wait_for(ws.recv(), timeout=3.0)
                print(f"Initial message: {init_response}")
            except asyncio.TimeoutError:
                print("No initial connection message received")
                
            # Send the LLM request
            request = {
                "type": "llm_request",
                "payload": {
                    "query": "What is the capital of France?",
                    "model": "llama3.2:latest",
                    "context": {
                        "window": "Test Window",
                        "active_apps": ["Test App"]
                    }
                }
            }
            
            print("\nSending LLM request...")
            await ws.send(json.dumps(request))
            
            # Try to receive multiple messages
            print("Waiting for responses...")
            
            # Keep receiving messages for a limited time
            start_time = asyncio.get_event_loop().time()
            while asyncio.get_event_loop().time() - start_time < 10.0:  # Try for 10 seconds
                try:
                    remaining = 10.0 - (asyncio.get_event_loop().time() - start_time)
                    response = await asyncio.wait_for(ws.recv(), timeout=remaining)
                    print(f"\nReceived: {response}")
                    
                    # Try parsing to see if this is an LLM response
                    try:
                        data = json.loads(response)
                        if data.get("type") == "query_response":
                            print("Found LLM response!")
                            print(f"Answer: {data.get('payload', {}).get('response', 'No content')[:100]}...")
                            success = True
                            break
                        
                        if "response" in str(data):
                            print("Response-like message found!")
                            print(f"Message data: {json.dumps(data, indent=2)}")
                    except:
                        pass
                        
                except asyncio.TimeoutError:
                    print("No more messages received")
                    break
                except Exception as e:
                    print(f"Error receiving message: {e}")
                    break
            
            return success
        finally:
            await ws.close()
    except Exception as e:
        print(f"Error during test: {e}")
        return False

if __name__ == "__main__":
    if asyncio.run(test_llm_request()):
        print("\nTest succeeded!")
        sys.exit(0)
    else:
        print("\nTest failed!")
        sys.exit(1)