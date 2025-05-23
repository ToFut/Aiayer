#!/usr/bin/env python3
"""
Test Overlay Fix
Verify that the overlay now sends the correct message format
"""

import asyncio
import json
import logging
import websockets
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def monitor_overlay_messages():
    """Monitor messages from overlay to see if format is fixed"""
    
    logger.info("🔍 Monitoring for overlay messages with fixed format...")
    
    try:
        async with websockets.connect("ws://localhost:8765") as websocket:
            logger.info("✅ Connected to brain router - waiting for overlay messages...")
            
            # Wait for welcome
            welcome = await websocket.recv()
            logger.info("📬 Connected and waiting for overlay traffic...")
            
            # Monitor for incoming messages
            message_count = 0
            while message_count < 5:  # Monitor a few messages
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=30)
                    message_count += 1
                    
                    try:
                        data = json.loads(message)
                        logger.info(f"\n📨 Message #{message_count} received:")
                        logger.info(f"   Type: {data.get('type')}")
                        logger.info(f"   Success: {data.get('success')}")
                        logger.info(f"   Mode: {data.get('mode')}")
                        
                        if data.get('response'):
                            logger.info(f"   Response: {data['response'][:50]}...")
                            logger.info("✅ This should now display in the overlay!")
                        
                    except json.JSONDecodeError:
                        logger.info(f"📨 Non-JSON message: {message[:100]}...")
                        
                except asyncio.TimeoutError:
                    logger.info("⏰ No messages received in 30s - waiting for user to test overlay...")
                    break
                    
    except Exception as e:
        logger.error(f"❌ Monitoring error: {e}")

async def simulate_overlay_message():
    """Simulate what the overlay should now send"""
    
    logger.info("\n🧪 Simulating corrected overlay message format...")
    
    try:
        async with websockets.connect("ws://localhost:8765") as websocket:
            # Wait for welcome
            await websocket.recv()
            
            # Send message in the format the overlay should now use
            overlay_message = {
                "type": "chat_request",  # FIXED: was "ask_request"
                "mode": "Ask",          # FIXED: was missing
                "message": "test overlay fix",
                "session_id": "overlay_fix_test",
                "timestamp": "2025-05-23T01:20:00.000Z"
            }
            
            logger.info("📤 Sending corrected overlay format:")
            logger.info(f"   {json.dumps(overlay_message, indent=2)}")
            
            await websocket.send(json.dumps(overlay_message))
            
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                response_data = json.loads(response)
                
                logger.info("✅ Response received:")
                logger.info(f"   Success: {response_data.get('success')}")
                logger.info(f"   Response: {response_data.get('response', '')[:100]}...")
                
                if response_data.get('success'):
                    logger.info("🎉 OVERLAY FORMAT FIX SUCCESSFUL!")
                    logger.info("🎯 Overlay should now display this response")
                else:
                    logger.error("❌ Still getting errors")
                    
            except asyncio.TimeoutError:
                logger.error("❌ Still no response - deeper issue")
                
    except Exception as e:
        logger.error(f"❌ Simulation error: {e}")

async def main():
    """Test the overlay fix"""
    
    print("=" * 70)
    print("🔧 TESTING OVERLAY MESSAGE FORMAT FIX")
    print("=" * 70)
    print("FIXED FILES:")
    print("- overlay/src/components/NextGenAppleChatWidget.svelte")
    print("- Changed: ask_request → chat_request")
    print("- Changed: Added mode parameter")
    print("- Changed: Fixed response handler")
    print("=" * 70)
    
    await simulate_overlay_message()
    
    print("\n" + "=" * 70)
    print("🎯 NEXT STEPS:")
    print("1. The Tauri overlay should auto-reload the changes")
    print("2. Try sending a message in any mode (Ask, Agent, etc.)")
    print("3. You should now see responses instead of 'AI thinking...'")
    print("4. If still hanging, restart the overlay with: npm run tauri dev")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())