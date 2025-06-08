#!/usr/bin/env python3
"""
Script to directly test the overlay's connection to the WebSocket server
"""
import asyncio
import websockets
import json
import logging
import sys
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('test_overlay_connection')

# Test WebSocket server
OVERLAY_WS_PORT = 8765  # The port the overlay connects to

async def test_agent_do_button():
    """Simulate DO button click and observe the response"""
    print(f"\n🔍 Testing agent DO button simulation on port {OVERLAY_WS_PORT}...")
    
    try:
        async with websockets.connect(f'ws://localhost:{OVERLAY_WS_PORT}') as ws:
            # Receive welcome message
            welcome = await ws.recv()
            print(f"✅ Connected to WebSocket server")
            print(f"📥 Received: {welcome}")
            
            # Create session ID
            session_id = f'test_session_{int(datetime.now().timestamp())}'
            
            # Simulate DO button message
            do_message = {
                "type": "agent_confirmation",
                "session_id": session_id,
                "action": "DO",
                "modifications": {},
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"\n🚀 Sending DO button message: {json.dumps(do_message)}")
            await ws.send(json.dumps(do_message))
            
            # Wait for responses
            print("\n📥 Waiting for responses...")
            try:
                for _ in range(5):  # Try to receive 5 messages
                    response = await asyncio.wait_for(ws.recv(), timeout=10)
                    print(f"\n📥 Received: {response}")
                    
                    # Parse response
                    try:
                        data = json.loads(response)
                        
                        if data.get('type') == 'agent_progress':
                            print(f"🔄 Progress update: {data.get('progress')}% - {data.get('message')}")
                            
                        if data.get('type') == 'agent_execution_success':
                            print(f"✅ Execution success: {data.get('summary')}")
                            
                    except json.JSONDecodeError:
                        print(f"⚠️ Non-JSON response")
                        
            except asyncio.TimeoutError:
                print("⚠️ Timeout waiting for response")
                
    except Exception as e:
        print(f"❌ Error connecting to WebSocket server: {e}")
        return False
        
    return True

async def test_direct_overlay_click():
    """Send a direct message to overlay to trigger DO button click"""
    print("\n🔍 Now testing direct message to overlay...")
    
    try:
        # Connect to the backend WebSocket to trigger a DO button click
        backend_port = 8767  # Main enterprise backend port
        async with websockets.connect(f'ws://localhost:{backend_port}') as ws:
            print(f"✅ Connected to backend WebSocket server on port {backend_port}")
            
            # First register as a client
            register_msg = {
                "type": "register",
                "client_type": "test_client",
                "client_id": f"test_client_{int(datetime.now().timestamp())}"
            }
            await ws.send(json.dumps(register_msg))
            print(f"📤 Sent registration message")
            
            # Receive response
            response = await asyncio.wait_for(ws.recv(), timeout=5)
            print(f"📥 Received: {response}")
            
            # Create a session ID
            session_id = f'test_session_{int(datetime.now().timestamp())}'
            
            # Create a test message that requests agent mode and should trigger a DO button
            agent_message = {
                "type": "chat_request",
                "mode": "agent",
                "message": "open settings",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"\n🚀 Sending agent request message: {json.dumps(agent_message)}")
            await ws.send(json.dumps(agent_message))
            
            # Wait for response
            print("\n📥 Waiting for agent response...")
            try:
                for _ in range(3):  # Try to receive 3 messages
                    response = await asyncio.wait_for(ws.recv(), timeout=20)
                    print(f"\n📥 Received from backend: {response[:200]}...")
                    
                    # Check if this is a response that should trigger the DO button
                    try:
                        data = json.loads(response)
                        if data.get('requiresConfirmation'):
                            print(f"✅ Received confirmation request that should trigger DO button")
                            print(f"   Session ID: {data.get('agentSessionId')}")
                            break
                    except json.JSONDecodeError:
                        pass
                        
            except asyncio.TimeoutError:
                print("⚠️ Timeout waiting for agent response")
                
    except Exception as e:
        print(f"❌ Error connecting to backend: {e}")
        return False
        
    return True

async def main():
    """Run the tests"""
    print("🧪 OVERLAY CONNECTION TEST")
    print("==========================")
    print("This script tests WebSocket connections related to the overlay DO button")
    
    # Test if the WebSocket server on port 8765 is working
    print("\n1. Testing if WebSocket server on port 8765 is running...")
    
    try:
        async with websockets.connect(f'ws://localhost:8765', ping_timeout=2) as ws:
            print(f"✅ WebSocket server on port 8765 is running")
            welcome = await asyncio.wait_for(ws.recv(), timeout=2)
            print(f"📥 Welcome message: {welcome}")
    except Exception as e:
        print(f"❌ WebSocket server on port 8765 is not running: {e}")
        print("❗ Please start the guaranteed WebSocket server first")
        return
        
    # Test 1: Simulate DO button click
    result1 = await test_agent_do_button()
    
    # Test 2: Try to trigger DO button through normal flow
    # result2 = await test_direct_overlay_click()
    
    print("\n==========================")
    if result1:
        print("✅ Tests completed. DO button message handler is working properly.")
        print("❗ If the DO button is still not working in the overlay, there might be an issue with:")
        print("   1. The overlay WebSocket connection (EnterpriseChatWidget.svelte)")
        print("   2. The button click handler in the overlay")
        print("   3. A mismatch between the formats expected by the overlay and our server")
    else:
        print("❌ Tests failed. Please check the logs for more details.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)