#!/usr/bin/env python3
"""
Task Memory Manager

Enhances memory persistence for maintaining state between task loops
by integrating with the memory system and providing persistent storage
for task state, execution context, and relevant task history.

This module serves as the bridge between the UniversalTaskLoopController
and the Memory System, ensuring that task state can be maintained even
across system restarts.
"""

import os
import json
import time
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime
import uuid

# Import task-related types
from universal_task_loop_controller import TaskStatus, TaskExecutionMetrics, LoopControllerState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/task_memory.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("task_memory")

# Storage paths
MEMORY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "memory")
TASK_MEMORY_DIR = os.path.join(MEMORY_DIR, "tasks")
os.makedirs(TASK_MEMORY_DIR, exist_ok=True)

@dataclass
class TaskMemoryRecord:
    """Represents a single task memory record in persistent storage"""
    task_id: str
    created_at: float
    updated_at: float
    status: str
    description: str
    memory_type: str = "task_state"  # Identifies this as a task memory record
    execution_context: Dict[str, Any] = field(default_factory=dict)
    current_step: int = 0
    total_steps: int = 0
    metrics: Dict[str, Any] = field(default_factory=dict)
    execution_history: List[Dict[str, Any]] = field(default_factory=list)
    related_memory_ids: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    semantic_vector: Optional[List[float]] = None
    expiration_time: Optional[float] = None  # When to prune from short-term memory
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskMemoryRecord':
        """Create from dictionary"""
        return cls(**data)
    
    def update_from_task_state(self, task_data: Dict[str, Any], metrics: Dict[str, Any] = None) -> None:
        """Update record from task state data"""
        self.updated_at = time.time()
        self.status = task_data.get("status", self.status)
        self.current_step = task_data.get("current_step", self.current_step)
        self.total_steps = task_data.get("total_steps", self.total_steps)
        
        # Store execution context
        self.execution_context.update({
            "last_step_details": task_data.get("current_step_details", {}),
            "last_updated_at": time.time(),
            "platform_state": task_data.get("platform_state", {})
        })
        
        # Update metrics if provided
        if metrics:
            self.metrics = metrics
            
        # Add to execution history
        self.execution_history.append({
            "timestamp": time.time(),
            "status": self.status,
            "current_step": self.current_step,
            "step_details": task_data.get("current_step_details", {})
        })
        
        # Limit history length to prevent excessive growth
        if len(self.execution_history) > 100:
            self.execution_history = self.execution_history[-100:]

