#!/usr/bin/env python3
"""
Simple Test - Test the unified system one message at a time
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

async def test_unified_system():
    """Simple test of the unified system"""
    logger.info("🧪 Simple Unified System Test")
    logger.info("=" * 50)
    
    try:
        # Connect to the unified backend
        uri = "ws://localhost:8767"
        logger.info(f"🔗 Connecting to {uri}")
        
        websocket = await websockets.connect(uri)
        
        # Wait for connection message
        message = await websocket.recv()
        data = json.loads(message)
        
        if data.get("type") == "connection_established":
            connection_id = data.get("connection_id")
            logger.info(f"✅ Connected! ID: {connection_id}")
            logger.info(f"📋 Capabilities: {data.get('capabilities', [])}")
        else:
            logger.error(f"❌ Unexpected connection message: {data}")
            return False
        
        # Test 1: Register
        logger.info("\n🔬 Test 1: Register")
        register_msg = {
            "type": "register",
            "client_type": "simple_test"
        }
        
        await websocket.send(json.dumps(register_msg))
        response = await websocket.recv()
        data = json.loads(response)
        
        if data.get("type") == "registration_success":
            logger.info("✅ Registration successful")
        else:
            logger.error(f"❌ Registration failed: {data}")
            return False
        
        # Test 2: Ping
        logger.info("\n🔬 Test 2: Ping")
        ping_msg = {
            "type": "ping",
            "payload": {}
        }
        
        await websocket.send(json.dumps(ping_msg))
        response = await websocket.recv()
        data = json.loads(response)
        
        if data.get("type") == "pong":
            stats = data.get("payload", {}).get("stats", {})
            logger.info(f"✅ Pong received - Connections: {stats.get('connections', 0)}")
        else:
            logger.error(f"❌ Ping failed: {data}")
            return False
        
        # Test 3: Get Current UI
        logger.info("\n🔬 Test 3: Get Current UI")
        ui_msg = {
            "type": "get_current_ui",
            "payload": {}
        }
        
        await websocket.send(json.dumps(ui_msg))
        response = await websocket.recv()
        data = json.loads(response)
        
        if data.get("type") == "current_ui_response":
            payload = data.get("payload", {})
            if "error" in payload:
                logger.warning(f"⚠️ No UI context: {payload['error']}")
            else:
                logger.info(f"✅ Current UI: {payload.get('app_name', 'Unknown')} with {payload.get('element_count', 0)} elements")
        else:
            logger.error(f"❌ Get Current UI failed: {data}")
            return False
        
        # Test 4: User Interaction
        logger.info("\n🔬 Test 4: User Interaction")
        interaction_msg = {
            "type": "user_interaction",
            "payload": {
                "query": "What's on my screen?",
                "mode": "chat"
            }
        }
        
        await websocket.send(json.dumps(interaction_msg))
        response = await websocket.recv()
        data = json.loads(response)
        
        if data.get("type") == "chat_response":
            payload = data.get("payload", {})
            logger.info(f"✅ Chat response: {payload.get('response', '')[:100]}...")
            logger.info(f"   UI Context: {payload.get('ui_context', {})}")
        else:
            logger.error(f"❌ User Interaction failed: {data}")
            return False
        
        # Test 5: UI Memory Query
        logger.info("\n🔬 Test 5: UI Memory Query")
        memory_msg = {
            "type": "ui_memory_query",
            "payload": {
                "query": "Finder",
                "limit": 3
            }
        }
        
        await websocket.send(json.dumps(memory_msg))
        response = await websocket.recv()
        data = json.loads(response)
        
        if data.get("type") == "ui_memory_results":
            payload = data.get("payload", {})
            results = payload.get("results", [])
            logger.info(f"✅ UI Memory results: {len(results)} results")
        else:
            logger.error(f"❌ UI Memory Query failed: {data}")
            return False
        
        # Test 6: Agent Execution
        logger.info("\n🔬 Test 6: Agent Execution")
        agent_msg = {
            "type": "agent_execute",
            "payload": {
                "action": "Click the first button"
            }
        }
        
        await websocket.send(json.dumps(agent_msg))
        response = await websocket.recv()
        data = json.loads(response)
        
        if data.get("type") == "agent_execution_result":
            payload = data.get("payload", {})
            logger.info(f"✅ Agent execution: {payload.get('success', False)}")
        else:
            logger.error(f"❌ Agent Execution failed: {data}")
            return False
        
        # Close connection
        await websocket.close()
        
        logger.info("\n" + "=" * 50)
        logger.info("🎉 All tests passed! Unified system is working perfectly!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test error: {e}")
        return False

async def main():
    """Main test function"""
    success = await test_unified_system()
    return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1) 