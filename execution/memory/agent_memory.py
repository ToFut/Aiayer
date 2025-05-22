#!/usr/bin/env python3
"""
AgentMemory - Comprehensive memory system for agent task tracking and context management.

This system provides:
- Task completion tracking
- Context-aware memory management
- Learning from past executions
- Performance optimization
- Smart pattern recognition
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import pickle
import sqlite3
from pathlib import Path
import threading
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Types of memory entries."""
    TASK_EXECUTION = "task_execution"
    CONTEXT_SNAPSHOT = "context_snapshot"
    USER_INTERACTION = "user_interaction"
    SYSTEM_EVENT = "system_event"
    LEARNING_PATTERN = "learning_pattern"
    PERFORMANCE_METRIC = "performance_metric"


class TaskOutcome(Enum):
    """Task execution outcomes."""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL_SUCCESS = "partial_success"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class MemoryEntry:
    """Individual memory entry."""
    entry_id: str
    memory_type: MemoryType
    timestamp: float
    data: Dict[str, Any]
    tags: Set[str] = field(default_factory=set)
    relevance_score: float = 1.0
    access_count: int = 0
    last_accessed: Optional[float] = None


@dataclass
class TaskMemory:
    """Memory specific to task execution."""
    task_id: str
    task_name: str
    task_type: str
    outcome: TaskOutcome
    execution_time: float
    steps_completed: int
    total_steps: int
    context_at_start: Dict[str, Any]
    context_at_end: Dict[str, Any]
    user_feedback: Optional[str] = None
    learned_patterns: List[str] = field(default_factory=list)
    optimization_hints: List[str] = field(default_factory=list)


@dataclass
class ContextSnapshot:
    """Snapshot of system context at a point in time."""
    timestamp: float
    screen_analysis: Optional[Dict[str, Any]] = None
    active_applications: List[str] = field(default_factory=list)
    user_activity: Optional[Dict[str, Any]] = None
    system_state: Dict[str, Any] = field(default_factory=dict)
    environmental_factors: Dict[str, Any] = field(default_factory=dict)


