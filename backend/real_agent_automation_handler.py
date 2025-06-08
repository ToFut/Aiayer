import asyncio
import logging
from typing import Optional, List, Dict, Any
from llm.llm_service import LLMService
from plan_persistence import PlanPersistence
from automation_plan import AutomationPlan

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealAgentAutomationHandler:
    """Handles automation tasks using LLM for planning and execution."""
    
    def __init__(self, llm_service: LLMService, plan_persistence: PlanPersistence):
        self.llm_service = llm_service
        self.plan_persistence = plan_persistence
        self.initialized = False
        
    async def initialize(self) -> bool:
        """Initialize the handler."""
        try:
            if not self.llm_service.initialized:
                if not await self.llm_service.initialize():
                    return False
            self.initialized = True
            return True
        except Exception as e:
            logger.error(f"Error initializing handler: {e}")
            return False
            
    async def create_plan(self, task_id: str, query: str) -> Optional[AutomationPlan]:
        """Create a plan for the given task."""
        try:
            if not self.initialized:
                raise RuntimeError("Agent handler not initialized")

            # Generate plan using LLM
            plan_text = ""
            try:
                async for response in self.llm_service.generate_agent_response(query):
                    plan_text += response
            except Exception as e:
                logger.error(f"Error getting LLM response: {e}")
                return None

            if not plan_text:
                logger.error("No plan text received from LLM")
                return None

            # Parse plan into steps
            steps = self._parse_plan_to_steps(plan_text)
            if not steps:
                logger.error("Failed to parse plan steps")
                return None

            # Create plan
            plan = AutomationPlan(task_id, steps)
            
            # Convert to dict and save
            try:
                plan_dict = plan.to_dict()
                if not self.plan_persistence.save_plan(plan_dict):
                    logger.error(f"Failed to save plan for task {task_id}")
                    return None
            except Exception as e:
                logger.error(f"Error saving plan: {e}")
                return None

            return plan

        except Exception as e:
            logger.error(f"Error creating plan: {e}")
            return None

    def _parse_plan_to_steps(self, plan_text: str) -> list:
        """Parse LLM response into structured steps."""
        try:
            steps = []
            lines = plan_text.split('\n')
            current_step = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Check for step markers
                if line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                    if current_step:
                        steps.append(current_step)
                    current_step = {
                        "action": "execute",
                        "description": line.split('.', 1)[1].strip()
                    }
                elif current_step:
                    # Append to current step description
                    current_step["description"] += f" {line}"
            
            # Add last step if exists
            if current_step:
                steps.append(current_step)
            
            if not steps:
                logger.error("No steps found in plan text")
                return []
                
            logger.info(f"Parsed {len(steps)} steps from plan")
            return steps
        except Exception as e:
            logger.error(f"Error parsing plan steps: {e}")
            return []

    async def execute_plan(self, task_id: str) -> bool:
        """Execute a plan with proper error handling."""
        try:
            plan = self.plan_persistence.load_plan(task_id)
            if not plan:
                logger.error(f"No plan found for task: {task_id}")
                return False

            for step in plan.steps:
                try:
                    await asyncio.wait_for(self._execute_step(step), timeout=10)
                except asyncio.TimeoutError:
                    logger.warning(f"Step execution timed out: {step}")
                    continue
                except Exception as e:
                    logger.error(f"Error executing step: {e}")
                    continue

            plan.completed = True
            # Save updated plan
            try:
                plan_dict = plan.to_dict()
                self.plan_persistence.save_plan(plan_dict)
            except Exception as e:
                logger.error(f"Error saving updated plan: {e}")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Error executing plan: {e}")
            return False

    async def _execute_step(self, step: Dict[str, Any]) -> None:
        """Execute a single step with proper error handling."""
        action = step["action"]
        description = step["description"]
        
        logger.info(f"Executing step: {description}")
        
        # Add your step execution logic here
        # For now, just simulate execution
        await asyncio.sleep(1)

    def get_plan(self, task_id: str) -> Optional[AutomationPlan]:
        """Get a plan by task ID."""
        return self.plan_persistence.load_plan(task_id)

# ... existing code ... 