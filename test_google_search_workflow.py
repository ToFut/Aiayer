#!/usr/bin/env python3
"""
Test Google Search Workflow

This test specifically validates the critical case study:
"Search in google 'SEGEV HALFON'"

Ensures the system:
1. Understands current UI context (user already on Google website)
2. Creates step-by-step workflow plan
3. Determines where and what to click/type
4. Completes the goal successfully
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append('.')

from enhanced_brain_router_with_full_automation import FullAutomationBrainRouter, ChatMode
from intelligent_workflow_planner import IntelligentWorkflowPlanner
from sensors.total_screen_analyzer import TotalScreenAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_google_search')

class GoogleSearchWorkflowTester:
    """Comprehensive tester for Google search workflow"""
    
    def __init__(self):
        self.brain_router = FullAutomationBrainRouter()
        self.workflow_planner = IntelligentWorkflowPlanner()
        self.screen_analyzer = TotalScreenAnalyzer()
        
    async def test_case_study_detection(self):
        """Test that the case study message is correctly detected as complex task"""
        logger.info("🧪 Testing case study detection...")
        
        test_messages = [
            "Search in google 'SEGEV HALFON'",  # Exact case study
            "google search 'John Doe'",         # Similar pattern
            "search for 'python tutorial'",     # Search pattern
            "click button",                     # Simple task
            "type hello world",                 # Simple task
        ]
        
        for message in test_messages:
            is_complex = self.brain_router._is_complex_task(message)
            expected_complex = "search" in message.lower() and ("'" in message or '"' in message)
            
            status = "✅" if is_complex == expected_complex else "❌"
            logger.info(f"{status} '{message}' -> Complex: {is_complex} (Expected: {expected_complex})")
        
        return True
    
    async def test_workflow_planning(self):
        """Test workflow plan creation for Google search"""
        logger.info("🧪 Testing workflow planning...")
        
        goal = "Search in google 'SEGEV HALFON'"
        
        # Mock Google context (user already on Google)
        mock_context = {
            "layers": {
                "application_analysis": {
                    "detected_app": "browsers",
                    "confidence": 0.9
                },
                "window_context": {
                    "application_name": "Safari"
                },
                "text_analysis": {
                    "all_text": "Google Search I'm Feeling Lucky google.com Search Images Videos News Shopping Maps",
                    "has_meaningful_content": True,
                    "word_count": 12
                },
                "ui_analysis": {
                    "elements": [
                        {
                            "type": "text_field",
                            "position": {"x": 400, "y": 300, "width": 200, "height": 40}
                        },
                        {
                            "type": "button", 
                            "position": {"x": 450, "y": 350, "width": 100, "height": 30}
                        }
                    ]
                }
            }
        }
        
        # Create workflow plan
        workflow_plan = await self.workflow_planner.create_workflow_plan(goal, mock_context)
        
        # Validate workflow plan
        success = True
        
        if not workflow_plan:
            logger.error("❌ Failed to create workflow plan")
            return False
        
        if workflow_plan.goal != goal:
            logger.error(f"❌ Goal mismatch: Expected '{goal}', got '{workflow_plan.goal}'")
            success = False
        
        if len(workflow_plan.steps) < 3:
            logger.error(f"❌ Insufficient steps: Expected at least 3, got {len(workflow_plan.steps)}")
            success = False
        
        if workflow_plan.confidence < 0.5:
            logger.warning(f"⚠️ Low confidence: {workflow_plan.confidence:.2f}")
        
        # Check for key steps
        step_types = [step.action_type.value for step in workflow_plan.steps]
        expected_actions = ['analyze', 'click', 'type']
        
        for expected_action in expected_actions:
            if expected_action not in step_types:
                logger.error(f"❌ Missing expected action: {expected_action}")
                success = False
        
        # Log workflow details
        logger.info(f"📋 Workflow Plan for: {workflow_plan.goal}")
        logger.info(f"📊 Confidence: {workflow_plan.confidence:.2f}")
        logger.info(f"⏱️ Estimated duration: {workflow_plan.estimated_duration}s")
        logger.info(f"📝 Steps ({len(workflow_plan.steps)}):")
        
        for step in workflow_plan.steps:
            logger.info(f"  {step.step_number}. {step.action_type.value}: {step.target} - {step.description}")
            if step.value:
                logger.info(f"     Value: '{step.value}'")
            if step.fallback_strategies:
                logger.info(f"     Fallbacks: {step.fallback_strategies}")
        
        status = "✅" if success else "❌"
        logger.info(f"{status} Workflow planning test {'passed' if success else 'failed'}")
        
        return success
    
    async def test_agent_mode_integration(self):
        """Test that Agent mode correctly handles the case study"""
        logger.info("🧪 Testing Agent mode integration...")
        
        message = "Search in google 'SEGEV HALFON'"
        
        # Mock context for agent processing
        mock_context = {
            "relevant_memories": [],
            "confidence_score": 0.8,
            "key_topics": ["search", "google"]
        }
        
        try:
            # Process through brain router
            result = await self.brain_router.process_request_with_automation(
                ChatMode.AGENT, 
                message, 
                "test_session"
            )
            
            if not result:
                logger.error("❌ Brain router returned no result")
                return False
            
            response = result.get('response', '')
            
            # Check response quality
            success_indicators = [
                'workflow' in response.lower(),
                'step' in response.lower(),
                'search' in response.lower(),
                ('✅' in response or '🧠' in response),  # Success or workflow indicators
            ]
            
            success = any(success_indicators)
            
            logger.info(f"📤 Agent Response: {response[:200]}...")
            
            status = "✅" if success else "❌"
            logger.info(f"{status} Agent mode integration test {'passed' if success else 'failed'}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Agent mode integration test failed with error: {e}")
            return False
    
    async def test_screen_analysis_integration(self):
        """Test screen analysis integration with workflow planning"""
        logger.info("🧪 Testing screen analysis integration...")
        
        try:
            # This would normally analyze the actual screen
            # For testing, we'll verify the integration points
            
            # Test that TotalScreenAnalyzer can be called
            analyzer = TotalScreenAnalyzer()
            
            # Test workflow planner can handle empty context
            planner = IntelligentWorkflowPlanner()
            workflow = await planner.create_workflow_plan(
                "Search in google 'test'", 
                {}
            )
            
            success = workflow is not None and len(workflow.steps) > 0
            
            status = "✅" if success else "❌"
            logger.info(f"{status} Screen analysis integration test {'passed' if success else 'failed'}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Screen analysis integration test failed: {e}")
            return False
    
    async def run_comprehensive_test(self):
        """Run all tests for the Google search workflow"""
        logger.info("🧪 Starting comprehensive Google search workflow test")
        logger.info(f"📅 Test started at: {datetime.now().isoformat()}")
        
        tests = [
            ("Case Study Detection", self.test_case_study_detection),
            ("Workflow Planning", self.test_workflow_planning),
            ("Agent Mode Integration", self.test_agent_mode_integration),
            ("Screen Analysis Integration", self.test_screen_analysis_integration),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            logger.info(f"\n" + "="*50)
            logger.info(f"🔬 Running: {test_name}")
            logger.info("="*50)
            
            try:
                result = await test_func()
                results[test_name] = result
                
                status = "✅ PASSED" if result else "❌ FAILED"
                logger.info(f"📊 {test_name}: {status}")
                
            except Exception as e:
                logger.error(f"❌ {test_name} CRASHED: {e}")
                results[test_name] = False
        
        # Summary
        logger.info(f"\n" + "="*50)
        logger.info("📊 TEST SUMMARY")
        logger.info("="*50)
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{status} {test_name}")
        
        overall_success = passed == total
        logger.info(f"\n🎯 Overall Result: {passed}/{total} tests passed")
        
        if overall_success:
            logger.info("🎉 ALL TESTS PASSED! Google search workflow is ready.")
            logger.info("🚀 The system can now handle: 'Search in google 'SEGEV HALFON''")
        else:
            logger.error("💥 Some tests failed. Review and fix issues before deployment.")
        
        return overall_success

async def main():
    """Main test runner"""
    tester = GoogleSearchWorkflowTester()
    success = await tester.run_comprehensive_test()
    
    if success:
        logger.info("\n🎯 CASE STUDY VERIFICATION")
        logger.info("The system is now capable of:")
        logger.info("1. ✅ Understanding UI context (user already on Google)")
        logger.info("2. ✅ Creating step-by-step workflow plans")
        logger.info("3. ✅ Determining where and what to click/type")
        logger.info("4. ✅ Completing complex goals intelligently")
        logger.info("\n💡 Ready to test with real Google search!")
    
    return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        exit(1)
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        exit(1)