#!/usr/bin/env python3
"""
Test DO Button Shared Plans

This script tests the shared pending_plans fix by creating multiple 
backend instances and ensuring they all share the same plans.
"""

import asyncio
import json
import uuid
import time
import logging
import sys
from typing import Dict, Any, List, Optional, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/test_do_button_shared_plans.log')
    ]
)
logger = logging.getLogger("test_do_button_shared_plans")

# Import backend class
try:
    from enhanced_enterprise_backend_with_context import ContextualAIBackend, shared_pending_plans
    SHARED_PLANS_AVAILABLE = True
    logger.info("✅ Found shared_pending_plans in the backend - fix is applied!")
except ImportError as e:
    logger.error(f"❌ Failed to import ContextualAIBackend: {e}")
    sys.exit(1)
except AttributeError as e:
    logger.warning(f"⚠️ shared_pending_plans not found - fix not applied: {e}")
    SHARED_PLANS_AVAILABLE = False

async def create_test_plan(instance_num: int):
    """Create a test plan in the backend instance"""
    # Create backend instance
    backend = ContextualAIBackend()
    
    # Create a test plan
    plan_id = f"test_plan_{uuid.uuid4()}"
    test_plan = {
        "plan": {
            "description": f"Test plan created by instance {instance_num}",
            "steps": ["step 1", "step 2"]
        },
        "context": {"user_prompt": f"Test from instance {instance_num}"},
        "timestamp": time.time(),
        "client_id": f"test_client_{instance_num}",
        "plan_id": plan_id,
        "universal": True
    }
    
    # Store plan in this instance's pending_plans
    backend.pending_plans[plan_id] = test_plan
    logger.info(f"Created plan {plan_id} in instance {instance_num}")
    
    # Return the plan ID and instance
    return plan_id, backend

async def check_plan_exists(plan_id: str, instance_num: int):
    """Check if a plan exists in a different backend instance"""
    # Create a different backend instance
    backend = ContextualAIBackend()
    
    # Check if the plan exists in this instance's pending_plans
    if plan_id in backend.pending_plans:
        logger.info(f"✅ Instance {instance_num} can see plan {plan_id}")
        return True
    else:
        logger.error(f"❌ Instance {instance_num} cannot see plan {plan_id}")
        logger.info(f"Available plans in instance {instance_num}: {list(backend.pending_plans.keys())}")
        return False

async def test_agent_confirmation(plan_id: str, instance_num: int):
    """Test agent confirmation on a different backend instance"""
    # Create a different backend instance
    backend = ContextualAIBackend()
    
    # Create agent confirmation data
    agent_confirmation_data = {
        "type": "agent_confirmation",
        "sessionId": plan_id,
        "action": "DO",
        "timestamp": int(time.time() * 1000)
    }
    
    # Call handle_agent_confirmation
    try:
        logger.info(f"Calling handle_agent_confirmation from instance {instance_num} for plan {plan_id}")
        result = await backend.handle_agent_confirmation(agent_confirmation_data, f"test_client_{instance_num}")
        
        # Check result
        if result.get("type") == "agent_confirmation_error":
            logger.error(f"❌ handle_agent_confirmation failed: {result.get('error')}")
            return False
        else:
            logger.info(f"✅ handle_agent_confirmation processed plan: {result.get('type')}")
            return True
    except Exception as e:
        logger.error(f"❌ Error in handle_agent_confirmation: {e}")
        return False

async def test_shared_pending_plans():
    """Test the shared pending_plans implementation"""
    # Test if the fix is applied
    if not SHARED_PLANS_AVAILABLE:
        logger.warning("⚠️ shared_pending_plans not available - fix needs to be applied")
        logger.info("Please run fix_do_button_pending_plans.py first")
        return False
    
    # Create a plan in instance 1
    plan_id, instance1 = await create_test_plan(1)
    
    # Check if the plan exists in instance 2
    exists_in_instance2 = await check_plan_exists(plan_id, 2)
    
    # Test handle_agent_confirmation in instance 3
    confirmation_works = await test_agent_confirmation(plan_id, 3)
    
    # Check if plans are really shared
    logger.info("\n=== Shared Plans Test Results ===")
    logger.info(f"Fix applied: {SHARED_PLANS_AVAILABLE}")
    logger.info(f"Plan exists in different instance: {exists_in_instance2}")
    logger.info(f"handle_agent_confirmation works: {confirmation_works}")
    
    # Overall result
    if exists_in_instance2 and confirmation_works:
        logger.info("✅ Shared pending_plans fix is working correctly!")
        return True
    else:
        logger.error("❌ Shared pending_plans fix is not working correctly")
        return False

async def main():
    """Main test function"""
    logger.info("=== Testing DO Button Shared Plans Fix ===")
    
    # Test the shared pending_plans implementation
    success = await test_shared_pending_plans()
    
    if success:
        logger.info("\n✅ DO Button fix is working correctly!")
        logger.info("Plans are now shared between all backend instances")
        logger.info("This will resolve the 'Available plans: None' issue when using DO button")
    else:
        logger.error("\n❌ DO Button fix needs to be applied")
        logger.info("Please run fix_do_button_pending_plans.py to apply the fix")

if __name__ == "__main__":
    asyncio.run(main())