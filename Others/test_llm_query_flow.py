#!/usr/bin/env python3
"""
Test LLM Query Flow
Tests the complete flow from Tauri overlay to backend LLM processing
"""
import asyncio
import websockets
import json
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Color:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_colored(color, message):
    print(f"{color}{message}{Color.END}")

def print_header(title):
    print_colored(Color.BOLD + Color.CYAN, f"\n{'='*60}")
    print_colored(Color.BOLD + Color.CYAN, f"{title}")
    print_colored(Color.BOLD + Color.CYAN, f"{'='*60}")

async def test_websocket_server_connection():
    """Test connection to WebSocket server (port 8765)"""
    print_header("TESTING WEBSOCKET SERVER CONNECTION (8765)")
    
    try:
        uri = "ws://localhost:8765"
        async with websockets.connect(uri) as websocket:
            print_colored(Color.GREEN, "✅ Connected to WebSocket server")
            
            # Send registration as UI client
            registration_msg = {
                "type": "register",
                "client_type": "ui",
                "payload": {
                    "client_id": "test_ui_client"
                }
            }
            
            await websocket.send(json.dumps(registration_msg))
            print_colored(Color.BLUE, "📤 Sent registration message")
            
            # Wait for registration confirmation
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                response_data = json.loads(response)
                print_colored(Color.GREEN, f"📥 Received: {response_data.get('type', 'unknown')}")
                
                # Wait for registration_confirmed if we got welcome first
                if response_data.get('type') == 'welcome':
                    print_colored(Color.BLUE, "⏳ Waiting for registration confirmation...")
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    response_data = json.loads(response)
                    print_colored(Color.GREEN, f"📥 Received: {response_data.get('type', 'unknown')}")
                
                if response_data.get('type') == 'registration_confirmed':
                    print_colored(Color.GREEN, "✅ Registration confirmed")
                    return True
                else:
                    print_colored(Color.YELLOW, f"⚠️ Unexpected response: {response_data}")
                    return False
                    
            except asyncio.TimeoutError:
                print_colored(Color.RED, "❌ No response from WebSocket server")
                return False
                
    except Exception as e:
        print_colored(Color.RED, f"❌ WebSocket server connection failed: {e}")
        return False

async def test_backend_server_connection():
    """Test connection to backend server (port 8767)"""
    print_header("TESTING BACKEND SERVER CONNECTION (8767)")
    
    try:
        uri = "ws://localhost:8767"
        async with websockets.connect(uri) as websocket:
            print_colored(Color.GREEN, "✅ Connected to backend server")
            
            # Wait for welcome message
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                response_data = json.loads(response)
                print_colored(Color.GREEN, f"📥 Received: {response_data.get('type', 'unknown')}")
                
                if response_data.get('type') == 'connection_established':
                    capabilities = response_data.get('capabilities', [])
                    print_colored(Color.GREEN, f"✅ Backend capabilities: {capabilities}")
                    return True
                else:
                    print_colored(Color.YELLOW, f"⚠️ Unexpected welcome: {response_data}")
                    return False
                    
            except asyncio.TimeoutError:
                print_colored(Color.RED, "❌ No welcome message from backend")
                return False
                
    except Exception as e:
        print_colored(Color.RED, f"❌ Backend server connection failed: {e}")
        return False

