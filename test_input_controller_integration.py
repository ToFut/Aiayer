#!/usr/bin/env python3
"""
Test script to verify InputController functionality and its integration with agent mode.
Tests both direct InputController methods and the integration with universal automation handler.
"""

import asyncio
import time
import logging
import sys
from typing import Dict, Any
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add parent directory to path to import from project root
project_root = Path(__file__).parent
sys.path.append(str(project_root))

async def test_direct_input_controller():
    """Test InputController directly to verify it works."""
    try:
        from agent_workflow.input_controller import InputController
        
        logger.info("🧪 Testing direct InputController functionality")
        
        # Create InputController with medium safety level
        controller = InputController(safety_level="medium")
        
        # Test getting current position
        position = controller.get_current_position()
        logger.info(f"Current position: {position}")
        
        # Test moving to a position near the current one (safer)
        current_x, current_y = position
        target_x = min(current_x + 100, controller.screen_width - 100)
        target_y = min(current_y + 100, controller.screen_height - 100)
        
        logger.info(f"Moving to position: ({target_x}, {target_y})")
        result = controller.move_to(target_x, target_y, duration=1.0)
        logger.info(f"Move result: {result}")
        
        # Test running an action sequence
        logger.info("Testing action sequence execution")
        actions = [
            {"action": "wait", "duration": 1.0},
            {"action": "move", "x": current_x, "y": current_y, "duration": 1.0}
        ]
        
        sequence_result = controller.execute_action_sequence(actions)
        logger.info(f"Action sequence result: {sequence_result}")
        
        # Cleanup
        controller.stop()
        logger.info("✅ Direct InputController test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing InputController: {e}")
        return False

async def test_integration_with_automation_handler():
    """Test integration with universal automation handler."""
    try:
        logger.info("🧪 Testing integration with universal automation handler")
        
        # First, try to import the universal automation handler
        try:
            from universal_intelligent_automation_handler import universal_automation_handler
            logger.info("Successfully imported universal_automation_handler")
        except ImportError as e:
            logger.error(f"Failed to import universal_automation_handler: {e}")
            return False
        
        # Verify that the automation handler has an InputController instance
        if not universal_automation_handler.input_controller:
            logger.warning("InputController not found in universal_automation_handler, will initialize")
            # Try to initialize
            from agent_workflow.input_controller import InputController
            universal_automation_handler.input_controller = InputController(safety_level="medium")
        
        logger.info("Creating a test plan for universal automation handler")
        
        # Create a simple test plan that doesn't do anything destructive
        from universal_intelligent_automation_handler import SmartAutomationStep, UniversalAutomationPlan
        
        test_plan = UniversalAutomationPlan(
            task_id=f"test_plan_{int(time.time())}",
            title="Test InputController Integration",
            description="A simple test plan to verify InputController integration",
            request_type="system_task",
            steps=[
                SmartAutomationStep(
                    id="step_1",
                    description="Wait for 1 second",
                    action_type="wait",
                    value="1.0",
                    estimated_duration=1.0,
                    confidence=0.9
                ),
                SmartAutomationStep(
                    id="step_2",
                    description="Move mouse slightly",
                    action_type="click_element",
                    coordinates=(100, 100),
                    estimated_duration=1.0,
                    confidence=0.9
                ),
                SmartAutomationStep(
                    id="step_3",
                    description="Wait for 1 second",
                    action_type="wait",
                    value="1.0",
                    estimated_duration=1.0,
                    confidence=0.9
                )
            ],
            estimated_duration=3.0,
            complexity_score=0.2,
            success_probability=0.9
        )
        
        # Store the test plan in the handler
        universal_automation_handler.active_plans[test_plan.task_id] = test_plan
        
        # Test executing the plan
        logger.info(f"Executing test plan with ID: {test_plan.task_id}")
        result = await universal_automation_handler._execute_universal_plan(test_plan, "test_session")
        
        if result.get("success", False):
            logger.info(f"✅ Plan execution successful: {result.get('success_rate', 0):.0%} steps completed")
            logger.info(f"Execution response: {result.get('response')[:100]}...")  # Show first 100 chars
        else:
            logger.error(f"❌ Plan execution failed: {result.get('response')}")
        
        return result.get("success", False)
        
    except Exception as e:
        logger.error(f"❌ Error testing integration with automation handler: {e}")
        return False

