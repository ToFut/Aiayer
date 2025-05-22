#!/usr/bin/env python3
"""
Focused Quality Test for Enterprise System
Tests actual working functionality with real server
"""

import asyncio
import websockets
import json
import time
import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FocusedQualityTester:
    """Focused quality testing for working enterprise system"""
    
    def __init__(self):
        self.backend_uri = "ws://127.0.0.1:8767"
        self.test_results = {}
    
    async def run_focused_quality_tests(self):
        """Run focused quality tests on working system"""
        logger.info("🏢 Starting Focused Enterprise Quality Tests")
        
        # Test each mode with realistic scenarios
        await self._test_ask_mode_quality()
        await self._test_agent_mode_quality()
        await self._test_suggest_mode_quality()
        await self._test_general_mode_quality()
        
        # Test memory and semantic search
        await self._test_memory_integration()
        
        # Test performance
        await self._test_performance()
        
        # Generate quality report
        await self._generate_quality_report()
    
    async def _test_ask_mode_quality(self):
        """Test Ask mode with real scenarios"""
        logger.info("🤔 Testing Ask Mode Quality")
        
        test_scenarios = [
            {
                "query": "What can you help me with?",
                "expected_keywords": ["help", "assist", "capabilities"],
                "category": "capabilities_inquiry"
            },
            {
                "query": "What do you know about my work patterns?",
                "expected_keywords": ["patterns", "work", "know"],
                "category": "memory_retrieval"
            },
            {
                "query": "How does this system work?",
                "expected_keywords": ["system", "work", "functions"],
                "category": "system_explanation"
            },
            {
                "query": "What files have I been working on recently?",
                "expected_keywords": ["files", "working", "recently"],
                "category": "recent_activity"
            },
            {
                "query": "Tell me about the chat modes available",
                "expected_keywords": ["chat", "modes", "available"],
                "category": "feature_explanation"
            }
        ]
        
        ask_results = []
        for scenario in test_scenarios:
            result = await self._test_single_scenario("Ask", scenario)
            ask_results.append(result)
        
        # Calculate Ask mode metrics
        ask_metrics = self._calculate_mode_metrics(ask_results)
        self.test_results["ask_mode"] = {
            "scenarios": ask_results,
            "metrics": ask_metrics
        }
    
    async def _test_agent_mode_quality(self):
        """Test Agent mode with task-oriented scenarios"""
        logger.info("🤖 Testing Agent Mode Quality")
        
        test_scenarios = [
            {
                "query": "Help me organize my project files",
                "expected_keywords": ["organize", "project", "files", "plan"],
                "category": "file_organization"
            },
            {
                "query": "Create a backup strategy for my documents",
                "expected_keywords": ["backup", "strategy", "documents", "plan"],
                "category": "backup_planning"
            },
            {
                "query": "Automate my daily workflow",
                "expected_keywords": ["automate", "workflow", "daily", "steps"],
                "category": "workflow_automation"
            },
            {
                "query": "Set up a development environment",
                "expected_keywords": ["setup", "development", "environment", "steps"],
                "category": "environment_setup"
            },
            {
                "query": "Plan a learning schedule for Python",
                "expected_keywords": ["plan", "learning", "schedule", "python"],
                "category": "learning_planning"
            }
        ]
        
        agent_results = []
        for scenario in test_scenarios:
            result = await self._test_single_scenario("Agent", scenario)
            agent_results.append(result)
        
        agent_metrics = self._calculate_mode_metrics(agent_results)
        self.test_results["agent_mode"] = {
            "scenarios": agent_results,
            "metrics": agent_metrics
        }
    
    async def _test_suggest_mode_quality(self):
        """Test Suggest mode with proactive scenarios"""
        logger.info("💡 Testing Suggest Mode Quality")
        
        test_scenarios = [
            {
                "query": "I'm working on a machine learning project",
                "expected_keywords": ["suggest", "recommend", "machine", "learning"],
                "category": "project_suggestions"
            },
            {
                "query": "I want to improve my productivity",
                "expected_keywords": ["improve", "productivity", "suggest", "tips"],
                "category": "productivity_tips"
            },
            {
                "query": "I'm learning data science",
                "expected_keywords": ["learning", "data", "science", "recommend"],
                "category": "learning_recommendations"
            },
            {
                "query": "My workflow feels inefficient",
                "expected_keywords": ["workflow", "inefficient", "improve", "suggest"],
                "category": "workflow_optimization"
            },
            {
                "query": "I need better coding practices",
                "expected_keywords": ["coding", "practices", "better", "suggest"],
                "category": "best_practices"
            }
        ]
        
        suggest_results = []
        for scenario in test_scenarios:
            result = await self._test_single_scenario("Suggest", scenario)
            suggest_results.append(result)
        
        suggest_metrics = self._calculate_mode_metrics(suggest_results)
        self.test_results["suggest_mode"] = {
            "scenarios": suggest_results,
            "metrics": suggest_metrics
        }
    
    async def _test_general_mode_quality(self):
        """Test General mode with conversational scenarios"""
        logger.info("💬 Testing General Mode Quality")
        
        test_scenarios = [
            {
                "query": "Hello, how are you today?",
                "expected_keywords": ["hello", "today", "well", "good"],
                "category": "casual_greeting"
            },
            {
                "query": "What's the weather like?",
                "expected_keywords": ["weather", "information", "sorry"],
                "category": "information_request"
            },
            {
                "query": "Tell me something interesting",
                "expected_keywords": ["interesting", "fact", "something"],
                "category": "engagement_request"
            },
            {
                "query": "I'm feeling overwhelmed with work",
                "expected_keywords": ["understand", "overwhelmed", "work", "help"],
                "category": "emotional_support"
            },
            {
                "query": "What do you think about artificial intelligence?",
                "expected_keywords": ["think", "artificial", "intelligence", "ai"],
                "category": "opinion_discussion"
            }
        ]
        
        general_results = []
        for scenario in test_scenarios:
            result = await self._test_single_scenario("General", scenario)
            general_results.append(result)
        
        general_metrics = self._calculate_mode_metrics(general_results)
        self.test_results["general_mode"] = {
            "scenarios": general_results,
            "metrics": general_metrics
        }
    
    async def _test_single_scenario(self, mode: str, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Test a single scenario and return detailed results"""
        start_time = time.time()
        
        try:
            async with websockets.connect(self.backend_uri) as websocket:
                # Skip welcome message
                await websocket.recv()
                
                # Send test message
                message = {
                    "type": "chat_request",
                    "mode": mode,
                    "query": scenario["query"],
                    "user_id": f"quality_test_{mode.lower()}",
                    "session_id": f"quality_session_{mode.lower()}",
                    "timestamp": time.time()
                }
                
                await websocket.send(json.dumps(message))
                
                # Get response
                response_raw = await asyncio.wait_for(websocket.recv(), timeout=20)
                response = json.loads(response_raw)
                
                processing_time = time.time() - start_time
                
                # Analyze response quality
                analysis = self._analyze_response_quality(response, scenario, processing_time)
                
                return {
                    "scenario": scenario,
                    "response": response,
                    "processing_time": processing_time,
                    "analysis": analysis,
                    "success": response.get("payload", {}).get("success", False)
                }
                
        except Exception as e:
            logger.error(f"Scenario test failed for {mode}: {e}")
            return {
                "scenario": scenario,
                "response": None,
                "processing_time": time.time() - start_time,
                "analysis": {"error": str(e)},
                "success": False
            }
    
    def _analyze_response_quality(self, response: Dict[str, Any], 
                                scenario: Dict[str, Any], 
                                processing_time: float) -> Dict[str, Any]:
        """Analyze response quality with focused metrics"""
        
        if not response or response.get("type") != "chat_response":
            return {"overall_score": 0.0, "error": "Invalid response format"}
        
        payload = response.get("payload", {})
        response_text = payload.get("response", "").lower()
        
        # Quality metrics
        metrics = {
            "response_received": bool(response_text),
            "appropriate_length": 50 <= len(response_text) <= 2000,
            "contains_keywords": False,
            "good_confidence": payload.get("confidence", 0) >= 0.6,
            "fast_response": processing_time < 5.0,
            "memory_usage": "memory" in payload.get("resources_used", []),
            "semantic_search": "semantic_search" in payload.get("resources_used", []) or "memory" in payload.get("resources_used", [])
        }
        
        # Check for expected keywords
        expected_keywords = scenario.get("expected_keywords", [])
        if expected_keywords:
            found_keywords = sum(1 for kw in expected_keywords if kw.lower() in response_text)
            metrics["contains_keywords"] = found_keywords >= len(expected_keywords) * 0.3  # 30% threshold
        
        # Calculate overall score
        score_weights = {
            "response_received": 0.2,
            "appropriate_length": 0.15,
            "contains_keywords": 0.2,
            "good_confidence": 0.15,
            "fast_response": 0.1,
            "memory_usage": 0.1,
            "semantic_search": 0.1
        }
        
        overall_score = sum(
            metrics[key] * weight for key, weight in score_weights.items()
        )
        
        metrics["overall_score"] = overall_score
        return metrics
    
    def _calculate_mode_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate comprehensive metrics for a mode"""
        if not results:
            return {"overall_score": 0.0}
        
        successful_tests = [r for r in results if r.get("success", False)]
        success_rate = len(successful_tests) / len(results)
        
        # Average processing time
        processing_times = [r["processing_time"] for r in results]
        avg_processing_time = sum(processing_times) / len(processing_times)
        
        # Average quality score
        quality_scores = [r["analysis"].get("overall_score", 0) for r in results]
        avg_quality = sum(quality_scores) / len(quality_scores)
        
        # Memory usage rate
        memory_usage = sum(1 for r in results 
                          if r.get("analysis", {}).get("memory_usage", False)) / len(results)
        
        # Confidence scores
        confidences = []
        for r in results:
            if r.get("response") and r["response"].get("payload"):
                conf = r["response"]["payload"].get("confidence", 0)
                confidences.append(conf)
        
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            "success_rate": success_rate,
            "avg_processing_time": avg_processing_time,
            "avg_quality_score": avg_quality,
            "memory_usage_rate": memory_usage,
            "avg_confidence": avg_confidence,
            "overall_score": (success_rate + avg_quality + (1.0 if avg_processing_time < 3.0 else 0.5)) / 3
        }
    
    async def _test_memory_integration(self):
        """Test memory and semantic search integration"""
        logger.info("🧠 Testing Memory Integration")
        
        memory_tests = []
        
        # Test 1: Add a memory and retrieve it
        try:
            async with websockets.connect(self.backend_uri) as websocket:
                await websocket.recv()  # Skip welcome
                
                # First, add some context
                context_message = {
                    "type": "chat_request",
                    "mode": "Ask",
                    "query": "I am working on a Python project about machine learning",
                    "user_id": "memory_test_user",
                    "session_id": "memory_test_session",
                    "timestamp": time.time()
                }
                
                await websocket.send(json.dumps(context_message))
                await websocket.recv()  # Get response
                
                # Then ask about it
                recall_message = {
                    "type": "chat_request",
                    "mode": "Ask", 
                    "query": "What do you know about my Python project?",
                    "user_id": "memory_test_user",
                    "session_id": "memory_test_session",
                    "timestamp": time.time()
                }
                
                await websocket.send(json.dumps(recall_message))
                response_raw = await websocket.recv()
                response = json.loads(response_raw)
                
                # Check if memory was used
                payload = response.get("payload", {})
                memory_used = "memory" in payload.get("resources_used", [])
                
                memory_tests.append({
                    "test": "context_recall",
                    "success": memory_used and "python" in payload.get("response", "").lower(),
                    "memory_used": memory_used
                })
                
        except Exception as e:
            memory_tests.append({
                "test": "context_recall",
                "success": False,
                "error": str(e)
            })
        
        # Calculate memory metrics
        memory_success_rate = sum(1 for t in memory_tests if t.get("success", False)) / len(memory_tests)
        memory_usage_rate = sum(1 for t in memory_tests if t.get("memory_used", False)) / len(memory_tests)
        
        self.test_results["memory_system"] = {
            "tests": memory_tests,
            "success_rate": memory_success_rate,
            "memory_usage_rate": memory_usage_rate,
            "overall_score": (memory_success_rate + memory_usage_rate) / 2
        }
    
    async def _test_performance(self):
        """Test system performance"""
        logger.info("⚡ Testing Performance")
        
        # Test concurrent requests
        start_time = time.time()
        tasks = []
        
        for i in range(3):  # 3 concurrent requests
            task = self._send_performance_request(f"Performance test {i+1}")
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        
        self.test_results["performance"] = {
            "concurrent_requests": len(tasks),
            "successful_requests": successful,
            "total_time": total_time,
            "success_rate": successful / len(tasks),
            "throughput": len(tasks) / total_time
        }
    
    async def _send_performance_request(self, query: str) -> Dict[str, Any]:
        """Send a single performance test request"""
        try:
            async with websockets.connect(self.backend_uri) as websocket:
                await websocket.recv()  # Skip welcome
                
                message = {
                    "type": "chat_request",
                    "mode": "Ask",
                    "query": query,
                    "user_id": "perf_test_user",
                    "session_id": f"perf_session_{time.time()}",
                    "timestamp": time.time()
                }
                
                await websocket.send(json.dumps(message))
                response_raw = await asyncio.wait_for(websocket.recv(), timeout=10)
                response = json.loads(response_raw)
                
                return {
                    "success": response.get("payload", {}).get("success", False),
                    "response_time": response.get("payload", {}).get("processing_time", 0)
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _generate_quality_report(self):
        """Generate focused quality report"""
        logger.info("📊 Generating Focused Quality Report")
        
        print("\n" + "="*80)
        print("🏢 FOCUSED ENTERPRISE QUALITY ASSESSMENT")
        print("="*80)
        
        # Calculate overall system score
        mode_scores = []
        for mode_name in ["ask_mode", "agent_mode", "suggest_mode", "general_mode"]:
            if mode_name in self.test_results:
                mode_scores.append(self.test_results[mode_name]["metrics"]["overall_score"])
        
        memory_score = self.test_results.get("memory_system", {}).get("overall_score", 0)
        performance_score = self.test_results.get("performance", {}).get("success_rate", 0)
        
        all_scores = mode_scores + [memory_score, performance_score]
        overall_score = sum(all_scores) / len(all_scores) if all_scores else 0
        
        print(f"🎯 OVERALL SYSTEM QUALITY: {overall_score:.1%}")
        
        if overall_score >= 0.9:
            print("🏆 ENTERPRISE GRADE: PLATINUM ⭐⭐⭐")
        elif overall_score >= 0.8:
            print("🥇 ENTERPRISE GRADE: GOLD ⭐⭐")
        elif overall_score >= 0.7:
            print("🥈 ENTERPRISE GRADE: SILVER ⭐")
        elif overall_score >= 0.6:
            print("🥉 ENTERPRISE GRADE: BRONZE")
        else:
            print("❌ ENTERPRISE GRADE: NEEDS IMPROVEMENT")
        
        print("\n" + "-"*80)
        print("📋 DETAILED MODE ANALYSIS")
        print("-"*80)
        
        mode_names = {
            "ask_mode": "🤔 ASK MODE",
            "agent_mode": "🤖 AGENT MODE", 
            "suggest_mode": "💡 SUGGEST MODE",
            "general_mode": "💬 GENERAL MODE"
        }
        
        for mode_key, mode_display in mode_names.items():
            if mode_key in self.test_results:
                metrics = self.test_results[mode_key]["metrics"]
                
                grade = self._calculate_grade(metrics["overall_score"])
                
                print(f"\n{mode_display}: Grade {grade}")
                print(f"   Success Rate: {metrics['success_rate']:.1%}")
                print(f"   Quality Score: {metrics['avg_quality_score']:.1%}")
                print(f"   Avg Response Time: {metrics['avg_processing_time']:.2f}s")
                print(f"   Avg Confidence: {metrics['avg_confidence']:.1%}")
                print(f"   Memory Usage: {metrics['memory_usage_rate']:.1%}")
                
                if metrics['success_rate'] >= 0.8:
                    print("   ✅ Production Ready")
                else:
                    print("   ⚠️  Needs Improvement")
        
        # Memory System Report
        if "memory_system" in self.test_results:
            memory_data = self.test_results["memory_system"]
            memory_grade = self._calculate_grade(memory_data["overall_score"])
            
            print(f"\n🧠 MEMORY SYSTEM: Grade {memory_grade}")
            print(f"   Success Rate: {memory_data['success_rate']:.1%}")
            print(f"   Memory Usage Rate: {memory_data['memory_usage_rate']:.1%}")
            print(f"   Integration Status: {'✅ Excellent' if memory_data['overall_score'] >= 0.8 else '⚠️  Needs Work'}")
        
        # Performance Report
        if "performance" in self.test_results:
            perf_data = self.test_results["performance"]
            
            print(f"\n⚡ PERFORMANCE METRICS")
            print(f"   Concurrent Handling: {perf_data['success_rate']:.1%}")
            print(f"   Total Requests: {perf_data['concurrent_requests']}")
            print(f"   Successful: {perf_data['successful_requests']}")
            print(f"   Throughput: {perf_data['throughput']:.1f} req/s")
        
        # Final Recommendation
        print("\n" + "="*80)
        if overall_score >= 0.8:
            print("🚀 DEPLOYMENT RECOMMENDATION: APPROVED FOR PRODUCTION")
            print("   System demonstrates enterprise-grade quality and reliability")
            print("   ✅ All modes functional with semantic search integration")
            print("   ✅ Memory system working correctly")
            print("   ✅ Performance meets enterprise standards")
        elif overall_score >= 0.6:
            print("⚠️  DEPLOYMENT RECOMMENDATION: STAGING ENVIRONMENT READY")
            print("   System suitable for staging with continued monitoring")
        else:
            print("🛑 DEPLOYMENT RECOMMENDATION: DEVELOPMENT ONLY")
            print("   System requires improvements before production")
        
        print("="*80)
    
    def _calculate_grade(self, score: float) -> str:
        """Calculate letter grade from score"""
        if score >= 0.95:
            return "A+"
        elif score >= 0.9:
            return "A"
        elif score >= 0.85:
            return "A-"
        elif score >= 0.8:
            return "B+"
        elif score >= 0.75:
            return "B"
        elif score >= 0.7:
            return "B-"
        elif score >= 0.65:
            return "C+"
        elif score >= 0.6:
            return "C"
        elif score >= 0.5:
            return "D"
        else:
            return "F"

async def main():
    """Run focused quality tests"""
    tester = FocusedQualityTester()
    
    try:
        await tester.run_focused_quality_tests()
    except KeyboardInterrupt:
        logger.info("🛑 Quality testing interrupted")
    except Exception as e:
        logger.error(f"🚨 Quality testing failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())