class AgentMemory:
    """
    Enterprise-grade memory system for agents.
    
    Features:
    - Persistent storage with SQLite
    - Fast in-memory caching
    - Context-aware retrieval
    - Learning pattern recognition
    - Performance optimization
    - Memory consolidation
    - Intelligent forgetting
    """
    
    def __init__(self, memory_path: Optional[str] = None, cache_size: int = 1000):
        """Initialize the memory system."""
        self.memory_path = memory_path or "logs/agent_memory.db"
        self.cache_size = cache_size
        
        # In-memory caches
        self.memory_cache: Dict[str, MemoryEntry] = {}
        self.recent_entries = deque(maxlen=cache_size)
        self.context_cache: Dict[str, ContextSnapshot] = {}
        
        # Task tracking
        self.active_tasks: Dict[str, TaskMemory] = {}
        self.task_patterns: Dict[str, List[str]] = defaultdict(list)
        
        # Performance tracking
        self.performance_metrics: Dict[str, List[float]] = defaultdict(list)
        self.success_patterns: List[Dict[str, Any]] = []
        self.failure_patterns: List[Dict[str, Any]] = []
        
        # Learning system
        self.learned_optimizations: Dict[str, str] = {}
        self.user_preferences: Dict[str, Any] = {}
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Initialize database
        self._init_database()
        
        # Load recent entries into cache
        self._load_cache()
        
        logger.info(f"AgentMemory initialized with database: {self.memory_path}")
    
    def _init_database(self) -> None:
        """Initialize SQLite database."""
        Path(self.memory_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.memory_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_entries (
                    entry_id TEXT PRIMARY KEY,
                    memory_type TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    data TEXT NOT NULL,
                    tags TEXT,
                    relevance_score REAL DEFAULT 1.0,
                    access_count INTEGER DEFAULT 0,
                    last_accessed REAL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_memory (
                    task_id TEXT PRIMARY KEY,
                    task_name TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    execution_time REAL NOT NULL,
                    steps_completed INTEGER NOT NULL,
                    total_steps INTEGER NOT NULL,
                    context_at_start TEXT NOT NULL,
                    context_at_end TEXT NOT NULL,
                    user_feedback TEXT,
                    learned_patterns TEXT,
                    optimization_hints TEXT,
                    timestamp REAL NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS context_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    timestamp REAL NOT NULL,
                    screen_analysis TEXT,
                    active_applications TEXT,
                    user_activity TEXT,
                    system_state TEXT,
                    environmental_factors TEXT
                )
            """)
            
            # Create indices
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_timestamp ON memory_entries(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_type ON memory_entries(memory_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_task_outcome ON task_memory(outcome)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_context_timestamp ON context_snapshots(timestamp)")
            
            conn.commit()
    
    def _load_cache(self) -> None:
        """Load recent entries into memory cache."""
        try:
            with sqlite3.connect(self.memory_path) as conn:
                cursor = conn.execute("""
                    SELECT entry_id, memory_type, timestamp, data, tags, 
                           relevance_score, access_count, last_accessed
                    FROM memory_entries
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (self.cache_size,))
                
                for row in cursor.fetchall():
                    entry_id, memory_type, timestamp, data_json, tags_json, \
                    relevance_score, access_count, last_accessed = row
                    
                    entry = MemoryEntry(
                        entry_id=entry_id,
                        memory_type=MemoryType(memory_type),
                        timestamp=timestamp,
                        data=json.loads(data_json),
                        tags=set(json.loads(tags_json)) if tags_json else set(),
                        relevance_score=relevance_score,
                        access_count=access_count,
                        last_accessed=last_accessed
                    )
                    
                    self.memory_cache[entry_id] = entry
                    self.recent_entries.append(entry_id)
                    
        except Exception as e:
            logger.warning(f"Failed to load memory cache: {e}")
    
    # ========== Memory Storage ==========
    
    def store_memory(self, memory_type: MemoryType, data: Dict[str, Any], 
                    tags: Optional[Set[str]] = None) -> str:
        """Store a memory entry."""
        entry_id = f"{memory_type.value}_{int(time.time() * 1000)}_{id(data)}"
        
        entry = MemoryEntry(
            entry_id=entry_id,
            memory_type=memory_type,
            timestamp=time.time(),
            data=data,
            tags=tags or set(),
            relevance_score=1.0
        )
        
        with self.lock:
            # Store in cache
            self.memory_cache[entry_id] = entry
            self.recent_entries.append(entry_id)
            
            # Store in database
            self._persist_memory_entry(entry)
        
        logger.debug(f"Stored memory entry: {entry_id}")
        return entry_id
    
    def _persist_memory_entry(self, entry: MemoryEntry) -> None:
        """Persist memory entry to database."""
        try:
            with sqlite3.connect(self.memory_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO memory_entries 
                    (entry_id, memory_type, timestamp, data, tags, 
                     relevance_score, access_count, last_accessed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry.entry_id,
                    entry.memory_type.value,
                    entry.timestamp,
                    json.dumps(entry.data),
                    json.dumps(list(entry.tags)),
                    entry.relevance_score,
                    entry.access_count,
                    entry.last_accessed
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to persist memory entry: {e}")
    
    # ========== Task Memory Management ==========
    
    def start_task_tracking(self, task_id: str, task_name: str, task_type: str,
                           total_steps: int, context: Dict[str, Any]) -> None:
        """Start tracking a task execution."""
        task_memory = TaskMemory(
            task_id=task_id,
            task_name=task_name,
            task_type=task_type,
            outcome=TaskOutcome.SUCCESS,  # Will be updated
            execution_time=0.0,
            steps_completed=0,
            total_steps=total_steps,
            context_at_start=context.copy(),
            context_at_end={}
        )
        
        with self.lock:
            self.active_tasks[task_id] = task_memory
        
        # Store initial context
        context_id = self.store_context_snapshot(ContextSnapshot(
            timestamp=time.time(),
            system_state=context
        ))
        
        # Store memory entry
        self.store_memory(MemoryType.TASK_EXECUTION, {
            'task_id': task_id,
            'task_name': task_name,
            'task_type': task_type,
            'event': 'task_started',
            'context_id': context_id,
            'total_steps': total_steps
        }, tags={'task_start', task_type})
        
        logger.info(f"Started tracking task: {task_name} ({task_id[:8]})")
    
    def update_task_progress(self, task_id: str, steps_completed: int,
                            context: Optional[Dict[str, Any]] = None) -> None:
        """Update task progress."""
        with self.lock:
            if task_id not in self.active_tasks:
                logger.warning(f"Task not found for progress update: {task_id}")
                return
            
            task_memory = self.active_tasks[task_id]
            task_memory.steps_completed = steps_completed
            
            if context:
                task_memory.context_at_end = context.copy()
        
        # Store progress update
        self.store_memory(MemoryType.TASK_EXECUTION, {
            'task_id': task_id,
            'event': 'progress_update',
            'steps_completed': steps_completed,
            'total_steps': task_memory.total_steps,
            'progress_percent': (steps_completed / task_memory.total_steps) * 100
        }, tags={'task_progress', task_memory.task_type})
    
    def complete_task_tracking(self, task_id: str, outcome: TaskOutcome,
                              execution_time: float, context: Dict[str, Any],
                              user_feedback: Optional[str] = None) -> None:
        """Complete task tracking and store results."""
        with self.lock:
            if task_id not in self.active_tasks:
                logger.warning(f"Task not found for completion: {task_id}")
                return
            
            task_memory = self.active_tasks[task_id]
            task_memory.outcome = outcome
            task_memory.execution_time = execution_time
            task_memory.context_at_end = context.copy()
            task_memory.user_feedback = user_feedback
            
            # Analyze for patterns
            self._analyze_task_patterns(task_memory)
            
            # Store in database
            self._persist_task_memory(task_memory)
            
            # Remove from active tasks
            del self.active_tasks[task_id]
        
        # Store completion event
        self.store_memory(MemoryType.TASK_EXECUTION, {
            'task_id': task_id,
            'event': 'task_completed',
            'outcome': outcome.value,
            'execution_time': execution_time,
            'user_feedback': user_feedback
        }, tags={'task_completion', outcome.value, task_memory.task_type})
        
        logger.info(f"Completed task tracking: {task_memory.task_name} ({outcome.value})")
    
    def _persist_task_memory(self, task_memory: TaskMemory) -> None:
        """Persist task memory to database."""
        try:
            with sqlite3.connect(self.memory_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO task_memory
                    (task_id, task_name, task_type, outcome, execution_time,
                     steps_completed, total_steps, context_at_start, context_at_end,
                     user_feedback, learned_patterns, optimization_hints, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task_memory.task_id,
                    task_memory.task_name,
                    task_memory.task_type,
                    task_memory.outcome.value,
                    task_memory.execution_time,
                    task_memory.steps_completed,
                    task_memory.total_steps,
                    json.dumps(task_memory.context_at_start),
                    json.dumps(task_memory.context_at_end),
                    task_memory.user_feedback,
                    json.dumps(task_memory.learned_patterns),
                    json.dumps(task_memory.optimization_hints),
                    time.time()
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to persist task memory: {e}")
    
    # ========== Context Management ==========
    
    def store_context_snapshot(self, context: ContextSnapshot) -> str:
        """Store a context snapshot."""
        snapshot_id = f"context_{int(time.time() * 1000)}"
        
        with self.lock:
            self.context_cache[snapshot_id] = context
        
        # Persist to database
        try:
            with sqlite3.connect(self.memory_path) as conn:
                conn.execute("""
                    INSERT INTO context_snapshots
                    (snapshot_id, timestamp, screen_analysis, active_applications,
                     user_activity, system_state, environmental_factors)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    snapshot_id,
                    context.timestamp,
                    json.dumps(context.screen_analysis) if context.screen_analysis else None,
                    json.dumps(context.active_applications),
                    json.dumps(context.user_activity) if context.user_activity else None,
                    json.dumps(context.system_state),
                    json.dumps(context.environmental_factors)
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to store context snapshot: {e}")
        
        return snapshot_id
    
    def get_context_snapshot(self, snapshot_id: str) -> Optional[ContextSnapshot]:
        """Retrieve a context snapshot."""
        # Check cache first
        with self.lock:
            if snapshot_id in self.context_cache:
                return self.context_cache[snapshot_id]
        
        # Load from database
        try:
            with sqlite3.connect(self.memory_path) as conn:
                cursor = conn.execute("""
                    SELECT timestamp, screen_analysis, active_applications,
                           user_activity, system_state, environmental_factors
                    FROM context_snapshots
                    WHERE snapshot_id = ?
                """, (snapshot_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                timestamp, screen_analysis, active_applications, \
                user_activity, system_state, environmental_factors = row
                
                context = ContextSnapshot(
                    timestamp=timestamp,
                    screen_analysis=json.loads(screen_analysis) if screen_analysis else None,
                    active_applications=json.loads(active_applications),
                    user_activity=json.loads(user_activity) if user_activity else None,
                    system_state=json.loads(system_state),
                    environmental_factors=json.loads(environmental_factors)
                )
                
                # Cache for future use
                with self.lock:
                    self.context_cache[snapshot_id] = context
                
                return context
                
        except Exception as e:
            logger.error(f"Failed to retrieve context snapshot: {e}")
            return None
    
    # ========== Pattern Recognition and Learning ==========
    
    def _analyze_task_patterns(self, task_memory: TaskMemory) -> None:
        """Analyze task execution for patterns."""
        # Add to success/failure patterns
        pattern = {
            'task_type': task_memory.task_type,
            'execution_time': task_memory.execution_time,
            'steps_completed': task_memory.steps_completed,
            'total_steps': task_memory.total_steps,
            'context': task_memory.context_at_start,
            'outcome': task_memory.outcome.value
        }
        
        if task_memory.outcome == TaskOutcome.SUCCESS:
            self.success_patterns.append(pattern)
        else:
            self.failure_patterns.append(pattern)
        
        # Learn optimization hints
        if task_memory.outcome == TaskOutcome.SUCCESS:
            optimization_hints = self._generate_optimization_hints(task_memory)
            task_memory.optimization_hints.extend(optimization_hints)
    
    def _generate_optimization_hints(self, task_memory: TaskMemory) -> List[str]:
        """Generate optimization hints based on successful task execution."""
        hints = []
        
        # Fast execution hint
        if task_memory.execution_time < 5.0:
            hints.append("fast_execution_pattern")
        
        # Complete execution hint
        if task_memory.steps_completed == task_memory.total_steps:
            hints.append("complete_execution_pattern")
        
        # Context-specific hints
        if 'active_app' in task_memory.context_at_start:
            app = task_memory.context_at_start['active_app']
            hints.append(f"successful_with_{app}")
        
        return hints
    
    def get_optimization_suggestions(self, task_type: str, context: Dict[str, Any]) -> List[str]:
        """Get optimization suggestions for a task type."""
        suggestions = []
        
        # Look for successful patterns
        for pattern in self.success_patterns:
            if pattern['task_type'] == task_type:
                # Check context similarity
                context_match = self._calculate_context_similarity(context, pattern['context'])
                if context_match > 0.7:
                    suggestions.append(f"Similar successful execution took {pattern['execution_time']:.1f}s")
        
        # Add learned optimizations
        if task_type in self.learned_optimizations:
            suggestions.append(self.learned_optimizations[task_type])
        
        return suggestions
    
    def _calculate_context_similarity(self, context1: Dict[str, Any], context2: Dict[str, Any]) -> float:
        """Calculate similarity between two contexts."""
        # Simple key-based similarity
        common_keys = set(context1.keys()) & set(context2.keys())
        total_keys = set(context1.keys()) | set(context2.keys())
        
        if not total_keys:
            return 0.0
        
        similarity = len(common_keys) / len(total_keys)
        
        # Check value similarity for common keys
        value_matches = 0
        for key in common_keys:
            if context1[key] == context2[key]:
                value_matches += 1
        
        if common_keys:
            value_similarity = value_matches / len(common_keys)
            similarity = (similarity + value_similarity) / 2
        
        return similarity
    
    # ========== Memory Retrieval ==========
    
    def search_memory(self, query: str, memory_type: Optional[MemoryType] = None,
                     tags: Optional[Set[str]] = None, limit: int = 10) -> List[MemoryEntry]:
        """Search memory entries."""
        results = []
        
        with self.lock:
            for entry in self.memory_cache.values():
                # Filter by type if specified
                if memory_type and entry.memory_type != memory_type:
                    continue
                
                # Filter by tags if specified
                if tags and not tags.intersection(entry.tags):
                    continue
                
                # Simple text search in data
                if query.lower() in json.dumps(entry.data).lower():
                    # Update access tracking
                    entry.access_count += 1
                    entry.last_accessed = time.time()
                    results.append(entry)
        
        # Sort by relevance and recency
        results.sort(key=lambda e: (e.relevance_score, e.timestamp), reverse=True)
        
        return results[:limit]
    
    def get_recent_tasks(self, task_type: Optional[str] = None, limit: int = 10) -> List[TaskMemory]:
        """Get recent task executions."""
        try:
            with sqlite3.connect(self.memory_path) as conn:
                if task_type:
                    cursor = conn.execute("""
                        SELECT task_id, task_name, task_type, outcome, execution_time,
                               steps_completed, total_steps, context_at_start, context_at_end,
                               user_feedback, learned_patterns, optimization_hints
                        FROM task_memory
                        WHERE task_type = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (task_type, limit))
                else:
                    cursor = conn.execute("""
                        SELECT task_id, task_name, task_type, outcome, execution_time,
                               steps_completed, total_steps, context_at_start, context_at_end,
                               user_feedback, learned_patterns, optimization_hints
                        FROM task_memory
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (limit,))
                
                tasks = []
                for row in cursor.fetchall():
                    task_id, task_name, task_type, outcome, execution_time, \
                    steps_completed, total_steps, context_start, context_end, \
                    user_feedback, learned_patterns, optimization_hints = row
                    
                    task = TaskMemory(
                        task_id=task_id,
                        task_name=task_name,
                        task_type=task_type,
                        outcome=TaskOutcome(outcome),
                        execution_time=execution_time,
                        steps_completed=steps_completed,
                        total_steps=total_steps,
                        context_at_start=json.loads(context_start),
                        context_at_end=json.loads(context_end),
                        user_feedback=user_feedback,
                        learned_patterns=json.loads(learned_patterns) if learned_patterns else [],
                        optimization_hints=json.loads(optimization_hints) if optimization_hints else []
                    )
                    tasks.append(task)
                
                return tasks
                
        except Exception as e:
            logger.error(f"Failed to retrieve recent tasks: {e}")
            return []
    
    # ========== Statistics and Analytics ==========
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics."""
        with self.lock:
            cache_stats = {
                'cached_entries': len(self.memory_cache),
                'active_tasks': len(self.active_tasks),
                'success_patterns': len(self.success_patterns),
                'failure_patterns': len(self.failure_patterns),
                'context_snapshots': len(self.context_cache)
            }
        
        # Database statistics
        try:
            with sqlite3.connect(self.memory_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM memory_entries")
                total_entries = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM task_memory")
                total_tasks = cursor.fetchone()[0]
                
                cursor = conn.execute("""
                    SELECT outcome, COUNT(*) 
                    FROM task_memory 
                    GROUP BY outcome
                """)
                task_outcomes = dict(cursor.fetchall())
                
        except Exception as e:
            logger.error(f"Failed to get database statistics: {e}")
            total_entries = 0
            total_tasks = 0
            task_outcomes = {}
        
        return {
            'cache_statistics': cache_stats,
            'database_statistics': {
                'total_memory_entries': total_entries,
                'total_tasks': total_tasks,
                'task_outcomes': task_outcomes
            }
        }
    
    # ========== Cleanup and Maintenance ==========
    
    def cleanup_old_entries(self, days_to_keep: int = 30) -> int:
        """Clean up old memory entries."""
        cutoff_time = time.time() - (days_to_keep * 24 * 3600)
        
        try:
            with sqlite3.connect(self.memory_path) as conn:
                # Delete old memory entries
                cursor = conn.execute("""
                    DELETE FROM memory_entries 
                    WHERE timestamp < ? AND access_count = 0
                """, (cutoff_time,))
                deleted_entries = cursor.rowcount
                
                # Delete old context snapshots
                cursor = conn.execute("""
                    DELETE FROM context_snapshots 
                    WHERE timestamp < ?
                """, (cutoff_time,))
                deleted_contexts = cursor.rowcount
                
                conn.commit()
                
                logger.info(f"Cleaned up {deleted_entries} memory entries and {deleted_contexts} context snapshots")
                return deleted_entries + deleted_contexts
                
        except Exception as e:
            logger.error(f"Failed to cleanup old entries: {e}")
            return 0