#!/usr/bin/env python3
"""
Test script for WebSocket server with memory system integration
"""
import asyncio
import websockets
import json
import sys

async def test_websocket():
    """Test the WebSocket server with memory integration"""
    try:
        # Connect to the WebSocket server
        uri = "ws://localhost:8765"
        print(f"Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            # Receive welcome message
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Connection established: {data}")
            
            # Send a test query
            print("\nSending test query...")
            test_query = {
                "type": "user_interaction",
                "payload": {
                    "type": "query",
                    "query": "Can you tell me about your memory system?"
                }
            }
            await websocket.send(json.dumps(test_query))
            
            # Receive response
            response = await websocket.recv()
            data = json.loads(response)
            print(f"\nResponse received: {data.get('type')}")
            if data.get('type') == 'query_response':
                print(f"\nQuery: {data.get('payload', {}).get('query')}")
                print(f"Response: {data.get('payload', {}).get('response')}")
                
                # Check if memory was used and which LLM was used
                memory_used = data.get('payload', {}).get('memory_used', False)
                advanced_llm = data.get('payload', {}).get('advanced_llm', False)
                print(f"Memory system used: {memory_used}")
                print(f"Advanced LLM used: {advanced_llm}")
            
            # Request status information
            print("\nRequesting status information...")
            status_request = {
                "type": "status_request"
            }
            await websocket.send(json.dumps(status_request))
            
            # Receive status
            response = await websocket.recv()
            data = json.loads(response)
            if data.get('type') == 'status_response':
                print(f"\nStatus: {json.dumps(data.get('payload', {}), indent=2)}")
            
            print("\nTest completed successfully!")
            
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Testing WebSocket server with memory integration...")
    result = asyncio.run(test_websocket())
    if not result:
        print("Test failed!")
        sys.exit(1)
    print("Test passed!")
    sys.exit(0)