#!/usr/bin/env python3
"""
Simple script to check if the Aiayer backend is running on port 8767
"""

import asyncio
import json
import websockets
import sys

async def check_backend_status(url="ws://localhost:8767"):
    """Try to connect to the backend and verify it's responding"""
    print(f"Checking backend status at {url}...")
    try:
        # Try to connect with a 5 second timeout
        websocket = await asyncio.wait_for(websockets.connect(url), timeout=5)
        
        # Wait for the connection established message
        response = await asyncio.wait_for(websocket.recv(), timeout=5)
        
        try:
            data = json.loads(response)
            if data.get("type") == "connection_established":
                client_id = data.get("client_id", "unknown")
                print(f"✅ Backend is RUNNING - Connected with client ID: {client_id}")
                
                # Send a simple ping to verify communication
                ping = {"type": "ping"}
                await websocket.send(json.dumps(ping))
                
                # Close the connection
                await websocket.close()
                return True
            else:
                print(f"⚠️ Backend responded with unexpected message type: {data.get('type', 'unknown')}")
                return False
        except json.JSONDecodeError:
            print(f"⚠️ Backend responded with invalid JSON: {response[:100]}...")
            return False
    
    except asyncio.TimeoutError:
        print("❌ Connection timed out - Backend may be running but not responding")
        return False
    except ConnectionRefusedError:
        print("❌ Connection refused - Backend is NOT running")
        return False
    except Exception as e:
        print(f"❌ Error checking backend: {e}")
        return False

async def main():
    """Main function"""
    url = "ws://localhost:8767"
    
    # Allow URL override from command line
    if len(sys.argv) > 1:
        url = sys.argv[1]
    
    result = await check_backend_status(url)
    
    # Exit with appropriate status code
    sys.exit(0 if result else 1)

if __name__ == "__main__":
    asyncio.run(main())