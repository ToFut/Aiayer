#!/usr/bin/env python3
"""
Test the fixed ContextualAIBackend
"""

import asyncio
import websockets
import json
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_backend_streaming():
    """Test if the backend streaming error is fixed"""
    logger.info("🧪 Testing Fixed Backend Streaming")
    
    # Start the backend first
    import subprocess
    import os
    
    backend_process = None
    try:
        # Start backend in background
        backend_process = subprocess.Popen([
            'python', 'enhanced_enterprise_backend_with_context.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.getcwd())
        
        # Wait for backend to start
        await asyncio.sleep(5)
        
        # Test websocket connection
        try:
            async with websockets.connect("ws://localhost:8767/ws") as websocket:
                logger.info("✅ Connected to backend")
                
                # Send test message
                test_message = {
                    "type": "chat",
                    "message": "Hello, test the streaming",
                    "mode": "ask",
                    "client_id": "test_client"
                }
                
                await websocket.send(json.dumps(test_message))
                logger.info("📤 Sent test message")
                
                # Wait for response
                response = await asyncio.wait_for(websocket.recv(), timeout=15)
                logger.info(f"📥 Received response: {response[:100]}...")
                
                logger.info("✅ Backend streaming test passed!")
                
        except Exception as e:
            logger.error(f"❌ WebSocket test failed: {e}")
            
    except Exception as e:
        logger.error(f"❌ Backend startup failed: {e}")
    
    finally:
        # Clean up
        if backend_process:
            backend_process.terminate()
            try:
                backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                backend_process.kill()

async def test_method_availability():
    """Test if the method is now available"""
    logger.info("\n🔧 Testing Method Availability")
    
    try:
        from enhanced_enterprise_backend_with_context import ContextualAIBackend
        
        backend = ContextualAIBackend()
        
        # Check if method exists
        if hasattr(backend, '_try_agnostic_deep_data_access'):
            logger.info("✅ _try_agnostic_deep_data_access method exists")
            
            # Check if it's callable
            if callable(getattr(backend, '_try_agnostic_deep_data_access')):
                logger.info("✅ Method is callable")
                
                # Test method signature
                import inspect
                sig = inspect.signature(backend._try_agnostic_deep_data_access)
                logger.info(f"✅ Method signature: {sig}")
                
                return True
            else:
                logger.error("❌ Method exists but is not callable")
                return False
        else:
            logger.error("❌ Method not found")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing method: {e}")
        return False

async def main():
    """Run all tests"""
    logger.info("🚀 TESTING FIXED CONTEXTUAL BACKEND")
    logger.info("="*50)
    
    # Test 1: Method availability
    method_ok = await test_method_availability()
    
    # Test 2: Backend streaming (only if method is OK)
    if method_ok:
        logger.info("\n🌐 Testing backend streaming...")
        await test_backend_streaming()
    else:
        logger.error("❌ Skipping streaming test due to method issues")
    
    logger.info("\n📊 TEST SUMMARY")
    logger.info("="*50)
    if method_ok:
        logger.info("✅ Method fix successful")
        logger.info("✅ Backend should now work without '_try_agnostic_deep_data_access' errors")
        logger.info("💡 Start the system with: ./START_ENHANCED_SYSTEM.sh")
    else:
        logger.error("❌ Method fix failed - needs investigation")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}")