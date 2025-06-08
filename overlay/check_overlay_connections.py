#!/usr/bin/env python3
"""
Diagnostic script to check overlay WebSocket connections
"""

import asyncio
import websockets
import json
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('overlay_connection_test')

async def test_connection(url, name, timeout=5):
    """Test a WebSocket connection with timeout"""
    try:
        logger.info(f"Testing connection to {name} at {url}...")
        async with websockets.connect(url, ping_timeout=timeout, close_timeout=timeout) as ws:
            logger.info(f"✅ Successfully connected to {name} at {url}")
            
            # Send a simple message
            test_message = {
                "type": "ping",
                "client_id": "diagnostic_tool",
                "timestamp": "2025-06-07T12:00:00Z"
            }
            await ws.send(json.dumps(test_message))
            logger.info(f"Sent test message to {name}: {test_message}")
            
            # Wait for response with timeout
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=timeout)
                logger.info(f"✅ Received response from {name}: {response[:100]}...")
                try:
                    data = json.loads(response)
                    logger.info(f"Response type: {data.get('type', 'unknown')}")
                except json.JSONDecodeError:
                    logger.warning(f"Response is not valid JSON: {response[:50]}...")
                return True
            except asyncio.TimeoutError:
                logger.error(f"❌ Timeout waiting for response from {name}")
                return False
            
    except Exception as e:
        logger.error(f"❌ Failed to connect to {name} at {url}: {e}")
        return False

async def main():
    """Test all WebSocket connections"""
    print("🔍 Overlay WebSocket Connection Diagnostic Tool 🔍")
    print("------------------------------------------------")
    
    # Define endpoints to test
    endpoints = [
        ("ws://localhost:8765", "DO Button Server (8765)"),
        ("ws://localhost:8767", "Enhanced Enterprise Backend (8767)"),
        ("ws://localhost:8768", "Fixed Bridge Server (8768)")
    ]
    
    # Check for active WebSocket servers
    import subprocess
    try:
        result = subprocess.run(['lsof', '-i', ':8765,8767,8768'], 
                              capture_output=True, text=True)
        print("\n🔌 Active WebSocket Servers:")
        if result.stdout:
            for line in result.stdout.splitlines():
                if 'LISTEN' in line:
                    print(f"  {line}")
        else:
            print("  No active WebSocket servers found!")
    except Exception as e:
        print(f"  Error checking active servers: {e}")
    
    print("\n🔄 Testing WebSocket Connections:")
    results = []
    
    # Test each endpoint concurrently
    tasks = [test_connection(url, name) for url, name in endpoints]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Report results
    success_count = sum(1 for r in results if r is True)
    print("\n📊 Connection Test Results:")
    for i, (url, name) in enumerate(endpoints):
        result = results[i]
        status = "✅ CONNECTED" if result is True else "❌ FAILED"
        print(f"  {name}: {status}")
    
    print(f"\n🏁 Summary: {success_count}/{len(endpoints)} connections successful")
    
    # Exit with status code
    if success_count == len(endpoints):
        print("\n✨ All connections successful! The overlay system should work properly.")
        return 0
    else:
        print("\n⚠️  Some connections failed. The overlay system may not work correctly.")
        if success_count == 0:
            print("❌ All connections failed. Please restart the backend services.")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)