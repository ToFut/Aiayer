#!/usr/bin/env python3
"""
Quick test to verify screen sharing is working after backend fix.
"""

import asyncio
import json
import websockets
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_screen_sharing():
    """Test screen sharing functionality with backend"""
    
    logger.info("🧪 Testing Screen Sharing with Fixed Backend...")
    
    try:
        # Connect to backend
        logger.info("🔗 Connecting to backend...")
        async with websockets.connect('ws://localhost:8767') as ws:
            
            # Wait for connection message
            connection_msg = await asyncio.wait_for(ws.recv(), timeout=5)
            connection_data = json.loads(connection_msg)
            logger.info(f"✅ Connected: {connection_data.get('message', 'Connected')}")
            
            # Send screen sharing request
            logger.info("📺 Requesting screen sharing...")
            request = {
                "type": "start_screen_sharing",
                "timestamp": asyncio.get_event_loop().time()
            }
            
            await ws.send(json.dumps(request))
            logger.info("📤 Screen sharing request sent")
            
            # Wait for response
            response_msg = await asyncio.wait_for(ws.recv(), timeout=10)
            response_data = json.loads(response_msg)
            
            logger.info(f"📨 Response type: {response_data.get('type')}")
            
            if response_data.get('type') == 'screen_frame':
                logger.info("🎉 SUCCESS: Screen frame received!")
                logger.info(f"   Resolution: {response_data.get('width')}x{response_data.get('height')}")
                logger.info(f"   Format: {response_data.get('format')}")
                logger.info(f"   FPS: {response_data.get('fps')}")
                logger.info(f"   UI Elements: {len(response_data.get('ui_elements', []))}")
                logger.info(f"   Cursor: {response_data.get('cursor_position')}")
                logger.info(f"   Data size: {len(response_data.get('data', ''))} chars")
                return True
                
            elif response_data.get('type') == 'screen_sharing_error':
                logger.error(f"❌ Screen sharing error: {response_data.get('message')}")
                return False
                
            else:
                logger.warning(f"⚠️ Unexpected response: {response_data}")
                return False
                
    except asyncio.TimeoutError:
        logger.error("❌ Timeout waiting for response")
        return False
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

async def main():
    """Main test function"""
    
    logger.info("🚀 Starting Screen Sharing Fix Test...")
    
    success = await test_screen_sharing()
    
    if success:
        logger.info("🎉 Screen sharing is working!")
        logger.info("✅ The backend fix was successful")
        logger.info("💡 You can now click the 📺 button in the chat interface")
        return True
    else:
        logger.error("❌ Screen sharing is not working")
        logger.error("🔧 Check backend logs for more details")
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)