#!/usr/bin/env python3
"""
Debug Plan Structure
Check exactly what structure the plan has when returned.
"""

import asyncio
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('debug_plan')

async def debug_plan_structure():
    """Debug the exact structure of the returned plan"""
    
    try:
        import sys, os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'agent_workflow'))
        from enhanced_automation_handler import EnhancedAutomationHandler
        
        handler = EnhancedAutomationHandler()
        result = await handler.create_execution_plan("Click on search button")
        
        logger.info(f"Result type: {type(result)}")
        logger.info(f"Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
        
        if 'execution_plan' in result:
            plan = result['execution_plan']
            logger.info(f"Plan type: {type(plan)}")
            logger.info(f"Plan attributes: {dir(plan)}")
            
            if hasattr(plan, '__dict__'):
                logger.info(f"Plan dict: {plan.__dict__}")
            
            # Try to access steps directly
            if hasattr(plan, 'steps'):
                logger.info(f"Steps count: {len(plan.steps)}")
                logger.info(f"First step: {plan.steps[0].__dict__ if plan.steps else 'No steps'}")
                
        return True
        
    except Exception as e:
        logger.error(f"Debug failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    await debug_plan_structure()

if __name__ == "__main__":
    asyncio.run(main())