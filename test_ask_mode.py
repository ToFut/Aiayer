#\!/usr/bin/env python3
"""
Test Ask Mode
Simple script to test the Ask mode functionality
"""

import asyncio
import json
import websockets
import time

async def test_ask_mode():
    """Test Ask mode functionality"""
    print("Testing Ask mode...")
    
    try:
        # Connect to WebSocket server
        async with websockets.connect('ws://localhost:8767') as websocket:
            # Register with server
            await websocket.send(json.dumps({
                "type": "register",
                "client_type": "test_client"
            }))
            
            # Wait for registration response
            response = await websocket.recv()
            print(f"Registration response: {json.loads(response)['type']}")
            
            # Send chat request
            await websocket.send(json.dumps({
                "type": "chat_request",
                "mode": "Ask",
                "message": "What applications are running on my computer?",
                "session_id": f"test_session_{int(time.time())}",
                "client_id": f"test_client_{int(time.time())}"
            }))
            
            print("Request sent, waiting for response...")
            
            # Wait for responses until we get a final_response
            timeout = 60  # 60 seconds total timeout
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    response_data = json.loads(response)
                    
                    print(f"\nResponse received: {response_data.get('type', 'unknown')}")
                    
                    # If we got the final response, we're done
                    if response_data.get('type') == 'final_response':
                        print(f"Mode: {response_data.get('mode', 'unknown')}")
                        print(f"AI powered: {response_data.get('ai_powered', False)}")
                        print(f"Brain router used: {response_data.get('brain_router_used', False)}")
                        
                        # Show the actual response
                        print("\nResponse content:")
                        print(f"{response_data.get('response', 'No response content')}")
                        return True
                        
                except asyncio.TimeoutError:
                    print("No response received in the last 10 seconds, still waiting...")
            
            print("Error: Total timeout reached")
            return False
                
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(test_ask_mode())