class TaskMemoryManager:
    """
    Manager for task memory persistence
    
    Provides functionality for storing, retrieving, and managing task state
    in the memory system for persistence between task executions.
    """
    
    def __init__(self, memory_system=None):
        """Initialize the task memory manager"""
        self.memory_system = memory_system
        self.active_task_records: Dict[str, TaskMemoryRecord] = {}
        self.loaded = False
        
        # Check if memory system is available
        self.memory_system_available = memory_system is not None
        if not self.memory_system_available:
            logger.warning("Memory system not available, falling back to local file storage only")
        
        # Generate index file path
        self.index_file = os.path.join(TASK_MEMORY_DIR, "task_index.json")
        
        # Load task index if exists
        self._load_task_index()
        
    def _load_task_index(self) -> None:
        """Load task index from disk"""
        try:
            if os.path.exists(self.index_file):
                with open(self.index_file, 'r') as f:
                    self.task_index = json.load(f)
            else:
                self.task_index = {
                    "version": "1.0",
                    "last_updated": time.time(),
                    "active_tasks": {},
                    "completed_tasks": {},
                    "failed_tasks": {}
                }
                # Save initial index
                self._save_task_index()
                
            logger.info(f"Loaded task index with {len(self.task_index.get('active_tasks', {}))} active tasks")
            self.loaded = True
            
        except Exception as e:
            logger.error(f"Error loading task index: {e}")
            # Create default index
            self.task_index = {
                "version": "1.0",
                "last_updated": time.time(),
                "active_tasks": {},
                "completed_tasks": {},
                "failed_tasks": {}
            }
            self.loaded = False
    
    def _save_task_index(self) -> None:
        """Save task index to disk"""
        try:
            # Update timestamp
            self.task_index["last_updated"] = time.time()
            
            with open(self.index_file, 'w') as f:
                json.dump(self.task_index, f, indent=2)
                
            logger.debug("Saved task index")
            
        except Exception as e:
            logger.error(f"Error saving task index: {e}")
    
    async def initialize(self) -> None:
        """Initialize and load tasks from storage"""
        try:
            # Ensure task directory exists
            os.makedirs(TASK_MEMORY_DIR, exist_ok=True)
            
            # Load index if not already loaded
            if not self.loaded:
                self._load_task_index()
            
            # Load active task records
            for task_id in self.task_index.get("active_tasks", {}):
                await self.load_task_record(task_id)
                
            logger.info(f"Initialized task memory manager with {len(self.active_task_records)} active tasks")
            
            # Start background task for periodic saving
            asyncio.create_task(self._periodic_save())
            
        except Exception as e:
            logger.error(f"Error initializing task memory manager: {e}")
    
    async def _periodic_save(self, interval: int = 60) -> None:
        """Periodically save all active task records"""
        while True:
            try:
                # Save all active task records
                for task_id in list(self.active_task_records.keys()):
                    await self.save_task_record(task_id)
                
                logger.debug(f"Saved {len(self.active_task_records)} active task records")
                
            except Exception as e:
                logger.error(f"Error in periodic save: {e}")
                
            await asyncio.sleep(interval)
    
    async def create_task_record(self, task_id: str, task_data: Dict[str, Any], metrics: Dict[str, Any] = None) -> TaskMemoryRecord:
        """Create a new task memory record"""
        try:
            # Create task record
            record = TaskMemoryRecord(
                task_id=task_id,
                created_at=time.time(),
                updated_at=time.time(),
                status=task_data.get("status", TaskStatus.PENDING.value),
                description=task_data.get("description", ""),
                current_step=task_data.get("current_step", 0),
                total_steps=task_data.get("total_steps", 0),
                metrics=metrics or {},
                execution_context=task_data.get("context", {}),
                tags=[task_data.get("type", "universal"), "task"]
            )
            
            # Store in active records
            self.active_task_records[task_id] = record
            
            # Update task index
            self.task_index["active_tasks"][task_id] = {
                "created_at": record.created_at,
                "updated_at": record.updated_at,
                "status": record.status,
                "description": record.description
            }
            self._save_task_index()
            
            # Save to disk
            await self.save_task_record(task_id)
            
            # Store in memory system if available
            if self.memory_system_available:
                await self._add_to_memory_system(record)
            
            logger.info(f"Created task record for {task_id}")
            return record
            
        except Exception as e:
            logger.error(f"Error creating task record: {e}")
            # Create minimal record to prevent errors
            record = TaskMemoryRecord(
                task_id=task_id,
                created_at=time.time(),
                updated_at=time.time(),
                status=TaskStatus.PENDING.value,
                description=task_data.get("description", "Error creating task record")
            )
            self.active_task_records[task_id] = record
            return record
    
    async def update_task_record(self, task_id: str, task_data: Dict[str, Any], metrics: Dict[str, Any] = None) -> Optional[TaskMemoryRecord]:
        """Update an existing task memory record"""
        try:
            # Get existing record
            record = self.active_task_records.get(task_id)
            if not record:
                # Try to load from storage
                record = await self.load_task_record(task_id)
                
            if not record:
                logger.warning(f"Task record not found for {task_id}, creating new")
                return await self.create_task_record(task_id, task_data, metrics)
            
            # Update record
            record.update_from_task_state(task_data, metrics)
            
            # Update task index
            self.task_index["active_tasks"][task_id] = {
                "created_at": record.created_at,
                "updated_at": record.updated_at,
                "status": record.status,
                "description": record.description
            }
            self._save_task_index()
            
            # Save to disk
            await self.save_task_record(task_id)
            
            # Update in memory system if available
            if self.memory_system_available:
                await self._update_in_memory_system(record)
            
            logger.debug(f"Updated task record for {task_id}")
            return record
            
        except Exception as e:
            logger.error(f"Error updating task record: {e}")
            return None
    
    async def save_task_record(self, task_id: str) -> bool:
        """Save a task record to disk"""
        try:
            record = self.active_task_records.get(task_id)
            if not record:
                logger.warning(f"Task record not found for {task_id}")
                return False
            
            # Save to disk
            file_path = os.path.join(TASK_MEMORY_DIR, f"{task_id}.json")
            with open(file_path, 'w') as f:
                json.dump(record.to_dict(), f, indent=2)
            
            logger.debug(f"Saved task record {task_id} to disk")
            return True
            
        except Exception as e:
            logger.error(f"Error saving task record: {e}")
            return False
    
    async def load_task_record(self, task_id: str) -> Optional[TaskMemoryRecord]:
        """Load a task record from disk"""
        try:
            # Check if already loaded
            if task_id in self.active_task_records:
                return self.active_task_records[task_id]
            
            # Load from disk
            file_path = os.path.join(TASK_MEMORY_DIR, f"{task_id}.json")
            if not os.path.exists(file_path):
                logger.warning(f"Task record file not found for {task_id}")
                return None
            
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Create record
            record = TaskMemoryRecord.from_dict(data)
            
            # Store in active records
            self.active_task_records[task_id] = record
            
            logger.debug(f"Loaded task record {task_id} from disk")
            return record
            
        except Exception as e:
            logger.error(f"Error loading task record: {e}")
            return None
    
    async def complete_task_record(self, task_id: str, final_status: str, task_data: Dict[str, Any] = None, metrics: Dict[str, Any] = None) -> bool:
        """Mark a task as completed or failed and update its record"""
        try:
            # Get existing record
            record = self.active_task_records.get(task_id)
            if not record:
                # Try to load from storage
                record = await self.load_task_record(task_id)
                
            if not record:
                logger.warning(f"Task record not found for {task_id}")
                return False
            
            # Update record with final state
            record.status = final_status
            record.updated_at = time.time()
            
            if task_data:
                record.update_from_task_state(task_data, metrics)
            
            # Add to completion history
            record.execution_context["completed_at"] = time.time()
            record.execution_context["final_status"] = final_status
            
            # Save record
            await self.save_task_record(task_id)
            
            # Update memory system
            if self.memory_system_available:
                await self._update_in_memory_system(record)
                
                # For completed tasks, also create a summary memory for long-term storage
                if final_status in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value]:
                    await self._create_task_summary_memory(record)
            
            # Update task index
            self._update_task_index(record, final_status)
            
            logger.info(f"Completed task record {task_id} with status {final_status}")
            return True
            
        except Exception as e:
            logger.error(f"Error completing task record: {e}")
            return False
    
    def _update_task_index(self, record: TaskMemoryRecord, final_status: str) -> None:
        """Update task index with completed or failed task"""
        try:
            # Remove from active tasks
            if record.task_id in self.task_index["active_tasks"]:
                del self.task_index["active_tasks"][record.task_id]
            
            # Add to completed or failed tasks
            if final_status == TaskStatus.COMPLETED.value:
                self.task_index["completed_tasks"][record.task_id] = {
                    "created_at": record.created_at,
                    "updated_at": record.updated_at,
                    "completed_at": record.updated_at,
                    "description": record.description
                }
            elif final_status == TaskStatus.FAILED.value:
                self.task_index["failed_tasks"][record.task_id] = {
                    "created_at": record.created_at,
                    "updated_at": record.updated_at,
                    "failed_at": record.updated_at,
                    "description": record.description
                }
            
            # Save index
            self._save_task_index()
            
        except Exception as e:
            logger.error(f"Error updating task index: {e}")
    
    async def _add_to_memory_system(self, record: TaskMemoryRecord) -> None:
        """Add task record to memory system"""
        if not self.memory_system_available:
            return
            
        try:
            # Create memory entry for task
            memory_data = {
                "timestamp": datetime.now().isoformat(),
                "memory_type": "task_state",
                "memory_id": f"task_{record.task_id}_{int(time.time())}",
                "task_id": record.task_id,
                "status": record.status,
                "description": record.description,
                "progress": (record.current_step / max(1, record.total_steps)) * 100.0,
                "context": record.execution_context,
                "metrics": record.metrics,
                "tags": record.tags
            }
            
            # Add to memory system
            await self.memory_system.add_to_short_term_memory(memory_data)
            
            logger.debug(f"Added task {record.task_id} to memory system")
            
        except Exception as e:
            logger.error(f"Error adding task to memory system: {e}")
    
    async def _update_in_memory_system(self, record: TaskMemoryRecord) -> None:
        """Update task record in memory system"""
        if not self.memory_system_available:
            return
            
        try:
            # Create updated memory entry
            memory_data = {
                "timestamp": datetime.now().isoformat(),
                "memory_type": "task_state",
                "memory_id": f"task_{record.task_id}_{int(time.time())}",
                "task_id": record.task_id,
                "status": record.status,
                "description": record.description,
                "progress": (record.current_step / max(1, record.total_steps)) * 100.0,
                "context": record.execution_context,
                "metrics": record.metrics,
                "tags": record.tags,
                "update": True
            }
            
            # Update in memory system
            await self.memory_system.add_to_short_term_memory(memory_data)
            
            logger.debug(f"Updated task {record.task_id} in memory system")
            
        except Exception as e:
            logger.error(f"Error updating task in memory system: {e}")
    
    async def _create_task_summary_memory(self, record: TaskMemoryRecord) -> None:
        """Create task summary for long-term memory"""
        if not self.memory_system_available:
            return
            
        try:
            # Calculate overall metrics
            progress = 100.0 if record.status == TaskStatus.COMPLETED.value else (record.current_step / max(1, record.total_steps)) * 100.0
            duration = time.time() - record.created_at if record.created_at else 0
            
            # Generate insights
            insights = [
                f"Task {'completed successfully' if record.status == TaskStatus.COMPLETED.value else 'failed'}",
                f"Completed {record.current_step} of {record.total_steps} steps ({progress:.1f}%)",
                f"Took {duration:.1f} seconds to execute"
            ]
            
            if record.metrics:
                if "time_saved" in record.metrics:
                    insights.append(f"Saved {record.metrics['time_saved']:.1f} seconds of manual work")
                if "monetary_value" in record.metrics:
                    insights.append(f"Generated ${record.metrics['monetary_value']:.2f} in value")
            
            # Create summary memory
            summary_data = {
                "timestamp": datetime.now().isoformat(),
                "memory_type": "task_summary",
                "memory_id": f"task_summary_{record.task_id}",
                "task_id": record.task_id,
                "description": record.description,
                "status": record.status,
                "steps_completed": record.current_step,
                "steps_total": record.total_steps,
                "duration": duration,
                "created_at": record.created_at,
                "completed_at": time.time(),
                "metrics": record.metrics,
                "insights": insights,
                "tags": record.tags + ["task_summary"]
            }
            
            # Add to long-term memory
            await self.memory_system.add_to_long_term_memory(summary_data)
            
            logger.info(f"Created task summary for {record.task_id} in long-term memory")
            
        except Exception as e:
            logger.error(f"Error creating task summary memory: {e}")
    
    async def search_task_records(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search task records using memory system's semantic search"""
        if not self.memory_system_available:
            logger.warning("Memory system not available for task search")
            return []
            
        try:
            # Search both short-term and long-term memory
            search_results = await self.memory_system.search_memory(
                query, 
                limit=limit,
                memory_types=["task_state", "task_summary"]
            )
            
            # Extract task IDs from results
            task_ids = set()
            for result in search_results:
                if "task_id" in result:
                    task_ids.add(result["task_id"])
            
            # Load detailed records for these tasks
            task_records = []
            for task_id in task_ids:
                record = await self.load_task_record(task_id)
                if record:
                    task_records.append(record.to_dict())
            
            return task_records
            
        except Exception as e:
            logger.error(f"Error searching task records: {e}")
            return []
    
    async def synchronize_with_controller(self, controller_state: LoopControllerState) -> None:
        """Synchronize task memory with controller state"""
        try:
            # Update active tasks
            for task_id, task_data in controller_state.active_tasks.items():
                metrics = controller_state.metrics.get(task_id, {})
                
                # Check if already in memory
                if task_id in self.active_task_records:
                    # Update existing record
                    await self.update_task_record(task_id, task_data, metrics)
                else:
                    # Create new record
                    await self.create_task_record(task_id, task_data, metrics)
            
            # Process completed tasks
            for task_data in controller_state.completed_tasks:
                task_id = task_data.get("task_id")
                if task_id:
                    metrics = controller_state.metrics.get(task_id, {})
                    await self.complete_task_record(task_id, TaskStatus.COMPLETED.value, task_data, metrics)
            
            # Process failed tasks
            for task_id, task_data in controller_state.failed_tasks.items():
                metrics = controller_state.metrics.get(task_id, {})
                await self.complete_task_record(task_id, TaskStatus.FAILED.value, task_data, metrics)
            
            logger.info(f"Synchronized {len(controller_state.active_tasks)} active tasks, "
                       f"{len(controller_state.completed_tasks)} completed tasks, and "
                       f"{len(controller_state.failed_tasks)} failed tasks with memory")
                       
        except Exception as e:
            logger.error(f"Error synchronizing with controller state: {e}")
    
    async def populate_controller_state(self, controller_state: LoopControllerState) -> LoopControllerState:
        """Populate controller state from persistent task memory"""
        try:
            # Get all task IDs from index
            active_task_ids = list(self.task_index.get("active_tasks", {}).keys())
            
            # Load active task records
            for task_id in active_task_ids:
                record = await self.load_task_record(task_id)
                if not record:
                    continue
                
                # Check if already in controller state
                if task_id in controller_state.active_tasks:
                    # Update existing task with memory data
                    self._enrich_task_data(controller_state.active_tasks[task_id], record)
                else:
                    # Create new task entry
                    task_data = await self._task_record_to_controller_format(record)
                    controller_state.active_tasks[task_id] = task_data
                
                # Update metrics
                if task_id not in controller_state.metrics and record.metrics:
                    controller_state.metrics[task_id] = record.metrics
            
            logger.info(f"Populated controller state with {len(active_task_ids)} tasks from memory")
            return controller_state
            
        except Exception as e:
            logger.error(f"Error populating controller state: {e}")
            return controller_state
    
    def _enrich_task_data(self, task_data: Dict[str, Any], record: TaskMemoryRecord) -> None:
        """Enrich task data with memory record information"""
        # Add memory-specific context if not already present
        task_data.setdefault("memory_context", {})
        
        # Update memory context
        task_data["memory_context"].update({
            "last_memory_update": record.updated_at,
            "has_persistent_record": True,
            "execution_history_length": len(record.execution_history)
        })
        
        # Add any missing execution context
        task_data.setdefault("context", {})
        for key, value in record.execution_context.items():
            if key not in task_data["context"]:
                task_data["context"][key] = value
    
    async def _task_record_to_controller_format(self, record: TaskMemoryRecord) -> Dict[str, Any]:
        """Convert task memory record to controller task format"""
        try:
            # Create basic task data
            task_data = {
                "task_id": record.task_id,
                "description": record.description,
                "status": record.status,
                "submitted_at": record.created_at,
                "context": record.execution_context,
                "current_step": record.current_step,
                "total_steps": record.total_steps,
                "memory_context": {
                    "last_memory_update": record.updated_at,
                    "has_persistent_record": True,
                    "execution_history_length": len(record.execution_history)
                },
                "results": {}
            }
            
            # Add execution history results
            for i, history_entry in enumerate(record.execution_history):
                step_idx = history_entry.get("current_step", i)
                if "step_details" in history_entry:
                    task_data["results"][f"step_{step_idx}"] = history_entry["step_details"]
            
            return task_data
            
        except Exception as e:
            logger.error(f"Error converting task record to controller format: {e}")
            # Return basic task data
            return {
                "task_id": record.task_id,
                "description": record.description,
                "status": record.status,
                "submitted_at": record.created_at,
                "current_step": record.current_step,
                "total_steps": record.total_steps,
                "context": {},
                "results": {}
            }
    
    async def cleanup_old_records(self, max_age_days: int = 30) -> int:
        """Clean up old task records"""
        try:
            now = time.time()
            max_age_seconds = max_age_days * 24 * 60 * 60
            deletion_count = 0
            
            # Get all completed and failed tasks
            completed_tasks = list(self.task_index.get("completed_tasks", {}).items())
            failed_tasks = list(self.task_index.get("failed_tasks", {}).items())
            
            # Check each completed task
            for task_id, metadata in completed_tasks:
                if now - metadata.get("completed_at", now) > max_age_seconds:
                    # Delete task record
                    file_path = os.path.join(TASK_MEMORY_DIR, f"{task_id}.json")
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        
                    # Remove from index
                    if task_id in self.task_index["completed_tasks"]:
                        del self.task_index["completed_tasks"][task_id]
                        
                    deletion_count += 1
            
            # Check each failed task
            for task_id, metadata in failed_tasks:
                if now - metadata.get("failed_at", now) > max_age_seconds:
                    # Delete task record
                    file_path = os.path.join(TASK_MEMORY_DIR, f"{task_id}.json")
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        
                    # Remove from index
                    if task_id in self.task_index["failed_tasks"]:
                        del self.task_index["failed_tasks"][task_id]
                        
                    deletion_count += 1
            
            # Save index if changes were made
            if deletion_count > 0:
                self._save_task_index()
                
            logger.info(f"Cleaned up {deletion_count} old task records")
            return deletion_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old records: {e}")
            return 0
    
    async def get_task_history(self, task_id: str) -> List[Dict[str, Any]]:
        """Get execution history for a task"""
        try:
            record = self.active_task_records.get(task_id)
            if not record:
                # Try to load from storage
                record = await self.load_task_record(task_id)
                
            if not record:
                logger.warning(f"Task record not found for {task_id}")
                return []
            
            return record.execution_history
            
        except Exception as e:
            logger.error(f"Error getting task history: {e}")
            return []
    
    async def generate_task_insights(self, task_id: str) -> List[str]:
        """Generate insights for a task based on its execution history"""
        try:
            record = self.active_task_records.get(task_id)
            if not record:
                # Try to load from storage
                record = await self.load_task_record(task_id)
                
            if not record:
                logger.warning(f"Task record not found for {task_id}")
                return []
            
            insights = []
            
            # Calculate metrics
            if record.metrics:
                time_saved = record.metrics.get("time_saved", 0)
                if time_saved > 0:
                    insights.append(f"Task saved {time_saved:.1f} seconds of manual work")
                    
                monetary_value = record.metrics.get("monetary_value", 0)
                if monetary_value > 0:
                    insights.append(f"Task generated ${monetary_value:.2f} in value")
            
            # Calculate execution time
            if record.created_at and record.updated_at:
                execution_time = record.updated_at - record.created_at
                insights.append(f"Task executed in {execution_time:.1f} seconds")
            
            # Calculate success rate
            if record.total_steps > 0:
                completion_rate = (record.current_step / record.total_steps) * 100.0
                insights.append(f"Task completion rate: {completion_rate:.1f}%")
            
            # Add status insight
            if record.status == TaskStatus.COMPLETED.value:
                insights.append("Task completed successfully")
            elif record.status == TaskStatus.FAILED.value:
                failure_reason = record.execution_context.get("failure_reason", "Unknown reason")
                insights.append(f"Task failed: {failure_reason}")
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating task insights: {e}")
            return []

# Create singleton instance
task_memory_manager = TaskMemoryManager()

# API functions
async def initialize(memory_system=None):
    """Initialize task memory manager"""
    task_memory_manager.memory_system = memory_system
    task_memory_manager.memory_system_available = memory_system is not None
    await task_memory_manager.initialize()

async def create_task_record(task_id: str, task_data: Dict[str, Any], metrics: Dict[str, Any] = None) -> Optional[TaskMemoryRecord]:
    """Create a new task memory record"""
    return await task_memory_manager.create_task_record(task_id, task_data, metrics)

async def update_task_record(task_id: str, task_data: Dict[str, Any], metrics: Dict[str, Any] = None) -> Optional[TaskMemoryRecord]:
    """Update an existing task memory record"""
    return await task_memory_manager.update_task_record(task_id, task_data, metrics)

async def complete_task_record(task_id: str, final_status: str, task_data: Dict[str, Any] = None, metrics: Dict[str, Any] = None) -> bool:
    """Mark a task as completed or failed"""
    return await task_memory_manager.complete_task_record(task_id, final_status, task_data, metrics)

async def search_task_records(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search task records using semantic search"""
    return await task_memory_manager.search_task_records(query, limit)

async def synchronize_with_controller(controller_state: LoopControllerState) -> None:
    """Synchronize task memory with controller state"""
    return await task_memory_manager.synchronize_with_controller(controller_state)

async def populate_controller_state(controller_state: LoopControllerState) -> LoopControllerState:
    """Populate controller state from persistent task memory"""
    return await task_memory_manager.populate_controller_state(controller_state)

async def get_task_history(task_id: str) -> List[Dict[str, Any]]:
    """Get execution history for a task"""
    return await task_memory_manager.get_task_history(task_id)

async def generate_task_insights(task_id: str) -> List[str]:
    """Generate insights for a task based on its execution history"""
    return await task_memory_manager.generate_task_insights(task_id)

async def cleanup_old_records(max_age_days: int = 30) -> int:
    """Clean up old task records"""
    return await task_memory_manager.cleanup_old_records(max_age_days)