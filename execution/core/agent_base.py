#!/usr/bin/env python3
"""
AgentBase - Enterprise-grade base class for all agents in the SensAI system.

This class provides the foundational architecture for scalable, reliable, and maintainable
agent systems inspired by Google Project Mariner and Claude Code.
"""

import asyncio
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Union, Callable
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Agent execution states."""
    IDLE = "idle"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    STOPPING = "stopping"
    STOPPED = "stopped"


class AgentCapability(Enum):
    """Agent capabilities for dynamic feature detection."""
    SCREEN_ANALYSIS = "screen_analysis"
    CONTEXT_AWARENESS = "context_awareness"
    TASK_AUTOMATION = "task_automation"
    SUGGESTION_GENERATION = "suggestion_generation"
    MEMORY_INTEGRATION = "memory_integration"
    LLM_REASONING = "llm_reasoning"
    VISUAL_PROCESSING = "visual_processing"


@dataclass
class AgentMetrics:
    """Comprehensive metrics for agent performance monitoring."""
    tasks_completed: int = 0
    tasks_failed: int = 0
    avg_response_time: float = 0.0
    uptime_seconds: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    success_rate: float = 0.0
    last_activity: Optional[float] = None
    
    def update_success_rate(self):
        """Calculate and update success rate."""
        total_tasks = self.tasks_completed + self.tasks_failed
        if total_tasks > 0:
            self.success_rate = self.tasks_completed / total_tasks
        else:
            self.success_rate = 0.0


@dataclass
class AgentConfig:
    """Configuration for agent behavior and performance."""
    name: str
    capabilities: List[AgentCapability] = field(default_factory=list)
    max_concurrent_tasks: int = 5
    task_timeout_seconds: int = 300
    retry_attempts: int = 3
    health_check_interval: int = 30
    enable_metrics: bool = True
    enable_logging: bool = True
    log_level: str = "INFO"
    custom_settings: Dict[str, Any] = field(default_factory=dict)


class AgentEventHandler(Protocol):
    """Protocol for agent event handlers."""
    
    def on_state_change(self, agent_id: str, old_state: AgentState, new_state: AgentState) -> None:
        """Handle agent state changes."""
        ...
    
    def on_task_start(self, agent_id: str, task_id: str, task_data: Dict[str, Any]) -> None:
        """Handle task start events."""
        ...
    
    def on_task_complete(self, agent_id: str, task_id: str, result: Any) -> None:
        """Handle task completion events."""
        ...
    
    def on_error(self, agent_id: str, error: Exception, context: Dict[str, Any]) -> None:
        """Handle agent errors."""
        ...


class AgentBase(ABC):
    """
    Enterprise-grade base class for all SensAI agents.
    
    Provides:
    - State management
    - Task execution and monitoring
    - Error handling and recovery
    - Metrics collection
    - Event system
    - Configuration management
    - Scalable architecture
    """
    
    def __init__(self, config: AgentConfig):
        """Initialize the agent with configuration."""
        self.config = config
        self.agent_id = str(uuid.uuid4())
        self.state = AgentState.IDLE
        self.metrics = AgentMetrics()
        self.start_time = time.time()
        
        # Task management
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.task_results: Dict[str, Any] = {}
        self.task_history: List[Dict[str, Any]] = []
        
        # Event handling
        self.event_handlers: List[AgentEventHandler] = []
        
        # Concurrency management
        self.executor = ThreadPoolExecutor(max_workers=config.max_concurrent_tasks)
        self.semaphore = asyncio.Semaphore(config.max_concurrent_tasks)
        
        # Health monitoring
        self.health_check_task: Optional[asyncio.Task] = None
        self.is_healthy = True
        
        # Logging
        self.logger = logging.getLogger(f"{self.__class__.__name__}({self.agent_id[:8]})")
        if config.enable_logging:
            self.logger.setLevel(getattr(logging, config.log_level))
        
        self.logger.info(f"Agent initialized: {self.config.name}")
    
    # ========== State Management ==========
    
    @property
    def is_running(self) -> bool:
        """Check if agent is in running state."""
        return self.state == AgentState.RUNNING
    
    @property
    def is_idle(self) -> bool:
        """Check if agent is idle."""
        return self.state == AgentState.IDLE
    
    def set_state(self, new_state: AgentState) -> None:
        """Set agent state and notify handlers."""
        old_state = self.state
        self.state = new_state
        
        self.logger.info(f"State changed: {old_state.value} -> {new_state.value}")
        
        # Notify event handlers
        for handler in self.event_handlers:
            try:
                handler.on_state_change(self.agent_id, old_state, new_state)
            except Exception as e:
                self.logger.error(f"Error in state change handler: {e}")
    
    # ========== Lifecycle Management ==========
    
    async def start(self) -> None:
        """Start the agent."""
        try:
            self.set_state(AgentState.INITIALIZING)
            
            # Perform initialization
            await self.initialize()
            
            # Start health monitoring
            if self.config.health_check_interval > 0:
                self.health_check_task = asyncio.create_task(self._health_check_loop())
            
            self.set_state(AgentState.RUNNING)
            self.logger.info("Agent started successfully")
            
        except Exception as e:
            self.set_state(AgentState.ERROR)
            self.logger.error(f"Failed to start agent: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the agent gracefully."""
        try:
            self.set_state(AgentState.STOPPING)
            
            # Cancel all active tasks
            for task_id, task in self.active_tasks.items():
                task.cancel()
                self.logger.info(f"Cancelled task: {task_id}")
            
            # Wait for tasks to complete
            if self.active_tasks:
                await asyncio.gather(*self.active_tasks.values(), return_exceptions=True)
            
            # Stop health monitoring
            if self.health_check_task:
                self.health_check_task.cancel()
            
            # Perform cleanup
            await self.cleanup()
            
            # Shutdown executor
            self.executor.shutdown(wait=True)
            
            self.set_state(AgentState.STOPPED)
            self.logger.info("Agent stopped successfully")
            
        except Exception as e:
            self.set_state(AgentState.ERROR)
            self.logger.error(f"Error during shutdown: {e}")
            raise
    
    async def pause(self) -> None:
        """Pause agent execution."""
        if self.state == AgentState.RUNNING:
            self.set_state(AgentState.PAUSED)
            self.logger.info("Agent paused")
    
    async def resume(self) -> None:
        """Resume agent execution."""
        if self.state == AgentState.PAUSED:
            self.set_state(AgentState.RUNNING)
            self.logger.info("Agent resumed")
    
    # ========== Task Management ==========
    
    async def execute_task(self, task_data: Dict[str, Any]) -> str:
        """
        Execute a task asynchronously.
        
        Args:
            task_data: Task parameters and data
            
        Returns:
            Task ID for tracking
        """
        task_id = str(uuid.uuid4())
        
        # Check if agent can accept more tasks
        if len(self.active_tasks) >= self.config.max_concurrent_tasks:
            raise RuntimeError("Agent at maximum task capacity")
        
        # Create and start task
        task = asyncio.create_task(self._execute_task_wrapper(task_id, task_data))
        self.active_tasks[task_id] = task
        
        # Notify handlers
        for handler in self.event_handlers:
            try:
                handler.on_task_start(self.agent_id, task_id, task_data)
            except Exception as e:
                self.logger.error(f"Error in task start handler: {e}")
        
        return task_id
    
    async def _execute_task_wrapper(self, task_id: str, task_data: Dict[str, Any]) -> Any:
        """Wrapper for task execution with error handling and metrics."""
        start_time = time.time()
        
        try:
            async with self.semaphore:  # Limit concurrency
                # Execute the actual task
                result = await asyncio.wait_for(
                    self.process_task(task_data),
                    timeout=self.config.task_timeout_seconds
                )
                
                # Update metrics
                execution_time = time.time() - start_time
                self.metrics.tasks_completed += 1
                self.metrics.avg_response_time = (
                    (self.metrics.avg_response_time * (self.metrics.tasks_completed - 1) + execution_time) /
                    self.metrics.tasks_completed
                )
                self.metrics.update_success_rate()
                self.metrics.last_activity = time.time()
                
                # Store result
                self.task_results[task_id] = result
                
                # Add to history
                self.task_history.append({
                    'task_id': task_id,
                    'task_data': task_data,
                    'result': result,
                    'execution_time': execution_time,
                    'timestamp': time.time(),
                    'success': True
                })
                
                # Notify handlers
                for handler in self.event_handlers:
                    try:
                        handler.on_task_complete(self.agent_id, task_id, result)
                    except Exception as e:
                        self.logger.error(f"Error in task complete handler: {e}")
                
                self.logger.info(f"Task completed: {task_id} in {execution_time:.2f}s")
                return result
                
        except Exception as e:
            # Handle task failure
            execution_time = time.time() - start_time
            self.metrics.tasks_failed += 1
            self.metrics.update_success_rate()
            
            # Add to history
            self.task_history.append({
                'task_id': task_id,
                'task_data': task_data,
                'error': str(e),
                'execution_time': execution_time,
                'timestamp': time.time(),
                'success': False
            })
            
            # Notify handlers
            for handler in self.event_handlers:
                try:
                    handler.on_error(self.agent_id, e, {'task_id': task_id, 'task_data': task_data})
                except Exception as handler_error:
                    self.logger.error(f"Error in error handler: {handler_error}")
            
            self.logger.error(f"Task failed: {task_id} - {e}")
            raise
            
        finally:
            # Clean up task tracking
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
    
    def get_task_result(self, task_id: str) -> Optional[Any]:
        """Get result of a completed task."""
        return self.task_results.get(task_id)
    
    def get_task_status(self, task_id: str) -> str:
        """Get status of a task."""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            if task.done():
                return "completed" if not task.cancelled() else "cancelled"
            else:
                return "running"
        elif task_id in self.task_results:
            return "completed"
        else:
            return "unknown"
    
    # ========== Health and Monitoring ==========
    
    async def _health_check_loop(self) -> None:
        """Continuous health monitoring loop."""
        while self.state != AgentState.STOPPED:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                
                if self.state in [AgentState.RUNNING, AgentState.PAUSED]:
                    self.is_healthy = await self.health_check()
                    
                    if not self.is_healthy:
                        self.logger.warning("Health check failed")
                        await self.handle_unhealthy_state()
                    
                    # Update uptime
                    self.metrics.uptime_seconds = time.time() - self.start_time
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in health check: {e}")
    
    async def health_check(self) -> bool:
        """Perform health check. Override in subclasses."""
        return True
    
    async def handle_unhealthy_state(self) -> None:
        """Handle unhealthy agent state. Override in subclasses."""
        pass
    
    def get_metrics(self) -> AgentMetrics:
        """Get current agent metrics."""
        return self.metrics
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status."""
        return {
            'agent_id': self.agent_id,
            'name': self.config.name,
            'state': self.state.value,
            'is_healthy': self.is_healthy,
            'active_tasks': len(self.active_tasks),
            'capabilities': [cap.value for cap in self.config.capabilities],
            'metrics': {
                'tasks_completed': self.metrics.tasks_completed,
                'tasks_failed': self.metrics.tasks_failed,
                'success_rate': self.metrics.success_rate,
                'avg_response_time': self.metrics.avg_response_time,
                'uptime_seconds': self.metrics.uptime_seconds,
                'last_activity': self.metrics.last_activity
            }
        }
    
    # ========== Event System ==========
    
    def add_event_handler(self, handler: AgentEventHandler) -> None:
        """Add an event handler."""
        self.event_handlers.append(handler)
    
    def remove_event_handler(self, handler: AgentEventHandler) -> None:
        """Remove an event handler."""
        if handler in self.event_handlers:
            self.event_handlers.remove(handler)
    
    # ========== Abstract Methods ==========
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the agent. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    async def process_task(self, task_data: Dict[str, Any]) -> Any:
        """Process a task. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources. Must be implemented by subclasses."""
        pass
    
    # ========== Configuration Management ==========
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update agent configuration dynamically."""
        for key, value in new_config.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                self.logger.info(f"Updated config: {key} = {value}")
    
    def has_capability(self, capability: AgentCapability) -> bool:
        """Check if agent has a specific capability."""
        return capability in self.config.capabilities
    
    # ========== Utility Methods ==========
    
    def __str__(self) -> str:
        """String representation of the agent."""
        return f"{self.__class__.__name__}(id={self.agent_id[:8]}, name={self.config.name}, state={self.state.value})"
    
    def __repr__(self) -> str:
        """Detailed representation of the agent."""
        return (f"{self.__class__.__name__}(id={self.agent_id}, name={self.config.name}, "
                f"state={self.state.value}, capabilities={[c.value for c in self.config.capabilities]})")