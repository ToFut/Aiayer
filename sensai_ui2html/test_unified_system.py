#!/usr/bin/env python3
"""
Test Unified System - Test client for the unified backend
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
import websockets

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedSystemTester:
    """Test client for the unified backend system"""
    
    def __init__(self, uri="ws://localhost:8767"):
        self.uri = uri
        self.websocket = None
        self.connection_id = None
    
    async def connect(self):
        """Connect to the unified backend"""
        try:
            logger.info(f"🔗 Connecting to {self.uri}")
            self.websocket = await websockets.connect(self.uri)
            
            # Wait for connection message
            message = await self.websocket.recv()
            data = json.loads(message)
            
            if data.get("type") == "connection_established":
                self.connection_id = data.get("connection_id")
                logger.info(f"✅ Connected! ID: {self.connection_id}")
                logger.info(f"📋 Capabilities: {data.get('capabilities', [])}")
                return True
            else:
                logger.error(f"❌ Unexpected connection message: {data}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False
    
    async def register(self, client_type="test_client"):
        """Register with the backend"""
        message = {
            "type": "register",
            "client_type": client_type
        }
        
        await self.websocket.send(json.dumps(message))
        
        # Wait for response
        response = await self.websocket.recv()
        data = json.loads(response)
        
        if data.get("type") == "registration_success":
            logger.info(f"✅ Registered as {client_type}")
            return True
        else:
            logger.error(f"❌ Registration failed: {data}")
            return False
    
    async def test_user_interaction(self, query="What's on my screen?"):
        """Test user interaction with UI context"""
        logger.info(f"🤖 Testing user interaction: {query}")
        
        message = {
            "type": "user_interaction",
            "payload": {
                "query": query,
                "mode": "chat"
            }
        }
        
        await self.websocket.send(json.dumps(message))
        
        # Wait for response
        response = await self.websocket.recv()
        data = json.loads(response)
        
        if data.get("type") == "chat_response":
            payload = data.get("payload", {})
            logger.info(f"✅ Chat response received:")
            logger.info(f"   Response: {payload.get('response', '')[:100]}...")
            logger.info(f"   UI Context: {payload.get('ui_context', {})}")
            return True
        else:
            logger.error(f"❌ Unexpected response: {data}")
            return False
    
    async def test_ui_memory_query(self, query="Finder"):
        """Test UI memory query"""
        logger.info(f"🔍 Testing UI memory query: {query}")
        
        message = {
            "type": "ui_memory_query",
            "payload": {
                "query": query,
                "limit": 3
            }
        }
        
        await self.websocket.send(json.dumps(message))
        
        # Wait for response
        response = await self.websocket.recv()
        data = json.loads(response)
        
        if data.get("type") == "ui_memory_results":
            payload = data.get("payload", {})
            results = payload.get("results", [])
            logger.info(f"✅ UI memory results received: {len(results)} results")
            for i, result in enumerate(results[:2]):  # Show first 2
                logger.info(f"   {i+1}. {result.get('metadata', {}).get('timestamp', 'Unknown')}")
            return True
        else:
            logger.error(f"❌ Unexpected response: {data}")
            return False
    
    async def test_get_current_ui(self):
        """Test getting current UI context"""
        logger.info("📱 Testing get current UI")
        
        message = {
            "type": "get_current_ui",
            "payload": {}
        }
        
        await self.websocket.send(json.dumps(message))
        
        # Wait for response
        response = await self.websocket.recv()
        data = json.loads(response)
        
        if data.get("type") == "current_ui_response":
            payload = data.get("payload", {})
            if "error" in payload:
                logger.warning(f"⚠️ No UI context: {payload['error']}")
            else:
                logger.info(f"✅ Current UI received:")
                logger.info(f"   App: {payload.get('app_name', 'Unknown')}")
                logger.info(f"   Elements: {payload.get('element_count', 0)}")
            return True
        else:
            logger.error(f"❌ Unexpected response: {data}")
            return False
    
    async def test_agent_execute(self, action="Click the first button"):
        """Test agent execution"""
        logger.info(f"🤖 Testing agent execution: {action}")
        
        message = {
            "type": "agent_execute",
            "payload": {
                "action": action
            }
        }
        
        await self.websocket.send(json.dumps(message))
        
        # Wait for response
        response = await self.websocket.recv()
        data = json.loads(response)
        
        if data.get("type") == "agent_execution_result":
            payload = data.get("payload", {})
            logger.info(f"✅ Agent execution result:")
            logger.info(f"   Success: {payload.get('success', False)}")
            logger.info(f"   Result: {payload.get('result', {}).get('message', '')}")
            return True
        else:
            logger.error(f"❌ Unexpected response: {data}")
            return False
    
    async def test_ping(self):
        """Test ping/pong"""
        logger.info("🏓 Testing ping/pong")
        
        message = {
            "type": "ping",
            "payload": {}
        }
        
        await self.websocket.send(json.dumps(message))
        
        # Wait for response
        response = await self.websocket.recv()
        data = json.loads(response)
        
        if data.get("type") == "pong":
            payload = data.get("payload", {})
            stats = payload.get("stats", {})
            logger.info(f"✅ Pong received:")
            logger.info(f"   Connections: {stats.get('connections', 0)}")
            logger.info(f"   UI Snapshots: {stats.get('ui_snapshots_captured', 0)}")
            logger.info(f"   Queries: {stats.get('queries_processed', 0)}")
            return True
        else:
            logger.error(f"❌ Unexpected response: {data}")
            return False
    
    async def run_all_tests(self):
        """Run all tests"""
        logger.info("🧪 Starting Unified System Tests")
        logger.info("=" * 50)
        
        # Connect
        if not await self.connect():
            return False
        
        # Register
        if not await self.register():
            return False
        
        # Wait a moment for UI context to be available
        logger.info("⏳ Waiting for UI context...")
        await asyncio.sleep(3)
        
        tests = [
            ("Ping Test", self.test_ping),
            ("Get Current UI", self.test_get_current_ui),
            ("UI Memory Query", self.test_ui_memory_query),
            ("User Interaction", self.test_user_interaction),
            ("Agent Execution", self.test_agent_execute),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                logger.info(f"\n🔬 Running {test_name}...")
                if await test_func():
                    logger.info(f"✅ {test_name} PASSED")
                    passed += 1
                else:
                    logger.error(f"❌ {test_name} FAILED")
            except Exception as e:
                logger.error(f"❌ {test_name} ERROR: {e}")
        
        logger.info("\n" + "=" * 50)
        logger.info(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed! Unified system is working perfectly!")
        else:
            logger.warning(f"⚠️ {total - passed} tests failed. Check the logs for details.")
        
        return passed == total
    
    async def close(self):
        """Close the connection"""
        if self.websocket:
            await self.websocket.close()
            logger.info("🔌 Connection closed")

async def main():
    """Main test function"""
    tester = UnifiedSystemTester()
    
    try:
        success = await tester.run_all_tests()
        return 0 if success else 1
    finally:
        await tester.close()

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test error: {e}")
        sys.exit(1) 