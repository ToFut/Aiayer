#!/usr/bin/env python3
"""
Test script to execute a specific plan
"""

import asyncio
import json
import logging
import os
import sys
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict, field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[ENHANCED-SYSTEM] %(levelname)s:%(name)s:%(message)s',
)
logger = logging.getLogger(__name__)

@dataclass
class SmartAutomationStep:
    """Enhanced automation step with smart execution capabilities"""
    id: str
    description: str
    action_type: str
    target: Optional[str] = None
    value: Optional[str] = None
    coordinates: Optional[tuple] = None
    confidence: float = 0.8
    status: str = "pending"
    estimated_duration: float = 2.0
    retry_count: int = 0
    max_retries: int = 3
    fallback_action: Optional[str] = None
    context_hints: list = field(default_factory=list)

@dataclass 
class UniversalAutomationPlan:
    """Universal automation plan that works with any request type"""
    task_id: str
    title: str
    description: str
    request_type: str
    steps: list
    estimated_duration: float
    complexity_score: float
    requires_approval: bool = True
    status: str = "awaiting_approval"
    success_probability: float = 0.8
    fallback_strategies: list = field(default_factory=list)
    user_guidance_needed: bool = False

async def load_plan(plan_id: str) -> Optional[Dict[str, Any]]:
    """Load a plan from the cache directory"""
    plan_path = os.path.join("cache", "plans", f"{plan_id}.json")
    
    if not os.path.exists(plan_path):
        logger.warning(f"Plan file not found: {plan_path}")
        return None
    
    try:
        with open(plan_path, 'r') as f:
            plan_data = json.load(f)
        logger.info(f"Loaded plan: {plan_id}")
        return plan_data
    except Exception as e:
        logger.error(f"Error loading plan: {e}")
        return None

async def convert_plan_to_class(plan_data: Dict[str, Any]) -> Optional[UniversalAutomationPlan]:
    """Convert plan data dictionary to UniversalAutomationPlan class"""
    if not plan_data:
        return None
    
    try:
        # Convert steps to SmartAutomationStep objects
        steps = []
        for step_data in plan_data.get("steps", []):
            # Convert coordinates if present
            coordinates = None
            if step_data.get("coordinates"):
                try:
                    coords = step_data["coordinates"]
                    if isinstance(coords, list) and len(coords) >= 2:
                        coordinates = (coords[0], coords[1])
                except Exception as e:
                    logger.warning(f"Error parsing coordinates: {e}")
            
            step = SmartAutomationStep(
                id=step_data.get("id", "unknown"),
                description=step_data.get("description", ""),
                action_type=step_data.get("action_type", "unknown"),
                target=step_data.get("target"),
                value=step_data.get("value"),
                coordinates=coordinates,
                confidence=float(step_data.get("confidence", 0.8)),
                status=step_data.get("status", "pending"),
                estimated_duration=float(step_data.get("estimated_duration", 2.0)),
                retry_count=int(step_data.get("retry_count", 0)),
                max_retries=int(step_data.get("max_retries", 3)),
                fallback_action=step_data.get("fallback_action"),
                context_hints=step_data.get("context_hints", []) or []
            )
            steps.append(step)
        
        # Create UniversalAutomationPlan
        plan = UniversalAutomationPlan(
            task_id=plan_data.get("task_id", "unknown"),
            title=plan_data.get("title", "Untitled Plan"),
            description=plan_data.get("description", ""),
            request_type=plan_data.get("request_type", "general"),
            steps=steps,
            estimated_duration=float(plan_data.get("estimated_duration", 0.0)),
            complexity_score=float(plan_data.get("complexity_score", 0.5)),
            requires_approval=bool(plan_data.get("requires_approval", True)),
            status=plan_data.get("status", "awaiting_approval"),
            success_probability=float(plan_data.get("success_probability", 0.8)),
            fallback_strategies=plan_data.get("fallback_strategies", []) or [],
            user_guidance_needed=bool(plan_data.get("user_guidance_needed", False))
        )
        
        logger.info(f"Converted plan {plan.task_id} to class object")
        return plan
    
    except Exception as e:
        logger.error(f"Error converting plan to class: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

async def execute_plan(plan_id: str) -> bool:
    """Execute a specific plan from the cache"""
    try:
        # Load the plan
        plan_data = await load_plan(plan_id)
        if not plan_data:
            logger.error(f"Failed to load plan: {plan_id}")
            return False
        
        # Log the plan data to understand its structure
        logger.info(f"Plan data type: {type(plan_data)}")
        logger.info(f"Plan data keys: {plan_data.keys() if isinstance(plan_data, dict) else 'Not a dict'}")
        
        # Convert to plan class if needed
        plan = await convert_plan_to_class(plan_data)
        if not plan:
            logger.error(f"Failed to convert plan to class: {plan_id}")
            return False
        
        # Import the handler
        try:
            from universal_intelligent_automation_handler import universal_automation_handler
            logger.info("Successfully imported universal_automation_handler")
        except ImportError as e:
            logger.error(f"Failed to import universal_automation_handler: {e}")
            return False
        
        # Debug the handler object
        logger.info(f"Handler object has attributes: {dir(universal_automation_handler)}")
        
        # Store the plan in the handler's active_plans
        logger.info(f"Adding plan to handler's active_plans dictionary")
        universal_automation_handler.active_plans[plan_id] = plan
        
        try:
            # Try direct execution
            result = await universal_automation_handler.handle_button_action('DO', plan_id, plan_id)
            logger.info(f"Execution result: {result}")
            return result.get('success', False)
        except AttributeError as e:
            logger.error(f"AttributeError: {e}")
            logger.info("Trying alternative execution methods...")
            
            try:
                # Try alternative method
                result = await universal_automation_handler._execute_plan(plan, plan_id)
                logger.info(f"Alternative execution result: {result}")
                return result.get('success', False)
            except Exception as e2:
                logger.error(f"Failed to execute plan with alternative method: {e2}")
                return False
        
    except Exception as e:
        logger.error(f"Error executing plan: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        plan_id = sys.argv[1]
    else:
        # Default test plan
        plan_id = "task_1749013294_overlay_session_1748997690672"
    
    logger.info(f"Executing plan: {plan_id}")
    success = await execute_plan(plan_id)
    logger.info(f"Plan execution {'succeeded' if success else 'failed'}")

if __name__ == "__main__":
    asyncio.run(main())