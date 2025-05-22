#!/usr/bin/env python3
"""
Enterprise Message Flow Test
Tests the complete message flow from client to brain router with all modes
"""

import asyncio
import websockets
import json
import time
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnterpriseMessageFlowTester:
    """Enterprise-grade message flow testing client"""
    
    def __init__(self):
        self.backend_uri = "ws://127.0.0.1:8767"
        self.test_results = []
    
    async def test_complete_message_flow(self):
        """Test complete message flow for all modes"""
        logger.info("🧪 Starting Enterprise Message Flow Test")
        
        # Test cases for each mode
        test_cases = [
            {
                "mode": "Ask",
                "query": "What can you help me with?",
                "expected_keywords": ["help", "assist", "capabilities"],
                "description": "Basic Ask mode functionality test"
            },
            {
                "mode": "Agent", 
                "query": "Help me organize my files",
                "expected_keywords": ["task", "plan", "files"],
                "description": "Agent mode task planning test"
            },
            {
                "mode": "Suggest",
                "query": "I'm working on a Python project",
                "expected_keywords": ["suggest", "recommend", "python"],
                "description": "Suggest mode proactive help test"
            },
            {
                "mode": "General",
                "query": "Hello, how are you today?",
                "expected_keywords": ["hello", "today", "well"],
                "description": "General mode conversation test"
            }
        ]
        
        # Run all test cases
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"🔍 Running Test {i}/4: {test_case['description']}")
            result = await self._test_single_mode(test_case)
            self.test_results.append(result)
            
            # Brief pause between tests
            await asyncio.sleep(1)
        
        # Generate test report
        await self._generate_test_report()
    
    async def _test_single_mode(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Test a single mode's message flow"""
        start_time = time.time()
        
        try:
            async with websockets.connect(self.backend_uri) as websocket:
                # Prepare message
                message = {
                    "type": "chat_request",
                    "mode": test_case["mode"],
                    "query": test_case["query"],
                    "user_id": "test_user",
                    "session_id": f"test_session_{int(time.time())}",
                    "timestamp": time.time()
                }
                
                logger.info(f"📤 Sending {test_case['mode']} mode message: {test_case['query']}")
                
                # Send message
                await websocket.send(json.dumps(message))
                
                # Wait for response
                response_raw = await asyncio.wait_for(websocket.recv(), timeout=30)
                response = json.loads(response_raw)
                
                processing_time = time.time() - start_time
                
                logger.info(f"📥 Received response in {processing_time:.2f}s")
                
                # Analyze response
                analysis = await self._analyze_response(response, test_case, processing_time)
                
                return {
                    "test_case": test_case,
                    "response": response,
                    "analysis": analysis,
                    "success": analysis["overall_success"],
                    "processing_time": processing_time
                }
                
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            return {
                "test_case": test_case,
                "response": None,
                "analysis": {"error": str(e), "overall_success": False},
                "success": False,
                "processing_time": time.time() - start_time
            }
    
    async def _analyze_response(self, response: Dict[str, Any], 
                              test_case: Dict[str, Any], processing_time: float) -> Dict[str, Any]:
        """Analyze the response quality and correctness"""
        analysis = {
            "response_received": response is not None,
            "correct_mode": False,
            "contains_keywords": False,
            "reasonable_time": processing_time < 10.0,
            "has_confidence": False,
            "semantic_search_used": False,
            "brain_router_used": False,
            "overall_success": False
        }
        
        if response:
            # Check if correct mode was used
            if response.get("mode_used") == test_case["mode"]:
                analysis["correct_mode"] = True
            
            # Check for expected keywords in response
            response_text = response.get("response", "").lower()
            if any(keyword.lower() in response_text for keyword in test_case["expected_keywords"]):
                analysis["contains_keywords"] = True
            
            # Check confidence score
            if "confidence" in response and isinstance(response["confidence"], (int, float)):
                analysis["has_confidence"] = True
            
            # Check if semantic search was used
            resources_used = response.get("resources_used", [])
            if "memory" in resources_used or "semantic_search" in resources_used:
                analysis["semantic_search_used"] = True
            
            # Check if brain router was involved
            if response.get("success") is not None:
                analysis["brain_router_used"] = True
            
            # Overall success calculation
            success_factors = [
                analysis["response_received"],
                analysis["correct_mode"],
                analysis["reasonable_time"],
                analysis["brain_router_used"]
            ]
            
            analysis["overall_success"] = sum(success_factors) >= 3
            analysis["success_score"] = sum(success_factors) / len(success_factors)
        
        return analysis
    
    async def _generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("📊 Generating Enterprise Test Report")
        
        successful_tests = sum(1 for result in self.test_results if result["success"])
        total_tests = len(self.test_results)
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        
        avg_processing_time = sum(r["processing_time"] for r in self.test_results) / total_tests
        
        print("\n" + "="*60)
        print("🏢 ENTERPRISE MESSAGE FLOW TEST REPORT")
        print("="*60)
        print(f"📈 Overall Success Rate: {success_rate:.1f}% ({successful_tests}/{total_tests})")
        print(f"⏱️  Average Processing Time: {avg_processing_time:.2f}s")
        print()
        
        # Detailed results
        for i, result in enumerate(self.test_results, 1):
            test_case = result["test_case"]
            analysis = result["analysis"]
            
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            
            print(f"Test {i}: {test_case['description']}")
            print(f"  Mode: {test_case['mode']} | Query: {test_case['query']}")
            print(f"  Status: {status} | Time: {result['processing_time']:.2f}s")
            
            if result["response"]:
                response = result["response"]
                print(f"  Response: {response.get('response', 'N/A')[:100]}...")
                print(f"  Confidence: {response.get('confidence', 'N/A')}")
                print(f"  Resources: {response.get('resources_used', [])}")
            
            if "error" in analysis:
                print(f"  Error: {analysis['error']}")
            
            print()
        
        # System health summary
        print("🏥 SYSTEM HEALTH SUMMARY")
        print("-" * 30)
        
        mode_success = {}
        for result in self.test_results:
            mode = result["test_case"]["mode"]
            if mode not in mode_success:
                mode_success[mode] = []
            mode_success[mode].append(result["success"])
        
        for mode, successes in mode_success.items():
            success_rate = (sum(successes) / len(successes)) * 100
            print(f"  {mode} Mode: {success_rate:.1f}% success rate")
        
        # Performance metrics
        fast_responses = sum(1 for r in self.test_results if r["processing_time"] < 5.0)
        print(f"  Performance: {fast_responses}/{total_tests} responses under 5s")
        
        # Final verdict
        print("\n" + "="*60)
        if success_rate >= 75:
            print("🎉 ENTERPRISE SYSTEM: READY FOR PRODUCTION")
        elif success_rate >= 50:
            print("⚠️  ENTERPRISE SYSTEM: NEEDS OPTIMIZATION")
        else:
            print("🚨 ENTERPRISE SYSTEM: CRITICAL ISSUES DETECTED")
        print("="*60)

async def main():
    """Main test execution"""
    tester = EnterpriseMessageFlowTester()
    
    try:
        await tester.test_complete_message_flow()
    except KeyboardInterrupt:
        logger.info("🛑 Test interrupted by user")
    except Exception as e:
        logger.error(f"🚨 Test suite failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())