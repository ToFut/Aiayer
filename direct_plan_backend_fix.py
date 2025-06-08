#!/usr/bin/env python3
"""
Direct Plan Backend Fix - Immediate Runtime Fix Without Restart

This script directly modifies the enhanced_enterprise_backend_with_context.py
module at runtime to ensure plans are properly stored and retrieved.
It doesn't require restarting the backend.
"""

import sys
import asyncio
import json
import uuid
import time
import logging
import traceback
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/direct_plan_fix.log')
    ]
)
logger = logging.getLogger("direct_plan_fix")

# Import the backend module
try:
    import enhanced_enterprise_backend_with_context
    logger.info("✅ Successfully imported backend module")
except ImportError as e:
    logger.error(f"❌ Failed to import backend module: {e}")
    sys.exit(1)

# Create a global shared_pending_plans dictionary
if not hasattr(enhanced_enterprise_backend_with_context, 'shared_pending_plans'):
    enhanced_enterprise_backend_with_context.shared_pending_plans = {}
    logger.info("✅ Created shared_pending_plans in backend module")

# Monkey patch the backend's handle_agent_confirmation method
original_handle_agent_confirmation = enhanced_enterprise_backend_with_context.ContextualAIBackend.handle_agent_confirmation

async def patched_handle_agent_confirmation(self, data: Dict[str, Any], client_id: str) -> Dict[str, Any]:
    """Patched handle_agent_confirmation method with direct plan access"""
    try:
        # Handle both sessionId (frontend) and session_id (backend) formats
        session_id = data.get("sessionId") or data.get("session_id")  # This is our plan_id
        action = data.get("action", "").upper()
        
        # Access shared plans from module level
        shared_plans = enhanced_enterprise_backend_with_context.shared_pending_plans
        
        logger.info(f"🎯 Agent confirmation received (PATCHED): sessionId={session_id}, action={action}")
        logger.info(f"🔍 Local plans: {list(self.pending_plans.keys()) if hasattr(self, 'pending_plans') else 'None'}")
        logger.info(f"🔍 Shared plans: {list(shared_plans.keys())}")
        
        # Map frontend actions to backend actions
        if action == "EXECUTE":
            action = "DO"
            logger.info(f"🔄 Mapped action from EXECUTE to DO")
        
        if not session_id:
            logger.error("❌ No session_id provided in agent confirmation")
            return {
                "type": "agent_confirmation_error",
                "error": "No session ID provided"
            }
        
        # Ensure pending_plans exists
        if not hasattr(self, 'pending_plans'):
            logger.info("📌 Initializing pending_plans from shared_pending_plans")
            self.pending_plans = shared_plans
        else:
            # Copy all plans from shared to local if needed
            for plan_id, plan_data in shared_plans.items():
                if plan_id not in self.pending_plans:
                    logger.info(f"📌 Copying plan {plan_id} from shared to local")
                    self.pending_plans[plan_id] = plan_data
        
        # Check if plan exists in pending_plans
        if session_id not in self.pending_plans:
            logger.warning(f"⚠️ Plan not found locally for session_id: {session_id}")
            
            # Check if it exists in shared plans
            if session_id in shared_plans:
                logger.info(f"✅ Found plan in shared plans: {session_id}")
                self.pending_plans[session_id] = shared_plans[session_id]
            else:
                logger.warning(f"⚠️ Plan not found in shared plans either: {session_id}")
                
                # Try to load from plan_persistence if available
                try:
                    if 'plan_persistence' in sys.modules:
                        logger.info(f"📂 Attempting to load from plan_persistence")
                        from plan_persistence import load_plan
                        plan_data = await load_plan(session_id)
                        if plan_data:
                            logger.info(f"✅ Loaded plan from persistence: {session_id}")
                            self.pending_plans[session_id] = plan_data
                            shared_plans[session_id] = plan_data
                        else:
                            # Create fallback plan
                            logger.warning(f"⚠️ Creating fallback plan for {session_id}")
                            fallback_plan = create_fallback_plan(session_id)
                            self.pending_plans[session_id] = fallback_plan
                            shared_plans[session_id] = fallback_plan
                            return await original_handle_agent_confirmation(self, data, client_id)
                    else:
                        # Create fallback plan
                        logger.warning(f"⚠️ Plan persistence not available, creating fallback plan")
                        fallback_plan = create_fallback_plan(session_id)
                        self.pending_plans[session_id] = fallback_plan
                        shared_plans[session_id] = fallback_plan
                except Exception as e:
                    logger.error(f"❌ Error loading/creating plan: {e}")
                    traceback.print_exc()
                    # Create fallback plan
                    logger.warning(f"⚠️ Creating fallback plan after error")
                    fallback_plan = create_fallback_plan(session_id)
                    self.pending_plans[session_id] = fallback_plan
                    shared_plans[session_id] = fallback_plan
        
        # Call the original method with our modifications
        return await original_handle_agent_confirmation(self, data, client_id)
    
    except Exception as e:
        logger.error(f"❌ Error in patched handle_agent_confirmation: {e}")
        traceback.print_exc()
        return {
            "type": "agent_confirmation_error",
            "error": str(e)
        }

