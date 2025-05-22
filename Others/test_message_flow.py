#!/usr/bin/env python3
"""
Test Message Flow
Tests the message flow from overlay to LLM backend via the WebSocket server.
"""
import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_overlay_to_backend():
    """Test sending a message from overlay (port 8765) to backend (port 8767)."""
    
    print("Testing message flow from overlay to LLM backend...")
    
    # Test 1: Connect to WebSocket server on 8765 (like the overlay)
    print("\n1. Testing connection to WebSocket server on 8765...")
    try:
        async with websockets.connect("ws://localhost:8765") as ws:
            print("✅ Connected to WebSocket server on 8765")
            
            # Register as UI client
            await ws.send(json.dumps({
                "type": "register",
                "client_type": "ui",
                "version": "1.0.0"
            }))
            print("📤 Sent registration message")
            
            # Wait for registration confirmation
            response = await ws.recv()
            data = json.loads(response)
            print(f"📥 Received: {data.get('type')}")
            
            # Send a chat message
            await ws.send(json.dumps({
                "type": "chat_message",
                "message": "Hello, can you help me test the system?",
                "query": "Hello, can you help me test the system?",
                "payload": {
                    "query": "Hello, can you help me test the system?",
                    "message": "Hello, can you help me test the system?"
                }
            }))
            print("📤 Sent chat message")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=10.0)
                data = json.loads(response)
                print(f"📥 Received response: {data.get('type')}")
                if 'payload' in data and 'response' in data['payload']:
                    print(f"💬 Response text: {data['payload']['response'][:100]}...")
                elif 'response' in data:
                    print(f"💬 Response text: {data['response'][:100]}...")
                else:
                    print(f"💬 Full response: {data}")
                print("✅ Message flow test PASSED!")
                return True
            except asyncio.TimeoutError:
                print("❌ Timeout waiting for response")
                return False
                
    except Exception as e:
        print(f"❌ Error testing WebSocket server: {e}")
        return False

async def test_direct_backend():
    """Test connecting directly to the LLM backend on 8767."""
    
    print("\n2. Testing direct connection to LLM backend on 8767...")
    try:
        async with websockets.connect("ws://localhost:8767") as ws:
            print("✅ Connected to LLM backend on 8767")
            
            # Register as a client
            await ws.send(json.dumps({
                "type": "register",
                "client_type": "test"
            }))
            print("📤 Sent registration message")
            
            # Wait for registration confirmation
            response = await ws.recv()
            data = json.loads(response)
            print(f"📥 Received: {data.get('type')}")
            
            # Send a user message directly
            await ws.send(json.dumps({
                "type": "user_message",
                "payload": {
                    "query": "Hello from direct test!",
                    "timestamp": "2025-05-21T16:20:00Z"
                }
            }))
            print("📤 Sent user message")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(response)
                print(f"📥 Received response: {data.get('type')}")
                if 'payload' in data and 'response' in data['payload']:
                    print(f"💬 Response text: {data['payload']['response'][:100]}...")
                else:
                    print(f"💬 Full response: {data}")
                print("✅ Direct backend test PASSED!")
                return True
            except asyncio.TimeoutError:
                print("❌ Timeout waiting for response")
                return False
                
    except Exception as e:
        print(f"❌ Error testing LLM backend: {e}")
        return False

async def main():
    """Run all tests."""
    print("🧪 Starting Message Flow Tests")
    print("=" * 50)
    
    # Test direct backend connection first
    backend_test = await test_direct_backend()
    
    # Test overlay to backend flow
    flow_test = await test_overlay_to_backend()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Direct Backend Test: {'✅ PASS' if backend_test else '❌ FAIL'}")
    print(f"   Overlay Flow Test:   {'✅ PASS' if flow_test else '❌ FAIL'}")
    
    if backend_test and flow_test:
        print("\n🎉 All tests PASSED! The message flow is working correctly.")
    elif backend_test:
        print("\n⚠️  Backend works but overlay flow has issues. Check WebSocket server forwarding.")
    else:
        print("\n❌ Backend connection failed. Check if LLM backend is running on port 8767.")

if __name__ == "__main__":
    asyncio.run(main())