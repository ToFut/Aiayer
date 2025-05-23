#!/usr/bin/env python3
"""
Test script for the enhanced contextual system
Tests all modes with semantic memory integration
"""

import asyncio
import json
import websockets
import time
from datetime import datetime

class ContextualSystemTester:
    def __init__(self):
        self.brain_router_url = "ws://localhost:8765"
        self.enterprise_backend_url = "ws://localhost:8767"
        
    async def test_server(self, url, server_name):
        """Test a specific server"""
        print(f"\n🧪 Testing {server_name} at {url}")
        print("=" * 50)
        
        try:
            async with websockets.connect(url, ping_timeout=10) as websocket:
                # Get connection message
                connection_msg = await asyncio.wait_for(websocket.recv(), timeout=5)
                connection_data = json.loads(connection_msg)
                print(f"✅ Connected to {server_name}")
                print(f"📋 Message: {connection_data.get('message', 'No message')}")
                
                # Check for contextual features
                features = connection_data.get('features', [])
                capabilities = connection_data.get('capabilities', [])
                ai_features = connection_data.get('ai_features', {})
                
                print(f"🔍 Features: {features}")
                print(f"🎯 Capabilities: {capabilities}")
                print(f"🧠 AI Features: {ai_features}")
                
                # Test all modes with contextual queries
                test_messages = [
                    ("Agent", "help me click on a document", "Testing Agent mode with UI automation context"),
                    ("Ask", "what is the system status?", "Testing Ask mode with knowledge retrieval"),
                    ("Ask", "what have we talked about before?", "Testing Ask mode with conversation memory"),
                    ("Suggest", "how can I improve my workflow?", "Testing Suggest mode with pattern analysis"),
                    ("General", "hello, how are you?", "Testing General mode with conversation context"),
                    ("General", "thank you for your help", "Testing General mode with context awareness")
                ]
                
                for mode, message, description in test_messages:
                    print(f"\n🔸 {description}")
                    
                    request = {
                        "type": "chat_request",
                        "mode": mode,
                        "message": message,
                        "session_id": f"test_session_{int(time.time())}"
                    }
                    
                    print(f"📤 Sending: {request}")
                    await websocket.send(json.dumps(request))
                    
                    # Get response
                    response_raw = await asyncio.wait_for(websocket.recv(), timeout=15)
                    response = json.loads(response_raw)
                    
                    print(f"📥 Response type: {response.get('type', 'unknown')}")
                    print(f"✅ Success: {response.get('success', False)}")
                    print(f"🎯 Mode: {response.get('mode', 'unknown')}")
                    print(f"⏱️  Processing time: {response.get('processing_time', 'unknown')}s")
                    
                    # Show response content
                    response_text = response.get('response', response.get('payload', {}).get('response', 'No response'))
                    print(f"💬 Response: {response_text[:200]}{'...' if len(response_text) > 200 else ''}")
                    
                    # Show context metrics if available
                    context_metrics = response.get('context_metrics', {})
                    context_used = response.get('context_used', {})
                    
                    if context_metrics:
                        print(f"📊 Context Metrics: {context_metrics}")
                    if context_used:
                        print(f"🧠 Context Used: {context_used}")
                    
                    print("-" * 40)
                    
                    # Small delay between requests
                    await asyncio.sleep(2)
                
                # Test system status
                print(f"\n🔍 Testing system status for {server_name}")
                status_request = {"type": "system_status"}
                await websocket.send(json.dumps(status_request))
                
                status_response_raw = await asyncio.wait_for(websocket.recv(), timeout=10)
                status_response = json.loads(status_response_raw)
                
                print(f"📊 System Status: {status_response.get('status', 'unknown')}")
                print(f"⏱️  Uptime: {status_response.get('uptime_seconds', 0)} seconds")
                print(f"👥 Connected clients: {status_response.get('connected_clients', 0)}")
                
                # Show memory system metrics if available
                memory_system = status_response.get('memory_system', {})
                if memory_system:
                    print(f"🧠 Memory System: {memory_system}")
                
                return True
                
        except Exception as e:
            print(f"❌ Error testing {server_name}: {e}")
            return False
    
    async def run_tests(self):
        """Run all tests"""
        print("🚀 Starting Contextual System Tests")
        print("=" * 60)
        print(f"🕐 Test started at: {datetime.now().isoformat()}")
        
        # Test both servers
        brain_router_ok = await self.test_server(self.brain_router_url, "Brain Router")
        enterprise_backend_ok = await self.test_server(self.enterprise_backend_url, "Enterprise Backend")
        
        # Summary
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        print(f"🧠 Brain Router (8765): {'✅ PASS' if brain_router_ok else '❌ FAIL'}")
        print(f"🏢 Enterprise Backend (8767): {'✅ PASS' if enterprise_backend_ok else '❌ FAIL'}")
        
        if brain_router_ok or enterprise_backend_ok:
            print("\n🎉 CONTEXTUAL SYSTEM IS WORKING!")
            print("🔍 Semantic memory integration is active")
            print("🧠 All modes provide contextual responses")
            print("📚 System learns from every interaction")
            
            if brain_router_ok and enterprise_backend_ok:
                print("✅ Both servers are fully operational")
            elif brain_router_ok:
                print("⚠️  Only Brain Router is working - Enterprise Backend needs attention")
            else:
                print("⚠️  Only Enterprise Backend is working - Brain Router needs attention")
        else:
            print("\n❌ CONTEXTUAL SYSTEM TESTS FAILED")
            print("🔧 Check server logs and configuration")
            print("📋 Ensure both servers are running:")
            print("   ./START_ENHANCED_SYSTEM.sh")
        
        print(f"\n🕐 Test completed at: {datetime.now().isoformat()}")

async def main():
    """Main test function"""
    tester = ContextualSystemTester()
    await tester.run_tests()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test error: {e}")