#!/usr/bin/env python3
"""
Debug WebSocket Traffic
Monitor actual WebSocket traffic to see what messages are being sent/received
"""

import asyncio
import json
import logging
import websockets
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketMonitor:
    def __init__(self):
        self.clients = {}
        self.message_count = 0
        
    async def monitor_connections(self):
        """Monitor WebSocket connections on port 8765"""
        
        logger.info("🕵️ Starting WebSocket traffic monitor on port 8765...")
        
        async def handle_client(websocket, path):
            client_id = f"monitor_{int(time.time() * 1000)}"
            self.clients[client_id] = websocket
            logger.info(f"👀 Monitor client connected: {client_id}")
            
            try:
                async for message in websocket:
                    self.message_count += 1
                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    
                    try:
                        data = json.loads(message)
                        logger.info(f"📨 [{timestamp}] Message #{self.message_count}")
                        logger.info(f"   Type: {data.get('type', 'unknown')}")
                        logger.info(f"   Keys: {list(data.keys())}")
                        if 'mode' in data:
                            logger.info(f"   Mode: {data['mode']}")
                        if 'message' in data:
                            logger.info(f"   Content: {data['message'][:50]}...")
                        logger.info(f"   Full: {json.dumps(data, indent=2)}")
                        
                    except json.JSONDecodeError:
                        logger.info(f"📨 [{timestamp}] Non-JSON message: {message[:100]}...")
                        
            except websockets.exceptions.ConnectionClosed:
                logger.info(f"👋 Monitor client disconnected: {client_id}")
            except Exception as e:
                logger.error(f"❌ Monitor error: {e}")
            finally:
                if client_id in self.clients:
                    del self.clients[client_id]
        
        # This won't work as we can't bind to the same port
        # Let me try a different approach
        logger.info("💡 Cannot monitor directly - will connect as client instead")

async def debug_actual_traffic():
    """Connect as a client and monitor what messages we send/receive"""
    
    logger.info("🔍 Debugging actual WebSocket traffic...")
    
    try:
        async with websockets.connect("ws://localhost:8765") as websocket:
            logger.info("✅ Connected to brain router for traffic debugging")
            
            # Wait for welcome message
            welcome_raw = await websocket.recv()
            logger.info(f"📬 RAW Welcome: {welcome_raw}")
            
            try:
                welcome_data = json.loads(welcome_raw)
                logger.info(f"📬 Parsed Welcome: {json.dumps(welcome_data, indent=2)}")
            except:
                logger.error("❌ Could not parse welcome message as JSON")
            
            # Test 1: Send the EXACT format that the overlay should be sending
            test_message = {
                "type": "chat_request",
                "mode": "Ask", 
                "message": "hello test",
                "session_id": "debug_traffic_test",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info("\n📤 Sending test message...")
            logger.info(f"📝 Message being sent: {json.dumps(test_message, indent=2)}")
            
            await websocket.send(json.dumps(test_message))
            logger.info("✅ Message sent successfully")
            
            # Wait for response
            logger.info("⏳ Waiting for response...")
            
            try:
                response_raw = await asyncio.wait_for(websocket.recv(), timeout=10)
                logger.info(f"📨 RAW Response: {response_raw}")
                
                try:
                    response_data = json.loads(response_raw)
                    logger.info(f"📨 Parsed Response: {json.dumps(response_data, indent=2)}")
                    
                    # Check if this is what the overlay expects
                    if response_data.get('success') and response_data.get('response'):
                        logger.info("✅ Response format matches what overlay expects")
                        logger.info(f"🎯 Response content: {response_data['response'][:100]}...")
                    else:
                        logger.warning("⚠️ Response format might not match overlay expectations")
                        
                except json.JSONDecodeError:
                    logger.error("❌ Response is not valid JSON")
                    
            except asyncio.TimeoutError:
                logger.error("❌ NO RESPONSE RECEIVED - This is the hanging issue!")
                logger.error("🔍 Brain router is not responding to chat_request messages")
                
    except Exception as e:
        logger.error(f"❌ Traffic debugging error: {e}")

async def test_all_modes():
    """Test all modes to see which ones work"""
    
    logger.info("\n🧪 Testing all modes individually...")
    
    modes = ["Ask", "Agent", "Suggest", "General"]
    
    for mode in modes:
        logger.info(f"\n📤 Testing {mode} mode...")
        
        try:
            async with websockets.connect("ws://localhost:8765") as websocket:
                # Wait for welcome
                await websocket.recv()
                
                test_message = {
                    "type": "chat_request",
                    "mode": mode,
                    "message": f"test {mode.lower()} mode",
                    "session_id": f"debug_{mode.lower()}_test"
                }
                
                await websocket.send(json.dumps(test_message))
                
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    response_data = json.loads(response)
                    
                    if response_data.get('success'):
                        logger.info(f"✅ {mode} mode: WORKING")
                        logger.info(f"   Response: {response_data.get('response', '')[:50]}...")
                    else:
                        logger.error(f"❌ {mode} mode: Got response but success=false")
                        logger.error(f"   Error: {response_data.get('error', 'unknown')}")
                        
                except asyncio.TimeoutError:
                    logger.error(f"❌ {mode} mode: TIMEOUT (hanging)")
                    
        except Exception as e:
            logger.error(f"❌ {mode} mode: CONNECTION ERROR - {e}")

async def check_brain_router_logs():
    """Check brain router logs for any errors"""
    
    logger.info("\n📋 Checking brain router logs...")
    
    try:
        # Check if there are recent error messages
        import subprocess
        
        result = subprocess.run([
            'tail', '-50', '/Users/segevbin/Desktop/SensAI/Aiayer/logs/enhanced_brain_router_automation.log'
        ], capture_output=True, text=True, timeout=5)
        
        if result.stdout:
            logger.info("📋 Recent brain router logs:")
            print(result.stdout)
        else:
            logger.warning("⚠️ No recent logs found")
            
        if result.stderr:
            logger.error(f"❌ Log reading error: {result.stderr}")
            
    except Exception as e:
        logger.warning(f"⚠️ Could not read logs: {e}")

async def main():
    """Run comprehensive traffic debugging"""
    
    print("=" * 70)
    print("🕵️ COMPREHENSIVE WEBSOCKET TRAFFIC DEBUGGING")
    print("=" * 70)
    print("Goal: Find exactly why messages are hanging")
    print("=" * 70)
    
    await check_brain_router_logs()
    await debug_actual_traffic()
    await test_all_modes()
    
    print("\n" + "=" * 70)
    print("📊 DEBUGGING SUMMARY")
    print("=" * 70)
    print("Check the output above to see:")
    print("1. If brain router is receiving messages")
    print("2. If brain router is sending responses") 
    print("3. Which modes are working/hanging")
    print("4. What the actual message format is")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())