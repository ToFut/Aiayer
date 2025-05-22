#!/usr/bin/env python3
"""
Direct WebSocket Test for Perception Query
This script directly tests the WebSocket server with a perception query
"""
import asyncio
import json
import websockets
import time
from datetime import datetime

# WebSocket server URL
WS_URL = "ws://localhost:8765"

async def send_perception_query():
    """Send a perception query directly to the WebSocket server"""
    async with websockets.connect(WS_URL) as websocket:
        # Skip welcome message
        await websocket.recv()
        
        # Send connection message
        await websocket.send(json.dumps({
            "type": "connection_established",
            "payload": {
                "client": "direct_test",
                "version": "1.0",
                "timestamp": datetime.now().isoformat()
            }
        }))
        
        # Skip ready message
        await websocket.recv()
        
        # Wait a moment
        await asyncio.sleep(1)
        
        # Send perception query
        query_message = {
            "type": "user_message",
            "content": "what am I seeing?",
            "timestamp": datetime.now().isoformat()
        }
        print(f"Sending: {json.dumps(query_message)}")
        await websocket.send(json.dumps(query_message))
        
        # Receive response
        response = await websocket.recv()
        response_data = json.loads(response)
        print(f"\nReceived response type: {response_data.get('type')}")
        print(f"Content: {response_data.get('content')}")
        
        if "payload" in response_data:
            payload = response_data["payload"]
            if "response" in payload:
                print(f"\nFull response: {payload['response']}")
                if "context_used" in payload:
                    print(f"Context used: {payload['context_used']}")
                if "context_keys" in payload:
                    print(f"Context keys: {payload['context_keys']}")

asyncio.run(send_perception_query())