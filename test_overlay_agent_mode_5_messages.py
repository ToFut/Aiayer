#!/usr/bin/env python3
"""
Comprehensive Overlay AgentMode Test
Test AgentMode from overlay perspective with 5 different messages.
Monitor the entire process including LLM integration, step generation, and responses.
"""

import asyncio
import json
import logging
import time
import websockets
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('overlay_agent_test')

class OverlayAgentModeTest:
    """Test AgentMode from overlay perspective with detailed process monitoring"""
    
    def __init__(self):
        self.backend_url = "ws://localhost:8767"
        self.test_results = []
        self.test_messages = [
            {
                "id": "test_1",
                "description": "Simple click automation",
                "message": "Click on the search button",
                "expected_complexity": "low"
            },
            {
                "id": "test_2", 
                "description": "Form filling automation",
                "message": "Fill out the contact form with name John Smith and email john@example.com",
                "expected_complexity": "medium"
            },
            {
                "id": "test_3",
                "description": "Multi-step navigation",
                "message": "Open YouTube and search for 'machine learning tutorial'",
                "expected_complexity": "high"
            },
            {
                "id": "test_4",
                "description": "E-commerce workflow",
                "message": "Add item to cart and proceed to checkout",
                "expected_complexity": "high"
            },
            {
                "id": "test_5",
                "description": "Settings configuration",
                "message": "Navigate to settings and enable dark mode",
                "expected_complexity": "medium"
            }
        ]
    
    async def test_backend_connection(self):
        """Test connection to the backend"""
        logger.info("🔗 Testing backend connection...")
        try:
            async with websockets.connect(self.backend_url) as websocket:
                logger.info("✅ Successfully connected to backend")
                return True
        except Exception as e:
            logger.error(f"❌ Backend connection failed: {e}")
            return False
    
    async def send_agent_request(self, test_case):
        """Send an agent request and monitor the complete process"""
        logger.info(f"\n🚀 Testing: {test_case['description']}")
        logger.info(f"📝 Message: {test_case['message']}")
        
        start_time = time.time()
        result = {
            "test_id": test_case["id"],
            "description": test_case["description"],
            "message": test_case["message"],
            "expected_complexity": test_case["expected_complexity"],
            "start_time": start_time,
            "success": False,
            "response_time": 0,
            "steps_generated": 0,
            "llm_used": False,
            "coordinates_provided": False,
            "error": None,
            "response_data": None
        }
        
        try:
            async with websockets.connect(self.backend_url) as websocket:
                # Send agent mode request
                request = {
                    "type": "chat_request",
                    "mode": "agent",
                    "message": test_case["message"]
                }
                
                logger.info(f"📤 Sending request: {json.dumps(request, indent=2)}")
                
                # First, handle the connection_established message
                connection_msg = await websocket.recv()
                connection_data = json.loads(connection_msg)
                logger.info(f"📡 Connection message: {connection_data.get('type', 'unknown')}")
                
                # Now send the actual request
                await websocket.send(json.dumps(request))
                
                # Wait for the actual response
                logger.info("⏳ Waiting for agent response...")
                response = await websocket.recv()
                
                end_time = time.time()
                response_time = end_time - start_time
                result["response_time"] = response_time
                
                logger.info(f"📥 Received response in {response_time:.2f}s")
                
                # Parse response
                try:
                    response_data = json.loads(response)
                    result["response_data"] = response_data
                    
                    logger.info(f"📊 Response type: {response_data.get('type', 'unknown')}")
                    logger.info(f"📊 Response success: {response_data.get('success', False)}")
                    
                    # Log full response for debugging
                    logger.info(f"📋 Full response keys: {list(response_data.keys())}")
                    
                    # Analyze response for AgentMode specifics
                    if response_data.get("success"):
                        result["success"] = True
                        
                        # Check for execution plan (both snake_case and camelCase)
                        plan = None
                        if "execution_plan" in response_data:
                            plan = response_data["execution_plan"]
                            logger.info("✅ Execution plan found in response (snake_case)")
                        elif "executionPlan" in response_data:
                            plan = response_data["executionPlan"]
                            logger.info("✅ Execution plan found in response (camelCase)")
                        
                        if plan:
                            # Count steps
                            if isinstance(plan, dict):
                                if "steps" in plan:
                                    if isinstance(plan["steps"], list):
                                        result["steps_generated"] = len(plan["steps"])
                                        logger.info(f"📋 Found {len(plan['steps'])} steps in execution plan")
                                    else:
                                        # Handle object with steps attribute
                                        steps = getattr(plan["steps"], '__len__', lambda: 0)()
                                        result["steps_generated"] = steps
                                elif hasattr(plan, 'steps'):
                                    result["steps_generated"] = len(getattr(plan, 'steps', []))
                                elif "total_steps" in plan:
                                    result["steps_generated"] = plan["total_steps"]
                                    logger.info(f"📋 Found total_steps: {plan['total_steps']}")
                            
                            # Check for coordinates
                            if "coordinates" in str(plan) or "x" in str(plan):
                                result["coordinates_provided"] = True
                                logger.info("✅ Coordinates found in plan")
                            
                            # Check for LLM usage
                            if response_data.get("llm_generated") or "llm" in str(plan).lower():
                                result["llm_used"] = True
                                logger.info("✅ LLM was used for step generation")
                        
                        # Log execution plan details
                        if plan:
                            logger.info(f"📋 Execution Plan Details:")
                            logger.info(f"   Steps: {result['steps_generated']}")
                            logger.info(f"   LLM Used: {result['llm_used']}")
                            logger.info(f"   Coordinates: {result['coordinates_provided']}")
                            
                            # Show first few steps
                            if isinstance(plan, dict) and "steps" in plan:
                                steps = plan["steps"]
                                if isinstance(steps, list) and len(steps) > 0:
                                    logger.info(f"   📝 First step: {steps[0] if len(steps) > 0 else 'None'}")
                                    if len(steps) > 1:
                                        logger.info(f"   📝 Second step: {steps[1]}")
                    else:
                        result["error"] = response_data.get("error", "Request failed")
                        logger.error(f"❌ Request failed: {result['error']}")
                
                except json.JSONDecodeError as e:
                    result["error"] = f"JSON decode error: {e}"
                    logger.error(f"❌ Failed to parse response: {e}")
                    logger.error(f"Raw response: {response}")
                
        except Exception as e:
            result["error"] = f"Connection error: {e}"
            logger.error(f"❌ Request failed: {e}")
        
        return result
    
    async def run_comprehensive_test(self):
        """Run comprehensive test with all 5 messages"""
        logger.info("🎯 Starting Comprehensive Overlay AgentMode Test")
        logger.info("=" * 80)
        logger.info(f"📊 Testing {len(self.test_messages)} different AgentMode scenarios")
        logger.info(f"🔗 Backend URL: {self.backend_url}")
        logger.info(f"⏰ Start Time: {datetime.now()}")
        
        # Test backend connection first
        if not await self.test_backend_connection():
            logger.error("💥 Cannot proceed - backend connection failed")
            return False
        
        # Run all test cases
        for i, test_case in enumerate(self.test_messages, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"🧪 TEST {i}/{len(self.test_messages)}: {test_case['id'].upper()}")
            logger.info(f"{'='*60}")
            
            result = await self.send_agent_request(test_case)
            self.test_results.append(result)
            
            # Wait between tests
            if i < len(self.test_messages):
                logger.info("⏳ Waiting 3s before next test...")
                await asyncio.sleep(3)
        
        # Analyze results
        await self.analyze_results()
    
    async def analyze_results(self):
        """Analyze and report test results"""
        logger.info("\n" + "="*80)
        logger.info("📊 COMPREHENSIVE TEST RESULTS ANALYSIS")
        logger.info("="*80)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r["success"])
        llm_usage_count = sum(1 for r in self.test_results if r["llm_used"])
        
        logger.info(f"📈 Overall Success Rate: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)")
        logger.info(f"🧠 LLM Usage Rate: {llm_usage_count}/{total_tests} ({llm_usage_count/total_tests*100:.1f}%)")
        
        # Response time analysis
        response_times = [r["response_time"] for r in self.test_results if r["success"]]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            logger.info(f"⚡ Average Response Time: {avg_response_time:.2f}s")
            logger.info(f"⚡ Response Time Range: {min(response_times):.2f}s - {max(response_times):.2f}s")
        
        # Step generation analysis
        steps_counts = [r["steps_generated"] for r in self.test_results if r["success"]]
        if steps_counts:
            avg_steps = sum(steps_counts) / len(steps_counts)
            logger.info(f"📋 Average Steps Generated: {avg_steps:.1f}")
            logger.info(f"📋 Steps Range: {min(steps_counts)} - {max(steps_counts)}")
        
        # Detailed test results
        logger.info(f"\n📋 DETAILED TEST RESULTS:")
        logger.info("-" * 80)
        
        for i, result in enumerate(self.test_results, 1):
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            llm_status = "🧠 LLM" if result["llm_used"] else "📋 Pattern"
            coord_status = "📍 Coords" if result["coordinates_provided"] else "❌ No Coords"
            
            logger.info(f"{i}. {result['test_id']} - {status}")
            logger.info(f"   📝 {result['description']}")
            logger.info(f"   ⏱️  {result['response_time']:.2f}s | 📋 {result['steps_generated']} steps | {llm_status} | {coord_status}")
            
            if result["error"]:
                logger.info(f"   ❌ Error: {result['error']}")
            
            logger.info("")
        
        # Final verdict
        logger.info("="*80)
        if successful_tests >= 4:  # At least 80% success rate
            logger.info("🎉 OVERLAY AGENTMODE TEST: SUCCESS!")
            logger.info("✨ AgentMode is working properly from overlay")
            if llm_usage_count >= 3:
                logger.info("🧠 LLM integration is working well")
            else:
                logger.info("📋 Using pattern-based fallback (LLM may be slow)")
        else:
            logger.error("💔 OVERLAY AGENTMODE TEST: NEEDS IMPROVEMENT")
        
        logger.info("="*80)
        return successful_tests >= 4

async def main():
    """Main test execution"""
    tester = OverlayAgentModeTest()
    success = await tester.run_comprehensive_test()
    
    if success:
        logger.info("\n🎊 SUCCESS: Overlay AgentMode testing completed successfully!")
    else:
        logger.error("\n💔 FAILURE: Overlay AgentMode testing needs improvements")

if __name__ == "__main__":
    asyncio.run(main())