import os
import json
import logging
from typing import Dict, Any, Optional
from automation_plan import AutomationPlan

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlanPersistence:
    def __init__(self, storage_dir: str = "plans"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        self.plans: Dict[str, Any] = {}
        self.load_plans()

    def load_plans(self) -> None:
        """Load all plans from storage."""
        try:
            for plan_file in os.listdir(self.storage_dir):
                if plan_file.endswith(".json"):
                    try:
                        with open(os.path.join(self.storage_dir, plan_file), 'r') as f:
                            plan_data = json.load(f)
                            self.plans[plan_data["task_id"]] = plan_data
                    except Exception as e:
                        logger.error(f"Error loading plan {plan_file}: {e}")
            logger.info(f"Loaded {len(self.plans)} plans from storage")
        except Exception as e:
            logger.error(f"Error loading plans: {e}")

    def save_plan(self, plan_data: Dict[str, Any]) -> bool:
        """Save a plan to storage."""
        try:
            if not isinstance(plan_data, dict):
                logger.error(f"Invalid plan data type: {type(plan_data)}")
                return False
                
            if "task_id" not in plan_data:
                logger.error("Plan data missing task_id")
                return False
                
            file_path = os.path.join(self.storage_dir, f"{plan_data['task_id']}.json")
            with open(file_path, 'w') as f:
                json.dump(plan_data, f, indent=2)
            logger.info(f"Plan saved to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving plan: {e}")
            return False

    def load_plan(self, task_id: str) -> Optional[AutomationPlan]:
        """Load a plan from storage."""
        try:
            file_path = os.path.join(self.storage_dir, f"{task_id}.json")
            if not os.path.exists(file_path):
                logger.warning(f"No plan found for task {task_id}")
                return None
                
            with open(file_path, 'r') as f:
                data = json.load(f)
            return AutomationPlan.from_dict(data)
        except Exception as e:
            logger.error(f"Error loading plan: {e}")
            return None

    def delete_plan(self, task_id: str) -> bool:
        """Delete a plan from persistent storage."""
        try:
            # Delete from disk
            plan_file = os.path.join(self.storage_dir, f"{task_id}.json")
            if os.path.exists(plan_file):
                os.remove(plan_file)
            
            # Delete from memory
            self.plans.pop(task_id, None)
            
            logger.info(f"Plan deleted successfully: {task_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting plan: {e}")
            return False

    def list_plans(self) -> Dict[str, Any]:
        """List all plans in storage."""
        return self.plans

    def get_plan(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a plan by task ID."""
        return self.plans.get(task_id) 