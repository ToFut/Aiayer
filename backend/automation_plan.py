from typing import List, Dict, Any

class AutomationPlan:
    """Represents an automation plan with steps."""
    
    def __init__(self, task_id: str, steps: List[Dict[str, Any]]):
        self.task_id = task_id
        self.steps = steps
        self.completed = False
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert plan to dictionary format."""
        return {
            "task_id": self.task_id,
            "steps": self.steps,
            "completed": self.completed
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AutomationPlan':
        """Create plan from dictionary format."""
        plan = cls(data["task_id"], data["steps"])
        plan.completed = data.get("completed", False)
        return plan
        
    def __str__(self) -> str:
        """String representation of the plan."""
        steps_str = "\n".join(f"  {i+1}. {step['description']}" for i, step in enumerate(self.steps))
        return f"Plan for task {self.task_id}:\n{steps_str}\nStatus: {'Completed' if self.completed else 'Pending'}" 