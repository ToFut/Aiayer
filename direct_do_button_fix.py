#!/usr/bin/env python3
"""
Direct DO Button Fix - Direct integration with the universal_intelligent_automation_handler
"""

import asyncio
import json
import logging
import os
import time
import sys
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[DIRECT-FIX] %(levelname)s:%(name)s:%(message)s',
)
logger = logging.getLogger(__name__)

# Define the same data structures as in universal_intelligent_automation_handler.py
@dataclass
class SmartAutomationStep:
    """Enhanced automation step with smart execution capabilities"""
    id: str
    description: str
    action_type: str
    target: Optional[str] = None
    value: Optional[str] = None
    coordinates: Optional[Tuple[int, int]] = None
    confidence: float = 0.8
    status: str = "pending"
    estimated_duration: float = 2.0
    retry_count: int = 0
    max_retries: int = 3
    fallback_action: Optional[str] = None
    context_hints: List[str] = field(default_factory=list)

@dataclass 
class UniversalAutomationPlan:
    """Universal automation plan that works with any request type"""
    task_id: str
    title: str
    description: str
    request_type: str
    steps: List[SmartAutomationStep]
    estimated_duration: float
    complexity_score: float
    requires_approval: bool = True
    status: str = "awaiting_approval"
    success_probability: float = 0.8
    fallback_strategies: List[str] = field(default_factory=list)
    user_guidance_needed: bool = False

async def create_test_plan(plan_id: str) -> UniversalAutomationPlan:
    """Create a test automation plan"""
    steps = [
        SmartAutomationStep(
            id="step_1",
            description="Open Safari browser",
            action_type="open_app",
            target="Safari",
            estimated_duration=2.0
        ),
        SmartAutomationStep(
            id="step_2",
            description="Navigate to example.com",
            action_type="navigate_url",
            value="https://example.com",
            estimated_duration=3.0
        )
    ]
    
    plan = UniversalAutomationPlan(
        task_id=plan_id,
        title="Test Automation Plan",
        description="Test plan for direct execution",
        request_type="web_navigation",
        steps=steps,
        estimated_duration=5.0,
        complexity_score=0.5,
        success_probability=0.9
    )
    return plan

async def save_plan_to_cache(plan_id: str, plan: UniversalAutomationPlan) -> bool:
    """Save plan to cache directory"""
    cache_dir = os.path.join("cache", "plans")
    os.makedirs(cache_dir, exist_ok=True)
    
    plan_path = os.path.join(cache_dir, f"{plan_id}.json")
    try:
        with open(plan_path, 'w') as f:
            json.dump(asdict(plan), f, indent=2)
        
        # Also update metadata file
        metadata_path = os.path.join(cache_dir, "plan_metadata.json")
        metadata = {}
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            except:
                pass
        
        # Add plan to metadata
        metadata[plan_id] = {
            "plan_id": plan_id,
            "title": plan.title,
            "timestamp": time.time(),
            "status": "created",
            "created": time.time(),
            "last_accessed": time.time()
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Saved plan {plan_id} to cache")
        return True
    except Exception as e:
        logger.error(f"Error saving plan to cache: {e}")
        return False

async def direct_register_plan(plan_id: str) -> bool:
    """Directly register plan with the universal_intelligent_automation_handler"""
    try:
        # Import the handler
        from universal_intelligent_automation_handler import universal_automation_handler
        
        # Create a test plan
        plan = await create_test_plan(plan_id)
        
        # Store plan in cache for persistence
        await save_plan_to_cache(plan_id, plan)
        
        # Register plan directly with the handler
        universal_automation_handler.active_plans[plan_id] = plan
        
        logger.info(f"Successfully registered plan {plan_id} with universal_automation_handler")
        return True
    except Exception as e:
        logger.error(f"Error registering plan: {e}")
        return False

async def direct_execute_plan(plan_id: str, session_id: str) -> Dict[str, Any]:
    """Direct execution of a plan through the universal_intelligent_automation_handler"""
    try:
        # Register the plan first
        registered = await direct_register_plan(plan_id)
        if not registered:
            logger.error(f"Failed to register plan {plan_id}")
            return {"success": False, "error": "Failed to register plan"}
        
        # Import the handler
        from universal_intelligent_automation_handler import universal_automation_handler
        
        # Execute the plan directly
        logger.info(f"Executing plan {plan_id} directly through universal_automation_handler")
        result = await universal_automation_handler.handle_button_action("DO", plan_id, session_id)
        
        logger.info(f"Execution result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error executing plan: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e)}

async def direct_execute_agent_confirmation(session_id: str, action: str = "DO") -> Dict[str, Any]:
    """Directly execute an agent confirmation message"""
    try:
        # This is the same as a plan_id in the handler
        plan_id = session_id
        
        # Register the plan first to ensure it exists
        registered = await direct_register_plan(plan_id)
        if not registered:
            logger.error(f"Failed to register plan for session {session_id}")
            return {"success": False, "error": "Failed to register plan"}
        
        # Import the handler
        from universal_intelligent_automation_handler import universal_automation_handler
        
        # Execute the plan directly
        logger.info(f"Executing agent confirmation for session {session_id} with action {action}")
        result = await universal_automation_handler.handle_button_action(action, plan_id, session_id)
        
        logger.info(f"Execution result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error executing agent confirmation: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e)}

async def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        # Use command line argument as plan_id or session_id
        plan_id = sys.argv[1]
    else:
        # Use default test plan ID
        plan_id = f"task_{int(time.time())}_direct_fix"
    
    logger.info(f"Using plan ID: {plan_id}")
    
    if len(sys.argv) > 2 and sys.argv[2] == "agent":
        # Execute as agent confirmation
        result = await direct_execute_agent_confirmation(plan_id)
    else:
        # Execute as direct plan execution
        result = await direct_execute_plan(plan_id, plan_id)
    
    if result.get("success", False):
        logger.info("✅ Execution succeeded!")
        if "response" in result:
            print("\nResponse:", result["response"])
    else:
        logger.error("❌ Execution failed!")
        if "error" in result:
            print("\nError:", result["error"])

if __name__ == "__main__":
    asyncio.run(main())