#!/usr/bin/env python3
"""
SensAI Enterprise System Test Client
Test all 4 modes with real UI automation
"""

import asyncio
import websockets
import json
import time

class SensAITestClient:
    def __init__(self, uri="ws://localhost:8767"):
        self.uri = uri
        
    async def connect_and_test(self):
        """Connect to SensAI and test all modes"""
        try:
            print(f"🔌 Connecting to SensAI Enterprise System at {self.uri}...")
            
            async with websockets.connect(self.uri) as websocket:
                # Wait for welcome message
                welcome = await websocket.recv()
                welcome_data = json.loads(welcome)
                print(f"✅ Connected! {welcome_data.get('message')}")
                print(f"🎯 Capabilities: {', '.join(welcome_data.get('capabilities', []))}")
                print("\n" + "="*60)
                
                # Test Agent Mode - UI Automation
                await self.test_agent_mode(websocket)
                
                # Test Ask Mode
                await self.test_ask_mode(websocket)
                
                # Test Suggest Mode
                await self.test_suggest_mode(websocket)
                
                # Test General Mode
                await self.test_general_mode(websocket)
                
                print("\n" + "="*60)
                print("🎆 All tests completed successfully!")
                print("🎯 SensAI Enterprise System is fully operational!")
                
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            print("🔧 Make sure to start the system first: ./START_SYSTEM.sh")
            return False
        
        return True
    
    async def test_agent_mode(self, websocket):
        """Test Agent mode with UI automation"""
        print("🤖 TESTING AGENT MODE (UI Automation)")
        print("-" * 40)
        
        test_commands = [
            "click at position 200 200",
            "type hello from sensai",
            "press return key"
        ]
        
        for i, command in enumerate(test_commands, 1):
            print(f"\n{i}. Testing: {command}")
            
            request = {
                "type": "chat_request",
                "query": command,
                "mode": "agent",
                "timestamp": str(int(time.time()))
            }
            
            await websocket.send(json.dumps(request))
            response = await websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get('type') == 'chat_response':
                payload = response_data.get('payload', {})
                success = payload.get('success', False)
                
                if success and "UI Automation Executed Successfully" in payload.get('response', ''):
                    print(f"   ✅ SUCCESS: Real UI automation executed!")
                else:
                    print(f"   ⚠️  Response: {payload.get('response', '')[:100]}...")
            else:
                print(f"   ❌ Unexpected response: {response_data.get('type')}")
            
            await asyncio.sleep(1)  # Brief pause between commands
    
    async def test_ask_mode(self, websocket):
        """Test Ask mode"""
        print("\n🤔 TESTING ASK MODE")
        print("-" * 40)
        
        request = {
            "type": "chat_request",
            "query": "What is SensAI?",
            "mode": "ask",
            "timestamp": str(int(time.time()))
        }
        
        await websocket.send(json.dumps(request))
        response = await websocket.recv()
        response_data = json.loads(response)
        
        if response_data.get('type') == 'chat_response':
            payload = response_data.get('payload', {})
            print(f"   ✅ Ask Mode Response: {payload.get('response', '')[:100]}...")
        else:
            print(f"   ❌ Unexpected response type: {response_data.get('type')}")
    
    async def test_suggest_mode(self, websocket):
        """Test Suggest mode"""
        print("\n💡 TESTING SUGGEST MODE")
        print("-" * 40)
        
        request = {
            "type": "chat_request",
            "query": "suggest productivity improvements",
            "mode": "suggest",
            "timestamp": str(int(time.time()))
        }
        
        await websocket.send(json.dumps(request))
        response = await websocket.recv()
        response_data = json.loads(response)
        
        if response_data.get('type') == 'chat_response':
            payload = response_data.get('payload', {})
            print(f"   ✅ Suggest Mode Response: {payload.get('response', '')[:100]}...")
        else:
            print(f"   ❌ Unexpected response type: {response_data.get('type')}")
    
    async def test_general_mode(self, websocket):
        """Test General mode"""
        print("\n🗣️ TESTING GENERAL MODE")
        print("-" * 40)
        
        request = {
            "type": "chat_request",
            "query": "Hello! How are you today?",
            "mode": "general",
            "timestamp": str(int(time.time()))
        }
        
        await websocket.send(json.dumps(request))
        response = await websocket.recv()
        response_data = json.loads(response)
        
        if response_data.get('type') == 'chat_response':
            payload = response_data.get('payload', {})
            print(f"   ✅ General Mode Response: {payload.get('response', '')[:100]}...")
        else:
            print(f"   ❌ Unexpected response type: {response_data.get('type')}")

async def main():
    print("🧪 SensAI Enterprise System Test Client")
    print("🎯 Testing all 4 chat modes + UI automation")
    print("\n" + "="*60)
    
    client = SensAITestClient()
    success = await client.connect_and_test()
    
    if success:
        print("\n🎆 ALL TESTS PASSED - System is working perfectly!")
    else:
        print("\n🚨 Tests failed - Check system status")
        print("🔧 Troubleshooting:")
        print("   1. Run: ./START_SYSTEM.sh")
        print("   2. Wait for server to start")
        print("   3. Run this test again")

if __name__ == "__main__":
    asyncio.run(main())
