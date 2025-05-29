#!/usr/bin/env python3
"""
Test AgentMode Click and Typing Coordination
Tests 5 different user messages with DO button execution simulation
"""

import asyncio
import json
import time
import logging
from typing import Dict, Any, List

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AgentModeCoordinationTester:
    """Test AgentMode coordination system with actual execution"""
    
    def __init__(self):
        self.test_results = []
        self.session_id = f"test_session_{int(time.time())}"
        
    async def run_comprehensive_test(self):
        """Run comprehensive test of AgentMode coordination"""
        print("🚀 Starting AgentMode Coordination Test")
        print("=" * 60)
        
        # Test messages covering different automation types
        test_messages = [
            "open YouTube and search for 'Python tutorial'",
            "open Calculator and compute 25 * 37",
            "create a new document in TextEdit",
            "search Google for 'best Mac automation tools'",
            "open Safari and navigate to github.com"
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n📝 Test {i}/5: {message}")
            print("-" * 40)
            
            try:
                # Test plan creation
                result = await self._test_plan_creation(message)
                
                if result["success"]:
                    # Test plan execution (simulate DO button)
                    execution_result = await self._test_plan_execution(result["plan_id"])
                    result.update(execution_result)
                
                self.test_results.append({
                    "test_number": i,
                    "message": message,
                    "result": result
                })
                
                # Brief pause between tests
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Test {i} failed: {e}")
                self.test_results.append({
                    "test_number": i,
                    "message": message,
                    "result": {"success": False, "error": str(e)}
                })
        
        # Generate comprehensive report
        await self._generate_test_report()
    
    async def _test_plan_creation(self, message: str) -> Dict[str, Any]:
        """Test automation plan creation"""
        try:
            # Import the real automation handler
            from real_agent_automation_handler import real_agent_handler
            
            print(f"🧠 Creating automation plan...")
            start_time = time.time()
            
            # Create automation plan
            result = await real_agent_handler.handle_agent_request(message, self.session_id)
            
            creation_time = time.time() - start_time
            
            if result["success"]:
                print(f"✅ Plan created successfully in {creation_time:.2f}s")
                print(f"   Plan ID: {result.get('plan_id', 'Unknown')}")
                print(f"   Steps: {len(result.get('buttons', [])) > 0}")
                print(f"   Interactive: {result.get('interactive', False)}")
                print(f"   AI Powered: {result.get('ai_powered', False)}")
                
                # Show plan details
                if result.get('plan_id') and result['plan_id'] in real_agent_handler.active_plans:
                    plan = real_agent_handler.active_plans[result['plan_id']]
                    print(f"   Plan Title: {plan.title}")
                    print(f"   Steps Count: {len(plan.steps)}")
                    print(f"   Estimated Duration: {plan.estimated_duration:.1f}s")
                    
                    # Show step details
                    print("   📋 Plan Steps:")
                    for i, step in enumerate(plan.steps, 1):
                        print(f"      {i}. {step.action_type}: {step.description}")
                        if step.target:
                            print(f"         Target: {step.target}")
                        if step.value:
                            print(f"         Value: {step.value}")
                
                return {
                    "success": True,
                    "plan_id": result.get('plan_id'),
                    "creation_time": creation_time,
                    "interactive": result.get('interactive', False),
                    "ai_powered": result.get('ai_powered', False),
                    "automation_available": result.get('automation_available', False)
                }
            else:
                print(f"❌ Plan creation failed: {result.get('response', 'Unknown error')}")
                return {
                    "success": False,
                    "error": result.get('response', 'Plan creation failed'),
                    "creation_time": creation_time
                }
                
        except Exception as e:
            logger.error(f"Error in plan creation: {e}")
            return {
                "success": False,
                "error": str(e),
                "creation_time": 0
            }
    
    async def _test_plan_execution(self, plan_id: str) -> Dict[str, Any]:
        """Test plan execution (simulate DO button click)"""
        try:
            if not plan_id:
                return {"execution_success": False, "execution_error": "No plan ID provided"}
            
            # Import the real automation handler
            from real_agent_automation_handler import real_agent_handler
            
            print(f"🟢 Simulating DO button click...")
            start_time = time.time()
            
            # Simulate DO button action
            execution_result = await real_agent_handler.handle_button_action(
                action="execute_plan",
                plan_id=plan_id,
                session_id=self.session_id
            )
            
            execution_time = time.time() - start_time
            
            if execution_result["success"]:
                print(f"✅ Plan executed successfully in {execution_time:.2f}s")
                
                # Show execution details
                if "steps_executed" in execution_result:
                    print(f"   Steps Executed: {execution_result['steps_executed']}")
                if "steps_failed" in execution_result:
                    print(f"   Steps Failed: {execution_result['steps_failed']}")
                if "success_rate" in execution_result:
                    print(f"   Success Rate: {execution_result['success_rate']:.1f}%")
                
                return {
                    "execution_success": True,
                    "execution_time": execution_time,
                    "steps_executed": execution_result.get('steps_executed', 0),
                    "steps_failed": execution_result.get('steps_failed', 0),
                    "success_rate": execution_result.get('success_rate', 0)
                }
            else:
                print(f"❌ Plan execution failed: {execution_result.get('response', 'Unknown error')}")
                return {
                    "execution_success": False,
                    "execution_error": execution_result.get('response', 'Execution failed'),
                    "execution_time": execution_time
                }
                
        except Exception as e:
            logger.error(f"Error in plan execution: {e}")
            return {
                "execution_success": False,
                "execution_error": str(e),
                "execution_time": 0
            }
    
    async def _generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 AGENT MODE COORDINATION TEST REPORT")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        successful_plans = sum(1 for r in self.test_results if r["result"].get("success", False))
        successful_executions = sum(1 for r in self.test_results if r["result"].get("execution_success", False))
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful Plan Creation: {successful_plans}/{total_tests} ({(successful_plans/total_tests)*100:.1f}%)")
        print(f"Successful Plan Execution: {successful_executions}/{total_tests} ({(successful_executions/total_tests)*100:.1f}%)")
        
        print("\n📋 DETAILED RESULTS:")
        print("-" * 40)
        
        for test in self.test_results:
            result = test["result"]
            print(f"\nTest {test['test_number']}: {test['message']}")
            
            if result.get("success"):
                print(f"  ✅ Plan Creation: SUCCESS ({result.get('creation_time', 0):.2f}s)")
                print(f"     AI Powered: {result.get('ai_powered', False)}")
                print(f"     Interactive: {result.get('interactive', False)}")
                print(f"     Automation Available: {result.get('automation_available', False)}")
                
                if result.get("execution_success"):
                    print(f"  ✅ Plan Execution: SUCCESS ({result.get('execution_time', 0):.2f}s)")
                    print(f"     Steps Executed: {result.get('steps_executed', 0)}")
                    print(f"     Steps Failed: {result.get('steps_failed', 0)}")
                    print(f"     Success Rate: {result.get('success_rate', 0):.1f}%")
                else:
                    print(f"  ❌ Plan Execution: FAILED")
                    if result.get("execution_error"):
                        print(f"     Error: {result['execution_error']}")
            else:
                print(f"  ❌ Plan Creation: FAILED")
                if result.get("error"):
                    print(f"     Error: {result['error']}")
        
        print("\n🔍 COORDINATION ANALYSIS:")
        print("-" * 40)
        
        # Analyze coordination effectiveness
        ai_powered_count = sum(1 for r in self.test_results if r["result"].get("ai_powered", False))
        interactive_count = sum(1 for r in self.test_results if r["result"].get("interactive", False))
        automation_available_count = sum(1 for r in self.test_results if r["result"].get("automation_available", False))
        
        print(f"AI-Powered Planning: {ai_powered_count}/{total_tests} tests")
        print(f"Interactive Mode: {interactive_count}/{total_tests} tests")
        print(f"Automation Components Available: {automation_available_count}/{total_tests} tests")
        
        # Calculate average timings
        creation_times = [r["result"].get("creation_time", 0) for r in self.test_results if r["result"].get("success")]
        execution_times = [r["result"].get("execution_time", 0) for r in self.test_results if r["result"].get("execution_success")]
        
        if creation_times:
            avg_creation_time = sum(creation_times) / len(creation_times)
            print(f"Average Plan Creation Time: {avg_creation_time:.2f}s")
        
        if execution_times:
            avg_execution_time = sum(execution_times) / len(execution_times)
            print(f"Average Plan Execution Time: {avg_execution_time:.2f}s")
        
        print("\n🎯 COORDINATION EFFECTIVENESS:")
        print("-" * 40)
        
        if successful_plans == total_tests and successful_executions == total_tests:
            print("🟢 EXCELLENT: All tests passed - Full coordination working")
        elif successful_plans == total_tests:
            print("🟡 GOOD: All plans created - Execution needs improvement")
        elif successful_plans > total_tests // 2:
            print("🟡 FAIR: Most plans created - Some coordination issues")
        else:
            print("🔴 POOR: Many failures - Coordination needs fixes")
        
        # Save detailed results to file
        timestamp = int(time.time())
        results_file = f"agent_mode_coordination_test_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump({
                "timestamp": timestamp,
                "session_id": self.session_id,
                "summary": {
                    "total_tests": total_tests,
                    "successful_plans": successful_plans,
                    "successful_executions": successful_executions,
                    "ai_powered_count": ai_powered_count,
                    "interactive_count": interactive_count,
                    "automation_available_count": automation_available_count
                },
                "detailed_results": self.test_results
            }, indent=2)
        
        print(f"\n💾 Detailed results saved to: {results_file}")
        print("=" * 60)

async def main():
    """Main test execution function"""
    try:
        tester = AgentModeCoordinationTester()
        await tester.run_comprehensive_test()
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())