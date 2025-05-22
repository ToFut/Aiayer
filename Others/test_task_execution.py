#!/usr/bin/env python3
import asyncio
import logging
from execution.core.task_orchestrator import TaskOrchestrator, TaskDefinition, TaskStep, TaskPriority
from execution.core.agent_base import AgentBase, AgentCapability, AgentState, AgentConfig
from dataclasses import dataclass
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a simple test agent
class TestAgent(AgentBase):
    def __init__(self, agent_id: str):
        config = AgentConfig(
            name="Test Agent",
            capabilities=[AgentCapability.TEST],
            max_concurrent_tasks=5,
            task_timeout_seconds=60
        )
        super().__init__(config)
        self.agent_id = agent_id
        self.state = AgentState.RUNNING

    async def initialize(self) -> None:
        """Initialize the agent."""
        logger.info("Test agent initialized")
        return

    async def process_task(self, task_data: Dict[str, Any]) -> Any:
        """Process a task."""
        # Simulate task processing
        await asyncio.sleep(1)
        return {"result": f"Processed task: {task_data['action']}"}

    async def cleanup(self) -> None:
        """Clean up agent resources."""
        logger.info("Test agent cleaned up")
        return

async def main():
    # Initialize orchestrator
    orchestrator = TaskOrchestrator(max_concurrent_tasks=5)
    
    # Create test agent
    test_agent = TestAgent("test_agent_1")
    orchestrator.register_agent(test_agent)
    
    # Start orchestrator
    await orchestrator.start()
    
    try:
        # Create a test task
        task = TaskDefinition(
            task_id="test_task_1",
            name="Test Task",
            description="A test task to verify execution",
            steps=[
                TaskStep(
                    step_id="step1",
                    agent_capability=AgentCapability.TEST,
                    action="test_action",
                    parameters={"param1": "value1"}
                ),
                TaskStep(
                    step_id="step2",
                    agent_capability=AgentCapability.TEST,
                    action="test_action2",
                    parameters={"param2": "value2"},
                    dependencies=["step1"]
                )
            ],
            priority=TaskPriority.NORMAL
        )
        
        # Submit task
        task_id = await orchestrator.submit_task(task)
        logger.info(f"Submitted task: {task_id}")
        
        # Monitor task status
        while True:
            status = orchestrator.get_task_status(task_id)
            if status:
                logger.info(f"Task status: {status['status']}, Progress: {status['progress']}%")
                if status['status'] in ['completed', 'failed']:
                    break
            await asyncio.sleep(1)
        
        # Get final statistics
        stats = orchestrator.get_task_statistics()
        logger.info(f"Task statistics: {stats}")
        
    finally:
        # Stop orchestrator
        await orchestrator.stop()

if __name__ == "__main__":
    asyncio.run(main()) 