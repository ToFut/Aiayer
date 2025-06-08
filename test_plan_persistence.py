#!/usr/bin/env python3
"""
Test suite for plan persistence and automation handling system
"""

import os
import json
import time
import asyncio
import pytest
import pytest_asyncio
from typing import Dict, Any, List
from dataclasses import asdict
from universal_intelligent_automation_handler import (
    UniversalIntelligentAutomationHandler,
    SmartAutomationStep,
    UniversalAutomationPlan
)
from plan_persistence import PlanPersistenceManager, save_plan, load_plan

# --- Helper functions for serialization/deserialization ---
def step_from_dict(data: Dict[str, Any]) -> SmartAutomationStep:
    return SmartAutomationStep(
        id=data["id"],
        description=data["description"],
        action_type=data["action_type"],
        target=data.get("target"),
        value=data.get("value"),
        coordinates=tuple(data["coordinates"]) if data.get("coordinates") else None,
        confidence=data.get("confidence", 0.8),
        status=data.get("status", "pending"),
        estimated_duration=data.get("estimated_duration", 2.0),
        retry_count=data.get("retry_count", 0),
        max_retries=data.get("max_retries", 3),
        fallback_action=data.get("fallback_action"),
        context_hints=data.get("context_hints")
    )

def plan_from_dict(data: Dict[str, Any]) -> UniversalAutomationPlan:
    return UniversalAutomationPlan(
        task_id=data["task_id"],
        title=data["title"],
        description=data["description"],
        request_type=data["request_type"],
        steps=[step_from_dict(s) for s in data["steps"]],
        estimated_duration=data["estimated_duration"],
        complexity_score=data["complexity_score"],
        requires_approval=data.get("requires_approval", True),
        status=data.get("status", "awaiting_approval"),
        success_probability=data.get("success_probability", 0.8),
        fallback_strategies=data.get("fallback_strategies"),
        user_guidance_needed=data.get("user_guidance_needed", False)
    )

# Test data
TEST_PLAN_ID = f"test_plan_{int(time.time())}"
TEST_SESSION_ID = f"test_session_{int(time.time())}"

@pytest_asyncio.fixture
async def plan_manager():
    """Create a test plan manager instance"""
    manager = PlanPersistenceManager(auto_save_interval=1)
    await manager.start()
    yield manager
    await manager.stop()
    # Cleanup after tests
    if os.path.exists(manager.storage_path):
        for file in os.listdir(manager.storage_path):
            if file.endswith(".json"):
                os.remove(os.path.join(manager.storage_path, file))

@pytest_asyncio.fixture
async def automation_handler():
    """Create a test automation handler instance"""
    handler = UniversalIntelligentAutomationHandler()
    yield handler
    # Cleanup after tests
    handler.active_plans.clear()

async def create_test_plan() -> UniversalAutomationPlan:
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
        task_id=TEST_PLAN_ID,
        title="Test Automation Plan",
        description="Test plan for persistence verification",
        request_type="web_navigation",
        steps=steps,
        estimated_duration=5.0,
        complexity_score=0.5,
        success_probability=0.9
    )
    return plan

@pytest.mark.asyncio
async def test_plan_persistence_save_load(plan_manager):
    """Test saving and loading plans"""
    # Create test plan
    plan = await create_test_plan()
    
    # Save plan
    success = await save_plan(TEST_PLAN_ID, asdict(plan))
    assert success, "Failed to save plan"
    
    # Load plan
    loaded_plan = await load_plan(TEST_PLAN_ID)
    assert loaded_plan is not None, "Failed to load plan"
    loaded_plan_obj = plan_from_dict(loaded_plan)
    assert loaded_plan_obj.task_id == TEST_PLAN_ID, "Loaded plan has wrong ID"
    assert len(loaded_plan_obj.steps) == 2, "Loaded plan has wrong number of steps"

@pytest.mark.asyncio
async def test_plan_metadata(plan_manager):
    """Test plan metadata handling"""
    # Create and save test plan
    plan = await create_test_plan()
    await save_plan(TEST_PLAN_ID, asdict(plan), plan_manager)
    
    # Check metadata
    metadata = plan_manager.plan_metadata.get(TEST_PLAN_ID)
    assert metadata is not None, "Plan metadata not found"
    assert metadata["title"] == "Test Automation Plan", "Wrong plan title in metadata"
    assert metadata["status"] == "created", "Wrong plan status in metadata"

@pytest.mark.asyncio
async def test_automation_handler_plan_creation(automation_handler):
    """Test plan creation in automation handler"""
    # Create plan request
    request = {
        "steps": [
            {
                "id": "step_1",
                "description": "Test step",
                "action_type": "analyze_screen",
                "estimated_duration": 1.0
            }
        ],
        "metadata": {
            "title": "Test Plan",
            "description": "Test automation plan"
        },
        "session_id": TEST_SESSION_ID
    }
    
    # Create plan
    result = await automation_handler.create_universal_automation_plan(request, TEST_SESSION_ID)
    assert result["success"], "Failed to create plan"
    assert "plan_id" in result, "No plan ID in response"
    
    # Verify plan exists
    plan = await automation_handler._ensure_plan_exists(result["plan_id"])
    assert plan is not None, "Created plan not found"
    assert plan.status == "created", "Wrong plan status"

@pytest.mark.asyncio
async def test_button_action_handling(automation_handler):
    """Test button action handling"""
    # Create test plan
    plan = await create_test_plan()
    automation_handler.active_plans[TEST_PLAN_ID] = plan
    
    # Test DO action
    result = await automation_handler.handle_button_action("DO", TEST_PLAN_ID, TEST_SESSION_ID)
    assert result["success"], "DO action failed"
    assert result["status"] == "executing", "Wrong status after DO action"
    
    # Test DISMISS action
    result = await automation_handler.handle_button_action("DISMISS", TEST_PLAN_ID, TEST_SESSION_ID)
    assert result["success"], "DISMISS action failed"
    assert result["status"] == "cancelled", "Wrong status after DISMISS action"

@pytest.mark.asyncio
async def test_plan_cleanup(plan_manager, automation_handler):
    """Test plan cleanup functionality"""
    # Create multiple test plans
    for i in range(3):
        plan = await create_test_plan()
        plan_id = f"test_plan_{i}_{int(time.time())}"
        await save_plan(plan_id, asdict(plan))
    
    # Wait for cleanup interval
    await asyncio.sleep(2)
    
    # Check if cleanup occurred
    metadata = await plan_manager.get_all_plan_metadata()
    assert len(metadata) > 0, "All plans were cleaned up"

@pytest.mark.asyncio
async def test_plan_execution(automation_handler):
    """Test plan execution"""
    # Create test plan
    plan = await create_test_plan()
    automation_handler.active_plans[TEST_PLAN_ID] = plan
    
    # Execute plan
    result = await automation_handler._execute_plan(plan, TEST_SESSION_ID)
    assert result["success"], "Plan execution failed"
    assert "execution_time" in result, "No execution time in result"
    assert "success_rate" in result, "No success rate in result"

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"]) 