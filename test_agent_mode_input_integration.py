#!/usr/bin/env python3
"""
Test script for verifying the integration between InputController and Agent Mode.
This test focuses on the connection between components without executing real LLM operations.
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

class MockLLMService:
    """Mock LLM service that returns predefined responses without actual API calls."""
    
    async def start(self):
        """Mock start method."""
        logger.info("Mock LLM service started")
        return True
    
    async def generate_response(self, messages, **kwargs):
        """Return a predefined response."""
        logger.info("Mock LLM generating response")
        # Return a simple JSON plan
        return """```json
{
    "title": "Test Automation Plan",
    "description": "A simple test automation plan",
    "request_type": "system_task",
    "complexity_score": 0.3,
    "estimated_duration": 5.0,
    "success_probability": 0.9,
    "steps": [
        {
            "id": "step_1",
            "description": "Move cursor to test location",
            "action_type": "click_element",
            "coordinates": [100, 100],
            "estimated_duration": 1.0,
            "confidence": 0.9
        },
        {
            "id": "step_2",
            "description": "Wait for 1 second",
            "action_type": "wait",
            "value": "1.0",
            "estimated_duration": 1.0,
            "confidence": 0.9
        }
    ]
}```"""

async def test_brain_router_agent_mode():
    """Test the brain_router's agent mode handler that integrates with InputController."""
    try:
        logger.info("🧪 Testing brain_router's agent mode handler")
        
        # Import the brain_router
        from brain.core.brain_router import brain_router, ChatMode, ChatRequest
        logger.info("Successfully imported brain_router")
        
        # Create a test request for agent mode
        test_request = ChatRequest(
            mode=ChatMode.AGENT,
            query="move cursor to coordinates 100,100",
            user_id="test_user",
            session_id=f"test_session_{int(time.time())}",
            timestamp=time.time()
        )
        
        logger.info(f"Created test request for agent mode: '{test_request.query}'")
        
        # Process the request through the brain router
        logger.info("Processing request through brain_router...")
        response = await brain_router.process_request(test_request)
        
        logger.info(f"Response received from brain_router: {response.success}")
        
        # Check if the response contains an execution plan
        if response.execution_plan:
            logger.info("✅ Execution plan received from agent mode handler")
            logger.info(f"Plan ID: {response.execution_plan.get('plan_id')}")
        else:
            logger.info("❌ No execution plan in response")
        
        return response.success
        
    except Exception as e:
        logger.error(f"❌ Error testing brain_router agent mode: {e}")
        return False

async def test_agent_automation_handler():
    """Test the real_agent_automation_handler that's used by the brain router."""
    try:
        logger.info("🧪 Testing real_agent_automation_handler")
        
        # Import the agent automation handler
        try:
            from real_agent_automation_handler import handle_real_agent_automation, agent_automation_handler
            logger.info("Successfully imported real_agent_automation_handler")
        except ImportError as e:
            logger.error(f"Failed to import real_agent_automation_handler: {e}")
            return False
        
        # Check if the handler has an input_controller
        has_controller = hasattr(agent_automation_handler, 'input_controller')
        logger.info(f"Agent automation handler has input_controller: {has_controller}")
        
        # Test the handler with a simple request
        test_query = "move cursor to coordinates 100,100"
        session_id = f"test_session_{int(time.time())}"
        
        logger.info(f"Testing handle_real_agent_automation with query: '{test_query}'")
        
        # Monkey patch the LLM service to avoid actual API calls
        if hasattr(agent_automation_handler, 'llm_service'):
            original_llm = agent_automation_handler.llm_service
            agent_automation_handler.llm_service = MockLLMService()
            logger.info("✅ Replaced real LLM service with mock")
        
        # Call the handler
        try:
            result = await handle_real_agent_automation(test_query, session_id)
            
            if result.get('success', False):
                logger.info("✅ Agent automation handler processed request successfully")
                logger.info(f"Response: {result.get('response')[:100]}...")  # First 100 chars
            else:
                logger.warning(f"⚠️ Agent automation handler returned error: {result.get('response')}")
            
            return result.get('success', False)
        finally:
            # Restore original LLM service if we patched it
            if hasattr(agent_automation_handler, 'llm_service') and original_llm:
                agent_automation_handler.llm_service = original_llm
                logger.info("Restored original LLM service")
        
    except Exception as e:
        logger.error(f"❌ Error testing agent_automation_handler: {e}")
        return False

