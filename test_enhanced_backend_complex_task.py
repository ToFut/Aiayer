#!/usr/bin/env python3
"""
Test Enhanced Backend Complex Task Planning
Tests the "open YouTube and search SEGEV" request to verify proper multi-step planning
"""

import asyncio
import websockets
import json
import sys

async def test_complex_task():
    """Test complex task planning with Enhanced Backend"""
    
    uri = "ws://localhost:8767"
    test_request = "open YouTube and search SEGEV"
    
    print(f"🔍 Testing Enhanced Backend Complex Task Planning")
    print(f"📍 Connecting to: {uri}")
    print(f"🎯 Test Request: '{test_request}'")
    print("=" * 60)
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to Enhanced Backend")
            
            # Send agent mode request
            message = {
                "type": "chat",
                "mode": "agent",
                "message": test_request,
                "user_id": "test_user",
                "session_id": "complex_task_test"
            }
            
            await websocket.send(json.dumps(message))
            print(f"📤 Sent: {test_request}")
            
            # Receive connection acknowledgment first
            connection_response = await websocket.recv()
            connection_data = json.loads(connection_response)
            
            if connection_data.get('type') == 'connection_established':
                print("✅ Connection acknowledged, waiting for task response...")
                
                # Now receive the actual task response
                response = await websocket.recv()
                data = json.loads(response)
            else:
                # If not connection message, treat as task response
                data = connection_data
            
            print("\n📥 RESPONSE:")
            print("=" * 40)
            
            # Check for complex task planning
            if 'execution_plan' in data:
                plan = data['execution_plan']
                steps = plan.get('steps', [])
                
                print(f"🔢 Steps: {len(steps)} actions")
                print(f"⏱️ Estimated Duration: {plan.get('estimated_duration', 'N/A')} seconds")
                print(f"🎯 Complexity: {plan.get('complexity', 'Unknown')}")
                
                if steps:
                    print("\n📋 EXECUTION STEPS:")
                    for i, step in enumerate(steps, 1):
                        action = step.get('action', 'Unknown action')
                        target = step.get('target', 'Unknown target')
                        duration = step.get('estimated_duration', 'N/A')
                        print(f"   {i}. {action} → {target} ({duration}s)")
                        
                    print(f"\n✅ SUCCESS: Complex task planning is working!")
                    print(f"🎉 Generated {len(steps)} steps for YouTube search request")
                    
                    # Check for enhanced features
                    if 'enhanced_features' in data:
                        features = data['enhanced_features']
                        print(f"\n🚀 ENHANCED FEATURES:")
                        print(f"   • Complex Task Handler: {features.get('complex_task_handler', False)}")
                        print(f"   • Enhanced UI Detection: {features.get('enhanced_ui_detection', False)}")
                        print(f"   • Max Complexity: {features.get('max_task_complexity', 'Unknown')}")
                        print(f"   • Max Concurrent Steps: {features.get('max_concurrent_steps', 'Unknown')}")
                        
                else:
                    print("❌ FAILURE: No steps generated")
                    print("🔍 This indicates the complex task planner is not working correctly")
                    
            else:
                print("❌ FAILURE: No execution_plan in response")
                print("🔍 Response structure:")
                for key, value in data.items():
                    if isinstance(value, dict):
                        print(f"   {key}: {type(value).__name__} with {len(value)} items")
                    else:
                        print(f"   {key}: {str(value)[:100]}...")
                        
    except websockets.exceptions.ConnectionRefused:
        print("❌ CONNECTION REFUSED")
        print("🔍 Enhanced Backend may not be running on port 8767")
        print("💡 Try: python enhanced_backend_with_complex_tasks.py")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print(f"🔍 Error type: {type(e).__name__}")

if __name__ == "__main__":
    asyncio.run(test_complex_task())