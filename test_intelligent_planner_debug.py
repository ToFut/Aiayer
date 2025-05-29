#!/usr/bin/env python3
"""
Debug test for intelligent automation planner
"""

import asyncio
import logging
from intelligent_automation_planner import intelligent_planner

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_planner():
    """Test the intelligent planner with simple request"""
    
    test_messages = [
        "open Google and search Omer Adam",
        "search YouTube for Omer Adam music",
        "open Safari and go to YouTube",
        "find Omer Adam on Google"
    ]
    
    for message in test_messages:
        logger.info(f"\n🧪 Testing: '{message}'")
        
        try:
            # Test intent analysis
            intent = await intelligent_planner.analyze_user_intent(message)
            logger.info(f"Intent analysis: {intent}")
            
            # Test plan creation
            plan = await intelligent_planner.create_intelligent_plan(message, "debug_session")
            
            logger.info(f"📋 Plan created:")
            logger.info(f"  Title: {plan.title}")
            logger.info(f"  Steps: {len(plan.steps)}")
            logger.info(f"  Duration: {plan.estimated_duration}")
            
            for i, step in enumerate(plan.steps, 1):
                logger.info(f"  {i}. {step.description} ({step.action_type})")
                if step.value:
                    logger.info(f"     → Value: {step.value}")
                if step.target:
                    logger.info(f"     → Target: {step.target}")
            
        except Exception as e:
            logger.error(f"❌ Error testing '{message}': {e}")
            import traceback
            traceback.print_exc()
        
        print("-" * 60)

if __name__ == "__main__":
    asyncio.run(test_planner())