#!/usr/bin/env python3
"""
Test script to verify the hotkey execution fix
"""

import asyncio
import websockets
import json

async def test_hotkey_execution():
    """Test the fixed hotkey execution with a simple agent request"""
    uri = "ws://localhost:8767"
    
    try:
        async with websockets.connect(uri) as websocket:
            # Register as client
            register_msg = {
                "type": "register",
                "client_type": "test_client",
                "client_id": "test_hotkey_fix"
            }
            await websocket.send(json.dumps(register_msg))
            response = await websocket.recv()
            print(f"Registration: {response}")
            
            # Send agent mode request
            agent_request = {
                "type": "chat_request",
                "message": "open calculator",
                "mode": "agent"
            }
            await websocket.send(json.dumps(agent_request))
            print("🤖 Sent agent request: 'open calculator'")
            
            # Wait for response
            response = await websocket.recv()
            print(f"Response: {response}")
            
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_hotkey_execution())