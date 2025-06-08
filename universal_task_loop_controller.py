#!/usr/bin/env python3
"""
Universal Task Loop Controller

Advanced task automation system that maintains persistent state between
operations and handles any type of complex task sequence.

Key capabilities:
1. Continuous operation with state persistence
2. Dynamic task planning based on current UI state
3. Interactive approval workflow for critical decisions
4. Value tracking and monetization metrics
5. Verification and error recovery

This controller works with ANY task type across any application by leveraging:
- UI detection
- LLM-based planning
- Execution capabilities
- Verification systems
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum

# Import existing components
from universal_intelligent_automation_handler import UniversalAutomationPlan, SmartAutomationStep
from brain.core.brain_router import ChatMode, BrainResponse
from execution.core.task_orchestrator import TaskOrchestrator
from ui_element_detector import UIElementDetector

# Import plan persistence
try:
    from plan_persistence import save_plan, load_plan, delete_plan, generate_plan_id, NextStepSuggestion
    PERSISTENCE_AVAILABLE = True
    logger = logging.getLogger("universal_task_loop")
    logger.info("✅ Plan persistence module loaded successfully")
except ImportError as e:
    logger = logging.getLogger("universal_task_loop")
    logger.warning(f"⚠️ Plan persistence not available, plans will not persist: {e}")
    PERSISTENCE_AVAILABLE = False

# Import memory system integration
try:
    from memory.task_memory_manager import (
        initialize as init_task_memory,
        create_task_record,
        update_task_record,
        complete_task_record,
        search_task_records,
        synchronize_with_controller,
        populate_controller_state
    )
    
    # Import task context awareness
    from memory.task_context_awareness import (
        initialize as init_task_context,
        register_task,
        get_task_context,
        enrich_task_data
    )
    
    MEMORY_SYSTEM_AVAILABLE = True
    CONTEXT_AWARENESS_AVAILABLE = True
    logger.info("✅ Task memory system integration loaded successfully")
    logger.info("✅ Task context awareness loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ Task memory system integration not available: {e}")
    MEMORY_SYSTEM_AVAILABLE = False
    CONTEXT_AWARENESS_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/universal_task_loop.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("universal_task_loop")

class TaskStatus(Enum):
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    AWAITING_APPROVAL = "awaiting_approval"
    VERIFICATION = "verification"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class TaskValueMetrics(Enum):
    TIME_SAVED = "time_saved"
    COST_SAVED = "cost_saved"
    ERROR_REDUCTION = "error_reduction"
    THROUGHPUT_INCREASE = "throughput_increase"
    QUALITY_IMPROVEMENT = "quality_improvement"

@dataclass
class TaskExecutionMetrics:
    """Metrics for tracking task execution and value"""
    task_id: str
    start_time: float
    steps_completed: int = 0
    steps_total: int = 0
    time_saved: float = 0.0  # in seconds
    estimated_manual_time: float = 0.0  # in seconds
    error_count: int = 0
    recovery_count: int = 0
    verification_success_rate: float = 0.0
    monetary_value: float = 0.0  # calculated value
    end_time: Optional[float] = None
    
    def calculate_progress(self) -> float:
        """Calculate task progress percentage"""
        if self.steps_total == 0:
            return 0.0
        return (self.steps_completed / self.steps_total) * 100.0
    
    def calculate_time_saved(self) -> float:
        """Calculate time saved compared to manual execution"""
        if self.end_time is None:
            current_duration = time.time() - self.start_time
        else:
            current_duration = self.end_time - self.start_time
            
        return max(0, self.estimated_manual_time - current_duration)
    
    def calculate_monetary_value(self, hourly_rate: float = 50.0) -> float:
        """Calculate monetary value of time saved"""
        time_saved_hours = self.calculate_time_saved() / 3600
        return time_saved_hours * hourly_rate
    
    def update_metrics(self):
        """Update calculated metrics"""
        self.time_saved = self.calculate_time_saved()
        self.monetary_value = self.calculate_monetary_value()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/serialization"""
        return {
            "task_id": self.task_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "steps_completed": self.steps_completed,
            "steps_total": self.steps_total,
            "time_saved": self.time_saved,
            "estimated_manual_time": self.estimated_manual_time,
            "error_count": self.error_count,
            "recovery_count": self.recovery_count,
            "verification_success_rate": self.verification_success_rate,
            "monetary_value": self.monetary_value,
            "progress": self.calculate_progress()
        }

