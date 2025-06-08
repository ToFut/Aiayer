#!/usr/bin/env python3
"""
Test script to verify the fix for the Universal Automation Handler button action execution.
This script simulates clicking the DO button in the overlay and verifies the execution flow.
"""

import asyncio
import json
import logging
import sys
import traceback
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import the necessary components
try:
    from universal_intelligent_automation_handler import universal_automation_handler, UniversalAutomationPlan
    from enhanced_enterprise_backend_with_context import ContextualAIBackend
except ImportError as e:
    logger.error(f"Failed to import required components: {e}")
    sys.exit(1)

async def test_universal_button_action():
    """Test universal button action execution flow"""
    logger.info("🧪 Starting universal button action test")
    
    try:
        # 1. Create test plan
        test_request = "search for Python tutorials"
        session_id = f"test_{int(asyncio.get_event_loop().time())}"
        
        # 2. Generate universal automation plan
        logger.info(f"🧠 Creating universal automation plan for: {test_request}")
        plan_result = await universal_automation_handler.create_universal_automation_plan(test_request, session_id)
        
        if not plan_result.get("success", False):
            logger.error(f"❌ Failed to create plan: {plan_result}")
            return False
        
        plan_id = plan_result.get("plan_id")
        logger.info(f"✅ Created plan with ID: {plan_id}")
        
        # 3. Simulate button action
        button_action_data = {
            "type": "button_action",
            "action": "DO",  # This should be mapped to execute_plan
            "plan_id": plan_id,
            "client_id": session_id,
            "timestamp": asyncio.get_event_loop().time() * 1000
        }
        
        # 4. Create a mock backend server instance
        backend = ContextualAIBackend()
        
        # 5. Initialize the backend (minimally)
        if hasattr(backend, 'initialize'):
            await backend.initialize()
        
        # 6. Store the plan in pending_plans
        if not hasattr(backend, 'pending_plans'):
            backend.pending_plans = {}
        
        backend.pending_plans[plan_id] = {
            "plan_id": plan_id,
            "context": {"user_prompt": test_request},
            "plan": plan_result,
            "universal": True  # Mark this as a universal plan
        }
        
        # 7. Send the button action directly to handle_button_action
        logger.info(f"🔘 Sending button action: {button_action_data['action']} for plan: {plan_id}")
        result = await backend.handle_button_action(button_action_data, session_id)
        
        # 8. Check if the result indicates successful handling
        if result and isinstance(result, dict):
            logger.info(f"✅ Button action result: {json.dumps(result, indent=2)[:500]}...")
            return "success" in result and result.get("success", False)
        else:
            logger.error(f"❌ Invalid result type: {type(result)}")
            return False
    
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        traceback.print_exc()
        return False

async def test_direct_universal_handler():
    """Test direct universal handler button action"""
    logger.info("🧪 Starting direct universal handler test")
    
    try:
        # 1. Create test plan
        test_request = "search for Python tutorials"
        session_id = f"test_direct_{int(asyncio.get_event_loop().time())}"
        
        # 2. Generate universal automation plan
        logger.info(f"🧠 Creating universal automation plan for: {test_request}")
        plan_result = await universal_automation_handler.create_universal_automation_plan(test_request, session_id)
        
        if not plan_result.get("success", False):
            logger.error(f"❌ Failed to create plan: {plan_result}")
            return False
        
        plan_id = plan_result.get("plan_id")
        logger.info(f"✅ Created plan with ID: {plan_id}")
        
        # 3. Call handle_button_action directly on the universal_automation_handler
        logger.info(f"🔘 Directly calling handle_button_action on universal_automation_handler")
        action_result = await universal_automation_handler.handle_button_action("execute_plan", plan_id, session_id)
        
        logger.info(f"✅ Direct action result: {json.dumps(action_result, indent=2)[:500]}...")
        return True
        
    except Exception as e:
        logger.error(f"❌ Direct test failed with exception: {e}")
        traceback.print_exc()
        return False

async def run_tests():
    """Run all tests"""
    logger.info("🚀 Starting Universal Button Action Fix tests")
    
    # Test 1: Check if universal_automation_handler can handle button actions directly
    direct_test_success = await test_direct_universal_handler()
    logger.info(f"{'✅' if direct_test_success else '❌'} Direct universal handler test: {'PASSED' if direct_test_success else 'FAILED'}")
    
    # Test 2: Check if button actions are properly routed through the backend
    integration_test_success = await test_universal_button_action()
    logger.info(f"{'✅' if integration_test_success else '❌'} Backend integration test: {'PASSED' if integration_test_success else 'FAILED'}")
    
    if direct_test_success and integration_test_success:
        logger.info("🎉 All tests passed! The fix is working correctly.")
        return True
    else:
        logger.error("⚠️ Some tests failed. The fix may not be complete.")
        return False

if __name__ == "__main__":
    # Run the tests
    success = asyncio.get_event_loop().run_until_complete(run_tests())
    sys.exit(0 if success else 1)