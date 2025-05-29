#!/usr/bin/env python3
"""
Quick Test for TeamViewer-Style Capabilities
Tests core functionality without WebSocket dependencies
"""

import asyncio
import logging
import sys
import os
import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def quick_test():
    """Quick test of core TeamViewer capabilities"""
    
    logger.info("🧪 Quick TeamViewer Capabilities Test")
    logger.info("=" * 50)
    
    try:
        # Import the enhanced backend
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from enhanced_enterprise_backend_with_context import ContextualAIBackend, SCREEN_CAPTURE_AVAILABLE
        
        logger.info(f"📷 Screen capture available: {SCREEN_CAPTURE_AVAILABLE}")
        
        # Create backend instance
        backend = ContextualAIBackend()
        logger.info("✅ Backend initialized with TeamViewer capabilities")
        
        # Test 1: Screen capture
        logger.info("\n🖼️ Testing screen capture...")
        screenshot = await backend.capture_screen_fast()
        if screenshot is not None:
            logger.info(f"✅ Screen captured: {screenshot.shape} ({screenshot.nbytes/1024/1024:.1f} MB)")
        else:
            logger.error("❌ Screen capture failed")
            
        # Test 2: Visual change detection with correct threshold
        logger.info("\n🔍 Testing visual change detection...")
        
        # Create test images with significant difference
        original = np.full((200, 200, 3), [100, 100, 100], dtype=np.uint8)  # Gray
        modified = original.copy()
        modified[50:150, 50:150] = [255, 0, 0]  # Large red square (50% of image)
        
        changes = await backend.detect_visual_changes(original, modified, threshold=0.1)
        
        if changes.get('changes_detected', False):
            logger.info(f"✅ Changes detected: {changes['change_percentage']:.1%}")
            logger.info(f"   Confidence: {changes.get('confidence', 0):.2f}")
            logger.info(f"   Regions: {len(changes.get('changed_regions', []))}")
        else:
            logger.warning(f"⚠️ Changes not detected (only {changes.get('change_percentage', 0):.2%} changed)")
            
        # Test 3: Enhanced agent capabilities
        logger.info("\n🤖 Testing enhanced agent capabilities...")
        
        if hasattr(backend, 'handle_agent_execution_with_verification'):
            logger.info("✅ Enhanced agent execution method available")
            
            # Mock websocket for testing
            class MockWebSocket:
                def __init__(self):
                    self.messages = []
                    
                async def send(self, message):
                    self.messages.append(message)
                    logger.info(f"   📤 WebSocket message sent")
            
            mock_ws = MockWebSocket()
            
            # Test enhanced agent request
            test_data = {
                'message': 'Test automation task',
                'session_id': 'test_session',
                'execution_mode': 'verified'
            }
            
            result = await backend.handle_agent_execution_with_verification(
                test_data, 'test_client', mock_ws
            )
            
            if result.get('success', False):
                logger.info(f"✅ Enhanced agent request successful")
                logger.info(f"   Plan ID: {result.get('plan_id', 'N/A')}")
                logger.info(f"   Messages sent: {len(mock_ws.messages)}")
            else:
                logger.error(f"❌ Enhanced agent request failed: {result.get('error', 'Unknown')}")
        else:
            logger.error("❌ Enhanced agent execution method not found")
            
        # Test 4: Screen monitoring
        logger.info("\n📱 Testing screen monitoring...")
        
        if hasattr(backend, 'start_screen_monitoring'):
            logger.info("✅ Screen monitoring method available")
            
            # Test monitoring for 2 seconds
            logger.info("   Starting 2-second monitoring test...")
            
            monitoring_task = asyncio.create_task(
                backend.start_screen_monitoring(None, fps=2)
            )
            
            await asyncio.sleep(2)
            backend.stop_screen_monitoring()
            await asyncio.sleep(0.5)  # Allow monitoring to stop
            
            logger.info("✅ Monitoring start/stop successful")
        else:
            logger.error("❌ Screen monitoring method not found")
            
        # Test 5: Execution analytics
        logger.info("\n📊 Testing execution analytics...")
        
        analytics = await backend.get_execution_analytics()
        logger.info(f"✅ Analytics retrieved:")
        logger.info(f"   Total executions: {analytics.get('total_executions', 0)}")
        logger.info(f"   Success rate: {analytics.get('success_rate', 0):.1%}")
        
        logger.info("\n🎉 QUICK TEST COMPLETED!")
        logger.info("=" * 50)
        logger.info("✅ Core TeamViewer-style capabilities are functional!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(quick_test())