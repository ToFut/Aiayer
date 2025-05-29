#!/usr/bin/env python3
"""
Performance Test for AgentMode Optimization
Tests response times before and after LLM warmup manager implementation
"""

import asyncio
import websockets
import json
import time
import uuid
from datetime import datetime

class PerformanceTest:
    def __init__(self):
        self.backend_url = "ws://localhost:8767"
        self.session_id = str(uuid.uuid4())
        self.results = []

    async def connect_and_test(self):
        """Connect to backend and run performance tests"""
        try:
            print(f"🚀 Starting Performance Test at {datetime.now()}")
            print("=" * 60)
            
            async with websockets.connect(self.backend_url) as websocket:
                print("✅ Connected to backend")
                
                # Handle connection message
                try:
                    connection_msg = await asyncio.wait_for(websocket.recv(), timeout=5)
                    print(f"📝 Connection message: {connection_msg}")
                except asyncio.TimeoutError:
                    print("⚠️  No connection message received")

                # Test cases for performance measurement
                test_cases = [
                    {
                        "name": "Simple Click Test",
                        "message": "Click on the search button",
                        "expected_time": 3.0  # Target: under 3 seconds
                    },
                    {
                        "name": "Type Text Test", 
                        "message": "Type 'hello world' in the input field",
                        "expected_time": 3.0
                    },
                    {
                        "name": "Navigation Test",
                        "message": "Navigate to the settings page",
                        "expected_time": 4.0
                    },
                    {
                        "name": "Multi-step Test",
                        "message": "Search for 'AI technology' and click the first result",
                        "expected_time": 5.0
                    }
                ]

                for i, case in enumerate(test_cases, 1):
                    print(f"\n🧪 Test {i}/4: {case['name']}")
                    print(f"📝 Message: {case['message']}")
                    
                    # Measure response time
                    start_time = time.time()
                    
                    # Send agent request
                    message = {
                        "type": "chat_request",
                        "message": case["message"],
                        "session_id": self.session_id,
                        "mode": "agent"
                    }
                    
                    await websocket.send(json.dumps(message))
                    print(f"📤 Sent request at {time.time():.3f}")
                    
                    # Wait for response
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=30)
                        end_time = time.time()
                        response_time = end_time - start_time
                        
                        print(f"📥 Received response at {end_time:.3f}")
                        print(f"⏱️  Response time: {response_time:.2f} seconds")
                        
                        # Parse response
                        try:
                            response_data = json.loads(response)
                            
                            # Check if it has automation plan
                            has_plan = 'plan' in response_data
                            has_steps = False
                            step_count = 0
                            
                            if has_plan and response_data['plan']:
                                plan = response_data['plan']
                                has_steps = 'steps' in plan and len(plan['steps']) > 0
                                step_count = len(plan.get('steps', []))
                            
                            # Determine success
                            is_fast = response_time <= case['expected_time']
                            success = has_plan and has_steps and is_fast
                            
                            result = {
                                "test": case['name'],
                                "response_time": response_time,
                                "expected_time": case['expected_time'],
                                "is_fast_enough": is_fast,
                                "has_plan": has_plan,
                                "has_steps": has_steps,
                                "step_count": step_count,
                                "success": success,
                                "improvement": "GOOD" if is_fast else "NEEDS_WORK"
                            }
                            
                            self.results.append(result)
                            
                            # Print result summary
                            status = "✅ PASS" if success else "❌ FAIL"
                            speed_status = "⚡ FAST" if is_fast else "🐌 SLOW"
                            plan_status = "📋 PLAN" if has_plan else "❌ NO_PLAN"
                            steps_status = f"📊 {step_count} STEPS" if has_steps else "❌ NO_STEPS"
                            
                            print(f"{status} | {speed_status} | {plan_status} | {steps_status}")
                            
                            if not is_fast:
                                print(f"⚠️  SLOW: {response_time:.2f}s > {case['expected_time']}s target")
                            
                        except json.JSONDecodeError as e:
                            print(f"❌ Failed to parse response: {e}")
                            self.results.append({
                                "test": case['name'],
                                "response_time": response_time,
                                "expected_time": case['expected_time'],
                                "success": False,
                                "error": "JSON decode error"
                            })
                    
                    except asyncio.TimeoutError:
                        print(f"❌ Timeout after 30 seconds")
                        self.results.append({
                            "test": case['name'],
                            "response_time": 30.0,
                            "expected_time": case['expected_time'],
                            "success": False,
                            "error": "Timeout"
                        })
                    
                    # Small delay between tests
                    await asyncio.sleep(1)

        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
        
        return True

    def print_summary(self):
        """Print performance test summary"""
        print("\n" + "=" * 60)
        print("🏁 PERFORMANCE TEST SUMMARY")
        print("=" * 60)
        
        if not self.results:
            print("❌ No test results available")
            return
        
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.get('success', False))
        fast_tests = sum(1 for r in self.results if r.get('is_fast_enough', False))
        
        success_rate = (successful_tests / total_tests) * 100
        speed_rate = (fast_tests / total_tests) * 100
        
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Successful: {successful_tests} ({success_rate:.1f}%)")
        print(f"⚡ Fast Enough: {fast_tests} ({speed_rate:.1f}%)")
        
        print("\n📋 Detailed Results:")
        print("-" * 60)
        
        for result in self.results:
            test_name = result['test']
            response_time = result.get('response_time', 0)
            expected_time = result.get('expected_time', 0)
            success = result.get('success', False)
            
            status_icon = "✅" if success else "❌"
            speed_icon = "⚡" if response_time <= expected_time else "🐌"
            
            print(f"{status_icon} {speed_icon} {test_name:<20} | {response_time:>6.2f}s | Target: {expected_time}s")
        
        # Performance improvement analysis
        print("\n🔍 Performance Analysis:")
        print("-" * 60)
        
        avg_response_time = sum(r.get('response_time', 0) for r in self.results) / total_tests
        print(f"📈 Average Response Time: {avg_response_time:.2f} seconds")
        
        if avg_response_time <= 3.0:
            print("🎉 EXCELLENT: Average response time meets target!")
        elif avg_response_time <= 5.0:
            print("👍 GOOD: Response time improved but could be better")
        else:
            print("⚠️  NEEDS IMPROVEMENT: Response time still too slow")
        
        # Check if optimization worked
        if speed_rate >= 75:
            print("🚀 OPTIMIZATION SUCCESS: Most tests are fast enough!")
        elif speed_rate >= 50:
            print("📈 PARTIAL SUCCESS: Some improvement, needs more work")
        else:
            print("❌ OPTIMIZATION FAILED: Still too slow")

async def main():
    """Run performance test"""
    test = PerformanceTest()
    
    print("🧪 Testing AgentMode Performance Optimizations")
    print("Target: Reduce response times from 13s+ to 2-3s")
    
    success = await test.connect_and_test()
    
    if success:
        test.print_summary()
    else:
        print("❌ Performance test failed to complete")

if __name__ == "__main__":
    asyncio.run(main())