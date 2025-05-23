#!/usr/bin/env python3
"""
Debug Message Processing
Test where exactly messages are getting stuck in the pipeline
"""

import asyncio
import json
import logging
import websockets
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_basic_message_processing():
    """Test direct message processing to find where it hangs"""
    
    logger.info("🧪 Testing basic message processing...")
    
    try:
        # Connect to brain router
        async with websockets.connect("ws://localhost:8765") as websocket:
            logger.info("✅ Connected to brain router")
            
            # Wait for welcome message
            welcome = await asyncio.wait_for(websocket.recv(), timeout=5)
            logger.info(f"📬 Welcome: {json.loads(welcome).get('type')}")
            
            # Test 1: Simple Ask mode message
            logger.info("\n🧪 TEST 1: Simple Ask Mode")
            ask_message = {
                "type": "chat_request",
                "mode": "Ask",
                "message": "hello",
                "session_id": "debug_test_ask"
            }
            
            logger.info("📤 Sending Ask message...")
            await websocket.send(json.dumps(ask_message))
            
            try:
                start_time = time.time()
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                elapsed = time.time() - start_time
                
                response_data = json.loads(response)
                logger.info(f"✅ Ask response received in {elapsed:.2f}s")
                logger.info(f"📝 Response type: {response_data.get('type')}")
                logger.info(f"📝 Success: {response_data.get('success')}")
                logger.info(f"📝 Response snippet: {str(response_data.get('response', ''))[:100]}...")
                
            except asyncio.TimeoutError:
                logger.error("❌ Ask mode TIMEOUT - no response received")
                
            # Test 2: Simple Agent mode message  
            logger.info("\n🧪 TEST 2: Simple Agent Mode")
            agent_message = {
                "type": "chat_request",
                "mode": "Agent",
                "message": "hello",
                "session_id": "debug_test_agent"
            }
            
            logger.info("📤 Sending Agent message...")
            await websocket.send(json.dumps(agent_message))
            
            try:
                start_time = time.time()
                response = await asyncio.wait_for(websocket.recv(), timeout=15)
                elapsed = time.time() - start_time
                
                response_data = json.loads(response)
                logger.info(f"✅ Agent response received in {elapsed:.2f}s")
                logger.info(f"📝 Response type: {response_data.get('type')}")
                logger.info(f"📝 Success: {response_data.get('success')}")
                logger.info(f"📝 Response snippet: {str(response_data.get('response', ''))[:100]}...")
                
            except asyncio.TimeoutError:
                logger.error("❌ Agent mode TIMEOUT - no response received")
                
            # Test 3: General mode message
            logger.info("\n🧪 TEST 3: General Mode") 
            general_message = {
                "type": "chat_request",
                "mode": "General",
                "message": "hello",
                "session_id": "debug_test_general"
            }
            
            logger.info("📤 Sending General message...")
            await websocket.send(json.dumps(general_message))
            
            try:
                start_time = time.time()
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                elapsed = time.time() - start_time
                
                response_data = json.loads(response)
                logger.info(f"✅ General response received in {elapsed:.2f}s")
                logger.info(f"📝 Response type: {response_data.get('type')}")
                logger.info(f"📝 Success: {response_data.get('success')}")
                logger.info(f"📝 Response snippet: {str(response_data.get('response', ''))[:100]}...")
                
            except asyncio.TimeoutError:
                logger.error("❌ General mode TIMEOUT - no response received")
                
            # Test 4: Check if memory system is working
            logger.info("\n🧪 TEST 4: Memory System Check")
            memory_message = {
                "type": "chat_request",
                "mode": "Ask",
                "message": "what did I just say?",
                "session_id": "debug_test_memory"
            }
            
            logger.info("📤 Sending memory test message...")
            await websocket.send(json.dumps(memory_message))
            
            try:
                start_time = time.time()
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                elapsed = time.time() - start_time
                
                response_data = json.loads(response)
                logger.info(f"✅ Memory test response received in {elapsed:.2f}s")
                logger.info(f"📝 Response: {str(response_data.get('response', ''))[:200]}...")
                
                # Check if it references previous messages
                if "hello" in response_data.get('response', '').lower():
                    logger.info("✅ Memory system is working - found reference to previous message")
                else:
                    logger.warning("⚠️ Memory system may not be working properly")
                    
            except asyncio.TimeoutError:
                logger.error("❌ Memory test TIMEOUT - no response received")
                
    except Exception as e:
        logger.error(f"❌ Connection error: {e}")

async def test_system_status():
    """Test system status endpoint"""
    
    logger.info("\n🧪 Testing system status...")
    
    try:
        async with websockets.connect("ws://localhost:8765") as websocket:
            # Wait for welcome
            await websocket.recv()
            
            # Request system status
            status_message = {
                "type": "system_status"
            }
            
            logger.info("📤 Requesting system status...")
            await websocket.send(json.dumps(status_message))
            
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                status_data = json.loads(response)
                
                logger.info(f"✅ System status received")
                logger.info(f"📊 Status: {status_data.get('status')}")
                logger.info(f"📊 Connected clients: {status_data.get('connected_clients')}")
                logger.info(f"📊 Available modes: {status_data.get('available_modes')}")
                logger.info(f"📊 Automation active: {status_data.get('automation_system', {}).get('ui_automation_active')}")
                logger.info(f"📊 Memory system: {status_data.get('memory_system', {}).get('semantic_search_active')}")
                
            except asyncio.TimeoutError:
                logger.error("❌ System status TIMEOUT")
                
    except Exception as e:
        logger.error(f"❌ Status check error: {e}")

async def main():
    """Run all debug tests"""
    
    print("=" * 60)
    print("🔧 DEBUGGING MESSAGE PROCESSING PIPELINE")
    print("=" * 60)
    
    await test_system_status()
    await test_basic_message_processing()
    
    print("\n" + "=" * 60)
    print("📊 DEBUG RESULTS SUMMARY")
    print("=" * 60)
    print("Check the output above to see which modes are working/hanging")
    print("If all modes timeout, the issue is in the core message handler")
    print("If only specific modes timeout, the issue is in those mode handlers")

if __name__ == "__main__":
    asyncio.run(main())