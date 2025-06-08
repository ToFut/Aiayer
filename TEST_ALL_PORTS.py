#!/usr/bin/env python3
import asyncio
import websockets
import json
import sys
from datetime import datetime

async def test_port(port, message):
    """Test a specific port with a simple notification message"""
    ws_url = f"ws://localhost:{port}"
    path_suffix = "/ws" if port == 8767 else ""
    full_url = f"{ws_url}{path_suffix}"
    
    print(f"\n===== Testing {full_url} =====")
    
    try:
        # Connect with a short timeout
        async with websockets.connect(full_url, ping_interval=None, close_timeout=5) as ws:
            # Try to get welcome message
            try:
                welcome = await asyncio.wait_for(ws.recv(), timeout=2.0)
                print(f"✅ Connected! Welcome: {welcome[:100]}...")
            except asyncio.TimeoutError:
                print("⚠️ No welcome message received")
            
            # Send a simple notification
            notification = {
                "success": True,
                "response": message,
                "mode": "Suggest",
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"📤 Sending: {json.dumps(notification)}")
            await ws.send(json.dumps(notification))
            
            # Try to get a response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                print(f"📥 Response: {response[:100]}...")
                return True
            except asyncio.TimeoutError:
                print("⚠️ No response received (this may be normal)")
                return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def main():
    message = sys.argv[1] if len(sys.argv) > 1 else f"Test notification {datetime.now().strftime('%H:%M:%S')}"
    
    print(f"🔔 Testing ALL ports with message: {message}")
    
    # Port 8765 (DO Button)
    await test_port(8765, message)
    
    # Port 8766 (LLM)
    await test_port(8766, message)
    
    # Port 8767 (Backend)
    await test_port(8767, message)
    
    # Port 8768 (Other)
    await test_port(8768, message)
    
    print("\n✅ Tests complete! Check your overlay for notifications.")
    print("👉 If you don't see notifications, try restarting the overlay.")

if __name__ == "__main__":
    asyncio.run(main())