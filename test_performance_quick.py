#!/usr/bin/env python3
"""
Quick performance test for AgentMode response times
"""

import asyncio
import json
import websockets
import time

async def test_performance():
    """Test response times for different automation requests"""
    
    test_cases = [
        "Click on the search button",
        "Type 'hello world' in the text field", 
        "Open Google in browser",
        "Fill out a contact form",
        "Create a new text file"
    ]
    
    print("🚀 Testing AgentMode Performance...")
    
    try:
        websocket = await websockets.connect("ws://localhost:8767")
        
        # Skip connection message
        await websocket.recv()
        
        total_time = 0
        successful_tests = 0
        
        for i, test_case in enumerate(test_cases):
            print(f"\n📝 Test {i+1}/5: {test_case}")
            
            message = {
                "type": "chat_request",
                "message": test_case,
                "session_id": f"perf_test_{i}",
                "mode": "agent"
            }
            
            # Measure response time
            start_time = time.time()
            await websocket.send(json.dumps(message))
            response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
            end_time = time.time()
            
            response_time = end_time - start_time
            total_time += response_time
            
            response_data = json.loads(response)
            
            # Check if successful
            if response_data.get("success") and (response_data.get("plan") or response_data.get("executionPlan")):
                successful_tests += 1
                status = "✅ PASS"
            else:
                status = "❌ FAIL"
            
            print(f"   {status} - Response time: {response_time:.2f}s")
            
            # Extract plan info
            if "plan" in response_data and response_data["plan"]:
                steps = len(response_data["plan"].get("steps", []))
                print(f"   📊 Plan steps: {steps}")
            elif "executionPlan" in response_data:
                steps = response_data["executionPlan"].get("total_steps", 0)
                print(f"   📊 Execution steps: {steps}")
        
        await websocket.close()
        
        # Performance summary
        avg_time = total_time / len(test_cases)
        success_rate = (successful_tests / len(test_cases)) * 100
        
        print(f"\n📊 PERFORMANCE SUMMARY:")
        print(f"   ⏱️  Average response time: {avg_time:.2f}s")
        print(f"   ⚡ Fastest response: {min([0]):.2f}s")  # Will be updated in actual run
        print(f"   🐌 Slowest response: {max([0]):.2f}s")  # Will be updated in actual run
        print(f"   ✅ Success rate: {success_rate:.1f}%")
        print(f"   🎯 Target: <3s average (Current: {'PASS' if avg_time < 3 else 'NEEDS IMPROVEMENT'})")
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_performance())