async def test_fixed_universal_automation():
    """Test the fixed universal automation handler."""
    try:
        logger.info("🧪 Testing fixed universal automation handler")
        
        try:
            from fixed_universal_automation_handler import fixed_handle_universal_automation
            logger.info("Successfully imported fixed_handle_universal_automation")
        except ImportError as e:
            logger.error(f"Failed to import fixed_handle_universal_automation: {e}")
            return False
        
        # Test creating a plan with the fixed handler
        test_request = "search for the weather"
        session_id = f"test_session_{int(time.time())}"
        
        logger.info(f"Creating a plan for request: '{test_request}'")
        result = await fixed_handle_universal_automation(test_request, session_id)
        
        if result.get("success", False):
            logger.info(f"✅ Plan creation successful")
            logger.info(f"Plan ID: {result.get('plan_id')}")
            logger.info(f"Automation available: {result.get('automation_available', False)}")
        else:
            logger.error(f"❌ Plan creation failed: {result.get('response')}")
        
        return result.get("success", False)
        
    except Exception as e:
        logger.error(f"❌ Error testing fixed universal automation: {e}")
        return False

async def test_llm_integration():
    """Test LLM integration to verify timeout issues are fixed."""
    try:
        logger.info("🧪 Testing LLM integration")
        
        # Import OllamaLLM
        try:
            from llm.model import OllamaLLM
            logger.info("Successfully imported OllamaLLM")
        except ImportError as e:
            logger.error(f"Failed to import OllamaLLM: {e}")
            return False
        
        # Create LLM instance
        llm = OllamaLLM(model_name="llama3.2:1b")
        logger.info(f"Created LLM instance with model: {llm.model_name}")
        logger.info(f"Configured timeout: {llm.timeout} seconds")
        
        # Start the LLM
        start_success = await llm.start()
        if not start_success:
            logger.error("Failed to start LLM")
            return False
        
        logger.info("LLM started successfully")
        
        # Test generating a simple response
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello world"}
        ]
        
        logger.info("Generating test response...")
        start_time = time.time()
        response = await llm.generate_response(messages)
        end_time = time.time()
        
        logger.info(f"Response generated in {end_time - start_time:.2f} seconds")
        logger.info(f"Response preview: {response[:50]}...")  # Show first 50 chars
        
        # Cleanup
        await llm.stop()
        logger.info("LLM stopped")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing LLM integration: {e}")
        return False

async def main():
    """Run all tests sequentially."""
    logger.info("🚀 Starting InputController Integration Tests")
    
    # Store test results
    results = {}
    
    # Test direct InputController functionality
    logger.info("\n=== Test 1: Direct InputController Functionality ===")
    results["direct_input_controller"] = await test_direct_input_controller()
    
    # Test integration with universal automation handler
    logger.info("\n=== Test 2: Integration with Universal Automation Handler ===")
    results["universal_automation_integration"] = await test_integration_with_automation_handler()
    
    # Test fixed universal automation handler
    logger.info("\n=== Test 3: Fixed Universal Automation Handler ===")
    results["fixed_universal_automation"] = await test_fixed_universal_automation()
    
    # Test LLM integration
    logger.info("\n=== Test 4: LLM Integration ===")
    results["llm_integration"] = await test_llm_integration()
    
    # Print summary
    logger.info("\n=== Test Results Summary ===")
    all_passed = True
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
        if not result:
            all_passed = False
    
    if all_passed:
        logger.info("\n🎉 All tests passed! InputController and integrations are working correctly.")
    else:
        logger.info("\n⚠️ Some tests failed. See above for details.")

if __name__ == "__main__":
    asyncio.run(main())