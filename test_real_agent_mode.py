#!/usr/bin/env python3
"""
Test Real Agent Mode End-to-End
Test the full Agent mode pipeline with UI automation
"""

import asyncio
import websockets
import json
import logging
import sys
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_real_agent_mode():
    """Test Agent mode through the enterprise backend"""
    
    print("🧪 Testing Real Agent Mode End-to-End")
    print("=" * 50)
    
    # Connect to enterprise backend
    uri = "ws://127.0.0.1:8767"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to enterprise backend")
            
            # Test UI automation commands
            test_cases = [
                "click at position 150 150",
                "type hello world",
                "press return key",
                "click at 200 200 then type AI Agent test"
            ]
            
            for i, query in enumerate(test_cases, 1):
                print(f"\n🤖 Test {i}: {query}")
                print("-" * 40)
                
                # Send Agent mode request
                message = {
                    "type": "chat_request",
                    "mode": "Agent",
                    "query": query,
                    "user_id": "test_user",
                    "session_id": "ui_test_session",
                    "timestamp": asyncio.get_event_loop().time()
                }
                
                print(f"📤 Sending: {query}")
                await websocket.send(json.dumps(message))
                
                # Wait for response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(response)
                    
                    if data.get("type") == "chat_response":
                        payload = data.get("payload", {})
                        success = payload.get("success", False)
                        response_text = payload.get("response", "")
                        confidence = payload.get("confidence", 0)
                        
                        print(f"📥 Success: {success}")
                        print(f"📥 Confidence: {confidence:.2f}")
                        
                        # Check for execution indicators
                        if "Task Completed Successfully" in response_text:
                            print("✅ REAL EXECUTION DETECTED!")
                        elif "plan" in response_text.lower() or "would" in response_text.lower():
                            print("⚠️ Planning fallback detected")
                        
                        # Show first 200 chars of response
                        preview = response_text[:200] + "..." if len(response_text) > 200 else response_text
                        print(f"📄 Response: {preview}")
                        
                    else:
                        print(f"❌ Unexpected response type: {data.get('type')}")
                        print(f"   Data: {data}")
                        
                except asyncio.TimeoutError:
                    print("⏰ Response timeout")
                except Exception as e:
                    print(f"❌ Error: {e}")
                
                # Small delay between tests
                await asyncio.sleep(1)
    
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("   Make sure enterprise backend is running on port 8767")

if __name__ == "__main__":
    asyncio.run(test_real_agent_mode())