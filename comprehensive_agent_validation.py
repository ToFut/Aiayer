#!/usr/bin/env python3
"""
Comprehensive Agent Validation Test
Tests the complete AgentMode system with detailed plan analysis
"""

import asyncio
import websockets
import json
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('agent_validation')

class ComprehensiveAgentValidator:
    def __init__(self):
        self.backend_url = "ws://localhost:8767"
        self.test_scenarios = [
            {
                "id": "simple_search",
                "name": "Simple Search Task",
                "message": "Search for 'machine learning' on Google",
                "expected_keywords": ["search", "google", "type", "click"]
            },
            {
                "id": "calculator_task", 
                "name": "Calculator Operation",
                "message": "Open calculator and calculate 15 * 23",
                "expected_keywords": ["calculator", "click", "multiply", "number"]
            },
            {
                "id": "file_task",
                "name": "File Management",
                "message": "Create a new text file and save it as 'test.txt'",
                "expected_keywords": ["create", "file", "save", "text"]
            },
            {
                "id": "settings_task",
                "name": "System Settings",
                "message": "Open system preferences and check Wi-Fi settings",
                "expected_keywords": ["settings", "preferences", "wifi", "open"]
            },
            {
                "id": "complex_workflow",
                "name": "Complex Multi-Step Workflow",
                "message": "Open a new document, type 'Hello World', format it as bold, and save the file",
                "expected_keywords": ["document", "type", "bold", "format", "save"]
            }
        ]
        self.results = []

    async def connect_to_backend(self):
        """Connect to the backend WebSocket"""
        try:
            websocket = await websockets.connect(self.backend_url)
            logger.info(f"✅ Connected to backend at {self.backend_url}")
            return websocket
        except Exception as e:
            logger.error(f"❌ Failed to connect to backend: {e}")
            return None

    async def send_agent_request(self, websocket, message: str):
        """Send an agent mode request and get response"""
        request = {
            "type": "chat_request",
            "data": {
                "message": message,
                "mode": "agent",
                "timestamp": str(int(time.time() * 1000))
            }
        }
        
        logger.info(f"📤 Sending request: {message}")
        await websocket.send(json.dumps(request))
        
        # Wait for response
        response_text = await websocket.recv()
        response = json.loads(response_text)
        
        logger.info(f"📥 Received response in {response.get('processing_time', 'unknown')}s")
        return response

    def analyze_plan_quality(self, response: dict, expected_keywords: list) -> dict:
        """Analyze the quality of the generated execution plan"""
        analysis = {
            "has_execution_plan": False,
            "has_steps": False,
            "step_count": 0,
            "has_coordinates": False,
            "has_keywords": False,
            "keyword_matches": [],
            "plan_quality": "unknown",
            "details": {}
        }
        
        try:
            # Check if response has execution plan
            if "execution_plan" in response:
                analysis["has_execution_plan"] = True
                plan = response["execution_plan"]
                analysis["details"]["execution_plan"] = plan
                
                # Check for steps
                if "steps" in plan and isinstance(plan["steps"], list):
                    analysis["has_steps"] = True
                    analysis["step_count"] = len(plan["steps"])
                    
                    # Analyze steps for keywords
                    plan_text = json.dumps(plan).lower()
                    for keyword in expected_keywords:
                        if keyword.lower() in plan_text:
                            analysis["keyword_matches"].append(keyword)
                    
                    analysis["has_keywords"] = len(analysis["keyword_matches"]) > 0
                
                # Check for coordinates
                if "coordinates" in plan:
                    analysis["has_coordinates"] = True
                    analysis["details"]["coordinates"] = plan["coordinates"]
                
                # Determine overall quality
                if analysis["step_count"] >= 3 and analysis["has_keywords"] and analysis["has_coordinates"]:
                    analysis["plan_quality"] = "excellent"
                elif analysis["step_count"] >= 2 and analysis["has_keywords"]:
                    analysis["plan_quality"] = "good"
                elif analysis["has_steps"]:
                    analysis["plan_quality"] = "basic"
                else:
                    analysis["plan_quality"] = "poor"
            
            # Check response content
            if "response" in response:
                analysis["details"]["response"] = response["response"]
                
        except Exception as e:
            logger.error(f"Error analyzing plan: {e}")
            analysis["details"]["error"] = str(e)
            
        return analysis

    async def run_validation_test(self):
        """Run comprehensive validation tests"""
        logger.info("🚀 Starting Comprehensive Agent Validation")
        logger.info("=" * 80)
        
        start_time = datetime.now()
        websocket = await self.connect_to_backend()
        
        if not websocket:
            logger.error("❌ Cannot proceed without backend connection")
            return
        
        try:
            for i, scenario in enumerate(self.test_scenarios, 1):
                logger.info(f"\n🧪 TEST {i}/{len(self.test_scenarios)}: {scenario['name']}")
                logger.info("-" * 60)
                
                test_start = time.time()
                
                # Send request
                response = await self.send_agent_request(websocket, scenario["message"])
                
                test_duration = time.time() - test_start
                
                # Analyze response
                analysis = self.analyze_plan_quality(response, scenario["expected_keywords"])
                
                # Store results
                result = {
                    "scenario": scenario,
                    "response": response,
                    "analysis": analysis,
                    "duration": test_duration,
                    "success": analysis["has_execution_plan"] and analysis["has_steps"]
                }
                self.results.append(result)
                
                # Log results
                logger.info(f"⏱️  Duration: {test_duration:.2f}s")
                logger.info(f"📋 Steps: {analysis['step_count']}")
                logger.info(f"🎯 Keywords: {analysis['keyword_matches']}")
                logger.info(f"📍 Coordinates: {analysis['has_coordinates']}")
                logger.info(f"⭐ Quality: {analysis['plan_quality']}")
                logger.info(f"✅ Success: {result['success']}")
                
                # Debug: Show actual response for troubleshooting
                logger.info(f"🔍 Response keys: {list(response.keys())}")
                if "response" in response:
                    logger.info(f"📄 Response text (first 200 chars): {str(response['response'])[:200]}...")
                
                # Wait between tests
                if i < len(self.test_scenarios):
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(f"Error during validation: {e}")
        finally:
            await websocket.close()
            
        # Generate final report
        self.generate_final_report(start_time)

    def generate_final_report(self, start_time: datetime):
        """Generate comprehensive final report"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 COMPREHENSIVE AGENT VALIDATION REPORT")
        logger.info("=" * 80)
        
        # Calculate statistics
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r["success"])
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        
        total_duration = (datetime.now() - start_time).total_seconds()
        avg_response_time = sum(r["duration"] for r in self.results) / total_tests if total_tests > 0 else 0
        
        total_steps = sum(r["analysis"]["step_count"] for r in self.results)
        avg_steps = total_steps / total_tests if total_tests > 0 else 0
        
        # Quality distribution
        quality_dist = {}
        for result in self.results:
            quality = result["analysis"]["plan_quality"]
            quality_dist[quality] = quality_dist.get(quality, 0) + 1
        
        # Report statistics
        logger.info(f"📈 Success Rate: {successful_tests}/{total_tests} ({success_rate:.1f}%)")
        logger.info(f"⏱️  Total Duration: {total_duration:.2f}s")
        logger.info(f"⚡ Average Response Time: {avg_response_time:.2f}s")
        logger.info(f"📋 Average Steps Generated: {avg_steps:.1f}")
        
        logger.info(f"\n🎯 Plan Quality Distribution:")
        for quality, count in quality_dist.items():
            percentage = (count / total_tests) * 100
            logger.info(f"   {quality}: {count} ({percentage:.1f}%)")
        
        # Detailed results
        logger.info(f"\n📋 DETAILED TEST RESULTS:")
        logger.info("-" * 80)
        
        for i, result in enumerate(self.results, 1):
            scenario = result["scenario"]
            analysis = result["analysis"]
            
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            logger.info(f"{i}. {scenario['name']} - {status}")
            logger.info(f"   📝 {scenario['message']}")
            logger.info(f"   ⏱️ {result['duration']:.2f}s | 📋 {analysis['step_count']} steps | {analysis['plan_quality']} quality")
            
            if analysis["keyword_matches"]:
                logger.info(f"   🎯 Keywords: {', '.join(analysis['keyword_matches'])}")
            
            if analysis["has_coordinates"]:
                coords = analysis["details"].get("coordinates", {})
                logger.info(f"   📍 Coordinates: ({coords.get('x', 'N/A')}, {coords.get('y', 'N/A')})")
            
            logger.info("")
        
        # Final assessment
        logger.info("=" * 80)
        if success_rate >= 90:
            logger.info("🎉 VALIDATION: EXCELLENT! AgentMode is production-ready")
        elif success_rate >= 75:
            logger.info("✅ VALIDATION: GOOD! AgentMode is mostly functional")
        elif success_rate >= 50:
            logger.info("⚠️ VALIDATION: FAIR! AgentMode needs improvements")
        else:
            logger.info("❌ VALIDATION: POOR! AgentMode needs major fixes")
        
        logger.info(f"🤖 System demonstrates {success_rate:.1f}% reliability for agent automation")
        logger.info("=" * 80)

async def main():
    """Main function to run comprehensive agent validation"""
    validator = ComprehensiveAgentValidator()
    await validator.run_validation_test()

if __name__ == "__main__":
    asyncio.run(main())