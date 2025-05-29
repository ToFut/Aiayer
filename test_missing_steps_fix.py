#!/usr/bin/env python3
"""
Missing Steps Fix Test
Tests and fixes scenarios where automation responses have missing or incomplete steps
"""

import asyncio
import websockets
import json
import time
import uuid
from datetime import datetime

class MissingStepsTest:
    def __init__(self):
        self.backend_url = "ws://localhost:8767"
        self.session_id = str(uuid.uuid4())
        self.results = []

    async def test_step_completeness(self):
        """Test scenarios that previously had missing steps"""
        try:
            print(f"📊 Starting Missing Steps Test at {datetime.now()}")
            print("=" * 60)
            
            async with websockets.connect(self.backend_url) as websocket:
                print("✅ Connected to backend")
                
                # Handle connection message
                try:
                    connection_msg = await asyncio.wait_for(websocket.recv(), timeout=5)
                    print(f"📝 Connection message received")
                except asyncio.TimeoutError:
                    print("⚠️  No connection message received")

                # Test cases that previously failed with missing steps
                test_cases = [
                    {
                        "name": "Form Filling Complex",
                        "message": "Fill out the registration form with name, email, password, and submit",
                        "expected_min_steps": 4,
                        "description": "Complex multi-field form interaction"
                    },
                    {
                        "name": "Multi-step Web Search",
                        "message": "Search for 'python tutorial', click the first result, then bookmark it",
                        "expected_min_steps": 3,
                        "description": "Sequential web navigation"
                    },
                    {
                        "name": "File Upload Workflow",
                        "message": "Click upload button, select file from computer, add description, and upload",
                        "expected_min_steps": 4,
                        "description": "File upload with metadata"
                    },
                    {
                        "name": "E-commerce Purchase",
                        "message": "Add item to cart, go to checkout, enter shipping info, and place order",
                        "expected_min_steps": 4,
                        "description": "Complete purchase workflow"
                    },
                    {
                        "name": "Social Media Interaction",
                        "message": "Create a new post, add an image, write caption, and publish",
                        "expected_min_steps": 4,
                        "description": "Content creation workflow"
                    },
                    {
                        "name": "Settings Configuration",
                        "message": "Go to settings, change theme to dark mode, enable notifications, save changes",
                        "expected_min_steps": 4,
                        "description": "Multi-setting configuration"
                    }
                ]

                for i, case in enumerate(test_cases, 1):
                    print(f"\n📊 Test {i}/6: {case['name']}")
                    print(f"📝 Message: {case['message']}")
                    print(f"🎯 Expected minimum steps: {case['expected_min_steps']}")
                    
                    # Send agent request
                    message = {
                        "type": "chat_request",
                        "message": case["message"],
                        "session_id": self.session_id,
                        "mode": "agent"
                    }
                    
                    await websocket.send(json.dumps(message))
                    
                    # Wait for response
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=15)
                        response_data = json.loads(response)
                        
                        # Analyze step completeness
                        step_count = 0
                        steps_detailed = False
                        has_plan = False
                        
                        # Check plan steps
                        if 'plan' in response_data and response_data['plan']:
                            plan = response_data['plan']
                            has_plan = True
                            if 'steps' in plan and isinstance(plan['steps'], list):
                                step_count = len(plan['steps'])
                                # Check if steps are detailed (not just generic)
                                steps_detailed = any(
                                    step.get('description', '').lower() not in ['execute action', 'prepare', 'execute']
                                    for step in plan['steps']
                                )
                        
                        # Check execution plan steps
                        if 'executionPlan' in response_data:
                            exec_plan = response_data['executionPlan']
                            if 'steps' in exec_plan and isinstance(exec_plan['steps'], list):
                                if step_count == 0:  # Only use if plan steps weren't found
                                    step_count = len(exec_plan['steps'])
                        
                        # Evaluate completeness
                        meets_minimum = step_count >= case['expected_min_steps']
                        has_sufficient_detail = steps_detailed
                        
                        result = {
                            "test": case['name'],
                            "has_plan": has_plan,
                            "step_count": step_count,
                            "expected_min_steps": case['expected_min_steps'],
                            "meets_minimum": meets_minimum,
                            "steps_detailed": steps_detailed,
                            "success": has_plan and meets_minimum and steps_detailed
                        }
                        
                        self.results.append(result)
                        
                        # Print result
                        status = "✅ PASS" if result['success'] else "❌ FAIL"
                        plan_status = "📋 PLAN" if has_plan else "❌ NO_PLAN"
                        step_status = f"📊 {step_count}/{case['expected_min_steps']}"
                        detail_status = "📝 DETAILED" if steps_detailed else "⚠️ GENERIC"
                        
                        print(f"{status} | {plan_status} | {step_status} | {detail_status}")
                        
                        if not meets_minimum:
                            print(f"⚠️  INSUFFICIENT STEPS: Got {step_count}, expected at least {case['expected_min_steps']}")
                        
                        if not steps_detailed:
                            print(f"⚠️  GENERIC STEPS: Steps lack specific detail for complex task")
                        
                        # Debug: Print actual steps if failing
                        if not result['success'] and 'plan' in response_data:
                            plan = response_data['plan']
                            if 'steps' in plan:
                                print(f"🔍 Actual steps:")
                                for j, step in enumerate(plan['steps'], 1):
                                    print(f"  {j}. {step.get('description', 'No description')}")
                        
                    except asyncio.TimeoutError:
                        print(f"❌ Timeout")
                        self.results.append({
                            "test": case['name'],
                            "success": False,
                            "error": "Timeout"
                        })
                    
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON decode error: {e}")
                        self.results.append({
                            "test": case['name'],
                            "success": False,
                            "error": "JSON decode error"
                        })
                    
                    # Small delay between tests
                    await asyncio.sleep(1)

        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
        
        return True

    def print_step_analysis(self):
        """Print detailed step completeness analysis"""
        print("\n" + "=" * 60)
        print("📊 STEP COMPLETENESS ANALYSIS")
        print("=" * 60)
        
        if not self.results:
            print("❌ No test results available")
            return
        
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.get('success', False))
        has_plans = sum(1 for r in self.results if r.get('has_plan', False))
        meets_minimum = sum(1 for r in self.results if r.get('meets_minimum', False))
        detailed_steps = sum(1 for r in self.results if r.get('steps_detailed', False))
        
        success_rate = (successful_tests / total_tests) * 100
        plan_rate = (has_plans / total_tests) * 100
        minimum_rate = (meets_minimum / total_tests) * 100
        detail_rate = (detailed_steps / total_tests) * 100
        
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Successful: {successful_tests} ({success_rate:.1f}%)")
        print(f"📋 Has Plans: {has_plans} ({plan_rate:.1f}%)")
        print(f"📏 Meets Minimum Steps: {meets_minimum} ({minimum_rate:.1f}%)")
        print(f"📝 Detailed Steps: {detailed_steps} ({detail_rate:.1f}%)")
        
        print("\n📋 Detailed Results:")
        print("-" * 60)
        
        for result in self.results:
            test_name = result['test']
            success = result.get('success', False)
            step_count = result.get('step_count', 0)
            expected = result.get('expected_min_steps', 0)
            detailed = result.get('steps_detailed', False)
            
            status_icon = "✅" if success else "❌"
            detail_icon = "📝" if detailed else "⚠️"
            
            print(f"{status_icon} {detail_icon} {test_name:<25} | {step_count:>2}/{expected} steps")
        
        print("\n🔍 Step Quality Issues:")
        print("-" * 60)
        
        if minimum_rate < 80:
            print("⚠️  LOW STEP COUNT: Many responses have insufficient steps for complex tasks")
            print("📋 RECOMMENDATION: Enhance step generation for multi-step workflows")
        
        if detail_rate < 70:
            print("⚠️  GENERIC STEPS: Steps lack specificity for complex tasks")
            print("📋 RECOMMENDATION: Improve step detail generation")
        
        if success_rate >= 80:
            print("🎉 EXCELLENT: Step generation working well for complex tasks!")
        elif success_rate >= 60:
            print("👍 GOOD: Step generation partially working")
        else:
            print("❌ NEEDS WORK: Step generation requires significant improvement")

async def main():
    """Run missing steps test"""
    test = MissingStepsTest()
    
    print("📊 Testing AgentMode Step Completeness")
    print("Goal: Fix missing steps in complex automation scenarios")
    
    success = await test.test_step_completeness()
    
    if success:
        test.print_step_analysis()
    else:
        print("❌ Step completeness test failed to complete")

if __name__ == "__main__":
    asyncio.run(main())