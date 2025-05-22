#!/usr/bin/env python3
"""
Test Overlay to Backend Connection
Simulates the exact connection flow that the Tauri overlay uses
"""
import asyncio
import json
import logging
import websockets
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_overlay_connection():
    """Test the connection flow that matches the Tauri overlay exactly."""
    logger.info("🎯 Testing Overlay-to-Backend Connection Flow")
    logger.info("=" * 60)
    
    # Test the main WebSocket server that the overlay connects to
    url = "ws://localhost:8765"
    
    try:
        logger.info(f"Connecting to main WebSocket server at {url}...")
        
        # Connect exactly like the Tauri overlay does
        websocket = await websockets.connect(url)
        logger.info("✅ Connected successfully")
        
        # Send registration message like the EnhancedBridge does
        registration_msg = {
            "type": "register",
            "payload": {
                "client_type": "ui",
                "version": "2.0.0",
                "capabilities": ["memory", "context", "notification"],
                "timestamp": 1700000000000  # Mock timestamp
            }
        }
        
        await websocket.send(json.dumps(registration_msg))
        logger.info("📤 Sent registration message")
        
        # Wait for registration confirmation
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            response_data = json.loads(response)
            logger.info(f"📨 Received: {response_data.get('type')} - {response_data.get('payload', {}).get('message', 'No message')}")
            
            if response_data.get('type') == 'registration_confirmed':
                logger.info("✅ Registration confirmed!")
            else:
                logger.warning(f"⚠️  Expected registration_confirmed, got {response_data.get('type')}")
            
        except asyncio.TimeoutError:
            logger.error("❌ No registration response within 5 seconds")
            return False
        
        # Test sending a user query (like the overlay would)
        logger.info("\n🤖 Testing AI Query Flow...")
        
        query_msg = {
            "type": "user_interaction",
            "payload": {
                "type": "query",
                "query": "Hello! Can you help me with something? This is a test from the overlay.",
                "timestamp": 1700000000000
            }
        }
        
        await websocket.send(json.dumps(query_msg))
        logger.info("📤 Sent user query")
        
        # Wait for AI response
        try:
            ai_response = await asyncio.wait_for(websocket.recv(), timeout=15)
            ai_data = json.loads(ai_response)
            
            logger.info(f"📨 Response type: {ai_data.get('type')}")
            
            if ai_data.get('type') == 'query_response':
                response_text = ai_data.get('payload', {}).get('response', '')
                if response_text and len(response_text.strip()) > 10:
                    logger.info("✅ Received meaningful AI response:")
                    logger.info(f"   📝 Response: {response_text[:200]}...")
                    logger.info(f"   📊 Length: {len(response_text)} characters")
                    
                    # Test context request
                    logger.info("\n🔍 Testing Context Request...")
                    context_msg = {
                        "type": "context_request",
                        "payload": {
                            "requestId": "test-123",
                            "timestamp": 1700000000000
                        }
                    }
                    
                    await websocket.send(json.dumps(context_msg))
                    logger.info("📤 Sent context request")
                    
                    try:
                        context_response = await asyncio.wait_for(websocket.recv(), timeout=5)
                        context_data = json.loads(context_response)
                        logger.info(f"📨 Context response: {context_data.get('type')}")
                        
                        if context_data.get('type') == 'context_response':
                            logger.info("✅ Context request working")
                        else:
                            logger.info(f"📋 Received {context_data.get('type')} instead of context_response")
                            
                    except asyncio.TimeoutError:
                        logger.warning("⏰ No context response within 5 seconds")
                    
                    await websocket.close()
                    return True
                else:
                    logger.error("❌ AI response is empty or too short")
                    logger.error(f"   Response: '{response_text}'")
            else:
                logger.error(f"❌ Expected query_response, got {ai_data.get('type')}")
                logger.error(f"   Full response: {ai_data}")
                
        except asyncio.TimeoutError:
            logger.error("❌ No AI response within 15 seconds")
            logger.error("   This suggests the LLM integration is not working")
        
        await websocket.close()
        return False
        
    except ConnectionRefusedError:
        logger.error("❌ Connection refused - main WebSocket server not running")
        return False
    except Exception as e:
        logger.error(f"❌ Connection error: {e}")
        return False

async def test_bridge_server_direct():
    """Test direct connection to bridge server."""
    logger.info("\n🌉 Testing Direct Bridge Server Connection...")
    
    try:
        websocket = await websockets.connect("ws://localhost:8766")
        logger.info("✅ Bridge server connection successful")
        
        # Send registration
        reg_msg = {"type": "register", "payload": {"client_type": "ui"}}
        await websocket.send(json.dumps(reg_msg))
        
        response = await asyncio.wait_for(websocket.recv(), timeout=5)
        response_data = json.loads(response)
        logger.info(f"📨 Bridge response: {response_data.get('type')}")
        
        await websocket.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Bridge server test failed: {e}")
        return False

async def main():
    """Run all tests."""
    logger.info("🔍 OVERLAY-BACKEND CONNECTION TEST")
    logger.info("This simulates the exact connection flow from the Tauri overlay")
    logger.info("=" * 60)
    
    # Test main connection flow
    main_test_result = await test_overlay_connection()
    
    # Test bridge server
    bridge_test_result = await test_bridge_server_direct()
    
    # Summary
    logger.info("\n🎯 TEST RESULTS:")
    logger.info("=" * 60)
    
    if main_test_result:
        logger.info("✅ MAIN CONNECTION: Working - Overlay can connect and get AI responses")
    else:
        logger.error("❌ MAIN CONNECTION: Failed - Check WebSocket server and LLM integration")
    
    if bridge_test_result:
        logger.info("✅ BRIDGE SERVER: Working - Direct connection successful")
    else:
        logger.error("❌ BRIDGE SERVER: Failed - Bridge server not responding")
    
    logger.info("\n💡 RECOMMENDATIONS:")
    if main_test_result and bridge_test_result:
        logger.info("🎉 All systems working! Your Tauri overlay should connect successfully.")
        logger.info("   You can now use the overlay to chat with the AI backend.")
    elif main_test_result:
        logger.info("✅ Main connection works - your overlay should function for basic chat.")
        logger.info("⚠️  Bridge server issues may affect sensor data integration.")
    else:
        logger.info("❌ Main connection issues detected.")
        logger.info("   1. Check if WebSocket server (port 8765) is running")
        logger.info("   2. Verify LLM service (Ollama) is working: ollama list")
        logger.info("   3. Check logs/websocket/ws_server_8765.log for errors")
    
    return main_test_result

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)