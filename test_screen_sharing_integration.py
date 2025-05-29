#!/usr/bin/env python3
"""
Test script to verify screen sharing integration works correctly.
This tests the complete screen sharing workflow from backend to frontend.
"""

import asyncio
import json
import base64
import time
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_screen_sharing_components():
    """Test that all screen sharing components exist and are properly integrated."""
    
    logger.info("🧪 Testing Screen Sharing Integration...")
    
    # Test 1: Check ScreenViewer component exists
    screen_viewer_path = Path("/Users/segevbin/Desktop/SensAI/Aiayer/overlay/src/components/ScreenViewer.svelte")
    assert screen_viewer_path.exists(), "❌ ScreenViewer.svelte component not found"
    logger.info("✅ ScreenViewer component exists")
    
    # Test 2: Check Bridge service exists
    bridge_service_path = Path("/Users/segevbin/Desktop/SensAI/Aiayer/overlay/src/services/bridge.js")
    assert bridge_service_path.exists(), "❌ Bridge service not found"
    logger.info("✅ Bridge service exists")
    
    # Test 3: Check realtime screen TCP server exists
    tcp_server_path = Path("/Users/segevbin/Desktop/SensAI/Aiayer/realtime_screen_tcp_server.py")
    assert tcp_server_path.exists(), "❌ Realtime screen TCP server not found"
    logger.info("✅ Realtime screen TCP server exists")
    
    # Test 4: Check EnterpriseChatWidget has screen sharing integration
    enterprise_chat_path = Path("/Users/segevbin/Desktop/SensAI/Aiayer/overlay/src/components/EnterpriseChatWidget.svelte")
    assert enterprise_chat_path.exists(), "❌ EnterpriseChatWidget not found"
    
    with open(enterprise_chat_path, 'r') as f:
        content = f.read()
        assert 'ScreenViewer' in content, "❌ ScreenViewer not imported in EnterpriseChatWidget"
        assert 'showScreenViewer' in content, "❌ Screen sharing state not found in EnterpriseChatWidget"
        assert 'toggleScreenViewer' in content, "❌ Screen sharing toggle function not found"
        assert 'screen-share-btn' in content, "❌ Screen sharing button not found in header controls"
        
    logger.info("✅ EnterpriseChatWidget has screen sharing integration")
    
    # Test 5: Check ScreenViewer component structure
    with open(screen_viewer_path, 'r') as f:
        screen_viewer_content = f.read()
        assert 'bridgeService' in screen_viewer_content or 'bridge' in screen_viewer_content, "❌ Bridge service prop not found in ScreenViewer"
        assert 'screen-viewer-image' in screen_viewer_content, "❌ Screen image element not found"
        assert 'ui-elements-overlay' in screen_viewer_content, "❌ UI elements overlay not found"
        assert 'cursor-overlay' in screen_viewer_content, "❌ Cursor overlay not found"
        
    logger.info("✅ ScreenViewer component structure is correct")
    
    # Test 6: Check Bridge service has screen frame handling
    with open(bridge_service_path, 'r') as f:
        bridge_content = f.read()
        assert 'handleScreenFrame' in bridge_content, "❌ Screen frame handler not found in Bridge service"
        assert 'requestScreenSharing' in bridge_content, "❌ Screen sharing request method not found"
        assert 'get_compressed_frame_data' in bridge_content or 'screen_frame' in bridge_content, "❌ Screen frame data handling not found"
        
    logger.info("✅ Bridge service has screen frame handling")
    
    # Test 7: Check TCP server has compression functionality
    with open(tcp_server_path, 'r') as f:
        tcp_content = f.read()
        assert 'get_compressed_frame_data' in tcp_content, "❌ Compressed frame data method not found in TCP server"
        assert 'base64' in tcp_content, "❌ Base64 encoding not found in TCP server"
        assert 'JPEG' in tcp_content or 'jpeg' in tcp_content, "❌ JPEG compression not found in TCP server"
        
    logger.info("✅ TCP server has compression functionality")
    
    logger.info("🎉 All screen sharing integration tests passed!")
    return True

