import asyncio
import pytest
import logging
from llm.llm_service import LLMService
from real_agent_automation_handler import RealAgentAutomationHandler
from plan_persistence import PlanPersistence

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_llm_response_stream():
    """Test that LLM response stream works correctly."""
    llm_service = LLMService()
    await llm_service.initialize()
    
    # Test query
    query = "Create a test plan with 3 steps"
    
    # Collect all responses
    responses = []
    try:
        async for response in llm_service.generate_agent_response(query):
            logger.info(f"Received response chunk: {response}")
            responses.append(response)
    except Exception as e:
        logger.error(f"Error in LLM response: {e}")
        raise
    
    # Verify we got responses
    assert len(responses) > 0, "No responses received from LLM"
    logger.info(f"Total response chunks: {len(responses)}")
    logger.info(f"Complete response: {''.join(responses)}")

@pytest.mark.asyncio
async def test_plan_creation():
    """Test that plan creation works correctly."""
    llm_service = LLMService()
    plan_persistence = PlanPersistence()
    handler = RealAgentAutomationHandler(llm_service, plan_persistence)
    
    # Initialize handler
    await handler.initialize()
    
    # Test query
    query = "Create a test plan with 3 steps"
    task_id = "test_task_123"
    
    # Create plan
    plan = await handler.create_plan(task_id, query)
    
    # Verify plan was created
    assert plan is not None, "Plan creation failed"
    assert plan.task_id == task_id, "Task ID mismatch"
    assert len(plan.steps) > 0, "No steps in plan"
    
    # Log plan details
    logger.info(f"Created plan: {plan}")
    logger.info(f"Number of steps: {len(plan.steps)}")
    for i, step in enumerate(plan.steps, 1):
        logger.info(f"Step {i}: {step}")

@pytest.mark.asyncio
async def test_plan_persistence():
    """Test that plan persistence works correctly."""
    llm_service = LLMService()
    plan_persistence = PlanPersistence()
    handler = RealAgentAutomationHandler(llm_service, plan_persistence)
    
    # Initialize handler
    await handler.initialize()
    
    # Test query
    query = "Create a test plan with 3 steps"
    task_id = "test_task_456"
    
    # Create and save plan
    plan = await handler.create_plan(task_id, query)
    assert plan is not None, "Plan creation failed"
    
    # Convert to dict and save
    plan_dict = plan.to_dict()
    assert plan_persistence.save_plan(plan_dict), "Failed to save plan"
    
    # Load plan
    loaded_plan = plan_persistence.load_plan(task_id)
    assert loaded_plan is not None, "Failed to load plan"
    assert loaded_plan.task_id == task_id, "Task ID mismatch in loaded plan"
    assert len(loaded_plan.steps) == len(plan.steps), "Step count mismatch in loaded plan"

if __name__ == "__main__":
    # Run tests
    asyncio.run(test_llm_response_stream())
    asyncio.run(test_plan_creation())
    asyncio.run(test_plan_persistence()) 