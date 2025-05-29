#!/usr/bin/env python3
"""
AgentMode Coordination Validation Test
Comprehensive test to identify issues and miscoordination in the system
"""

import asyncio
import json
import time
import logging
import websockets
from typing import Dict, Any, List
import subprocess
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CoordinationValidator:
    """Validates AgentMode coordination and identifies issues"""
    
    def __init__(self):
        self.test_results = []
        self.identified_issues = []
        self.coordination_metrics = {
            "plan_creation_success": 0,
            "plan_execution_success": 0,
            "button_response_time": [],
            "llm_json_errors": 0,
            "websocket_errors": 0,
            "automation_errors": 0,
            "total_tests": 0
        }
        
    async def run_validation_tests(self):
        """Run comprehensive validation tests"""
        print("🔍 AgentMode Coordination Validation Starting")
        print("=" * 60)
        
        # Test 1: Backend Connection Validation
        await self._test_backend_connection()
        
        # Test 2: Plan Creation Coordination
        await self._test_plan_creation_coordination()
        
        # Test 3: DO Button Execution Validation
        await self._test_do_button_coordination()
        
        # Test 4: Error Handling Validation
        await self._test_error_handling()
        
        # Test 5: Performance Coordination Check
        await self._test_performance_coordination()
        
        # Generate comprehensive report
        await self._generate_validation_report()
        
    async def _test_backend_connection(self):
        """Test backend connection and WebSocket coordination"""
        print("\n🔌 Testing Backend Connection & WebSocket Coordination")
        print("-" * 50)
        
        try:
            # Test WebSocket connection to enterprise backend
            uri = "ws://localhost:8767"
            
            async with websockets.connect(uri, timeout=5) as websocket:
                print("✅ WebSocket connection established")
                
                # Send test message
                test_message = {
                    "type": "chat_request",
                    "client_id": "test_validator",
                    "message": "test connection",
                    "mode": "Agent"
                }
                
                await websocket.send(json.dumps(test_message))
                print("✅ Test message sent")
                
                # Wait for response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10)
                    response_data = json.loads(response)
                    print(f"✅ Response received: {response_data.get('type', 'unknown')}")
                    
                    if "buttons" in response_data and len(response_data["buttons"]) > 0:
                        print("✅ Interactive buttons present in response")
                        self.coordination_metrics["plan_creation_success"] += 1
                    else:
                        self.identified_issues.append("❌ No interactive buttons in response")
                        
                except asyncio.TimeoutError:
                    self.identified_issues.append("❌ Backend response timeout (>10s)")
                    
        except Exception as e:
            self.identified_issues.append(f"❌ Backend connection failed: {e}")
            print(f"❌ Backend connection failed: {e}")
            
        self.coordination_metrics["total_tests"] += 1
    
    async def _test_plan_creation_coordination(self):
        """Test automation plan creation coordination"""
        print("\n📝 Testing Plan Creation Coordination")
        print("-" * 50)
        
        test_commands = [
            "open Calculator and compute 15 * 25",
            "open YouTube and search for Python tutorial",
            "create a new document in TextEdit",
            "search Google for best Mac automation tools"
        ]
        
        for i, command in enumerate(test_commands, 1):
            print(f"\nTest {i}: '{command}'")
            
            try:
                # Import real automation handler
                from real_agent_automation_handler import real_agent_handler
                
                start_time = time.time()
                session_id = f"test_session_{int(time.time())}_{i}"
                
                # Test plan creation
                result = await real_agent_handler.handle_agent_request(command, session_id)
                creation_time = time.time() - start_time
                
                print(f"   ⏱️  Creation time: {creation_time:.2f}s")
                
                if result["success"]:
                    print("   ✅ Plan created successfully")
                    
                    # Check for interactive elements
                    if result.get("interactive") and result.get("buttons"):
                        print(f"   ✅ Interactive buttons: {len(result['buttons'])} buttons")
                        
                        # Check button structure
                        for button in result["buttons"]:
                            if not all(key in button for key in ["text", "action", "plan_id"]):
                                self.identified_issues.append(f"❌ Malformed button in plan: {command}")
                                
                        self.coordination_metrics["plan_creation_success"] += 1
                    else:
                        self.identified_issues.append(f"❌ No interactive buttons for: {command}")
                        
                    # Check plan structure
                    plan_id = result.get("plan_id")
                    if plan_id and plan_id in real_agent_handler.active_plans:
                        plan = real_agent_handler.active_plans[plan_id]
                        print(f"   ✅ Plan stored: {len(plan.steps)} steps")
                        
                        if len(plan.steps) == 0:
                            self.identified_issues.append(f"❌ Empty plan created for: {command}")
                    else:
                        self.identified_issues.append(f"❌ Plan not stored properly: {command}")
                        
                else:
                    self.identified_issues.append(f"❌ Plan creation failed: {command} - {result.get('response', 'Unknown error')}")
                    print(f"   ❌ Failed: {result.get('response', 'Unknown error')}")
                    
                # Track LLM/JSON errors from logs
                if "JSON" in str(result) or "parse" in str(result).lower():
                    self.coordination_metrics["llm_json_errors"] += 1
                    
            except Exception as e:
                self.identified_issues.append(f"❌ Plan creation exception: {command} - {e}")
                print(f"   ❌ Exception: {e}")
                
            self.coordination_metrics["total_tests"] += 1
            await asyncio.sleep(1)  # Prevent overwhelming system
    
    async def _test_do_button_coordination(self):
        """Test DO button execution coordination"""
        print("\n🟢 Testing DO Button Execution Coordination")
        print("-" * 50)
        
        # Create a simple test plan
        try:
            from real_agent_automation_handler import real_agent_handler
            
            test_command = "open Calculator"
            session_id = f"do_test_{int(time.time())}"
            
            # Create plan
            result = await real_agent_handler.handle_agent_request(test_command, session_id)
            
            if result["success"] and result.get("plan_id"):
                plan_id = result["plan_id"]
                print(f"✅ Test plan created: {plan_id}")
                
                # Test DO button execution
                start_time = time.time()
                exec_result = await real_agent_handler.handle_button_action(
                    "execute_plan", 
                    plan_id, 
                    session_id
                )
                execution_time = time.time() - start_time
                
                print(f"⏱️  Execution time: {execution_time:.2f}s")
                self.coordination_metrics["button_response_time"].append(execution_time)
                
                if exec_result["success"]:
                    print("✅ DO button execution successful")
                    
                    # Check execution details
                    success_rate = exec_result.get("success_rate", 0)
                    steps_executed = exec_result.get("steps_executed", 0)
                    
                    print(f"   📊 Success rate: {success_rate}%")
                    print(f"   📊 Steps executed: {steps_executed}")
                    
                    if success_rate >= 75:
                        self.coordination_metrics["plan_execution_success"] += 1
                    else:
                        self.identified_issues.append(f"❌ Low execution success rate: {success_rate}%")
                        
                else:
                    self.identified_issues.append(f"❌ DO button execution failed: {exec_result.get('response', 'Unknown error')}")
                    print(f"❌ Execution failed: {exec_result.get('response', 'Unknown error')}")
                    
            else:
                self.identified_issues.append("❌ Could not create test plan for DO button testing")
                
        except Exception as e:
            self.identified_issues.append(f"❌ DO button test exception: {e}")
            print(f"❌ DO button test failed: {e}")
            
        self.coordination_metrics["total_tests"] += 1
    
    async def _test_error_handling(self):
        """Test error handling and recovery coordination"""
        print("\n⚠️  Testing Error Handling Coordination")
        print("-" * 50)
        
        error_test_cases = [
            {"command": "", "expected": "empty_input_handling"},
            {"command": "invalid nonsensical robot command xyz123", "expected": "graceful_degradation"},
            {"plan_id": "nonexistent_plan_id", "expected": "plan_not_found"},
        ]
        
        for i, test_case in enumerate(error_test_cases, 1):
            print(f"\nError Test {i}: {test_case}")
            
            try:
                from real_agent_automation_handler import real_agent_handler
                
                if "command" in test_case:
                    # Test invalid command handling
                    result = await real_agent_handler.handle_agent_request(
                        test_case["command"], 
                        f"error_test_{i}"
                    )
                    
                    if not result["success"] and "error" in result.get("response", "").lower():
                        print("   ✅ Error properly handled")
                    else:
                        self.identified_issues.append(f"❌ Poor error handling for: {test_case['command']}")
                        
                elif "plan_id" in test_case:
                    # Test invalid plan ID handling
                    result = await real_agent_handler.handle_button_action(
                        "execute_plan",
                        test_case["plan_id"],
                        f"error_test_{i}"
                    )
                    
                    if not result["success"] and "not found" in result.get("response", "").lower():
                        print("   ✅ Invalid plan ID properly handled")
                    else:
                        self.identified_issues.append(f"❌ Poor error handling for invalid plan ID")
                        
            except Exception as e:
                print(f"   ⚠️  Exception during error test: {e}")
                # This might be expected for some error cases
                
        self.coordination_metrics["total_tests"] += len(error_test_cases)
    
    async def _test_performance_coordination(self):
        """Test performance coordination metrics"""
        print("\n⚡ Testing Performance Coordination")
        print("-" * 50)
        
        # Test rapid successive requests
        rapid_commands = [
            "open Terminal",
            "open Finder", 
            "open System Preferences"
        ]
        
        start_time = time.time()
        results = []
        
        for command in rapid_commands:
            try:
                from real_agent_automation_handler import real_agent_handler
                
                cmd_start = time.time()
                result = await real_agent_handler.handle_agent_request(
                    command, 
                    f"perf_test_{int(time.time())}"
                )
                cmd_time = time.time() - cmd_start
                
                results.append({
                    "command": command,
                    "success": result["success"],
                    "time": cmd_time
                })
                
                print(f"   {command}: {'✅' if result['success'] else '❌'} ({cmd_time:.2f}s)")
                
            except Exception as e:
                results.append({
                    "command": command,
                    "success": False,
                    "time": None,
                    "error": str(e)
                })
                print(f"   {command}: ❌ Exception: {e}")
                
        total_time = time.time() - start_time
        successful = sum(1 for r in results if r["success"])
        
        print(f"\n📊 Performance Summary:")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Success rate: {successful}/{len(rapid_commands)} ({(successful/len(rapid_commands)*100):.1f}%)")
        
        avg_time = sum(r["time"] for r in results if r["time"]) / len([r for r in results if r["time"]])
        print(f"   Average response time: {avg_time:.2f}s")
        
        if avg_time > 5.0:
            self.identified_issues.append(f"❌ Slow performance: Average {avg_time:.2f}s response time")
            
        if successful < len(rapid_commands):
            self.identified_issues.append(f"❌ Performance degradation: {len(rapid_commands) - successful} failures in rapid testing")
            
        self.coordination_metrics["total_tests"] += len(rapid_commands)
    
    async def _generate_validation_report(self):
        """Generate comprehensive validation report"""
        print("\n" + "=" * 60)
        print("📊 AGENTMODE COORDINATION VALIDATION REPORT")
        print("=" * 60)
        
        # Calculate success rates
        total_tests = self.coordination_metrics["total_tests"]
        plan_success_rate = (self.coordination_metrics["plan_creation_success"] / total_tests * 100) if total_tests > 0 else 0
        exec_success_rate = (self.coordination_metrics["plan_execution_success"] / max(1, self.coordination_metrics["plan_creation_success"]) * 100)
        
        print(f"\n📋 OVERALL COORDINATION HEALTH:")
        print(f"   Total Tests Conducted: {total_tests}")
        print(f"   Plan Creation Success: {plan_success_rate:.1f}% ({self.coordination_metrics['plan_creation_success']}/{total_tests})")
        print(f"   Plan Execution Success: {exec_success_rate:.1f}% ({self.coordination_metrics['plan_execution_success']}/{self.coordination_metrics['plan_creation_success']})")
        
        # Response time analysis
        if self.coordination_metrics["button_response_time"]:
            avg_response = sum(self.coordination_metrics["button_response_time"]) / len(self.coordination_metrics["button_response_time"])
            print(f"   Average Button Response: {avg_response:.2f}s")
        
        # Error analysis
        print(f"\n⚠️  ERROR ANALYSIS:")
        print(f"   LLM/JSON Parsing Errors: {self.coordination_metrics['llm_json_errors']}")
        print(f"   WebSocket Errors: {self.coordination_metrics['websocket_errors']}")
        print(f"   Automation Errors: {self.coordination_metrics['automation_errors']}")
        
        # Identified Issues
        print(f"\n🔍 IDENTIFIED COORDINATION ISSUES ({len(self.identified_issues)} total):")
        if self.identified_issues:
            for i, issue in enumerate(self.identified_issues, 1):
                print(f"   {i}. {issue}")
        else:
            print("   ✅ No coordination issues identified!")
        
        # Recommendations
        print(f"\n💡 COORDINATION RECOMMENDATIONS:")
        
        if self.coordination_metrics['llm_json_errors'] > 0:
            print("   🔧 Fix LLM JSON parsing - implement better error handling")
            
        if plan_success_rate < 80:
            print("   🔧 Improve plan creation reliability")
            
        if exec_success_rate < 75:
            print("   🔧 Enhance execution coordination and error recovery")
            
        if any("timeout" in issue.lower() for issue in self.identified_issues):
            print("   🔧 Optimize response times and timeout handling")
            
        if any("button" in issue.lower() for issue in self.identified_issues):
            print("   🔧 Fix interactive button generation and handling")
            
        # Overall Grade
        print(f"\n🎯 COORDINATION GRADE:")
        if len(self.identified_issues) == 0 and plan_success_rate >= 90 and exec_success_rate >= 90:
            grade = "A+ EXCELLENT"
            color = "🟢"
        elif len(self.identified_issues) <= 2 and plan_success_rate >= 75 and exec_success_rate >= 75:
            grade = "B+ GOOD"
            color = "🟡"
        elif len(self.identified_issues) <= 5 and plan_success_rate >= 50:
            grade = "C NEEDS IMPROVEMENT"
            color = "🟠"
        else:
            grade = "D POOR - SIGNIFICANT ISSUES"
            color = "🔴"
            
        print(f"   {color} {grade}")
        
        # Save detailed report
        timestamp = int(time.time())
        report_data = {
            "timestamp": timestamp,
            "metrics": self.coordination_metrics,
            "identified_issues": self.identified_issues,
            "grade": grade,
            "recommendations": []
        }
        
        report_file = f"coordination_validation_report_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
            
        print(f"\n💾 Detailed report saved: {report_file}")
        print("=" * 60)

async def main():
    """Main validation function"""
    try:
        validator = CoordinationValidator()
        await validator.run_validation_tests()
        
    except KeyboardInterrupt:
        print("\n⏹️  Validation interrupted by user")
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())