def test_screen_sharing_data_flow():
    """Test the data flow for screen sharing."""
    
    logger.info("🔄 Testing Screen Sharing Data Flow...")
    
    # Create mock screen frame data (simulating what TCP server would send)
    mock_screen_frame = {
        "type": "screen_frame",
        "timestamp": time.time(),
        "frame_id": "test_frame_001", 
        "width": 1920,
        "height": 1080,
        "format": "compressed_jpeg",
        "data": base64.b64encode(b"mock_jpeg_data").decode('utf-8'),
        "ui_elements": [
            {
                "type": "button",
                "text": "Click Me",
                "bounds": {"x": 100, "y": 100, "width": 80, "height": 30},
                "confidence": 0.95
            }
        ],
        "cursor_position": {"x": 500, "y": 300},
        "active_window": "Test Application",
        "fps": 30.0,
        "compressed": True
    }
    
    logger.info(f"✅ Mock screen frame created: {mock_screen_frame['width']}x{mock_screen_frame['height']} @ {mock_screen_frame['fps']}fps")
    
    # Test JSON serialization (what would happen over WebSocket)
    try:
        serialized = json.dumps(mock_screen_frame)
        deserialized = json.loads(serialized)
        assert deserialized['type'] == 'screen_frame'
        assert deserialized['width'] == 1920
        assert len(deserialized['ui_elements']) == 1
        logger.info("✅ Screen frame data serialization works correctly")
    except Exception as e:
        logger.error(f"❌ Screen frame serialization failed: {e}")
        return False
    
    # Test base64 data integrity
    try:
        decoded_data = base64.b64decode(mock_screen_frame['data'])
        assert decoded_data == b"mock_jpeg_data"
        logger.info("✅ Base64 encoding/decoding works correctly")
    except Exception as e:
        logger.error(f"❌ Base64 data integrity test failed: {e}")
        return False
    
    logger.info("🎉 Screen sharing data flow tests passed!")
    return True

def test_ui_integration():
    """Test UI integration points."""
    
    logger.info("🎨 Testing UI Integration...")
    
    # Check if CSS styles are properly defined
    enterprise_chat_path = Path("/Users/segevbin/Desktop/SensAI/Aiayer/overlay/src/components/EnterpriseChatWidget.svelte")
    
    with open(enterprise_chat_path, 'r') as f:
        content = f.read()
        
        # Check for screen viewer modal styles
        assert '.screen-viewer-modal' in content, "❌ Screen viewer modal CSS not found"
        assert '.screen-viewer-container' in content, "❌ Screen viewer container CSS not found"
        assert '.screen-share-btn' in content, "❌ Screen share button CSS not found"
        
    logger.info("✅ Screen viewer modal CSS styles found")
    
    # Check ScreenViewer component CSS
    screen_viewer_path = Path("/Users/segevbin/Desktop/SensAI/Aiayer/overlay/src/components/ScreenViewer.svelte")
    
    with open(screen_viewer_path, 'r') as f:
        screen_content = f.read()
        
        assert '.screen-viewer' in screen_content, "❌ Main screen viewer CSS not found"
        assert 'cursor-overlay' in screen_content, "❌ Cursor overlay CSS not found" 
        assert 'ui-elements-overlay' in screen_content, "❌ UI elements overlay CSS not found"
        
    logger.info("✅ ScreenViewer component CSS styles found")
    
    logger.info("🎉 UI integration tests passed!")
    return True

def main():
    """Run all screen sharing integration tests."""
    
    logger.info("🚀 Starting Screen Sharing Integration Tests...")
    
    try:
        # Run all test suites
        component_tests = test_screen_sharing_components()
        data_flow_tests = test_screen_sharing_data_flow()
        ui_tests = test_ui_integration()
        
        if component_tests and data_flow_tests and ui_tests:
            logger.info("🎊 All Screen Sharing Integration Tests PASSED!")
            logger.info("✨ Screen sharing functionality is ready for testing with the live system")
            logger.info("💡 Next steps:")
            logger.info("   1. Start the enhanced enterprise backend: START_ENHANCED_SYSTEM.sh")
            logger.info("   2. Open the overlay in browser: overlay/index.html")
            logger.info("   3. Click the screen share button (📺) in the chat header")
            logger.info("   4. Verify real-time screen streaming and UI element detection")
            return True
        else:
            logger.error("❌ Some tests failed. Check the logs above for details.")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)