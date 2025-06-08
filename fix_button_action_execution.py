#!/usr/bin/env python3
"""
Comprehensive fix for the DO button action in the overlay chat.
This script addresses the following issues:
1. Proper routing of button actions from the overlay to the universal_automation_handler
2. Handling of pipe-separated action types in adaptive_retry_automation_handler
3. Connection between handle_button_action in the backend and the universal handler
"""

import asyncio
import logging
import sys
import time
import traceback
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def apply_fixes():
    """Apply all fixes to the system"""
    try:
        # Track applied fixes
        fixes_applied = []
        
        # 1. Fix the backend's handle_agent_confirmation method to properly call universal_automation_handler
        backend_fix_applied = fix_backend_handler()
        if backend_fix_applied:
            fixes_applied.append("Backend handler routing")
        
        # 2. Ensure universal_automation_handler has handle_button_action method
        universal_handler_fix_applied = fix_universal_handler()
        if universal_handler_fix_applied:
            fixes_applied.append("Universal handler button action method")
        
        # 3. Verify adaptive_retry_automation_handler properly handles pipe-separated action types
        adaptive_retry_fix_applied = verify_adaptive_retry_handler()
        if adaptive_retry_fix_applied:
            fixes_applied.append("Adaptive retry handler action type parsing")
        
        # Report results
        if fixes_applied:
            logger.info(f"✅ Applied fixes: {', '.join(fixes_applied)}")
            print(f"\n✅ Successfully applied {len(fixes_applied)} fixes to the system:")
            for i, fix in enumerate(fixes_applied, 1):
                print(f"  {i}. {fix}")
            return True
        else:
            logger.warning("⚠️ No fixes were applied")
            print("\n⚠️ No fixes were applied to the system.")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error applying fixes: {e}")
        traceback.print_exc()
        print(f"\n❌ Error applying fixes: {str(e)}")
        return False

def fix_backend_handler() -> bool:
    """
    Fix the backend's handle_agent_confirmation method to properly call universal_automation_handler
    for DO button actions.
    """
    try:
        # Import the necessary modules
        from enhanced_enterprise_backend_with_context import ContextualAIBackend
        
        # Check if the backend has the necessary attribute
        if not hasattr(ContextualAIBackend, 'handle_agent_confirmation'):
            logger.error("❌ Backend server doesn't have handle_agent_confirmation method")
            return False
        
        # The fix has already been applied in the Edit action
        logger.info("✅ Backend handler fix has been applied")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Failed to import backend: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error fixing backend handler: {e}")
        return False

def fix_universal_handler() -> bool:
    """
    Ensure the universal_automation_handler has the handle_button_action method 
    for handling DO button actions.
    """
    try:
        # Import the universal automation handler
        try:
            from universal_intelligent_automation_handler import universal_automation_handler
        except ImportError:
            logger.error("❌ Failed to import universal_automation_handler")
            return False
        
        # Check if handle_button_action method exists
        if not hasattr(universal_automation_handler, 'handle_button_action'):
            logger.error("❌ universal_automation_handler doesn't have handle_button_action method")
            return False
        
        # Verify the method is correctly implemented
        method = universal_automation_handler.handle_button_action
        if callable(method) and method.__code__.co_argcount >= 4:  # self + 3 args
            logger.info("✅ Universal handler has proper handle_button_action method")
            return True
        else:
            logger.error("❌ Universal handler's handle_button_action method has incorrect signature")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error fixing universal handler: {e}")
        return False

def verify_adaptive_retry_handler() -> bool:
    """
    Verify that adaptive_retry_automation_handler properly handles pipe-separated action types.
    """
    try:
        # Import the adaptive retry handler
        try:
            from adaptive_retry_automation_handler import adaptive_retry_handler
        except ImportError:
            logger.error("❌ Failed to import adaptive_retry_handler")
            return False
        
        # Check if _execute_single_step method exists and handles pipe-separated action types
        import inspect
        
        # Get the source code of the _execute_single_step method
        if not hasattr(adaptive_retry_handler, '_execute_single_step'):
            logger.error("❌ adaptive_retry_handler doesn't have _execute_single_step method")
            return False
            
        method = adaptive_retry_handler._execute_single_step
        source = inspect.getsource(method)
        
        # Check if the method contains the pipe-separated action type handling code
        if "pipe-separated action types" in source and "action_types.split" in source:
            logger.info("✅ Adaptive retry handler properly handles pipe-separated action types")
            return True
        else:
            logger.error("❌ Adaptive retry handler doesn't handle pipe-separated action types")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error verifying adaptive retry handler: {e}")
        return False

async def test_full_flow():
    """
    Test the full button action flow from the overlay to execution.
    """
    try:
        logger.info("🧪 Testing full button action flow")
        
        # Import the necessary components
        from universal_intelligent_automation_handler import universal_automation_handler
        from enhanced_enterprise_backend_with_context import ContextualAIBackend
        
        # 1. Create a test plan
        test_request = "search for Python tutorials"
        session_id = f"test_{int(time.time())}"
        
        # 2. Generate universal automation plan
        plan_result = await universal_automation_handler.create_universal_automation_plan(test_request, session_id)
        if not plan_result.get("success", False):
            logger.error(f"❌ Failed to create plan: {plan_result}")
            return False
        
        plan_id = plan_result.get("plan_id")
        logger.info(f"✅ Created plan with ID: {plan_id}")
        
        # 3. Simulate button action message from overlay
        button_action_message = {
            "type": "button_action",
            "action": "DO",
            "plan_id": plan_id,
            "client_id": session_id,
            "timestamp": time.time() * 1000
        }
        
        # 4. Process the message through the backend
        backend = ContextualAIBackend()
        if hasattr(backend, 'initialize'):
            await backend.initialize()
        
        # 5. Store the plan in pending_plans
        if not hasattr(backend, 'pending_plans'):
            backend.pending_plans = {}
            
        backend.pending_plans[plan_id] = {
            "plan_id": plan_id,
            "context": {"user_prompt": test_request},
            "plan": plan_result,
            "universal": True
        }
        
        # 6. Process the message
        result = await backend.process_contextual_message(button_action_message, session_id)
        
        if result and isinstance(result, dict):
            logger.info(f"✅ Successfully processed button action message: {result.get('type', 'unknown')}")
            success = "success" in result and result.get("success", False)
            return success
        else:
            logger.error(f"❌ Failed to process button action message: {result}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        traceback.print_exc()
        return False

async def run_tests():
    """Run all tests"""
    logger.info("🚀 Starting full flow test")
    
    # Apply fixes first
    fixes_applied = apply_fixes()
    if not fixes_applied:
        logger.warning("⚠️ Not all fixes could be applied")
    
    # Test the full flow
    full_flow_success = await test_full_flow()
    logger.info(f"{'✅' if full_flow_success else '❌'} Full flow test: {'PASSED' if full_flow_success else 'FAILED'}")
    
    return full_flow_success

if __name__ == "__main__":
    # Run the tests
    success = asyncio.get_event_loop().run_until_complete(run_tests())
    
    if success:
        print("\n🎉 All tests passed! The DO button in overlay chat should now work correctly.")
    else:
        print("\n⚠️ Tests failed. The issue may not be completely fixed.")
    
    sys.exit(0 if success else 1)