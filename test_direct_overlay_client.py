#!/usr/bin/env python3
"""
Test client for direct overlay handler
"""
import asyncio
import websockets
import json
import sys

async def send_test_message():
    """Send a test message to the overlay handler"""
    try:
        uri = "ws://localhost:8766"
        print(f"Connecting to {uri}...")
        
        async with websockets.connect(uri) as ws:
            print("Connected")
            
            # Wait for welcome message
            welcome = await ws.recv()
            print(f"Welcome message: {welcome}")
            
            # Register
            registration = {
                "type": "register",
                "payload": {
                    "client_type": "test_client",
                    "client_id": "test_client",
                    "version": "1.0",
                    "capabilities": ["text"]
                }
            }
            print("Sending registration...")
            await ws.send(json.dumps(registration))
            
            # Wait for registration confirmation
            reg_response = await ws.recv()
            print(f"Registration response: {reg_response}")
            
            # Send test query
            query = "This is a test query"
            if len(sys.argv) > 1:
                query = " ".join(sys.argv[1:])
                
            test_query = {
                "type": "llm_request",
                "payload": {
                    "query": query,
                    "mode": "ask",
                    "session_id": "test_session",
                    "user_id": "test_user"
                }
            }
            print(f"Sending test query: {query}")
            await ws.send(json.dumps(test_query))
            
            # Wait for response
            response = await ws.recv()
            print(f"Response: {response}")
            
            print("Test completed successfully")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(send_test_message())