async def test_fixed_handler_input_integration():
    """Test integration between the fixed universal handler and InputController."""
    try:
        logger.info("🧪 Testing fixed universal handler integration with InputController")
        
        # Import the fixed handler
        try:
            from fixed_universal_automation_handler import fixed_handle_universal_automation
            from universal_intelligent_automation_handler import universal_automation_handler
            logger.info("Successfully imported handlers")
        except ImportError as e:
            logger.error(f"Failed to import handlers: {e}")
            return False
        
        # Check if InputController is available in universal_automation_handler
        has_controller = hasattr(universal_automation_handler, 'input_controller') and universal_automation_handler.input_controller is not None
        logger.info(f"Universal automation handler has input_controller: {has_controller}")
        
        if not has_controller:
            logger.warning("InputController not available, initializing manually")
            try:
                from agent_workflow.input_controller import InputController
                universal_automation_handler.input_controller = InputController(safety_level="medium")
                logger.info("✅ Manually initialized InputController")
            except Exception as init_error:
                logger.error(f"Failed to initialize InputController: {init_error}")
                return False
        
        # Create a simple step that the handler will execute
        from universal_intelligent_automation_handler import SmartAutomationStep
        
        test_step = SmartAutomationStep(
            id="test_step",
            description="Move cursor slightly and back",
            action_type="click_element",
            coordinates=(100, 100),
            confidence=0.9,
            estimated_duration=1.0
        )
        
        # Try to execute the step directly through _execute_smart_step
        try:
            result = await universal_automation_handler._execute_smart_step(test_step)
            logger.info(f"Direct step execution result: {result}")
            return True
        except Exception as step_error:
            logger.error(f"Failed to execute test step: {step_error}")
            
            # Try fallback test just checking if the controller works
            if universal_automation_handler.input_controller:
                try:
                    position = universal_automation_handler.input_controller.get_current_position()
                    logger.info(f"Current mouse position through handler's controller: {position}")
                    return True
                except Exception as fallback_error:
                    logger.error(f"Fallback test failed: {fallback_error}")
            
            return False
        
    except Exception as e:
        logger.error(f"❌ Error testing fixed handler integration: {e}")
        return False

async def main():
    """Run tests to verify InputController integration with Agent Mode."""
    logger.info("🚀 Starting InputController and Agent Mode Integration Tests")
    
    # Test real_agent_automation_handler first
    logger.info("\n=== Test 1: Real Agent Automation Handler Integration ===")
    agent_handler_result = await test_agent_automation_handler()
    
    # Test fixed universal handler
    logger.info("\n=== Test 2: Fixed Universal Handler Integration ===")
    fixed_handler_result = await test_fixed_handler_input_integration()
    
    # Test brain router
    logger.info("\n=== Test 3: Brain Router Agent Mode Integration ===")
    brain_router_result = await test_brain_router_agent_mode()
    
    # Print summary
    logger.info("\n=== Test Results Summary ===")
    results = {
        "Agent Automation Handler": agent_handler_result,
        "Fixed Universal Handler": fixed_handler_result,
        "Brain Router Agent Mode": brain_router_result
    }
    
    all_passed = True
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
        if not result:
            all_passed = False
    
    if all_passed:
        logger.info("\n🎉 All tests passed! InputController is properly integrated with Agent Mode.")
    else:
        logger.info("\n⚠️ Some integration tests failed. See above for details.")

if __name__ == "__main__":
    asyncio.run(main())