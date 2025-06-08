#!/usr/bin/env python3
"""
Debug script to identify issues with plan IDs and execution flow.
This will help determine why the DO button isn't executing plans.
"""

import asyncio
import logging
import json
import sys
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_plan_creation_and_execution():
    """Test the plan creation and execution flow with DEBUG logging"""
    try:
        # Import necessary components
        try:
            from universal_intelligent_automation_handler import universal_automation_handler
        except ImportError:
            logger.error("Failed to import universal_automation_handler")
            return False

        # 1. Create a test automation plan
        test_request = "open Safari"
        session_id = f"debug_test"
        
        logger.info(f"Creating universal automation plan for: {test_request}")
        plan_result = await universal_automation_handler.create_universal_automation_plan(test_request, session_id)
        
        if not plan_result.get("success", False):
            logger.error(f"Failed to create plan: {plan_result}")
            return False
        
        # 2. Extract plan details for debugging
        plan_id = plan_result.get("plan_id")
        response = plan_result.get("response", "")
        buttons = plan_result.get("buttons", [])
        
        logger.info(f"✅ Plan created with ID: {plan_id}")
        logger.info(f"✅ Plan contains {len(buttons)} buttons")
        
        # 3. Check the active plans
        if not hasattr(universal_automation_handler, 'active_plans'):
            logger.error("Universal automation handler doesn't have active_plans attribute")
            return False
        
        active_plans = universal_automation_handler.active_plans
        logger.info(f"Active plans: {list(active_plans.keys())}")
        
        # 4. Verify if the plan is stored correctly
        if plan_id not in active_plans:
            logger.error(f"Plan ID {plan_id} not found in active_plans")
            return False
        
        logger.info(f"✅ Plan found in active_plans")
        
        # 5. Get the actual plan details
        plan = active_plans[plan_id]
        logger.info(f"Plan type: {type(plan).__name__}")
        logger.info(f"Plan title: {plan.title}")
        logger.info(f"Plan has {len(plan.steps)} steps")
        
        # 6. Now simulate button action execution (DO button)
        logger.info(f"Simulating DO button action for plan: {plan_id}")
        action_result = await universal_automation_handler.handle_button_action("execute_plan", plan_id, session_id)
        
        logger.info(f"Action result: {json.dumps(action_result, indent=2)[:500]}...")
        
        # 7. Check plan status after execution
        if plan_id not in active_plans:
            logger.info("✅ Plan was removed from active_plans after execution (expected)")
        else:
            logger.warning(f"⚠️ Plan still exists in active_plans after execution")
        
        return action_result.get("success", False)
        
    except Exception as e:
        logger.error(f"Debug test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

async def debug_backend_plan_handling():
    """Test how the backend handles plans"""
    try:
        # Import necessary components
        try:
            from enhanced_enterprise_backend_with_context import ContextualAIBackend
            from universal_intelligent_automation_handler import universal_automation_handler
        except ImportError as e:
            logger.error(f"Failed to import components: {e}")
            return False
        
        # 1. Create backend instance
        backend = ContextualAIBackend()
        
        # 2. Create test plan
        test_request = "open Safari"
        session_id = f"debug_backend_test"
        
        logger.info(f"Creating universal automation plan for: {test_request}")
        plan_result = await universal_automation_handler.create_universal_automation_plan(test_request, session_id)
        
        if not plan_result.get("success", False):
            logger.error(f"Failed to create plan: {plan_result}")
            return False
        
        # 3. Extract plan details
        plan_id = plan_result.get("plan_id")
        logger.info(f"✅ Plan created with ID: {plan_id}")
        
        # 4. Store the plan in backend's pending_plans
        if not hasattr(backend, 'pending_plans'):
            backend.pending_plans = {}
        
        # Store plan with universal_ prefix for testing
        backend.pending_plans[plan_id] = {
            "plan": plan_result,
            "context": {"user_prompt": test_request},
            "timestamp": 0,
            "client_id": "test_client",
            "plan_id": plan_id,
            "universal": True
        }
        
        logger.info(f"Stored plan in backend pending_plans: {plan_id}")
        logger.info(f"Backend pending_plans keys: {list(backend.pending_plans.keys())}")
        
        # 5. Create button action data
        button_action_data = {
            "type": "button_action",
            "action": "DO",
            "plan_id": plan_id,
            "client_id": "test_client",
            "timestamp": 0
        }
        
        # 6. Simulate button action execution through backend
        logger.info(f"Simulating button action through backend for plan: {plan_id}")
        
        # First check if the condition in handle_agent_confirmation would match
        if "universal_" in plan_id:
            logger.info(f"✅ Plan ID contains 'universal_' prefix: {plan_id}")
        else:
            logger.error(f"❌ Plan ID does NOT contain 'universal_' prefix: {plan_id}")
            # Try to fix the plan_id for testing
            fixed_plan_id = f"universal_{plan_id}"
            logger.info(f"Using fixed plan_id for testing: {fixed_plan_id}")
            # Update references
            backend.pending_plans[fixed_plan_id] = backend.pending_plans[plan_id]
            backend.pending_plans[fixed_plan_id]["plan_id"] = fixed_plan_id
            del backend.pending_plans[plan_id]
            button_action_data["plan_id"] = fixed_plan_id
            plan_id = fixed_plan_id
        
        # 7. Call handle_button_action directly
        try:
            action_result = await backend.handle_button_action(button_action_data, "test_client")
            logger.info(f"Button action result: {json.dumps(action_result, indent=2)[:500]}...")
        except Exception as e:
            logger.error(f"Error in handle_button_action: {e}")
            return False
        
        # 8. Call handle_agent_confirmation directly to debug the actual execution
        agent_confirmation_data = {
            "action": "DO",
            "sessionId": plan_id,
            "session_id": plan_id,
            "button_data": {},
            "timestamp": 0
        }
        
        try:
            logger.info(f"Calling handle_agent_confirmation directly for plan: {plan_id}")
            confirmation_result = await backend.handle_agent_confirmation(agent_confirmation_data, "test_client")
            logger.info(f"Agent confirmation result: {json.dumps(confirmation_result, indent=2)[:500]}...")
            
            return confirmation_result.get("type") == "agent_execution_success"
        except Exception as e:
            logger.error(f"Error in handle_agent_confirmation: {e}")
            return False
        
    except Exception as e:
        logger.error(f"Backend debug test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n🔍 Starting debug tests for plan IDs and execution flow...\n")
    
    # Run tests
    result1 = asyncio.get_event_loop().run_until_complete(debug_plan_creation_and_execution())
    print(f"\n{'✅' if result1 else '❌'} Direct universal handler test: {'PASSED' if result1 else 'FAILED'}\n")
    
    result2 = asyncio.get_event_loop().run_until_complete(debug_backend_plan_handling())
    print(f"\n{'✅' if result2 else '❌'} Backend plan handling test: {'PASSED' if result2 else 'FAILED'}\n")
    
    if result1 and result2:
        print("🎉 Both tests passed! The plan creation and execution flow is working correctly.")
        print("If the DO button still isn't working in the overlay, the issue may be with:")
        print("1. The button action message from the overlay not being sent correctly")
        print("2. The WebSocket connection between overlay and backend")
        print("3. The plan ID format in the button message not matching the expected format")
    else:
        print("⚠️ Tests failed. The plan execution flow has issues that need to be fixed.")
    
    sys.exit(0 if result1 and result2 else 1)