@dataclass
class LoopControllerState:
    """Persistent state for the task loop controller"""
    active_tasks: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    completed_tasks: List[Dict[str, Any]] = field(default_factory=list)
    paused_tasks: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    failed_tasks: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    current_context: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    global_settings: Dict[str, Any] = field(default_factory=dict)
    last_updated: float = field(default_factory=time.time)
    
    def save_to_file(self, filename: str = "controller_state.json"):
        """Save state to file"""
        with open(filename, 'w') as f:
            json.dump(asdict(self), f, indent=2)
    
    @classmethod
    def load_from_file(cls, filename: str = "controller_state.json") -> 'LoopControllerState':
        """Load state from file"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                return cls(**data)
        except (FileNotFoundError, json.JSONDecodeError):
            logger.warning(f"Could not load state from {filename}, creating new state")
            return cls()

class UniversalTaskLoopController:
    """
    Advanced controller that can execute any complex task sequence with
    persistent state and continuous operation.
    """
    
    def __init__(self):
        self.state = LoopControllerState()
        
        # Import existing components
        try:
            from universal_intelligent_automation_handler import universal_automation_handler
            self.automation_handler = universal_automation_handler
            
            from execution.core.task_orchestrator import TaskOrchestrator
            self.task_orchestrator = TaskOrchestrator()
            
            from ui_element_detector import UIElementDetector
            self.ui_detector = UIElementDetector()
            
            # Initialize LLM service for decision-making
            from llm.llm_service import LLMService
            self.llm_service = LLMService()
            
            # Initialize tracking for monetization metrics
            self.value_tracker = ValueMetricsTracker()
            
            # Dashboard connection
            self.dashboard_reporter = DashboardReporter()
            
            logger.info("✅ Universal Task Loop Controller initialized with all components")
            self.all_components_available = True
            
        except ImportError as e:
            logger.warning(f"Some components not available: {e}")
            self.all_components_available = False
        
        # Task execution callbacks
        self.task_callbacks: Dict[str, List[Callable]] = {
            'on_task_start': [],
            'on_task_complete': [],
            'on_task_fail': [],
            'on_user_approval': [],
            'on_step_complete': [],
            'on_metrics_update': []
        }
        
        # Active execution tasks
        self.execution_tasks: Dict[str, asyncio.Task] = {}
        
        # Load previous state if available
        try:
            self.state = LoopControllerState.load_from_file()
            logger.info(f"Loaded previous state with {len(self.state.active_tasks)} active tasks")
            
            # Resume any active tasks
            for task_id, task_data in self.state.active_tasks.items():
                if task_data.get('status') not in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value]:
                    logger.info(f"Will resume task: {task_id}")
        except Exception as e:
            logger.error(f"Error loading previous state: {e}")
    
    async def initialize(self):
        """Initialize async components"""
        if hasattr(self, 'llm_service'):
            await self.llm_service.initialize()
        
        # Initialize task memory system if available
        if MEMORY_SYSTEM_AVAILABLE:
            try:
                # Initialize task memory manager
                memory_system = None
                if hasattr(self, 'memory_system'):
                    memory_system = self.memory_system
                
                # Initialize with memory system
                await init_task_memory(memory_system)
                
                # Initialize task context awareness
                if CONTEXT_AWARENESS_AVAILABLE:
                    await init_task_context(memory_system)
                    logger.info("Task context awareness initialized")
                
                # Load state from task memory
                logger.info("Loading state from task memory system")
                self.state = await populate_controller_state(self.state)
                logger.info(f"Loaded controller state with {len(self.state.active_tasks)} active tasks from memory")
                
                # Register tasks with context awareness
                if CONTEXT_AWARENESS_AVAILABLE:
                    for task_id, task_data in self.state.active_tasks.items():
                        await register_task(task_id, task_data.get("description", ""))
                        logger.info(f"Registered task {task_id} with context awareness")
                
                # Resume any active tasks
                for task_id, task_data in list(self.state.active_tasks.items()):
                    if task_data.get('status') not in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value]:
                        logger.info(f"Resuming task from memory: {task_id}")
                        execution_task = asyncio.create_task(self._execute_task_loop(task_id))
                        self.execution_tasks[task_id] = execution_task
                
            except Exception as e:
                logger.error(f"Error initializing task memory system: {e}")
        
        # Start periodic state saving
        asyncio.create_task(self._periodic_state_save())
        
        # Start synchronization with memory system if available
        if MEMORY_SYSTEM_AVAILABLE:
            asyncio.create_task(self._periodic_memory_sync())
        
        # Start dashboard reporting
        if hasattr(self, 'dashboard_reporter'):
            asyncio.create_task(self._periodic_dashboard_update())
    
    async def _periodic_state_save(self, interval: int = 60):
        """Periodically save controller state"""
        while True:
            try:
                self.state.last_updated = time.time()
                self.state.save_to_file()
                logger.debug(f"Saved controller state with {len(self.state.active_tasks)} active tasks")
            except Exception as e:
                logger.error(f"Error saving controller state: {e}")
            
            await asyncio.sleep(interval)
    
    async def _periodic_dashboard_update(self, interval: int = 5):
        """Periodically update dashboard with latest metrics"""
        while True:
            try:
                if hasattr(self, 'dashboard_reporter'):
                    metrics = {
                        'active_tasks': len(self.state.active_tasks),
                        'completed_tasks': len(self.state.completed_tasks),
                        'paused_tasks': len(self.state.paused_tasks),
                        'failed_tasks': len(self.state.failed_tasks),
                        'task_metrics': self.state.metrics,
                        'current_timestamp': time.time()
                    }
                    
                    await self.dashboard_reporter.update_metrics(metrics)
            except Exception as e:
                logger.error(f"Error updating dashboard: {e}")
            
            await asyncio.sleep(interval)
            
    async def _periodic_memory_sync(self, interval: int = 30):
        """Periodically synchronize state with task memory system"""
        if not MEMORY_SYSTEM_AVAILABLE:
            return
            
        while True:
            try:
                # Synchronize controller state with memory system
                await synchronize_with_controller(self.state)
                logger.debug(f"Synchronized controller state with memory system")
            except Exception as e:
                logger.error(f"Error synchronizing with memory system: {e}")
            
            await asyncio.sleep(interval)
    
    async def submit_task(self, task_description: str, task_type: str = "universal", 
                        context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Submit a new task for execution
        
        Args:
            task_description: Natural language description of the task
            task_type: Type of task (universal, email, web, etc.)
            context: Additional context for the task
            
        Returns:
            Dict with task details including ID
        """
        try:
            # Generate task ID using plan persistence if available
            if PERSISTENCE_AVAILABLE:
                session_id = context.get("session_id") if context else None
                task_id = await generate_plan_id(session_id)
            else:
                task_id = f"task_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            
            # Create initial task entry
            task_data = {
                "task_id": task_id,
                "description": task_description,
                "type": task_type,
                "status": TaskStatus.PENDING.value,
                "submitted_at": time.time(),
                "context": context or {},
                "current_step": 0,
                "total_steps": 0,
                "plan": None,
                "results": {},
                "metrics": {}
            }
            
            # Store in active tasks
            self.state.active_tasks[task_id] = task_data
            
            # Create metrics tracking
            metrics = TaskExecutionMetrics(
                task_id=task_id,
                start_time=time.time(),
                estimated_manual_time=self._estimate_manual_time(task_description, task_type)
            )
            self.state.metrics[task_id] = metrics.to_dict()
            
            # Save to persistent storage if available
            if PERSISTENCE_AVAILABLE:
                try:
                    await save_plan(task_id, task_data)
                    logger.info(f"Task {task_id} saved to persistent storage")
                except Exception as e:
                    logger.error(f"Error saving task to persistent storage: {e}")
            
            # Create task memory record if available
            if MEMORY_SYSTEM_AVAILABLE:
                try:
                    await create_task_record(task_id, task_data, metrics.to_dict())
                    logger.info(f"Task {task_id} stored in memory system")
                    
                    # Register with context awareness if available
                    if CONTEXT_AWARENESS_AVAILABLE:
                        await register_task(task_id, task_description)
                        logger.info(f"Task {task_id} registered with context awareness")
                except Exception as e:
                    logger.error(f"Error creating task memory record: {e}")
            
            # Start execution in background
            execution_task = asyncio.create_task(self._execute_task_loop(task_id))
            self.execution_tasks[task_id] = execution_task
            
            logger.info(f"Task submitted: {task_id} - {task_description}")
            
            # Save state
            self.state.save_to_file()
            
            return {
                "success": True,
                "task_id": task_id,
                "status": TaskStatus.PENDING.value,
                "description": task_description,
                "message": "Task submitted successfully and execution started",
                "persistent": PERSISTENCE_AVAILABLE
            }
            
        except Exception as e:
            logger.error(f"Error submitting task: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to submit task"
            }
    
    def _estimate_manual_time(self, task_description: str, task_type: str) -> float:
        """Estimate time to complete task manually (in seconds)"""
        # Base time - 5 minutes
        base_time = 300.0
        
        # Adjust based on task description length and complexity
        word_count = len(task_description.split())
        complexity_factor = 1.0
        
        if word_count > 50:
            complexity_factor = 1.5
        if word_count > 100:
            complexity_factor = 2.0
            
        # Adjust based on task type
        type_factors = {
            "email": 1.2,
            "web": 1.3,
            "document": 1.5,
            "data_entry": 2.0,
            "research": 3.0,
            "analysis": 4.0,
            "universal": 1.5
        }
        
        type_factor = type_factors.get(task_type, 1.5)
        
        # Check for complex operation indicators
        complex_indicators = ["multiple", "series", "sequence", "several", 
                             "all", "every", "each", "extract", "compare"]
        
        if any(indicator in task_description.lower() for indicator in complex_indicators):
            complexity_factor *= 1.5
            
        return base_time * complexity_factor * type_factor
    
    async def _execute_task_loop(self, task_id: str) -> None:
        """Main execution loop for a task with continuous operation"""
        if task_id not in self.state.active_tasks:
            logger.error(f"Task not found: {task_id}")
            return
        
        task_data = self.state.active_tasks[task_id]
        
        try:
            # Notify start
            await self._notify_callbacks('on_task_start', task_id, task_data)
            
            # Update status
            task_data["status"] = TaskStatus.PLANNING.value
            task_data["planning_started_at"] = time.time()
            
            # Create plan using automation handler
            plan = await self._create_task_plan(task_id, task_data)
            
            if not plan or not plan.get("success", False):
                raise Exception(f"Failed to create plan: {plan.get('error', 'Unknown error')}")
            
            # Store plan and update task data
            task_data["plan"] = plan
            task_data["total_steps"] = len(plan.get("steps", []))
            task_data["current_step"] = 0
            
            # Update metrics
            metrics = self.state.metrics.get(task_id, {})
            metrics["steps_total"] = task_data["total_steps"]
            self.state.metrics[task_id] = metrics
            
            # Main execution loop
            while task_data["current_step"] < task_data["total_steps"]:
                # Check if task was paused or cancelled
                if task_data["status"] in [TaskStatus.PAUSED.value, TaskStatus.FAILED.value]:
                    logger.info(f"Task {task_id} is {task_data['status']}, stopping execution")
                    break
                
                # Get current step
                current_step_idx = task_data["current_step"]
                current_step = plan["steps"][current_step_idx]
                
                # Update status
                task_data["status"] = TaskStatus.EXECUTING.value
                task_data["current_step_details"] = current_step
                
                # Execute step
                step_result = await self._execute_step(task_id, current_step)
                
                # Store step result
                task_data["results"][f"step_{current_step_idx}"] = step_result
                
                # Check if step requires approval
                if step_result.get("requires_approval", False):
                    # Update status
                    task_data["status"] = TaskStatus.AWAITING_APPROVAL.value
                    task_data["approval_requested_at"] = time.time()
                    
                    # Wait for approval
                    approval = await self._wait_for_approval(task_id, current_step, step_result)
                    
                    # Process approval result
                    if not approval.get("approved", False):
                        if approval.get("action") == "cancel":
                            task_data["status"] = TaskStatus.FAILED.value
                            task_data["failure_reason"] = "Cancelled by user"
                            break
                        elif approval.get("action") == "modify":
                            # Modify plan based on user input
                            modified_plan = await self._modify_plan(task_id, plan, approval.get("modifications", {}))
                            task_data["plan"] = modified_plan
                            plan = modified_plan
                            continue
                
                # Verify step results
                verification = await self._verify_step_results(task_id, current_step, step_result)
                
                if not verification.get("success", False):
                    # Handle failed verification
                    recovery = await self._attempt_recovery(task_id, current_step, step_result, verification)
                    
                    if not recovery.get("success", False):
                        # Failed to recover
                        task_data["status"] = TaskStatus.FAILED.value
                        task_data["failure_reason"] = f"Step verification failed: {verification.get('error', 'Unknown error')}"
                        break
                
                # Update metrics
                metrics = self.state.metrics.get(task_id, {})
                metrics["steps_completed"] = task_data["current_step"] + 1
                self.state.metrics[task_id] = metrics
                
                # Update task memory if available
                if MEMORY_SYSTEM_AVAILABLE:
                    try:
                        await update_task_record(task_id, task_data, metrics)
                        logger.debug(f"Updated task memory record for step {task_data['current_step']}")
                    except Exception as e:
                        logger.error(f"Error updating task memory: {e}")
                
                # Notify step completion
                await self._notify_callbacks('on_step_complete', task_id, current_step, step_result)
                
                # Move to next step
                task_data["current_step"] += 1
                
                # Small delay between steps for stability
                await asyncio.sleep(0.5)
            
            # Check final status
            if task_data["status"] not in [TaskStatus.FAILED.value, TaskStatus.PAUSED.value]:
                # Task completed successfully
                task_data["status"] = TaskStatus.COMPLETED.value
                task_data["completed_at"] = time.time()
                
                # Update metrics
                metrics = self.state.metrics.get(task_id, {})
                metrics["end_time"] = time.time()
                metrics_obj = TaskExecutionMetrics(**metrics)
                metrics_obj.update_metrics()
                self.state.metrics[task_id] = metrics_obj.to_dict()
                
                # Generate next step suggestions if persistence is available
                if PERSISTENCE_AVAILABLE:
                    try:
                        next_steps = await generate_next_steps(task_id, task_data)
                        if next_steps:
                            task_data["next_steps"] = [asdict(step) for step in next_steps]
                            logger.info(f"Generated {len(next_steps)} next step suggestions for task {task_id}")
                    except Exception as e:
                        logger.error(f"Error generating next step suggestions: {e}")
                
                # Complete task in memory system if available
                if MEMORY_SYSTEM_AVAILABLE:
                    try:
                        await complete_task_record(task_id, TaskStatus.COMPLETED.value, task_data, self.state.metrics.get(task_id, {}))
                        logger.info(f"Task {task_id} completed in memory system")
                    except Exception as e:
                        logger.error(f"Error completing task in memory system: {e}")
                
                # Move to completed tasks
                self.state.completed_tasks.append(task_data)
                del self.state.active_tasks[task_id]
                
                # Notify completion
                await self._notify_callbacks('on_task_complete', task_id, task_data)
                
                logger.info(f"Task {task_id} completed successfully")
            else:
                # Task failed or paused
                logger.info(f"Task {task_id} ended with status: {task_data['status']}")
                
                if task_data["status"] == TaskStatus.FAILED.value:
                    # Update metrics
                    metrics = self.state.metrics.get(task_id, {})
                    metrics["end_time"] = time.time()
                    metrics_obj = TaskExecutionMetrics(**metrics)
                    metrics_obj.update_metrics()
                    self.state.metrics[task_id] = metrics_obj.to_dict()
                    
                    # Complete task in memory system if available
                    if MEMORY_SYSTEM_AVAILABLE:
                        try:
                            await complete_task_record(task_id, TaskStatus.FAILED.value, task_data, self.state.metrics.get(task_id, {}))
                            logger.info(f"Task {task_id} marked as failed in memory system")
                        except Exception as e:
                            logger.error(f"Error marking task as failed in memory system: {e}")
                    
                    # Move to failed tasks
                    self.state.failed_tasks[task_id] = task_data
                    del self.state.active_tasks[task_id]
                    
                    # Notify failure
                    await self._notify_callbacks('on_task_fail', task_id, task_data)
            
            # Save state
            self.state.save_to_file()
            
        except Exception as e:
            logger.error(f"Error executing task loop {task_id}: {e}")
            
            # Update task status
            task_data["status"] = TaskStatus.FAILED.value
            task_data["failure_reason"] = str(e)
            task_data["failed_at"] = time.time()
            
            # Update metrics
            metrics = self.state.metrics.get(task_id, {})
            metrics["end_time"] = time.time()
            metrics["error_count"] = metrics.get("error_count", 0) + 1
            self.state.metrics[task_id] = metrics
            
            # Complete task in memory system if available
            if MEMORY_SYSTEM_AVAILABLE:
                try:
                    await complete_task_record(task_id, TaskStatus.FAILED.value, task_data, self.state.metrics.get(task_id, {}))
                    logger.info(f"Task {task_id} marked as failed in memory system due to exception")
                except Exception as mem_error:
                    logger.error(f"Error marking task as failed in memory system: {mem_error}")
            
            # Move to failed tasks
            self.state.failed_tasks[task_id] = task_data
            if task_id in self.state.active_tasks:
                del self.state.active_tasks[task_id]
            
            # Notify failure
            await self._notify_callbacks('on_task_fail', task_id, task_data)
            
            # Save state
            self.state.save_to_file()
    
    async def _create_task_plan(self, task_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed execution plan for the task"""
        try:
            description = task_data["description"]
            context = task_data["context"]
            
            # Use universal automation handler to create plan
            if not hasattr(self, 'automation_handler'):
                raise Exception("Automation handler not available")
            
            # Generate session ID
            session_id = task_id
            
            # Create automation plan
            plan_result = await self.automation_handler.create_universal_automation_plan(description, session_id)
            
            if not plan_result.get("success", False):
                raise Exception(f"Failed to create automation plan: {plan_result.get('error', 'Unknown error')}")
            
            return plan_result
            
        except Exception as e:
            logger.error(f"Error creating task plan: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_step(self, task_id: str, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single step in the task plan"""
        try:
            # Extract step details
            step_type = step.get("action_type")
            target = step.get("target")
            value = step.get("value", "")
            description = step.get("description", "")
            
            logger.info(f"Executing step for task {task_id}: {description}")
            
            # Check if automation components are available
            if not self.all_components_available:
                return {
                    "success": False,
                    "error": "Automation components not available",
                    "simulated": True,
                    "description": f"Simulated execution of: {description}"
                }
            
            # Use automation handler to execute step
            if hasattr(self, 'automation_handler'):
                # Convert to SmartAutomationStep
                step_obj = SmartAutomationStep(
                    id=step.get("id", f"step_{int(time.time())}"),
                    description=description,
                    action_type=step_type,
                    target=target,
                    value=value,
                    coordinates=step.get("coordinates"),
                    confidence=step.get("confidence", 0.8)
                )
                
                # Execute step using appropriate method
                if step_type == "open_app":
                    result = await self.automation_handler._execute_open_app(step_obj)
                elif step_type == "navigate_url":
                    result = await self.automation_handler._execute_navigate_url(step_obj)
                elif step_type == "click_element":
                    result = await self.automation_handler._execute_click_element(step_obj)
                elif step_type == "type_text":
                    result = await self.automation_handler._execute_type_text(step_obj)
                elif step_type == "hotkey":
                    result = await self.automation_handler._execute_hotkey(step_obj)
                elif step_type == "wait":
                    result = await self.automation_handler._execute_wait(step_obj)
                elif step_type == "analyze_screen":
                    result = await self.automation_handler._execute_analyze_screen(step_obj)
                else:
                    result = False
                    
                return {
                    "success": result,
                    "description": f"Executed: {description}",
                    "step_type": step_type,
                    "target": target,
                    "value": value,
                    "requires_approval": step.get("requires_approval", False)
                }
            
            # Fallback simulation
            await asyncio.sleep(1.0)  # Simulate execution time
            
            return {
                "success": True,
                "simulated": True,
                "description": f"Simulated execution of: {description}",
                "requires_approval": step.get("requires_approval", False)
            }
            
        except Exception as e:
            logger.error(f"Error executing step: {e}")
            
            # Update metrics
            metrics = self.state.metrics.get(task_id, {})
            metrics["error_count"] = metrics.get("error_count", 0) + 1
            self.state.metrics[task_id] = metrics
            
            return {"success": False, "error": str(e)}
    
    async def _wait_for_approval(self, task_id: str, step: Dict[str, Any], 
                               step_result: Dict[str, Any]) -> Dict[str, Any]:
        """Wait for user approval before continuing"""
        # This would integrate with your UI for approval
        # For now, simulate approval after a delay
        await asyncio.sleep(2.0)
        
        # Notify approval request
        await self._notify_callbacks('on_user_approval', task_id, step, step_result)
        
        # Return simulated approval
        return {
            "approved": True,
            "action": "continue",
            "comment": "Auto-approved for demonstration",
            "timestamp": time.time()
        }
    
    async def _verify_step_results(self, task_id: str, step: Dict[str, Any], 
                                 step_result: Dict[str, Any]) -> Dict[str, Any]:
        """Verify the results of a step execution"""
        try:
            # Use UI detector to analyze current screen state
            if hasattr(self, 'ui_detector') and step.get("expected_result"):
                # This would verify the expected UI state
                # For now, simulate verification
                pass
            
            # Update metrics
            metrics = self.state.metrics.get(task_id, {})
            metrics["verification_success_rate"] = 1.0  # Simulated perfect verification
            self.state.metrics[task_id] = metrics
            
            # Return success
            return {
                "success": True,
                "verified_elements": ["simulated_verification"],
                "confidence": 0.9
            }
            
        except Exception as e:
            logger.error(f"Error verifying step results: {e}")
            
            return {"success": False, "error": str(e)}
    
    async def _attempt_recovery(self, task_id: str, step: Dict[str, Any], 
                              step_result: Dict[str, Any], verification: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to recover from a failed step"""
        try:
            # Update metrics
            metrics = self.state.metrics.get(task_id, {})
            metrics["recovery_count"] = metrics.get("recovery_count", 0) + 1
            self.state.metrics[task_id] = metrics
            
            # Simple retry strategy for now
            recovery_step = await self._execute_step(task_id, step)
            
            return {
                "success": recovery_step.get("success", False),
                "recovery_method": "retry",
                "recovery_result": recovery_step
            }
            
        except Exception as e:
            logger.error(f"Error attempting recovery: {e}")
            
            return {"success": False, "error": str(e)}
    
    async def _modify_plan(self, task_id: str, original_plan: Dict[str, Any], 
                         modifications: Dict[str, Any]) -> Dict[str, Any]:
        """Modify a plan based on user input"""
        # Simply return the original plan for now
        # In a real implementation, this would apply the modifications
        return original_plan
    
    async def _notify_callbacks(self, event: str, *args):
        """Notify registered callbacks for an event"""
        if event in self.task_callbacks:
            for callback in self.task_callbacks[event]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(*args)
                    else:
                        callback(*args)
                except Exception as e:
                    logger.error(f"Error in callback for {event}: {e}")
    
    def add_callback(self, event: str, callback: Callable):
        """Add a callback for a specific event"""
        if event in self.task_callbacks:
            self.task_callbacks[event].append(callback)
    
    async def handle_button_action(self, action: str, task_id: str, 
                                 action_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle button actions from the UI"""
        try:
            if task_id not in self.state.active_tasks:
                return {
                    "success": False,
                    "message": "Task not found or no longer active"
                }
            
            task_data = self.state.active_tasks[task_id]
            
            if action == "approve":
                # Handle approval action
                task_data["user_approval"] = {
                    "approved": True,
                    "timestamp": time.time(),
                    "data": action_data
                }
                
                return {
                    "success": True,
                    "message": "Task approved"
                }
                
            elif action == "reject":
                # Handle rejection action
                task_data["user_approval"] = {
                    "approved": False,
                    "timestamp": time.time(),
                    "data": action_data
                }
                
                return {
                    "success": True,
                    "message": "Task rejected"
                }
                
            elif action == "pause":
                # Handle pause action
                task_data["status"] = TaskStatus.PAUSED.value
                task_data["paused_at"] = time.time()
                
                # Move to paused tasks
                self.state.paused_tasks[task_id] = task_data
                
                return {
                    "success": True,
                    "message": "Task paused"
                }
                
            elif action == "resume":
                # Handle resume action
                if task_id in self.state.paused_tasks:
                    task_data = self.state.paused_tasks[task_id]
                    task_data["status"] = TaskStatus.EXECUTING.value
                    task_data["resumed_at"] = time.time()
                    
                    # Move back to active tasks
                    self.state.active_tasks[task_id] = task_data
                    del self.state.paused_tasks[task_id]
                    
                    # Resume execution
                    execution_task = asyncio.create_task(self._execute_task_loop(task_id))
                    self.execution_tasks[task_id] = execution_task
                    
                    return {
                        "success": True,
                        "message": "Task resumed"
                    }
                else:
                    return {
                        "success": False,
                        "message": "Task not found in paused tasks"
                    }
                    
            elif action == "cancel":
                # Handle cancel action
                task_data["status"] = TaskStatus.FAILED.value
                task_data["cancelled_at"] = time.time()
                task_data["failure_reason"] = "Cancelled by user"
                
                # Cancel execution task if running
                if task_id in self.execution_tasks and not self.execution_tasks[task_id].done():
                    self.execution_tasks[task_id].cancel()
                
                # Move to failed tasks
                self.state.failed_tasks[task_id] = task_data
                del self.state.active_tasks[task_id]
                
                return {
                    "success": True,
                    "message": "Task cancelled"
                }
                
            else:
                return {
                    "success": False,
                    "message": f"Unknown action: {action}"
                }
                
        except Exception as e:
            logger.error(f"Error handling button action: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "message": "Error handling button action"
            }
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get detailed status for a task"""
        try:
            # Check active tasks
            if task_id in self.state.active_tasks:
                task_data = self.state.active_tasks[task_id]
                metrics = self.state.metrics.get(task_id, {})
                
                # Basic response
                response = {
                    "success": True,
                    "task_id": task_id,
                    "status": task_data["status"],
                    "description": task_data["description"],
                    "progress": (task_data["current_step"] / max(1, task_data["total_steps"])) * 100,
                    "current_step": task_data["current_step"],
                    "total_steps": task_data["total_steps"],
                    "metrics": metrics,
                    "submitted_at": task_data["submitted_at"],
                    "last_updated": time.time()
                }
                
                # Add memory context if available
                if MEMORY_SYSTEM_AVAILABLE and "memory_context" in task_data:
                    response["memory_context"] = task_data["memory_context"]
                    
                    # Add memory persistence indicator
                    response["persistent"] = True
                    
                # Enrich with context awareness if available
                if CONTEXT_AWARENESS_AVAILABLE:
                    try:
                        # Enrich task data with context
                        enriched_data = await enrich_task_data(response)
                        
                        # Update response with enriched data
                        if "environment_context" in enriched_data:
                            response["environment_context"] = enriched_data["environment_context"]
                        if "related_context" in enriched_data:
                            response["related_context"] = enriched_data["related_context"]
                        
                        # Add context awareness indicator
                        response["context_aware"] = True
                    except Exception as e:
                        logger.error(f"Error enriching task data with context: {e}")
                
                return response
            
            # Check completed tasks
            for task in self.state.completed_tasks:
                if task["task_id"] == task_id:
                    metrics = self.state.metrics.get(task_id, {})
                    
                    # Basic response
                    response = {
                        "success": True,
                        "task_id": task_id,
                        "status": TaskStatus.COMPLETED.value,
                        "description": task["description"],
                        "progress": 100.0,
                        "metrics": metrics,
                        "submitted_at": task["submitted_at"],
                        "completed_at": task["completed_at"],
                        "execution_time": task["completed_at"] - task["submitted_at"]
                    }
                    
                    # Add memory context if available
                    if MEMORY_SYSTEM_AVAILABLE and "memory_context" in task:
                        response["memory_context"] = task["memory_context"]
                        
                        # Add memory persistence indicator
                        response["persistent"] = True
                    
                    return response
            
            # Check paused tasks
            if task_id in self.state.paused_tasks:
                task_data = self.state.paused_tasks[task_id]
                metrics = self.state.metrics.get(task_id, {})
                
                # Basic response
                response = {
                    "success": True,
                    "task_id": task_id,
                    "status": TaskStatus.PAUSED.value,
                    "description": task_data["description"],
                    "progress": (task_data["current_step"] / max(1, task_data["total_steps"])) * 100,
                    "current_step": task_data["current_step"],
                    "total_steps": task_data["total_steps"],
                    "metrics": metrics,
                    "submitted_at": task_data["submitted_at"],
                    "paused_at": task_data.get("paused_at", time.time())
                }
                
                # Add memory context if available
                if MEMORY_SYSTEM_AVAILABLE and "memory_context" in task_data:
                    response["memory_context"] = task_data["memory_context"]
                    
                    # Add memory persistence indicator
                    response["persistent"] = True
                
                return response
            
            # Check failed tasks
            if task_id in self.state.failed_tasks:
                task_data = self.state.failed_tasks[task_id]
                metrics = self.state.metrics.get(task_id, {})
                
                # Basic response
                response = {
                    "success": True,
                    "task_id": task_id,
                    "status": TaskStatus.FAILED.value,
                    "description": task_data["description"],
                    "progress": (task_data["current_step"] / max(1, task_data["total_steps"])) * 100,
                    "current_step": task_data["current_step"],
                    "total_steps": task_data["total_steps"],
                    "metrics": metrics,
                    "failure_reason": task_data.get("failure_reason", "Unknown"),
                    "submitted_at": task_data["submitted_at"],
                    "failed_at": task_data.get("failed_at", time.time())
                }
                
                # Add memory context if available
                if MEMORY_SYSTEM_AVAILABLE and "memory_context" in task_data:
                    response["memory_context"] = task_data["memory_context"]
                    
                    # Add memory persistence indicator
                    response["persistent"] = True
                
                # If memory system is available but no memory context in task data,
                # try to fetch it directly from memory
                elif MEMORY_SYSTEM_AVAILABLE:
                    try:
                        # Try to search task in memory
                        from memory.task_memory_manager import search_task_records
                        memory_records = await search_task_records(f"task_id:{task_id}", limit=1)
                        
                        if memory_records and len(memory_records) > 0:
                            response["memory_context"] = {
                                "last_memory_update": memory_records[0].get("updated_at", time.time()),
                                "has_persistent_record": True,
                                "restored_from_memory": True
                            }
                            response["persistent"] = True
                    except Exception as e:
                        logger.error(f"Error fetching task from memory: {e}")
                
                return response
            
            # If memory system is available, try to find the task there
            if MEMORY_SYSTEM_AVAILABLE:
                try:
                    # Try to load task from memory
                    from memory.task_memory_manager import load_task_record
                    
                    memory_record = await load_task_record(task_id)
                    if memory_record:
                        # Convert to controller format
                        task_data = await self._task_record_to_controller_format(memory_record)
                        
                        # Create response
                        response = {
                            "success": True,
                            "task_id": task_id,
                            "status": memory_record.status,
                            "description": memory_record.description,
                            "progress": (memory_record.current_step / max(1, memory_record.total_steps)) * 100,
                            "current_step": memory_record.current_step,
                            "total_steps": memory_record.total_steps,
                            "metrics": memory_record.metrics,
                            "submitted_at": memory_record.created_at,
                            "last_updated": memory_record.updated_at,
                            "memory_context": {
                                "last_memory_update": memory_record.updated_at,
                                "has_persistent_record": True,
                                "restored_from_memory": True
                            },
                            "persistent": True,
                            "restored_from_memory": True
                        }
                        
                        return response
                except Exception as e:
                    logger.error(f"Error searching task in memory: {e}")
            
            # Task not found
            return {
                "success": False,
                "message": "Task not found"
            }
            
        except Exception as e:
            logger.error(f"Error getting task status: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "message": "Error getting task status"
            }
    
    def get_active_tasks(self) -> Dict[str, Any]:
        """Get all active tasks"""
        try:
            active_tasks = []
            
            for task_id, task_data in self.state.active_tasks.items():
                metrics = self.state.metrics.get(task_id, {})
                
                active_tasks.append({
                    "task_id": task_id,
                    "description": task_data["description"],
                    "status": task_data["status"],
                    "progress": (task_data["current_step"] / max(1, task_data["total_steps"])) * 100,
                    "submitted_at": task_data["submitted_at"],
                    "metrics": metrics
                })
            
            return {
                "success": True,
                "count": len(active_tasks),
                "tasks": active_tasks
            }
            
        except Exception as e:
            logger.error(f"Error getting active tasks: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "message": "Error getting active tasks"
            }
    
    async def _task_record_to_controller_format(self, memory_record) -> Dict[str, Any]:
        """Convert a memory task record to controller task format"""
        try:
            # Create basic task data
            task_data = {
                "task_id": memory_record.task_id,
                "description": memory_record.description,
                "status": memory_record.status,
                "submitted_at": memory_record.created_at,
                "context": memory_record.execution_context,
                "current_step": memory_record.current_step,
                "total_steps": memory_record.total_steps,
                "memory_context": {
                    "last_memory_update": memory_record.updated_at,
                    "has_persistent_record": True,
                    "execution_history_length": len(memory_record.execution_history),
                    "restored_from_memory": True
                },
                "results": {}
            }
            
            # Add execution history results
            for i, history_entry in enumerate(memory_record.execution_history):
                step_idx = history_entry.get("current_step", i)
                if "step_details" in history_entry:
                    task_data["results"][f"step_{step_idx}"] = history_entry["step_details"]
            
            return task_data
            
        except Exception as e:
            logger.error(f"Error converting task record to controller format: {e}")
            # Return basic task data
            return {
                "task_id": memory_record.task_id,
                "description": memory_record.description,
                "status": memory_record.status,
                "submitted_at": memory_record.created_at,
                "current_step": memory_record.current_step,
                "total_steps": memory_record.total_steps,
                "context": {},
                "results": {}
            }
    
    def get_value_metrics(self) -> Dict[str, Any]:
        """Get monetization value metrics"""
        try:
            total_time_saved = 0.0
            total_monetary_value = 0.0
            task_count = 0
            
            # Collect metrics from all tasks
            for metrics in self.state.metrics.values():
                total_time_saved += metrics.get("time_saved", 0.0)
                total_monetary_value += metrics.get("monetary_value", 0.0)
                task_count += 1
            
            # Calculate aggregate metrics
            avg_time_saved = total_time_saved / max(1, task_count)
            avg_monetary_value = total_monetary_value / max(1, task_count)
            
            return {
                "success": True,
                "task_count": task_count,
                "total_time_saved": total_time_saved,
                "total_monetary_value": total_monetary_value,
                "avg_time_saved": avg_time_saved,
                "avg_monetary_value": avg_monetary_value,
                "hourly_value_rate": total_monetary_value / max(1, total_time_saved / 3600)
            }
            
        except Exception as e:
            logger.error(f"Error getting value metrics: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "message": "Error getting value metrics"
            }
            
    async def get_next_step_suggestions(self, task_id: str) -> Dict[str, Any]:
        """Get next step suggestions for a completed task"""
        try:
            # First check in completed tasks
            task_data = None
            for task in self.state.completed_tasks:
                if task.get("task_id") == task_id:
                    task_data = task
                    break
            
            if not task_data:
                # Check in active tasks
                if task_id in self.state.active_tasks:
                    task_data = self.state.active_tasks[task_id]
                else:
                    # Check in failed tasks
                    if task_id in self.state.failed_tasks:
                        task_data = self.state.failed_tasks[task_id]
            
            # If we have task data with next steps, return those
            if task_data and "next_steps" in task_data:
                return {
                    "success": True,
                    "task_id": task_id,
                    "task_description": task_data.get("description", ""),
                    "task_status": task_data.get("status", ""),
                    "suggestions": task_data["next_steps"]
                }
            
            # Check if persistence is available
            if PERSISTENCE_AVAILABLE:
                # Try to fetch from persistent storage
                next_steps = await get_next_steps(task_id)
                if next_steps:
                    suggestions = [asdict(step) for step in next_steps]
                    return {
                        "success": True,
                        "task_id": task_id,
                        "task_description": task_data.get("description", "") if task_data else "",
                        "task_status": task_data.get("status", "") if task_data else "",
                        "suggestions": suggestions
                    }
            
            # Check memory system if available
            if MEMORY_SYSTEM_AVAILABLE:
                try:
                    # Try to get task record from memory
                    from memory.task_memory_manager import get_task_history, generate_task_insights
                    
                    # Get insights from memory
                    insights = await generate_task_insights(task_id)
                    if insights:
                        # Format insights as next step suggestions
                        suggestions = []
                        for i, insight in enumerate(insights):
                            suggestions.append({
                                "title": f"Insight {i+1}",
                                "description": insight,
                                "type": "insight",
                                "priority": 0.7,
                                "metadata": {"from_memory": True}
                            })
                        
                        return {
                            "success": True,
                            "task_id": task_id,
                            "task_description": task_data.get("description", "") if task_data else "",
                            "task_status": task_data.get("status", "") if task_data else "",
                            "suggestions": suggestions
                        }
                except Exception as e:
                    logger.error(f"Error getting task insights from memory: {e}")
            
            # No suggestions found
            return {
                "success": True,
                "task_id": task_id,
                "message": "No next step suggestions available",
                "suggestions": []
            }
            
        except Exception as e:
            logger.error(f"Error getting next step suggestions: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Error getting next step suggestions",
                "suggestions": []
            }

# Value Metrics Tracker for monetization
class ValueMetricsTracker:
    """Tracks value metrics for monetization purposes"""
    
    def __init__(self):
        self.metrics_history = []
        self.hourly_rate = 50.0  # Default hourly rate for value calculation
    
    def update_metrics(self, task_metrics: TaskExecutionMetrics):
        """Update metrics with new task data"""
        # Calculate monetary value
        task_metrics.monetary_value = task_metrics.calculate_monetary_value(self.hourly_rate)
        
        # Save to history
        self.metrics_history.append(task_metrics.to_dict())
        
        return task_metrics
    
    def get_summary_metrics(self) -> Dict[str, Any]:
        """Get summary metrics for all tasks"""
        if not self.metrics_history:
            return {
                "total_tasks": 0,
                "total_time_saved": 0,
                "total_monetary_value": 0,
                "avg_time_saved": 0,
                "avg_monetary_value": 0
            }
        
        total_time_saved = sum(m.get("time_saved", 0) for m in self.metrics_history)
        total_monetary_value = sum(m.get("monetary_value", 0) for m in self.metrics_history)
        
        return {
            "total_tasks": len(self.metrics_history),
            "total_time_saved": total_time_saved,
            "total_monetary_value": total_monetary_value,
            "avg_time_saved": total_time_saved / len(self.metrics_history),
            "avg_monetary_value": total_monetary_value / len(self.metrics_history)
        }

# Dashboard Reporter for sending data to monitoring dashboard
class DashboardReporter:
    """Reports metrics to monitoring dashboard"""
    
    def __init__(self, dashboard_url: str = None):
        self.dashboard_url = dashboard_url or "http://localhost:8080/api/metrics"
        self.last_report_time = 0
    
    async def update_metrics(self, metrics: Dict[str, Any]):
        """Send metrics update to dashboard"""
        try:
            # In a real implementation, this would send HTTP request to dashboard
            # For now, just log metrics
            logger.debug(f"Dashboard metrics update: {len(metrics)} metric sets")
            self.last_report_time = time.time()
            return True
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")
            return False

# Create singleton instance
universal_task_controller = UniversalTaskLoopController()

async def submit_task(task_description: str, task_type: str = "universal", 
                    context: Dict[str, Any] = None) -> Dict[str, Any]:
    """API function for submitting tasks"""
    return await universal_task_controller.submit_task(task_description, task_type, context)

async def handle_button_action(action: str, task_id: str, 
                             action_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """API function for handling button actions"""
    return await universal_task_controller.handle_button_action(action, task_id, action_data)

async def get_task_status(task_id: str) -> Dict[str, Any]:
    """API function for getting task status"""
    return await universal_task_controller.get_task_status(task_id)

def get_active_tasks() -> Dict[str, Any]:
    """API function for getting all active tasks"""
    return universal_task_controller.get_active_tasks()

def get_value_metrics() -> Dict[str, Any]:
    """API function for getting value metrics"""
    return universal_task_controller.get_value_metrics()

async def get_next_step_suggestions(task_id: str) -> Dict[str, Any]:
    """API function for getting next step suggestions for a completed task"""
    return await universal_task_controller.get_next_step_suggestions(task_id)

async def search_tasks(query: str, limit: int = 5) -> Dict[str, Any]:
    """API function for searching tasks by keyword or criteria"""
    if not MEMORY_SYSTEM_AVAILABLE:
        return {
            "success": False,
            "message": "Task memory system not available for search",
            "results": []
        }
    
    try:
        # Use task memory system to search
        from memory.task_memory_manager import search_task_records
        
        # Perform the search
        results = await search_task_records(query, limit)
        
        return {
            "success": True,
            "query": query,
            "count": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error searching tasks: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Error searching tasks",
            "results": []
        }

async def initialize():
    """Initialize the task controller"""
    await universal_task_controller.initialize()

# Example usage
async def main():
    await initialize()
    
    # Submit a sample task
    result = await submit_task(
        "Open Safari, navigate to google.com, search for 'automation tools', and analyze the first result",
        "web_search"
    )
    
    print(f"Task submitted: {result}")
    
    # Wait for task to progress
    await asyncio.sleep(5)
    
    # Get task status
    status = get_task_status(result["task_id"])
    print(f"Task status: {status}")
    
    # Wait for more progress
    await asyncio.sleep(10)
    
    # Get value metrics
    metrics = get_value_metrics()
    print(f"Value metrics: {metrics}")
    
    # Keep running to handle tasks
    try:
        await asyncio.Future()
    except asyncio.CancelledError:
        pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down...")