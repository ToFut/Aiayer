#!/usr/bin/env python3
"""
TaskOrchestrator - Enterprise-grade task coordination system.

This orchestrator manages complex multi-step tasks across multiple agents,
providing intelligent routing, dependency management, and execution optimization.
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable, Union
import networkx as nx
from concurrent.futures import ThreadPoolExecutor

from .agent_base import AgentBase, AgentCapability, AgentState

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRY = "retry"


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class TaskStep:
    """Individual step in a complex task."""
    step_id: str
    agent_capability: AgentCapability
    action: str
    parameters: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    timeout_seconds: int = 60
    retry_count: int = 0
    max_retries: int = 3
    result: Optional[Any] = None
    error: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None


@dataclass
class TaskDefinition:
    """Complete task definition with steps and metadata."""
    task_id: str
    name: str
    description: str
    steps: List[TaskStep]
    priority: TaskPriority = TaskPriority.NORMAL
    timeout_seconds: int = 300
    created_at: float = field(default_factory=time.time)
    created_by: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Execution tracking
    status: TaskStatus = TaskStatus.PENDING
    current_step: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class TaskOrchestrator:
    """
    Enterprise-grade task orchestration system.
    
    Features:
    - Complex multi-step task execution
    - Intelligent agent routing
    - Dependency management
    - Parallel execution optimization
    - Retry and error handling
    - Priority-based scheduling
    - Real-time monitoring
    - Scalable architecture
    """
    
    def __init__(self, max_concurrent_tasks: int = 10):
        """Initialize the task orchestrator."""
        self.max_concurrent_tasks = max_concurrent_tasks
        self.agents: Dict[str, AgentBase] = {}
        self.capability_map: Dict[AgentCapability, List[str]] = {}
        
        # Task management
        self.tasks: Dict[str, TaskDefinition] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.task_history: List[TaskDefinition] = []
        
        # Execution control
        self.is_running = False
        self.executor_task: Optional[asyncio.Task] = None
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        
        # Dependencies and scheduling
        self.dependency_graph = nx.DiGraph()
        self.scheduler_task: Optional[asyncio.Task] = None
        
        # Event callbacks
        self.task_callbacks: Dict[str, List[Callable]] = {
            'on_task_start': [],
            'on_task_complete': [],
            'on_task_fail': [],
            'on_step_complete': []
        }
        
        logger.info("TaskOrchestrator initialized")
    
    # ========== Agent Management ==========
    
    def register_agent(self, agent: AgentBase) -> None:
        """Register an agent with the orchestrator."""
        self.agents[agent.agent_id] = agent
        
        # Update capability mapping
        for capability in agent.config.capabilities:
            if capability not in self.capability_map:
                self.capability_map[capability] = []
            self.capability_map[capability].append(agent.agent_id)
        
        logger.info(f"Registered agent: {agent.config.name} ({agent.agent_id[:8]})")
    
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent."""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            
            # Remove from capability mapping
            for capability in agent.config.capabilities:
                if capability in self.capability_map:
                    self.capability_map[capability].remove(agent_id)
                    if not self.capability_map[capability]:
                        del self.capability_map[capability]
            
            del self.agents[agent_id]
            logger.info(f"Unregistered agent: {agent_id[:8]}")
    
    def get_agents_by_capability(self, capability: AgentCapability) -> List[AgentBase]:
        """Get all agents with a specific capability."""
        agent_ids = self.capability_map.get(capability, [])
        return [self.agents[agent_id] for agent_id in agent_ids if agent_id in self.agents]
    
    def select_best_agent(self, capability: AgentCapability) -> Optional[AgentBase]:
        """Select the best available agent for a capability."""
        candidates = self.get_agents_by_capability(capability)
        
        if not candidates:
            return None
        
        # Filter to running agents
        available = [agent for agent in candidates if agent.state == AgentState.RUNNING]
        
        if not available:
            return None
        
        # Select agent with lowest load (fewest active tasks)
        return min(available, key=lambda a: len(a.active_tasks))
    
    # ========== Task Management ==========
    
    async def submit_task(self, task_def: TaskDefinition) -> str:
        """Submit a task for execution."""
        # Validate task definition
        self._validate_task(task_def)
        
        # Build dependency graph
        self._build_dependency_graph(task_def)
        
        # Store task
        self.tasks[task_def.task_id] = task_def
        
        # Queue for execution
        await self.task_queue.put(task_def.task_id)
        
        logger.info(f"Submitted task: {task_def.name} ({task_def.task_id[:8]})")
        return task_def.task_id
    
    def _validate_task(self, task_def: TaskDefinition) -> None:
        """Validate task definition."""
        if not task_def.steps:
            raise ValueError("Task must have at least one step")
        
        # Check if required capabilities are available
        for step in task_def.steps:
            if step.agent_capability not in self.capability_map:
                raise ValueError(f"No agents available for capability: {step.agent_capability}")
        
        # Validate dependencies
        step_ids = {step.step_id for step in task_def.steps}
        for step in task_def.steps:
            for dep_id in step.dependencies:
                if dep_id not in step_ids:
                    raise ValueError(f"Invalid dependency: {dep_id} not found in task steps")
    
    def _build_dependency_graph(self, task_def: TaskDefinition) -> None:
        """Build dependency graph for task execution."""
        graph_id = f"task_{task_def.task_id}"
        
        # Add nodes
        for step in task_def.steps:
            self.dependency_graph.add_node(f"{graph_id}_{step.step_id}", step=step)
        
        # Add edges for dependencies
        for step in task_def.steps:
            for dep_id in step.dependencies:
                self.dependency_graph.add_edge(
                    f"{graph_id}_{dep_id}",
                    f"{graph_id}_{step.step_id}"
                )
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task."""
        if task_id not in self.tasks:
            return False
        
        task_def = self.tasks[task_id]
        
        # Cancel if running
        if task_id in self.active_tasks:
            self.active_tasks[task_id].cancel()
        
        # Update status
        task_def.status = TaskStatus.CANCELLED
        task_def.end_time = time.time()
        
        logger.info(f"Cancelled task: {task_def.name} ({task_id[:8]})")
        return True
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed task status."""
        if task_id not in self.tasks:
            return None
        
        task_def = self.tasks[task_id]
        
        # Calculate progress
        total_steps = len(task_def.steps)
        completed_steps = sum(1 for step in task_def.steps if step.status == TaskStatus.COMPLETED)
        progress = (completed_steps / total_steps) * 100 if total_steps > 0 else 0
        
        return {
            'task_id': task_id,
            'name': task_def.name,
            'status': task_def.status.value,
            'progress': progress,
            'current_step': task_def.current_step,
            'steps': [
                {
                    'step_id': step.step_id,
                    'action': step.action,
                    'status': step.status.value,
                    'duration': (step.end_time - step.start_time) if step.start_time and step.end_time else None,
                    'error': step.error
                }
                for step in task_def.steps
            ],
            'created_at': task_def.created_at,
            'start_time': task_def.start_time,
            'end_time': task_def.end_time,
            'duration': (task_def.end_time - task_def.start_time) if task_def.start_time and task_def.end_time else None
        }
    
    # ========== Execution Engine ==========
    
    async def start(self) -> None:
        """Start the task orchestrator."""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Start task executor
        self.executor_task = asyncio.create_task(self._task_executor())
        
        # Start scheduler
        self.scheduler_task = asyncio.create_task(self._task_scheduler())
        
        logger.info("TaskOrchestrator started")
    
    async def stop(self) -> None:
        """Stop the task orchestrator."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Cancel active tasks
        for task_id, task in self.active_tasks.items():
            task.cancel()
            logger.info(f"Cancelled active task: {task_id[:8]}")
        
        # Stop executor and scheduler
        if self.executor_task:
            self.executor_task.cancel()
        if self.scheduler_task:
            self.scheduler_task.cancel()
        
        logger.info("TaskOrchestrator stopped")
    
    async def _task_executor(self) -> None:
        """Main task execution loop."""
        while self.is_running:
            try:
                # Get next task from queue
                task_id = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                if task_id in self.tasks:
                    # Execute task
                    task_def = self.tasks[task_id]
                    execution_task = asyncio.create_task(self._execute_task(task_def))
                    self.active_tasks[task_id] = execution_task
                    
                    # Don't await here - let tasks run concurrently
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in task executor: {e}")
    
    async def _task_scheduler(self) -> None:
        """Intelligent task scheduling loop."""
        while self.is_running:
            try:
                await asyncio.sleep(1.0)  # Check every second
                
                # Clean up completed tasks
                completed_tasks = []
                for task_id, task in self.active_tasks.items():
                    if task.done():
                        completed_tasks.append(task_id)
                
                for task_id in completed_tasks:
                    del self.active_tasks[task_id]
                
                # Priority-based task reordering could be implemented here
                
            except Exception as e:
                logger.error(f"Error in task scheduler: {e}")
    
    async def _execute_task(self, task_def: TaskDefinition) -> None:
        """Execute a complete task with all its steps."""
        async with self.semaphore:  # Limit concurrent tasks
            try:
                task_def.status = TaskStatus.RUNNING
                task_def.start_time = time.time()
                
                # Notify callbacks
                await self._notify_callbacks('on_task_start', task_def)
                
                logger.info(f"Starting task execution: {task_def.name}")
                
                # Execute steps based on dependency order
                await self._execute_steps_in_order(task_def)
                
                # Task completed successfully
                task_def.status = TaskStatus.COMPLETED
                task_def.end_time = time.time()
                
                # Collect results
                task_def.result = {
                    step.step_id: step.result for step in task_def.steps
                    if step.result is not None
                }
                
                # Notify callbacks
                await self._notify_callbacks('on_task_complete', task_def)
                
                logger.info(f"Task completed: {task_def.name} in {task_def.end_time - task_def.start_time:.2f}s")
                
            except Exception as e:
                task_def.status = TaskStatus.FAILED
                task_def.end_time = time.time()
                task_def.error = str(e)
                
                # Notify callbacks
                await self._notify_callbacks('on_task_fail', task_def)
                
                logger.error(f"Task failed: {task_def.name} - {e}")
                
            finally:
                # Move to history
                self.task_history.append(task_def)
                
                # Clean up dependency graph
                self._cleanup_task_dependencies(task_def.task_id)
    
    async def _execute_steps_in_order(self, task_def: TaskDefinition) -> None:
        """Execute task steps in dependency order."""
        graph_id = f"task_{task_def.task_id}"
        
        # Get topological order of steps
        try:
            step_order = list(nx.topological_sort(self.dependency_graph.subgraph(
                [f"{graph_id}_{step.step_id}" for step in task_def.steps]
            )))
        except nx.NetworkXError:
            raise ValueError("Circular dependency detected in task steps")
        
        # Execute steps
        for step_node in step_order:
            step_id = step_node.split('_', 2)[2]  # Extract step_id from node name
            step = next(s for s in task_def.steps if s.step_id == step_id)
            
            task_def.current_step = step_id
            await self._execute_step(step, task_def)
    
    async def _execute_step(self, step: TaskStep, task_def: TaskDefinition) -> None:
        """Execute a single task step."""
        step.status = TaskStatus.RUNNING
        step.start_time = time.time()
        
        try:
            # Select agent for this step
            agent = self.select_best_agent(step.agent_capability)
            if not agent:
                raise RuntimeError(f"No available agent for capability: {step.agent_capability}")
            
            logger.info(f"Executing step: {step.step_id} on agent {agent.agent_id[:8]}")
            
            # Prepare task data for agent
            agent_task_data = {
                'action': step.action,
                'parameters': step.parameters,
                'step_id': step.step_id,
                'task_id': task_def.task_id,
                'context': {
                    'task_name': task_def.name,
                    'previous_results': {
                        s.step_id: s.result for s in task_def.steps
                        if s.result is not None and s.step_id != step.step_id
                    }
                }
            }
            
            # Execute step on agent
            agent_task_id = await agent.execute_task(agent_task_data)
            
            # Wait for completion with timeout
            start_wait = time.time()
            while True:
                task_status = agent.get_task_status(agent_task_id)
                
                if task_status == "completed":
                    step.result = agent.get_task_result(agent_task_id)
                    break
                elif task_status in ["cancelled", "unknown"]:
                    raise RuntimeError(f"Agent task failed: {task_status}")
                
                # Check timeout
                if time.time() - start_wait > step.timeout_seconds:
                    raise asyncio.TimeoutError(f"Step timeout: {step.step_id}")
                
                await asyncio.sleep(0.1)  # Small delay
            
            step.status = TaskStatus.COMPLETED
            step.end_time = time.time()
            
            # Notify callbacks
            await self._notify_callbacks('on_step_complete', step, task_def)
            
            logger.info(f"Step completed: {step.step_id} in {step.end_time - step.start_time:.2f}s")
            
        except Exception as e:
            step.status = TaskStatus.FAILED
            step.end_time = time.time()
            step.error = str(e)
            
            # Retry logic
            if step.retry_count < step.max_retries:
                step.retry_count += 1
                step.status = TaskStatus.RETRY
                logger.warning(f"Retrying step: {step.step_id} (attempt {step.retry_count})")
                await asyncio.sleep(2 ** step.retry_count)  # Exponential backoff
                await self._execute_step(step, task_def)
            else:
                logger.error(f"Step failed: {step.step_id} - {e}")
                raise
    
    def _cleanup_task_dependencies(self, task_id: str) -> None:
        """Clean up dependency graph for completed task."""
        graph_id = f"task_{task_id}"
        nodes_to_remove = [node for node in self.dependency_graph.nodes() if node.startswith(graph_id)]
        self.dependency_graph.remove_nodes_from(nodes_to_remove)
    
    # ========== Event System ==========
    
    def add_callback(self, event: str, callback: Callable) -> None:
        """Add event callback."""
        if event in self.task_callbacks:
            self.task_callbacks[event].append(callback)
    
    async def _notify_callbacks(self, event: str, *args) -> None:
        """Notify event callbacks."""
        if event in self.task_callbacks:
            for callback in self.task_callbacks[event]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(*args)
                    else:
                        callback(*args)
                except Exception as e:
                    logger.error(f"Error in callback for {event}: {e}")
    
    # ========== Monitoring and Statistics ==========
    
    def get_orchestrator_status(self) -> Dict[str, Any]:
        """Get comprehensive orchestrator status."""
        return {
            'is_running': self.is_running,
            'registered_agents': len(self.agents),
            'active_tasks': len(self.active_tasks),
            'queued_tasks': self.task_queue.qsize(),
            'total_tasks': len(self.tasks),
            'completed_tasks': len([t for t in self.task_history if t.status == TaskStatus.COMPLETED]),
            'failed_tasks': len([t for t in self.task_history if t.status == TaskStatus.FAILED]),
            'capabilities': list(self.capability_map.keys()),
            'agents_by_capability': {
                cap.value: len(agents) for cap, agents in self.capability_map.items()
            }
        }
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """Get task execution statistics."""
        all_tasks = list(self.tasks.values()) + self.task_history
        
        if not all_tasks:
            return {'total_tasks': 0}
        
        completed_tasks = [t for t in all_tasks if t.status == TaskStatus.COMPLETED]
        failed_tasks = [t for t in all_tasks if t.status == TaskStatus.FAILED]
        
        avg_duration = 0
        if completed_tasks:
            durations = [
                t.end_time - t.start_time for t in completed_tasks
                if t.start_time and t.end_time
            ]
            avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            'total_tasks': len(all_tasks),
            'completed_tasks': len(completed_tasks),
            'failed_tasks': len(failed_tasks),
            'success_rate': len(completed_tasks) / len(all_tasks) if all_tasks else 0,
            'average_duration': avg_duration,
            'active_tasks': len(self.active_tasks),
            'queued_tasks': self.task_queue.qsize()
        }