async def test_backend_llm_query():
    """Test LLM query processing on backend"""
    print_header("TESTING BACKEND LLM QUERY PROCESSING")
    
    try:
        uri = "ws://localhost:8767"
        async with websockets.connect(uri) as websocket:
            print_colored(Color.GREEN, "✅ Connected to backend for LLM test")
            
            # Wait for welcome message
            welcome = await asyncio.wait_for(websocket.recv(), timeout=5)
            print_colored(Color.BLUE, "📥 Received welcome message")
            
            # Send test query
            test_query = {
                "type": "query",
                "message": "Hello, this is a test query. Can you see my context?",
                "context": {
                    "active_app": "Terminal",
                    "active_window": "Test Window",
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            await websocket.send(json.dumps(test_query))
            print_colored(Color.BLUE, "📤 Sent test query")
            
            # Wait for thinking response
            try:
                thinking_response = await asyncio.wait_for(websocket.recv(), timeout=5)
                thinking_data = json.loads(thinking_response)
                print_colored(Color.YELLOW, f"🤔 {thinking_data.get('response', 'Processing...')}")
                
                # Wait for actual response
                final_response = await asyncio.wait_for(websocket.recv(), timeout=15)
                final_data = json.loads(final_response)
                
                response_text = final_data.get('response', '')
                if response_text and response_text != "thinking...":
                    print_colored(Color.GREEN, f"✅ LLM Response: {response_text}")
                    print_colored(Color.GREEN, f"✅ Status: {final_data.get('status', 'unknown')}")
                    return True
                else:
                    print_colored(Color.RED, f"❌ Empty or invalid LLM response: {response_text}")
                    return False
                    
            except asyncio.TimeoutError:
                print_colored(Color.RED, "❌ Timeout waiting for LLM response")
                return False
                
    except Exception as e:
        print_colored(Color.RED, f"❌ LLM query test failed: {e}")
        return False

async def test_full_overlay_simulation():
    """Test full Tauri overlay simulation through WebSocket server to backend"""
    print_header("TESTING FULL OVERLAY TO BACKEND FLOW")
    
    try:
        # Connect to WebSocket server (like Tauri overlay would)
        ws_uri = "ws://localhost:8765"
        async with websockets.connect(ws_uri) as ws_websocket:
            print_colored(Color.GREEN, "✅ Connected to WebSocket server (overlay simulation)")
            
            # Register as UI client
            registration_msg = {
                "type": "register",
                "client_type": "ui",
                "payload": {
                    "client_id": "tauri_overlay_simulation"
                }
            }
            
            await ws_websocket.send(json.dumps(registration_msg))
            
            # Handle welcome and registration confirmation
            welcome = await asyncio.wait_for(ws_websocket.recv(), timeout=5)
            welcome_data = json.loads(welcome)
            print_colored(Color.BLUE, f"📥 WebSocket: {welcome_data.get('type')}")
            
            if welcome_data.get('type') == 'welcome':
                confirmation = await asyncio.wait_for(ws_websocket.recv(), timeout=5)
                confirmation_data = json.loads(confirmation)
                print_colored(Color.BLUE, f"📥 WebSocket: {confirmation_data.get('type')}")
            
            # Now connect to backend directly (simulate query forwarding)
            backend_uri = "ws://localhost:8767"
            async with websockets.connect(backend_uri) as backend_websocket:
                print_colored(Color.GREEN, "✅ Connected to backend (query forwarding simulation)")
                
                # Wait for backend welcome
                backend_welcome = await asyncio.wait_for(backend_websocket.recv(), timeout=5)
                print_colored(Color.BLUE, "📥 Backend welcome received")
                
                # Send a meaningful query
                query_msg = {
                    "type": "query",
                    "message": "What can you help me with? I'm testing the connection.",
                    "context": {
                        "active_app": "Test Application",
                        "active_window": "Connection Test",
                        "source": "tauri_overlay_simulation"
                    }
                }
                
                await backend_websocket.send(json.dumps(query_msg))
                print_colored(Color.BLUE, "📤 Sent query to backend")
                
                # Receive thinking response
                thinking = await asyncio.wait_for(backend_websocket.recv(), timeout=5)
                thinking_data = json.loads(thinking)
                print_colored(Color.YELLOW, f"🤔 Backend: {thinking_data.get('response', 'Processing...')}")
                
                # Receive final response
                final = await asyncio.wait_for(backend_websocket.recv(), timeout=15)
                final_data = json.loads(final)
                
                response_text = final_data.get('response', '')
                if response_text and response_text != "thinking...":
                    print_colored(Color.GREEN, f"✅ Final Response: {response_text}")
                    print_colored(Color.GREEN, "✅ Full flow completed successfully!")
                    return True
                else:
                    print_colored(Color.RED, f"❌ Invalid final response: {response_text}")
                    return False
                    
    except Exception as e:
        print_colored(Color.RED, f"❌ Full flow test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print_colored(Color.BOLD + Color.CYAN, "LLM Query Flow Test Suite")
    print_colored(Color.BOLD + Color.CYAN, "=" * 50)
    
    tests = [
        ("WebSocket Server Connection", test_websocket_server_connection),
        ("Backend Server Connection", test_backend_server_connection),
        ("Backend LLM Query Processing", test_backend_llm_query),
        ("Full Overlay to Backend Flow", test_full_overlay_simulation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print_colored(Color.BOLD, f"\n🧪 Running: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
            if result:
                print_colored(Color.GREEN, f"✅ {test_name}: PASSED")
            else:
                print_colored(Color.RED, f"❌ {test_name}: FAILED")
        except Exception as e:
            print_colored(Color.RED, f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
        
        # Small delay between tests
        await asyncio.sleep(1)
    
    # Summary
    print_header("TEST RESULTS SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        color = Color.GREEN if result else Color.RED
        print_colored(color, f"{status:4} - {test_name}")
    
    print_colored(Color.BOLD, f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print_colored(Color.GREEN, "🎉 All tests passed! LLM query flow is working correctly.")
    elif passed >= total * 0.75:
        print_colored(Color.YELLOW, "⚠️ Most tests passed, but some issues need attention.")
    else:
        print_colored(Color.RED, "❌ Critical issues found. System needs fixing.")

if __name__ == "__main__":
    asyncio.run(main())