#!/usr/bin/env python3
"""
Test all chat modes with llama3.2:1b model
Verify meaningful responses across Ask, Agent, Suggest, and General modes
"""

import asyncio
import websockets
import json
import time
from datetime import datetime

class ChatModesTester:
    def __init__(self):
        self.backend_url = "ws://localhost:8767"
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "model": "llama3.2:1b",
            "test_results": {}
        }
        
        # Test cases for each mode
        self.test_cases = {
            "ask": [
                {
                    "query": "What is machine learning?",
                    "expected_aspects": ["definition", "algorithms", "data", "learning"]
                },
                {
                    "query": "How do I center a div in CSS?",
                    "expected_aspects": ["flexbox", "grid", "margin", "center"]
                },
                {
                    "query": "What's the difference between Python and JavaScript?",
                    "expected_aspects": ["syntax", "use cases", "differences", "comparison"]
                }
            ],
            "agent": [
                {
                    "query": "Help me plan a website redesign project",
                    "expected_aspects": ["steps", "planning", "timeline", "tasks"]
                },
                {
                    "query": "I need to optimize my web app performance",
                    "expected_aspects": ["analysis", "optimization", "steps", "monitoring"]
                },
                {
                    "query": "Create a marketing strategy for a new app",
                    "expected_aspects": ["strategy", "target audience", "channels", "goals"]
                }
            ],
            "suggest": [
                {
                    "query": "I'm stuck on this coding problem",
                    "expected_aspects": ["suggestions", "solutions", "approaches", "tips"]
                },
                {
                    "query": "What should I learn next in web development?",
                    "expected_aspects": ["recommendations", "skills", "technologies", "path"]
                },
                {
                    "query": "How can I improve my team's productivity?",
                    "expected_aspects": ["suggestions", "tools", "methods", "improvements"]
                }
            ],
            "general": [
                {
                    "query": "Tell me about the latest trends in AI",
                    "expected_aspects": ["trends", "technologies", "developments", "AI"]
                },
                {
                    "query": "What are some good practices for remote work?",
                    "expected_aspects": ["practices", "tips", "remote", "productivity"]
                },
                {
                    "query": "Explain the concept of microservices",
                    "expected_aspects": ["architecture", "services", "benefits", "design"]
                }
            ]
        }

    async def test_mode(self, mode, test_cases):
        """Test a specific chat mode with multiple queries"""
        print(f"\n{'='*60}")
        print(f"TESTING {mode.upper()} MODE")
        print(f"{'='*60}")
        
        mode_results = {
            "mode": mode,
            "tests": [],
            "success_rate": 0,
            "avg_response_time": 0,
            "avg_quality_score": 0
        }
        
        successful_tests = 0
        total_time = 0
        total_quality = 0
        
        for i, test_case in enumerate(test_cases):
            print(f"\nTest {i+1}/{len(test_cases)}: {test_case['query']}")
            print("-" * 50)
            
            start_time = time.time()
            
            try:
                async with websockets.connect(self.backend_url) as websocket:
                    # Send test message
                    message = {
                        "type": "chat_request",
                        "mode": mode,
                        "message": test_case["query"],
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    await websocket.send(json.dumps(message))
                    
                    # Wait for response
                    response = await websocket.recv()
                    end_time = time.time()
                    
                    response_data = json.loads(response)
                    response_time = end_time - start_time
                    
                    if response_data.get("type") == "chat_response":
                        ai_response = response_data.get("response", "")
                        
                        # Analyze response quality
                        quality_score = self.analyze_response_quality(ai_response, test_case)
                        
                        print(f"✅ Response received ({response_time:.1f}s)")
                        print(f"Quality Score: {quality_score:.1f}/10")
                        print(f"Response: {ai_response[:200]}{'...' if len(ai_response) > 200 else ''}")
                        
                        test_result = {
                            "query": test_case["query"],
                            "response": ai_response,
                            "response_time": response_time,
                            "quality_score": quality_score,
                            "success": True,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        successful_tests += 1
                        total_time += response_time
                        total_quality += quality_score
                        
                    else:
                        print(f"❌ Unexpected response type: {response_data.get('type')}")
                        test_result = {
                            "query": test_case["query"],
                            "error": f"Unexpected response type: {response_data.get('type')}",
                            "response_time": response_time,
                            "success": False
                        }
                    
            except Exception as e:
                end_time = time.time()
                response_time = end_time - start_time
                print(f"❌ Error: {str(e)}")
                
                test_result = {
                    "query": test_case["query"],
                    "error": str(e),
                    "response_time": response_time,
                    "success": False
                }
            
            mode_results["tests"].append(test_result)
            
            # Brief pause between tests
            await asyncio.sleep(2)
        
        # Calculate mode statistics
        if successful_tests > 0:
            mode_results["success_rate"] = (successful_tests / len(test_cases)) * 100
            mode_results["avg_response_time"] = total_time / successful_tests
            mode_results["avg_quality_score"] = total_quality / successful_tests
        
        print(f"\n{mode.upper()} MODE SUMMARY:")
        print(f"Success Rate: {mode_results['success_rate']:.1f}%")
        print(f"Avg Response Time: {mode_results['avg_response_time']:.1f}s")
        print(f"Avg Quality Score: {mode_results['avg_quality_score']:.1f}/10")
        
        return mode_results

    def analyze_response_quality(self, response, test_case):
        """Analyze response quality based on relevance and completeness"""
        if not response:
            return 0
        
        score = 0
        max_score = 10
        
        # 1. Length check (2 points)
        word_count = len(response.split())
        if 30 <= word_count <= 200:
            score += 2
        elif 20 <= word_count < 30 or 200 < word_count <= 300:
            score += 1.5
        elif word_count >= 15:
            score += 1
        
        # 2. Relevance to expected aspects (4 points)
        expected_aspects = test_case.get("expected_aspects", [])
        if expected_aspects:
            found_aspects = 0
            for aspect in expected_aspects:
                if any(word.lower() in response.lower() for word in aspect.split()):
                    found_aspects += 1
            score += (found_aspects / len(expected_aspects)) * 4
        else:
            score += 2  # Default if no aspects specified
        
        # 3. Structure and coherence (2 points)
        sentences = [s.strip() for s in response.split('.') if s.strip()]
        if len(sentences) >= 3:
            score += 2
        elif len(sentences) >= 2:
            score += 1.5
        elif len(sentences) >= 1:
            score += 1
        
        # 4. Actionability and usefulness (2 points)
        useful_indicators = ["you can", "try", "consider", "recommend", "suggest", "steps", "first", "next"]
        found_indicators = sum(1 for indicator in useful_indicators if indicator.lower() in response.lower())
        score += min(2, found_indicators * 0.4)
        
        return min(max_score, score)

    async def run_all_tests(self):
        """Run tests for all chat modes"""
        print("COMPREHENSIVE CHAT MODES TEST")
        print(f"Testing with model: llama3.2:1b")
        print(f"Backend URL: {self.backend_url}")
        print("=" * 80)
        
        # Test each mode
        for mode, test_cases in self.test_cases.items():
            mode_results = await self.test_mode(mode, test_cases)
            self.test_results["test_results"][mode] = mode_results
        
        # Generate summary report
        self.generate_summary_report()
        
        # Save detailed results
        with open("chat_modes_test_results_llama1b.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\n{'='*80}")
        print("ALL TESTS COMPLETED!")
        print("Results saved to: chat_modes_test_results_llama1b.json")
        print("=" * 80)

    def generate_summary_report(self):
        """Generate human-readable summary report"""
        print(f"\n{'='*80}")
        print("FINAL SUMMARY REPORT")
        print("=" * 80)
        
        overall_stats = {
            "total_tests": 0,
            "successful_tests": 0,
            "avg_response_time": 0,
            "avg_quality_score": 0
        }
        
        # Calculate overall statistics
        for mode, results in self.test_results["test_results"].items():
            mode_total = len(results["tests"])
            mode_successful = sum(1 for test in results["tests"] if test["success"])
            
            overall_stats["total_tests"] += mode_total
            overall_stats["successful_tests"] += mode_successful
            
            if mode_successful > 0:
                overall_stats["avg_response_time"] += results["avg_response_time"] * mode_successful
                overall_stats["avg_quality_score"] += results["avg_quality_score"] * mode_successful
        
        if overall_stats["successful_tests"] > 0:
            overall_stats["avg_response_time"] /= overall_stats["successful_tests"]
            overall_stats["avg_quality_score"] /= overall_stats["successful_tests"]
        
        # Print mode-by-mode summary
        print("MODE PERFORMANCE:")
        print("-" * 40)
        for mode, results in self.test_results["test_results"].items():
            status = "✅ WORKING" if results["success_rate"] >= 80 else "⚠️  ISSUES" if results["success_rate"] >= 60 else "❌ FAILING"
            print(f"{mode.upper():10} | {status} | {results['success_rate']:5.1f}% | {results['avg_response_time']:5.1f}s | {results['avg_quality_score']:4.1f}/10")
        
        print(f"\nOVERALL PERFORMANCE:")
        print(f"Total Tests: {overall_stats['total_tests']}")
        print(f"Success Rate: {(overall_stats['successful_tests']/overall_stats['total_tests']*100):.1f}%")
        print(f"Avg Response Time: {overall_stats['avg_response_time']:.1f}s")
        print(f"Avg Quality Score: {overall_stats['avg_quality_score']:.1f}/10")
        
        # Recommendations
        print(f"\nRECOMMENDations:")
        if overall_stats["avg_response_time"] < 30:
            print("✅ Response times are acceptable for real-time chat")
        else:
            print("⚠️  Consider implementing streaming for better UX")
            
        if overall_stats["avg_quality_score"] > 7:
            print("✅ Response quality is good for production use")
        else:
            print("⚠️  Consider prompt engineering improvements")
            
        if (overall_stats["successful_tests"]/overall_stats["total_tests"]) > 0.9:
            print("✅ System reliability is excellent")
        else:
            print("⚠️  System reliability needs improvement")

if __name__ == "__main__":
    tester = ChatModesTester()
    asyncio.run(tester.run_all_tests())