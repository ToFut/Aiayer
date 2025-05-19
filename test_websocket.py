#!/usr/bin/env python3
"""
Test WebSocket connection to both ports 8765 and 8767
"""
import asyncio
import websockets
import json
import sys

async def test_connection(url):
    """Test connection to a WebSocket server"""
    print(f"Trying to connect to {url}...")
    try:
        async with websockets.connect(url, ping_interval=None) as ws:
            print(f"Connected to {url} successfully!")
            
            # Send a test message
            test_message = {
                "type": "test",
                "payload": {
                    "message": "Hello from test client",
                    "timestamp": 12345678
                }
            }
            await ws.send(json.dumps(test_message))
            print(f"Sent test message to {url}")
            
            # Wait for response with 5 second timeout
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                print(f"Received response from {url}: {response}")
                return True
            except asyncio.TimeoutError:
                print(f"No response received from {url} within timeout")
                return False
                
    except (ConnectionRefusedError, websockets.exceptions.WebSocketException) as e:
        print(f"Failed to connect to {url}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error connecting to {url}: {e}")
        return False

async def main():
    """Test both WebSocket servers"""
    urls = [
        "ws://localhost:8765",
        "ws://localhost:8767"
    ]
    
    results = []
    for url in urls:
        result = await test_connection(url)
        results.append((url, result))
        print("-" * 50)
    
    # Print summary
    print("\nSummary:")
    for url, result in results:
        status = "✅ WORKING" if result else "❌ NOT WORKING"
        print(f"{url}: {status}")
    
    # Exit with appropriate code
    if any(result for _, result in results):
        return 0  # At least one server working
    else:
        return 1  # All servers failed

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))