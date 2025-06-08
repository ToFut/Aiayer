#!/usr/bin/env python3
"""
Simple test client for the Fixed Neural UI Detector WebSocket server
"""

import asyncio
import websockets
import json
import time

async def test_connection():
    """Test the Fixed Neural UI Detector WebSocket connection"""
    print("Connecting to Fixed Neural UI Detector WebSocket server on port 8768...")
    try:
        async with websockets.connect('ws://localhost:8768') as websocket:
            print("Connected to server!")
            
            # Receive welcome message
            response = await websocket.recv()
            print(f"Received: {response}")
            
            # Send ping message
            ping_msg = {"action": "ping"}
            print(f"Sending: {ping_msg}")
            await websocket.send(json.dumps(ping_msg))
            
            # Receive response
            response = await websocket.recv()
            print(f"Received: {response}")
            
            # Send a simple ping string (for basic testing)
            print("Sending simple ping...")
            await websocket.send("ping")
            
            # Receive response
            response = await websocket.recv()
            print(f"Received: {response}")
            
            print("Test completed successfully!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())