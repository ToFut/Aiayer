#!/usr/bin/env python3
"""
Simple test for Enhanced Backend Complex Task Planning
"""

import asyncio
import websockets
import json
import sys

async def simple_test():
    """Simple test with timeout"""
    
    uri = "ws://localhost:8767"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to Enhanced Backend")
            
            # Send a simple agent mode request
            message = {
                "type": "chat_request",
                "mode": "agent", 
                "message": "open YouTube and search SEGEV"
            }
            
            print("📤 Sending request...")
            await websocket.send(json.dumps(message))
            
            # Try to receive responses with timeout
            try:
                # First response (connection ack)
                response1 = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data1 = json.loads(response1)
                print(f"📥 Response 1: {data1.get('type', 'unknown')}")
                
                # Second response (actual result)
                response2 = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                data2 = json.loads(response2) 
                print(f"📥 Response 2: {data2.get('type', 'unknown')}")
                
                # Check for execution plan
                if 'execution_plan' in data2:
                    plan = data2['execution_plan']
                    steps = plan.get('steps', [])
                    print(f"✅ SUCCESS: Generated {len(steps)} steps")
                else:
                    print(f"❌ No execution_plan found")
                    print(f"Keys in response: {list(data2.keys())}")
                    
                    # Show response content
                    print(f"Response content: {data2.get('response', 'No response')}")
                    
                    # Check enhanced_features
                    if 'enhanced_features' in data2:
                        features = data2['enhanced_features']
                        print(f"Enhanced features: {features}")
                    
            except asyncio.TimeoutError:
                print("⏰ Timeout waiting for response")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(simple_test())