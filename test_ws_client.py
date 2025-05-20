#!/usr/bin/env python3
"""
Test WebSocket Client
Tests connecting to WebSocket server using different hostnames/IPs
"""
import asyncio
import websockets
import json
import logging
import os
import sys
from datetime import datetime

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_ws_client.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('test_ws_client')

async def test_connection(url):
    """Test connection to WebSocket server"""
    logger.info(f"Trying to connect to {url}")
    print(f"Connecting to {url}...")
    
    try:
        async with websockets.connect(url, ping_interval=None, close_timeout=5) as websocket:
            logger.info(f"Successfully connected to {url}")
            print(f"✅ Connected to {url}")
            
            # Send test message
            await websocket.send(json.dumps({
                "type": "connection_established",
                "payload": {
                    "client": "test_client",
                    "version": "1.0"
                }
            }))
            logger.info(f"Sent test message to {url}")
            
            # Wait for response
            response = await websocket.recv()
            data = json.loads(response)
            logger.info(f"Received response: {data.get('type')}")
            print(f"Received: {data.get('type')}")
            
            # Send another test message
            await websocket.send(json.dumps({
                "type": "test_message",
                "payload": {
                    "message": "Hello WebSocket Server!",
                    "timestamp": datetime.now().isoformat()
                }
            }))
            logger.info(f"Sent second test message to {url}")
            
            # Wait for response
            response = await websocket.recv()
            data = json.loads(response)
            logger.info(f"Received response: {data.get('type')}")
            print(f"Received: {data.get('type')}")
            
            return True
            
    except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
        logger.error(f"Connection error with {url}: {e}")
        print(f"❌ Failed to connect to {url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error testing {url}: {e}")
        print(f"❌ Error: {e}")
        return False

async def main():
    """Test connection to WebSocket server using different URLs"""
    # Test URLs
    urls = [
        "ws://localhost:8765",
        "ws://127.0.0.1:8765",
        "ws://[::1]:8765",  # IPv6 localhost
    ]
    
    results = {}
    
    for url in urls:
        print(f"\n--- Testing {url} ---")
        result = await test_connection(url)
        results[url] = result
        
        # Short pause between tests
        await asyncio.sleep(1)
    
    # Print summary
    print("\n=== Connection Test Summary ===")
    for url, result in results.items():
        status = "✅ SUCCESS" if result else "❌ FAILED"
        print(f"{url}: {status}")

if __name__ == "__main__":
    print("\n=== WebSocket Client Connection Test ===")
    print("Testing connection to WebSocket server with different hostnames/IPs")
    print("This will help diagnose connection issues")
    print("=====================================\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")