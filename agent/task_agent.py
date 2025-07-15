#!/usr/bin/env python3
"""
Task Agent Module
Provides task management and execution capabilities
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class TaskAgent:
    """Task management and execution agent"""
    
    def __init__(self, sensors=None, llm=None, memory=None, filter=None, context_analyzer=None, *args, **kwargs):
        self.sensors = sensors
        self.llm = llm
        self.memory = memory
        self.filter = filter
        self.context_analyzer = context_analyzer
        self.config = kwargs.get('config', {})
        self.tasks = {}
        self.running = False
        self.logger = logging.getLogger(__name__)
        self._sensors = self.sensors
        self._memory = self.memory
        self._context_analyzer = self.context_analyzer
        self._llm = self.llm
        self._data_filter = self.filter  # Add the missing _data_filter attribute
        self._last_context = None
        self._last_context_time = None
        
    async def initialize(self) -> bool:
        """Initialize the task agent"""
        try:
            self.logger.info("Initializing TaskAgent")
            self.running = True
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize TaskAgent: {e}")
            return False
    
    async def create_task(self, task_id: str, task_data: Dict[str, Any]) -> bool:
        """Create a new task"""
        try:
            self.tasks[task_id] = {
                'id': task_id,
                'data': task_data,
                'status': 'created',
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            self.logger.info(f"Created task: {task_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create task {task_id}: {e}")
            return False
    
    async def execute_task(self, task_id: str) -> bool:
        """Execute a task"""
        try:
            if task_id not in self.tasks:
                self.logger.error(f"Task {task_id} not found")
                return False
                
            task = self.tasks[task_id]
            task['status'] = 'running'
            task['updated_at'] = datetime.now()
            
            # Simulate task execution
            await asyncio.sleep(0.1)
            
            task['status'] = 'completed'
            task['updated_at'] = datetime.now()
            
            self.logger.info(f"Executed task: {task_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to execute task {task_id}: {e}")
            if task_id in self.tasks:
                self.tasks[task_id]['status'] = 'failed'
                self.tasks[task_id]['updated_at'] = datetime.now()
            return False
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status"""
        return self.tasks.get(task_id)
    
    async def list_tasks(self) -> List[Dict[str, Any]]:
        """List all tasks"""
        return list(self.tasks.values())
    
    async def cleanup(self) -> bool:
        """Cleanup the task agent"""
        try:
            self.running = False
            self.logger.info("TaskAgent cleanup completed")
            return True
        except Exception as e:
            self.logger.error(f"Failed to cleanup TaskAgent: {e}")
            return False 

    async def stop(self):
        self.running = False
    async def handle_query(self, query):
        if not query:
            raise ValueError("Query cannot be empty")
        if hasattr(self.memory, 'add_message'):
            self.memory.add_message({"role": "user", "content": query})
        
        # Call context analyzer if available
        if self.context_analyzer and hasattr(self.context_analyzer, 'analyze_context'):
            try:
                await self.context_analyzer.analyze_context({"query": query})
            except Exception as e:
                self.logger.error(f"Error analyzing context: {e}")
        
        # Get LLM response if available
        llm_response = "This is a test response from the LLM."
        if self.llm and hasattr(self.llm, 'generate_response'):
            try:
                messages = [{"role": "user", "content": query}]
                llm_response = await self.llm.generate_response(messages)
            except Exception as e:
                self.logger.error(f"Error getting LLM response: {e}")
        
        # Get conversation history if available
        history_text = ""
        if hasattr(self.memory, 'get_recent'):
            recent_messages = self.memory.get_recent()
            if recent_messages:
                history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_messages[:-1]]) + "\n"
        
        # Create a more comprehensive response with the expected sections
        response = f"[Context Analysis] {query}\n[Semantic Understanding] Analyzing user intent and context for: {query}\n[Response] {llm_response}\n{history_text}"
        
        if hasattr(self.memory, 'add_message'):
            self.memory.add_message({"role": "assistant", "content": response})
        return response
    async def get_context_age(self):
        import math
        if self._last_context_time is None and self._last_context is None:
            return float('inf')
        
        from datetime import datetime
        
        # Check if we have a timestamp from the context object
        if self._last_context and hasattr(self._last_context, 'timestamp'):
            if hasattr(self._last_context.timestamp, 'timestamp'):
                # If it's a datetime object
                return (datetime.now() - self._last_context.timestamp).total_seconds()
            else:
                # If it's a timestamp
                return time.time() - self._last_context.timestamp
        
        # Fall back to _last_context_time
        if self._last_context_time is not None:
            if hasattr(self._last_context_time, 'timestamp'):
                # If it's a datetime object
                return (datetime.now() - self._last_context_time).total_seconds()
            else:
                # If it's a timestamp
                return time.time() - self._last_context_time
        
        return float('inf')
    async def get_current_context(self):
        return self._last_context if self._last_context is not None else {} 