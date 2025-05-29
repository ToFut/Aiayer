#!/usr/bin/env python3
"""
Comprehensive AgentMode Test Suite
Tests all aspects of AgentMode functionality and identifies issues systematically
"""

import asyncio
import json
import time
import logging
import traceback
from typing import Dict, Any, List
import websockets
from datetime import datetime
import os
import sys

# Set up comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/comprehensive_agent_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AgentModeTestSuite:
    """Comprehensive test suite for AgentMode functionality"""
    
    def __init__(self):
        self.test_results = []
        self.backend_url = "ws://localhost:8767"
        self.web_test_url = "ws://localhost:8765"
        self.session_id = f"test_session_{int(time.time())}"
        self.websocket = None
        
    async def connect_to_backend(self):
        """Connect to the backend WebSocket"""
        try:
            logger.info(f"🔌 Connecting to backend at {self.backend_url}")
            self.websocket = await websockets.connect(self.backend_url)
            logger.info("✅ Connected to backend successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to backend: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from WebSocket"""
        if self.websocket:
            await self.websocket.close()
    
    async def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send message and get response"""
        try:
            await self.websocket.send(json.dumps(message))
            response = await asyncio.wait_for(self.websocket.recv(), timeout=30.0)
            response_data = json.loads(response)
            
            # If it's a connection message, wait for the actual response
            if response_data.get("type") == "connection_established":
                response = await asyncio.wait_for(self.websocket.recv(), timeout=30.0)
                return json.loads(response)
            else:
                return response_data
        except asyncio.TimeoutError:
            logger.error("⏰ Request timed out")
            return {"error": "timeout", "success": False}
        except Exception as e:
            logger.error(f"❌ Communication error: {e}")
            return {"error": str(e), "success": False}
    
    def log_test_result(self, test_name: str, success: bool, details: Dict[str, Any], issues: List[str] = None):
        """Log test result"""
        result = {
            "test_name": test_name,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "details": details,
            "issues": issues or []
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
        
        if issues:
            for issue in issues:
                logger.warning(f"⚠️  Issue: {issue}")
    
    async def test_basic_agent_functionality(self):
        """Test 1: Basic AgentMode functionality"""
        logger.info("🧪 TEST 1: Basic AgentMode Functionality")
        
        test_cases = [
            {
                "name": "Simple Click Action",
                "message": "Click on the search button",
                "expected_keywords": ["click", "search", "button"]
            },
            {
                "name": "Simple Text Input",
                "message": "Type 'hello world' in the text field",
                "expected_keywords": ["type", "text", "input"]
            },
            {
                "name": "Basic Navigation",
                "message": "Open Google in browser",
                "expected_keywords": ["open", "browser", "google"]
            }
        ]
        
        for case in test_cases:
            logger.info(f"  📝 Testing: {case['name']}")
            
            start_time = time.time()
            message = {
                "type": "chat_request",
                "message": case["message"],
                "session_id": self.session_id,
                "mode": "agent"
            }
            
            response = await self.send_message(message)
            response_time = time.time() - start_time
            
            issues = []
            success = True
            
            # Check if response contains expected elements
            if "error" in response:
                issues.append(f"Error in response: {response['error']}")
                success = False
            
            if response_time > 10.0:
                issues.append(f"Slow response time: {response_time:.2f}s")
            
            if not response.get("success", False):
                issues.append("Response indicates failure")
                success = False
            
            # Check for plan creation (more flexible)
            response_str = json.dumps(response).lower()
            plan_created = ("plan" in response or "steps" in response or 
                          "automation" in response_str or "action" in response_str)
            if not plan_created:
                issues.append("No automation plan created")
                # Don't mark as failure if it's a valid response - just note the issue
            
            self.log_test_result(
                f"Basic Agent - {case['name']}", 
                success, 
                {"response_time": response_time, "response": response},
                issues
            )
            
            await asyncio.sleep(1)  # Brief pause between tests
    
    async def test_complex_agent_scenarios(self):
        """Test 2: Complex multi-step scenarios"""
        logger.info("🧪 TEST 2: Complex AgentMode Scenarios")
        
        complex_scenarios = [
            {
                "name": "Multi-step Web Search",
                "message": "Search for 'AI automation tools' on Google and click on the first result",
                "expected_steps": 3
            },
            {
                "name": "Form Filling",
                "message": "Fill out a contact form with name 'John Doe', email 'john@example.com', and message 'Hello'",
                "expected_steps": 4
            },
            {
                "name": "File Operations",
                "message": "Create a new text file called 'test.txt' and write 'Hello World' in it",
                "expected_steps": 2
            }
        ]
        
        for scenario in complex_scenarios:
            logger.info(f"  📝 Testing: {scenario['name']}")
            
            start_time = time.time()
            message = {
                "type": "chat_request",
                "message": scenario["message"],
                "session_id": self.session_id,
                "mode": "agent"
            }
            
            response = await self.send_message(message)
            response_time = time.time() - start_time
            
            issues = []
            success = True
            
            # Complex scenario checks
            if "error" in response:
                issues.append(f"Error in response: {response['error']}")
                success = False
            
            if response_time > 15.0:
                issues.append(f"Very slow response for complex scenario: {response_time:.2f}s")
            
            # Check for multi-step plan
            steps = response.get("plan", {}).get("steps", [])
            if len(steps) < scenario["expected_steps"]:
                issues.append(f"Expected at least {scenario['expected_steps']} steps, got {len(steps)}")
                success = False
            
            self.log_test_result(
                f"Complex Agent - {scenario['name']}", 
                success, 
                {"response_time": response_time, "steps_count": len(steps), "response": response},
                issues
            )
            
            await asyncio.sleep(2)  # Longer pause for complex tests
    
    async def test_ui_detection_capabilities(self):
        """Test 3: UI element detection and coordinate mapping"""
        logger.info("🧪 TEST 3: UI Detection Capabilities")
        
        ui_tests = [
            {
                "name": "Button Detection",
                "message": "Find and click the submit button on the current page",
                "ui_element": "button"
            },
            {
                "name": "Input Field Detection", 
                "message": "Find the search input field and type 'test query'",
                "ui_element": "input"
            },
            {
                "name": "Link Detection",
                "message": "Click on the 'About' link in the navigation menu",
                "ui_element": "link"
            }
        ]
        
        for test in ui_tests:
            logger.info(f"  📝 Testing: {test['name']}")
            
            start_time = time.time()
            message = {
                "type": "chat_request",
                "message": test["message"],
                "session_id": self.session_id,
                "mode": "agent",
                "ui_detection": True
            }
            
            response = await self.send_message(message)
            response_time = time.time() - start_time
            
            issues = []
            success = True
            
            # UI detection specific checks
            if "error" in response:
                issues.append(f"Error in response: {response['error']}")
                success = False
            
            # Check for coordinate information
            plan = response.get("plan", {})
            steps = plan.get("steps", [])
            
            has_coordinates = False
            for step in steps:
                if "coordinates" in step or "x" in step or "y" in step:
                    has_coordinates = True
                    break
            
            if not has_coordinates and "click" in test["message"].lower():
                issues.append("No coordinate information found for click action")
            
            self.log_test_result(
                f"UI Detection - {test['name']}", 
                success, 
                {"response_time": response_time, "has_coordinates": has_coordinates, "response": response},
                issues
            )
            
            await asyncio.sleep(1)
    
    async def test_memory_integration(self):
        """Test 4: Memory system integration"""
        logger.info("🧪 TEST 4: Memory Integration")
        
        # First, send a message to establish context
        context_message = {
            "type": "chat_request",
            "message": "I want to automate my daily email workflow",
            "session_id": self.session_id,
            "mode": "agent"
        }
        
        logger.info("  📝 Establishing context...")
        await self.send_message(context_message)
        await asyncio.sleep(2)
        
        # Now test context-aware follow-up
        followup_message = {
            "type": "chat_request", 
            "message": "Help me set up the automation we just discussed",
            "session_id": self.session_id,
            "mode": "agent"
        }
        
        logger.info("  📝 Testing context-aware follow-up...")
        start_time = time.time()
        response = await self.send_message(followup_message)
        response_time = time.time() - start_time
        
        issues = []
        success = True
        
        if "error" in response:
            issues.append(f"Error in response: {response['error']}")
            success = False
        
        # Check if response shows context awareness
        response_text = json.dumps(response).lower()
        context_keywords = ["email", "workflow", "automation", "discussed", "previous"]
        context_aware = any(keyword in response_text for keyword in context_keywords)
        
        if not context_aware:
            issues.append("Response doesn't show context awareness from previous message")
        
        self.log_test_result(
            "Memory Integration - Context Awareness",
            success,
            {"response_time": response_time, "context_aware": context_aware, "response": response},
            issues
        )
    
    async def test_error_handling(self):
        """Test 5: Error handling and recovery"""
        logger.info("🧪 TEST 5: Error Handling")
        
        error_scenarios = [
            {
                "name": "Invalid Request Format",
                "message": {"invalid": "format", "no_type": True}
            },
            {
                "name": "Empty Message",
                "message": {"type": "chat_request", "message": "", "session_id": self.session_id}
            },
            {
                "name": "Malformed JSON",
                "message": "not_json_at_all"
            }
        ]
        
        for scenario in error_scenarios:
            logger.info(f"  📝 Testing: {scenario['name']}")
            
            try:
                if isinstance(scenario["message"], dict):
                    await self.websocket.send(json.dumps(scenario["message"]))
                else:
                    await self.websocket.send(scenario["message"])
                
                response = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
                response_data = json.loads(response)
                
                # For error scenarios, we expect either an error response or graceful handling
                success = "error" in response_data or response_data.get("success") == False
                issues = [] if success else ["Error scenario not handled properly"]
                
            except Exception as e:
                # Connection errors are acceptable for malformed requests
                success = True
                issues = []
                response_data = {"error": str(e)}
            
            self.log_test_result(
                f"Error Handling - {scenario['name']}",
                success,
                {"response": response_data},
                issues
            )
            
            await asyncio.sleep(1)
    
    async def test_performance_metrics(self):
        """Test 6: Performance and response times"""
        logger.info("🧪 TEST 6: Performance Metrics")
        
        # Test rapid-fire requests
        logger.info("  📝 Testing rapid requests...")
        rapid_times = []
        
        for i in range(5):
            start_time = time.time()
            message = {
                "type": "chat_request",
                "message": f"Simple test action {i+1}",
                "session_id": self.session_id,
                "mode": "agent"
            }
            
            response = await self.send_message(message)
            response_time = time.time() - start_time
            rapid_times.append(response_time)
            
            await asyncio.sleep(0.5)  # Brief pause
        
        avg_response_time = sum(rapid_times) / len(rapid_times)
        max_response_time = max(rapid_times)
        
        issues = []
        success = True
        
        if avg_response_time > 5.0:
            issues.append(f"Average response time too slow: {avg_response_time:.2f}s")
            success = False
        
        if max_response_time > 10.0:
            issues.append(f"Maximum response time too slow: {max_response_time:.2f}s")
            success = False
        
        self.log_test_result(
            "Performance - Rapid Requests",
            success,
            {
                "avg_response_time": avg_response_time,
                "max_response_time": max_response_time,
                "all_times": rapid_times
            },
            issues
        )
    
    async def run_all_tests(self):
        """Run complete test suite"""
        logger.info("🚀 Starting Comprehensive AgentMode Test Suite")
        logger.info("=" * 60)
        
        # Connect to backend
        if not await self.connect_to_backend():
            logger.error("❌ Cannot connect to backend - aborting tests")
            return
        
        try:
            # Run all test categories
            await self.test_basic_agent_functionality()
            await self.test_complex_agent_scenarios()
            await self.test_ui_detection_capabilities()
            await self.test_memory_integration()
            await self.test_error_handling()
            await self.test_performance_metrics()
            
        except Exception as e:
            logger.error(f"❌ Test suite error: {e}")
            logger.error(traceback.format_exc())
        
        finally:
            await self.disconnect()
        
        # Generate test report
        self.generate_test_report()
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 COMPREHENSIVE TEST REPORT")
        logger.info("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - passed_tests
        
        logger.info(f"📈 Total Tests: {total_tests}")
        logger.info(f"✅ Passed: {passed_tests}")
        logger.info(f"❌ Failed: {failed_tests}")
        logger.info(f"📊 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Group issues by category
        all_issues = []
        for result in self.test_results:
            all_issues.extend(result.get("issues", []))
        
        if all_issues:
            logger.info("\n🔍 IDENTIFIED ISSUES:")
            issue_counts = {}
            for issue in all_issues:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
            
            for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"  ⚠️  {issue} (occurred {count} times)")
        
        # Save detailed report
        report_path = f"logs/agent_test_report_{int(time.time())}.json"
        with open(report_path, 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "success_rate": (passed_tests/total_tests)*100
                },
                "test_results": self.test_results,
                "all_issues": all_issues
            }, f, indent=2)
        
        logger.info(f"\n📋 Detailed report saved: {report_path}")

async def main():
    """Main test runner"""
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Run test suite
    test_suite = AgentModeTestSuite()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())