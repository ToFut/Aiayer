#!/usr/bin/env python3
"""
Test screen sharing with multiple attempts to handle startup delay.
"""

import asyncio
import json
import websockets
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_screen_sharing_with_retries():
    """Test screen sharing functionality with multiple attempts"""
    
    logger.info("🧪 Testing Screen Sharing with Multiple Attempts...")
    
    try:
        # Connect to backend
        logger.info("🔗 Connecting to backend...")
        async with websockets.connect('ws://localhost:8767') as ws:
            
            # Wait for connection message
            connection_msg = await asyncio.wait_for(ws.recv(), timeout=5)
            connection_data = json.loads(connection_msg)
            logger.info(f"✅ Connected: {connection_data.get('message', 'Connected')}")
            
            # Try screen sharing multiple times with delays
            for attempt in range(3):
                logger.info(f"📺 Screen sharing attempt {attempt + 1}/3...")
                
                # Send screen sharing request
                request = {
                    "type": "start_screen_sharing",
                    "timestamp": time.time()
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
                    
                    # Also test if the image data is valid base64
                    try:
                        import base64
                        decoded = base64.b64decode(response_data.get('data', ''))
                        logger.info(f"   ✅ Valid base64 image data: {len(decoded)} bytes")
                    except Exception as e:
                        logger.warning(f"   ⚠️ Image data validation failed: {e}")
                    
                    return True
                    
                elif response_data.get('type') == 'screen_sharing_error':
                    logger.warning(f"⚠️ Screen sharing error (attempt {attempt + 1}): {response_data.get('message')}")
                    
                    if attempt < 2:  # Not the last attempt
                        logger.info(f"⏳ Waiting 3 seconds before retry...")
                        await asyncio.sleep(3)
                    
                else:
                    logger.warning(f"⚠️ Unexpected response: {response_data}")
                    
            logger.error("❌ All attempts failed")
            return False
                
    except asyncio.TimeoutError:
        logger.error("❌ Timeout waiting for response")
        return False
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

async def main():
    """Main test function"""
    
    logger.info("🚀 Starting Screen Sharing Test with Retries...")
    
    success = await test_screen_sharing_with_retries()
    
    if success:
        logger.info("🎉 Screen sharing is working!")
        logger.info("✅ The backend and screen capture are functional")
        logger.info("💡 You can now click the 📺 button in the chat interface")
        logger.info("🔧 If the frontend button doesn't work, check browser console for errors")
        return True
    else:
        logger.error("❌ Screen sharing is not working after all attempts")
        logger.error("🔧 Possible issues:")
        logger.error("   - Screen capture permissions not granted")
        logger.error("   - Screen capture initialization delay")
        logger.error("   - Backend screen capture module issues")
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)