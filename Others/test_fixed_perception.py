#!/usr/bin/env python3
"""
Test the fixed perception query handler
This script tests the simplified agent with perception query handling
"""
import asyncio
import websockets
import json
from datetime import datetime

# Read WebSocket port from file
with open('ws_port.txt', 'r') as f:
    WS_PORT = int(f.read().strip())

# WebSocket server URL
WS_URL = f"ws://localhost:{WS_PORT}"

async def test_perception_query():
    # Connect to WebSocket server
    async with websockets.connect(WS_URL) as websocket:
        # Skip welcome message
        await websocket.recv()
        
        # Send connection message
        await websocket.send(json.dumps({
            "type": "connection_established",
            "payload": {
                "client": "test",
                "version": "1.0.0",
                "timestamp": datetime.now().isoformat()
            }
        }))
        
        # Receive server ready message
        await websocket.recv()
        
        # Request context
        await websocket.send(json.dumps({
            "type": "context_request",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Receive context update
        context_response = await websocket.recv()
        context_data = json.loads(context_response)
        
        print("Context Response:")
        if "payload" in context_data and "context" in context_data["payload"]:
            context = context_data["payload"]["context"]
            print(f"  Window: {context.get('window', 'Unknown')}")
            print(f"  Active apps: {context.get('active_apps', [])}")
            print(f"  Screen content length: {len(context.get('screen_content', ''))}")
        
        # Send perception query
        await websocket.send(json.dumps({
            "type": "user_message",
            "content": "what am I seeing?",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Receive response
        response = await websocket.recv()
        response_data = json.loads(response)
        
        print("\nPerception Query Response:")
        print(f"Response type: {response_data.get('type')}")
        print(f"Content: {response_data.get('content')}")
        
        if "payload" in response_data:
            payload = response_data["payload"]
            print(f"Model: {payload.get('model')}")
            print(f"Context used: {payload.get('context_used')}")
            print(f"Context keys: {payload.get('context_keys', [])}")

if __name__ == "__main__":
    asyncio.run(test_perception_query())