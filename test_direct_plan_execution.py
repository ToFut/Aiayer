#!/usr/bin/env python3
"""
Test direct plan execution through universal_automation_handler
"""
import os
import sys
import json
import asyncio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/test_direct_plan_execution.log')
    ]
)
logger = logging.getLogger('test_direct_plan_execution')

# Try to import the universal automation handler
try:
    from universal_intelligent_automation_handler import universal_automation_handler
    HANDLER_AVAILABLE = True
    logger.info("✅ Universal automation handler loaded successfully")
except ImportError as e:
    logger.error(f"❌ Universal automation handler not available: {e}")
    HANDLER_AVAILABLE = False
    universal_automation_handler = None

async def test_direct_execution():
    """Test direct plan execution"""
    if not HANDLER_AVAILABLE:
        logger.error("Universal automation handler not available, cannot proceed with test")
        return False
    
    # Prepare a test plan
    plan_id = f"test_plan_{int(datetime.now().timestamp())}"
    test_plan = {
        "task_id": plan_id,
        "title": "Test Task",
        "description": "Test task for direct execution",
        "steps": [
            {
                "id": "step_1",
                "description": "First step",
                "action_type": "wait",
                "target": None,
                "value": None,
                "coordinates": None,
                "status": "pending",
                "estimated_duration": 1
            }
        ],
        "estimated_duration": 1,
        "requires_approval": False,
        "status": "approved"
    }
    
    # Add plan to handler
    logger.info(f"Adding test plan {plan_id} to active plans")
    universal_automation_handler.active_plans[plan_id] = test_plan
    
    # Execute plan
    logger.info(f"Executing test plan {plan_id}")
    
    # Debug the handler object
    logger.info(f"Handler object has attributes: {dir(universal_automation_handler)}")
    
    try:
        # Try direct execution
        result = await universal_automation_handler.handle_button_action('execute_plan', plan_id, plan_id)
        logger.info(f"Execution result: {result}")
        return result.get('success', False)
    except AttributeError as e:
        logger.error(f"AttributeError: {e}")
        logger.info("Trying alternative execution methods...")
        
        # Try execute method if available
        if hasattr(universal_automation_handler, 'execute_plan'):
            logger.info("Using execute_plan method")
            result = await universal_automation_handler.execute_plan(plan_id)
            logger.info(f"Execution result: {result}")
            return result.get('success', False)
        
        # Try handle_plan_execution if available
        if hasattr(universal_automation_handler, 'handle_plan_execution'):
            logger.info("Using handle_plan_execution method")
            result = await universal_automation_handler.handle_plan_execution(plan_id)
            logger.info(f"Execution result: {result}")
            return result.get('success', False)
        
        logger.error("No suitable execution method found")
        return False
    except Exception as e:
        logger.error(f"Error executing plan: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    """Main function"""
    logger.info("Starting direct plan execution test")
    
    success = await test_direct_execution()
    
    if success:
        logger.info("✅ Test passed: Direct plan execution successful")
    else:
        logger.error("❌ Test failed: Direct plan execution failed")

if __name__ == "__main__":
    asyncio.run(main())