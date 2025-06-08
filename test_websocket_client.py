#!/usr/bin/env python3
import asyncio
import websockets
import json
import sys

async def test_websocket_connection(url):
    """Test WebSocket connection and receive messages."""
    print(f"Connecting to {url}...")
    try:
        async with websockets.connect(url, ping_timeout=10) as ws:
            print(f"Connected to {url}")
            
            # Send identification message
            await ws.send(json.dumps({
                "type": "connection_established",
                "payload": {
                    "client": "test_client",
                    "version": "1.0.0"
                }
            }))
            print(f"Sent identification message")
            
            # Wait for initial responses
            for _ in range(3):
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    print(f"Received: {response[:200]}...")
                except asyncio.TimeoutError:
                    print("Timeout waiting for response")
                    break
            
            # Send a test message
            test_message = {
                "type": "test_message",
                "payload": {
                    "message": "Hello from test client"
                }
            }
            await ws.send(json.dumps(test_message))
            print(f"Sent test message")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                print(f"Received response: {response[:200]}...")
            except asyncio.TimeoutError:
                print("Timeout waiting for response to test message")
            
            return True
    except Exception as e:
        print(f"Error connecting to {url}: {e}")
        return False

async def main():
    """Test connections to all relevant WebSocket servers."""
    servers = [
        "ws://localhost:8765",  # DO button server
        "ws://localhost:8766",  # Expected in config.js
        "ws://localhost:8767",  # Running backend server
        "ws://localhost:8768",  # Bridge server
    ]
    
    results = {}
    
    for server in servers:
        print(f"\n=== Testing {server} ===")
        result = await test_websocket_connection(server)
        results[server] = result
    
    print("\n=== Summary ===")
    for server, result in results.items():
        status = "✅ CONNECTED" if result else "❌ FAILED"
        print(f"{server}: {status}")

if __name__ == "__main__":
    asyncio.run(main())