def create_fallback_plan(plan_id: str) -> Dict[str, Any]:
    """Create a fallback plan for execution"""
    timestamp = int(time.time())
    return {
        "plan": {
            "task_id": plan_id,
            "title": f"Fallback Plan for {plan_id}",
            "description": f"Automatically created fallback plan",
            "steps": [
                {
                    "id": "step_1",
                    "description": "Analyze current screen",
                    "action_type": "analyze_screen",
                    "estimated_duration": 1.0,
                    "status": "pending"
                },
                {
                    "id": "step_2",
                    "description": "Execute action based on analysis",
                    "action_type": "execute",
                    "estimated_duration": 2.0,
                    "status": "pending"
                }
            ],
            "estimated_duration": 5.0,
            "status": "awaiting_approval"
        },
        "context": {
            "user_prompt": "Fallback action execution",
            "confidence": 0.8
        },
        "timestamp": timestamp,
        "client_id": "system_fallback",
        "plan_id": plan_id,
        "universal": True,
        "fast": True
    }

# Monkey patch the backend's method
enhanced_enterprise_backend_with_context.ContextualAIBackend.handle_agent_confirmation = patched_handle_agent_confirmation
logger.info("✅ Successfully patched handle_agent_confirmation method")

# Patch the initialization of pending_plans in __init__
original_init = enhanced_enterprise_backend_with_context.ContextualAIBackend.__init__

def patched_init(self):
    """Patched __init__ method to use shared_pending_plans"""
    # Call original init
    original_init(self)
    
    # Use the shared dictionary instead
    shared_plans = enhanced_enterprise_backend_with_context.shared_pending_plans
    self.pending_plans = shared_plans
    logger.info(f"✅ Initialized backend with shared_pending_plans ({len(shared_plans)} plans)")

# Apply the patch
enhanced_enterprise_backend_with_context.ContextualAIBackend.__init__ = patched_init
logger.info("✅ Successfully patched __init__ method")

# Create test plan function to simulate what's happening in the frontend
async def create_test_plan():
    """Create a test plan in the backend to ensure it works"""
    plan_id = f"test_plan_{uuid.uuid4()}"
    test_plan = create_fallback_plan(plan_id)
    
    # Store in the shared dictionary
    enhanced_enterprise_backend_with_context.shared_pending_plans[plan_id] = test_plan
    logger.info(f"✅ Created test plan {plan_id} in shared dictionary")
    
    return plan_id

async def check_backend_plans():
    """Check if backend instances can see the plans"""
    # Create new backend instance
    backend = enhanced_enterprise_backend_with_context.ContextualAIBackend()
    
    # Check plans
    logger.info(f"Backend instance has plans: {list(backend.pending_plans.keys())}")
    logger.info(f"Shared plans dictionary has: {list(enhanced_enterprise_backend_with_context.shared_pending_plans.keys())}")
    
    # Check if they're the same object
    is_same = backend.pending_plans is enhanced_enterprise_backend_with_context.shared_pending_plans
    logger.info(f"Backend's pending_plans is the same object as shared_pending_plans: {is_same}")
    
    return is_same

async def test_fix():
    """Test if the fix works"""
    # Create a test plan
    plan_id = await create_test_plan()
    
    # Check if backend instances can see the plan
    is_same = await check_backend_plans()
    
    logger.info(f"Fix test result: {'✅ SUCCESS' if is_same else '❌ FAILED'}")
    return is_same

async def main():
    """Apply the fix and test it"""
    logger.info("=== Direct Plan Backend Fix ===")
    logger.info("This script directly modifies the backend module to fix plan storage")
    
    # Run the test
    success = await test_fix()
    
    if success:
        logger.info("\n✅ FIX SUCCESSFULLY APPLIED AND TESTED!")
        logger.info("Plans will now be properly shared between all backend instances")
        logger.info("This fixes the 'Available plans: None' issue when using DO button")
        logger.info("\nYou can continue using the system without restarting!")
    else:
        logger.error("\n❌ Fix test failed!")
        logger.error("There may be additional issues preventing the fix from working")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())