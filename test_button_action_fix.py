#!/usr/bin/env python3
"""
Test script to verify the button action execution fix for Agent Mode.
This script simulates the complete flow from generating an automation plan
to clicking the DO button and executing the steps.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class AutomationStep:
    """Represents a single automation step"""
    id: str
    description: str
    action_type: str  # 'click', 'type', 'open', 'hotkey', 'analyze'
    target: Optional[str] = None
    value: Optional[str] = None
    coordinates: Optional[Tuple[int, int]] = None
    confidence: float = 0.8
    status: str = "pending"  # pending, approved, executing, completed, failed
    estimated_duration: float = 2.0  # Default duration in seconds
    
@dataclass
class AutomationPlan:
    """Complete automation plan with interactive approval"""
    task_id: str
    title: str
    description: str
    steps: List[AutomationStep]
    estimated_duration: float
    requires_approval: bool = True
    status: str = "awaiting_approval"  # awaiting_approval, approved, executing, completed, cancelled

# Import adaptive_retry_automation_handler (to test our fix)
sys.path.append('/Users/segevbin/Desktop/SensAI/Aiayer')
try:
    from adaptive_retry_automation_handler import AdaptiveRetryAutomationHandler
    retry_handler = AdaptiveRetryAutomationHandler()
    logger.info("✅ Successfully imported AdaptiveRetryAutomationHandler")
except ImportError as e:
    logger.error(f"❌ Failed to import AdaptiveRetryAutomationHandler: {e}")
    retry_handler = None

async def test_pipe_separated_action_types():
    """Test handling of pipe-separated action types"""
    logger.info("🧪 Testing pipe-separated action types fix")
    
    # Create a test plan with pipe-separated action types
    plan = AutomationPlan(
        task_id="test_task_123",
        title="Test Automation Plan",
        description="Test plan with pipe-separated action types",
        estimated_duration=10.0,
        steps=[
            AutomationStep(
                id="step_1",
                description="Open YouTube",
                action_type="open_app|navigate_url",  # Pipe-separated action types
                target="YouTube",
                estimated_duration=3.0
            ),
            AutomationStep(
                id="step_2",
                description="Search for a video",
                action_type="click_element|type_text",  # Pipe-separated action types
                target="search_box",
                value="test video",
                estimated_duration=2.0
            ),
            AutomationStep(
                id="step_3",
                description="Press Enter",
                action_type="hotkey",  # Single action type
                target="enter",
                estimated_duration=0.5
            )
        ]
    )
    
    logger.info(f"📋 Created test plan with {len(plan.steps)} steps")
    
    # Test each step with the retry handler
    if retry_handler:
        for i, step in enumerate(plan.steps):
            logger.info(f"🔍 Testing step {i+1}: {step.description}")
            logger.info(f"  Action type: {step.action_type}")
            
            # Execute with retry handler
            try:
                # Direct test of _execute_single_step to verify our fix
                success = await retry_handler._execute_single_step(step, plan.task_id)
                logger.info(f"  Result: {'✅ Success' if success else '❌ Failed'}")
            except Exception as e:
                logger.error(f"  Exception: {e}")
    else:
        logger.error("❌ Cannot test without retry handler")
    
    logger.info("✅ Test completed")

async def test_complete_button_action_flow():
    """Test the complete flow from button action to execution"""
    logger.info("🧪 Testing complete button action flow")
    
    try:
        # Import the universal handler
        from universal_intelligent_automation_handler import universal_automation_handler
        
        # Create a test plan
        test_plan_id = f"test_plan_{int(time.time())}"
        
        # Add the plan to the universal handler's active plans
        plan = AutomationPlan(
            task_id=test_plan_id,
            title="Test Button Action Plan",
            description="Test plan for button action execution",
            estimated_duration=10.0,
            steps=[
                AutomationStep(
                    id="step_1",
                    description="Type a search query",
                    action_type="type_text",  # Clean action type
                    value="test search",
                    estimated_duration=2.0
                ),
                AutomationStep(
                    id="step_2",
                    description="Press Enter",
                    action_type="hotkey",
                    target="enter",
                    estimated_duration=0.5
                )
            ]
        )
        
        # Convert to universal handler's plan format
        from universal_intelligent_automation_handler import SmartAutomationStep, UniversalAutomationPlan
        
        universal_steps = []
        for step in plan.steps:
            universal_steps.append(SmartAutomationStep(
                id=step.id,
                description=step.description,
                action_type=step.action_type,
                target=step.target,
                value=step.value,
                coordinates=step.coordinates,
                confidence=step.confidence,
                estimated_duration=step.estimated_duration
            ))
        
        universal_plan = UniversalAutomationPlan(
            task_id=plan.task_id,
            title=plan.title,
            description=plan.description,
            request_type="test_request",
            steps=universal_steps,
            estimated_duration=plan.estimated_duration,
            complexity_score=0.5,
            success_probability=0.9
        )
        
        # Add to active plans
        universal_automation_handler.active_plans[test_plan_id] = universal_plan
        
        logger.info(f"📋 Added test plan to universal handler: {test_plan_id}")
        
        # Simulate clicking the DO button
        logger.info("🔘 Simulating DO button click...")
        result = await universal_automation_handler.handle_button_action("execute_plan", test_plan_id, "test_session")
        
        # Check the result
        if result.get("success", False):
            logger.info("✅ Button action execution successful!")
            logger.info(f"📝 Response: {result.get('response', '')[:100]}...")
        else:
            logger.warning(f"⚠️ Button action execution failed: {result.get('response', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error testing button action flow: {e}")
        return {"success": False, "error": str(e)}

async def main():
    """Run all tests"""
    logger.info("🚀 Starting button action fix verification tests")
    
    # Test pipe-separated action types
    await test_pipe_separated_action_types()
    
    # Test complete button action flow
    logger.info("\n==== TESTING COMPLETE BUTTON ACTION FLOW ====")
    button_result = await test_complete_button_action_flow()
    
    if button_result and button_result.get("success", False):
        logger.info("✅ CRITICAL FIX VERIFIED: Button action now works correctly!")
        logger.info("✅ The DO button will now execute automation plans!")
    else:
        logger.error("❌ Button action fix verification FAILED")
        if button_result:
            logger.error(f"Error: {button_result.get('response', 'Unknown error')}")
    
    logger.info("✅ All tests completed")

if __name__ == "__main__":
    asyncio.run(main())