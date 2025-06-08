#!/usr/bin/env python3
"""
Direct test for brain router
"""
import asyncio
import websockets
import json
import sys

async def test_brain_router():
    """Send a test message directly to the brain router on port 8767"""
    try:
        uri = "ws://localhost:8767"
        print(f"Connecting to {uri}...")
        
        async with websockets.connect(uri) as ws:
            print("Connected")
            
            # Wait for welcome message
            welcome = await ws.recv()
            print(f"Welcome: {welcome[:100]}...")
            
            # Register
            register_msg = {
                "type": "register",
                "client_type": "test_client",
                "client_id": "test_direct",
                "capabilities": ["text"]
            }
            
            print("Registering...")
            await ws.send(json.dumps(register_msg))
            
            # Get registration response
            reg_response = await ws.recv()
            print(f"Registration: {reg_response[:100]}...")
            
            # Send chat request
            query = "Testing direct brain router connection"
            if len(sys.argv) > 1:
                query = " ".join(sys.argv[1:])
                
            chat_request = {
                "type": "chat_request",
                "message": query,
                "mode": "ask",
                "session_id": "test_session",
                "client_id": "test_direct"
            }
            
            print(f"Sending query: {query}")
            await ws.send(json.dumps(chat_request))
            
            # Wait for response (may take a moment)
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=20)
                print(f"Response: {response[:200]}...")
                
                # Check for more responses
                for _ in range(3):
                    try:
                        more = await asyncio.wait_for(ws.recv(), timeout=5)
                        print(f"Additional response: {more[:200]}...")
                    except asyncio.TimeoutError:
                        break
                
            except asyncio.TimeoutError:
                print("No response received after 20 seconds")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_brain_router())