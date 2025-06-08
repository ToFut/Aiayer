#!/usr/bin/env python3
import asyncio
import logging
import sys
from universal_intelligent_automation_handler import universal_automation_handler

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("automation_test")

async def test_automation_plan_creation():
    """Test the creation of an automation plan"""
    logger.info("Testing Universal Automation Plan Creation")
    
    # Test request
    user_request = "Help me search for cute cat pictures on Google"
    session_id = "test_session_123"
    
    try:
        # Import the fixed function
        from fixed_universal_automation_handler import fixed_handle_universal_automation
        
        # Create the automation plan using the fixed handler
        result = await fixed_handle_universal_automation(user_request, session_id)
        
        # Check if plan was created successfully
        if result.get("success"):
            logger.info(f"✅ Successfully created automation plan: {result.get('plan_id')}")
            logger.info(f"Plan type: {result.get('request_type')}")
            
            # Check if we can access the plan from the handler
            plan_id = result.get("plan_id")
            if plan_id in universal_automation_handler.active_plans:
                plan = universal_automation_handler.active_plans[plan_id]
                logger.info(f"Plan title: {plan.title}")
                logger.info(f"Number of steps: {len(plan.steps)}")
                
                for i, step in enumerate(plan.steps, 1):
                    logger.info(f"Step {i}: {step.description} ({step.action_type})")
            
            return True
        else:
            logger.error(f"Failed to create automation plan: {result.get('response')}")
            return False
    except Exception as e:
        logger.error(f"Error testing automation plan creation: {e}")
        return False

async def main():
    """Run all tests"""
    try:
        success = await test_automation_plan_creation()
        
        if success:
            logger.info("All tests completed successfully!")
        else:
            logger.error("Tests failed")
    finally:
        # Clean up
        if hasattr(universal_automation_handler, 'llm_service') and universal_automation_handler.llm_service:
            if hasattr(universal_automation_handler.llm_service, 'stop'):
                await universal_automation_handler.llm_service.stop()
                logger.info("Stopped LLM service")

if __name__ == "__main__":
    asyncio.run(main())