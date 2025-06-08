#!/usr/bin/env python3
"""
Task Context Awareness

Enhances task memory with contextual awareness of user state, 
screen content, and running applications to provide richer
task execution context.

This module links task state with the broader memory system
for improved context awareness during task execution.
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/task_context.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("task_context")

class TaskContextAwareness:
    """
    Enhances task memory with contextual awareness
    
    Links task state with broader memory system for improved
    context during task execution, including:
    - User activity state
    - Screen content
    - Running applications
    - Historical context
    """
    
    def __init__(self, memory_system=None):
        """Initialize task context awareness"""
        self.memory_system = memory_system
        self.memory_system_available = memory_system is not None
        self.task_contexts = {}
        self.last_context_update = {}
        
        # Set update frequency
        self.context_update_interval = 10  # seconds
    
    async def initialize(self):
        """Initialize task context awareness"""
        if not self.memory_system_available:
            logger.warning("Memory system not available for context awareness")
            return
            
        logger.info("Task context awareness initialized")
        
        # Start background context updates
        asyncio.create_task(self._periodic_context_updates())
    
    async def _periodic_context_updates(self):
        """Periodically update context for active tasks"""
        if not self.memory_system_available:
            return
            
        while True:
            try:
                # Update context for all active tasks
                for task_id in list(self.task_contexts.keys()):
                    # Check if update is needed
                    last_update = self.last_context_update.get(task_id, 0)
                    if time.time() - last_update > self.context_update_interval:
                        await self.update_task_context(task_id)
                
                logger.debug(f"Updated context for {len(self.task_contexts)} active tasks")
            except Exception as e:
                logger.error(f"Error in periodic context updates: {e}")
                
            await asyncio.sleep(5)  # Check every 5 seconds
    
    async def register_task(self, task_id: str, description: str):
        """Register a new task for context awareness"""
        if not self.memory_system_available:
            logger.warning("Memory system not available for context registration")
            return
            
        # Initialize task context
        self.task_contexts[task_id] = {
            "task_id": task_id,
            "description": description,
            "registered_at": time.time(),
            "last_updated": time.time(),
            "user_activity": {},
            "screen_content": {},
            "active_applications": [],
            "execution_environment": {},
            "related_memories": []
        }
        
        # Mark for immediate update
        self.last_context_update[task_id] = 0
        
        logger.info(f"Registered task {task_id} for context awareness")
    
    async def update_task_context(self, task_id: str):
        """Update context for a task"""
        if not self.memory_system_available or task_id not in self.task_contexts:
            return
            
        try:
            # Get latest short-term memories
            latest_memories = await self._get_latest_memories(10)
            
            # Extract context information
            user_activity = self._extract_user_activity(latest_memories)
            screen_content = self._extract_screen_content(latest_memories)
            active_apps = self._extract_active_applications(latest_memories)
            
            # Update task context
            self.task_contexts[task_id].update({
                "user_activity": user_activity,
                "screen_content": screen_content,
                "active_applications": active_apps,
                "last_updated": time.time()
            })
            
            # Record update time
            self.last_context_update[task_id] = time.time()
            
            # Add related memories
            await self._find_related_memories(task_id)
            
            logger.debug(f"Updated context for task {task_id}")
            
        except Exception as e:
            logger.error(f"Error updating task context: {e}")
    
    async def _get_latest_memories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get latest memories from memory system"""
        if not self.memory_system_available:
            return []
            
        try:
            # Get recent memory from memory system
            return self.memory_system.short_term_memory[:limit]
        except Exception as e:
            logger.error(f"Error getting latest memories: {e}")
            return []
    
    def _extract_user_activity(self, memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract user activity information from memories"""
        # Initialize with default values
        activity = {
            "primary_activity": "unknown",
            "workflow_stage": "unknown",
            "productivity_level": "medium",
            "last_updated": time.time()
        }
        
        # Look for intelligent_system_state memories
        for memory in memories:
            if memory.get("memory_type") == "intelligent_system_state":
                if "user_activity" in memory:
                    user_act = memory["user_activity"]
                    activity["primary_activity"] = user_act.get("primary_activity", activity["primary_activity"])
                    activity["application_used"] = user_act.get("application_used", "")
                    activity["professional_context"] = user_act.get("professional_context", "")
                    
                    # Extract activity specifics
                    if "activity_specifics" in user_act and isinstance(user_act["activity_specifics"], list):
                        activity["activity_specifics"] = user_act["activity_specifics"]
                    
                    # Extract productivity score
                    activity["productivity_score"] = user_act.get("productivity_score", 0.5)
                
                if "context_analysis" in memory:
                    ctx = memory["context_analysis"]
                    activity["workflow_stage"] = ctx.get("workflow_stage", activity["workflow_stage"])
                    activity["user_intent"] = ctx.get("user_intent", "")
                    activity["productivity_context"] = ctx.get("productivity_context", "")
                    activity["meaningful_interaction"] = ctx.get("meaningful_interaction", False)
                
                # Use the latest timestamp
                if "timestamp" in memory:
                    try:
                        activity["last_updated"] = datetime.fromisoformat(memory["timestamp"]).timestamp()
                    except:
                        pass
                
                # Once we found a valid memory, we can break
                break
        
        return activity
    
    def _extract_screen_content(self, memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract screen content information from memories"""
        # Initialize with default values
        screen_info = {
            "has_content": False,
            "content_type": "unknown",
            "last_updated": time.time()
        }
        
        # Look for screen sensor memories with content
        for memory in memories:
            if memory.get("memory_type") in ["screen_content", "visual_content"]:
                screen_info["has_content"] = True
                
                # Extract content type and summary if available
                if "content_type" in memory:
                    screen_info["content_type"] = memory["content_type"]
                
                if "content_summary" in memory:
                    screen_info["content_summary"] = memory["content_summary"]
                
                if "ui_elements" in memory and isinstance(memory["ui_elements"], list):
                    screen_info["ui_elements_count"] = len(memory["ui_elements"])
                    
                    # Extract UI elements of interest
                    buttons = []
                    text_fields = []
                    for element in memory["ui_elements"]:
                        if element.get("type") == "button":
                            buttons.append(element.get("text", ""))
                        elif element.get("type") in ["text_field", "input"]:
                            text_fields.append(element.get("label", ""))
                    
                    if buttons:
                        screen_info["buttons"] = buttons[:5]  # Limit to 5 buttons
                    if text_fields:
                        screen_info["text_fields"] = text_fields[:5]  # Limit to 5 text fields
                
                # Use the latest timestamp
                if "timestamp" in memory:
                    try:
                        screen_info["last_updated"] = datetime.fromisoformat(memory["timestamp"]).timestamp()
                    except:
                        pass
                
                # Once we found a valid memory, we can break
                break
        
        return screen_info
    
    def _extract_active_applications(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract active applications information from memories"""
        active_apps = []
        
        # Look for process sensor memories with applications
        for memory in memories:
            if memory.get("memory_type") == "intelligent_system_state":
                if "user_activity" in memory and "current_applications" in memory["user_activity"]:
                    apps = memory["user_activity"]["current_applications"]
                    
                    # Convert string apps to dicts if needed
                    processed_apps = []
                    for app in apps:
                        if isinstance(app, str):
                            processed_apps.append({"name": app})
                        elif isinstance(app, dict):
                            processed_apps.append(app)
                    
                    active_apps = processed_apps[:10]  # Limit to 10 apps
                    break
            
            # Also check direct process sensor data
            elif memory.get("memory_type") == "process_data" and "active_apps" in memory:
                apps = memory["active_apps"]
                
                # Convert to consistent format
                processed_apps = []
                for app in apps:
                    if isinstance(app, str):
                        processed_apps.append({"name": app})
                    elif isinstance(app, dict):
                        processed_apps.append(app)
                
                active_apps = processed_apps[:10]  # Limit to 10 apps
                break
        
        return active_apps
    
    async def _find_related_memories(self, task_id: str):
        """Find memories related to the task"""
        if not self.memory_system_available or task_id not in self.task_contexts:
            return
            
        try:
            # Get task description
            description = self.task_contexts[task_id]["description"]
            
            # Search memory for related content
            search_results = await self.memory_system.search_memory(description, limit=5)
            
            # Store related memory IDs
            related_memories = []
            for result in search_results:
                if "memory_id" in result:
                    related_memories.append({
                        "memory_id": result["memory_id"],
                        "memory_type": result.get("memory_type", "unknown"),
                        "timestamp": result.get("timestamp", ""),
                        "relevance": result.get("relevance", 0.0)
                    })
            
            # Update task context
            self.task_contexts[task_id]["related_memories"] = related_memories
            
            logger.debug(f"Found {len(related_memories)} related memories for task {task_id}")
            
        except Exception as e:
            logger.error(f"Error finding related memories: {e}")
    
    async def unregister_task(self, task_id: str):
        """Unregister a task from context awareness"""
        if task_id in self.task_contexts:
            del self.task_contexts[task_id]
        
        if task_id in self.last_context_update:
            del self.last_context_update[task_id]
        
        logger.debug(f"Unregistered task {task_id} from context awareness")
    
    async def get_task_context(self, task_id: str) -> Dict[str, Any]:
        """Get current context for a task"""
        if not self.memory_system_available or task_id not in self.task_contexts:
            return {}
            
        # Make sure context is updated
        if time.time() - self.last_context_update.get(task_id, 0) > self.context_update_interval:
            await self.update_task_context(task_id)
            
        return self.task_contexts.get(task_id, {})
    
    async def enrich_task_data(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich task data with contextual information"""
        if not self.memory_system_available:
            return task_data
            
        try:
            task_id = task_data.get("task_id")
            if not task_id:
                return task_data
                
            # Get task context
            context = await self.get_task_context(task_id)
            if not context:
                # Register and get context if not registered yet
                await self.register_task(task_id, task_data.get("description", ""))
                context = await self.get_task_context(task_id)
            
            # Add context to task data if available
            if context:
                # Add or update memory_context
                task_data.setdefault("memory_context", {})
                task_data["memory_context"]["context_aware"] = True
                task_data["memory_context"]["last_context_update"] = context.get("last_updated", time.time())
                
                # Add environment context
                task_data.setdefault("environment_context", {})
                task_data["environment_context"].update({
                    "user_activity": context.get("user_activity", {}),
                    "active_applications": context.get("active_applications", []),
                    "screen_content_available": context.get("screen_content", {}).get("has_content", False)
                })
                
                # Add related memories
                if "related_memories" in context and context["related_memories"]:
                    task_data.setdefault("related_context", {})
                    task_data["related_context"]["memory_references"] = context["related_memories"]
            
            return task_data
            
        except Exception as e:
            logger.error(f"Error enriching task data: {e}")
            return task_data

# Create singleton instance
task_context_awareness = TaskContextAwareness()

# API functions
async def initialize(memory_system=None):
    """Initialize task context awareness"""
    task_context_awareness.memory_system = memory_system
    task_context_awareness.memory_system_available = memory_system is not None
    await task_context_awareness.initialize()

async def register_task(task_id: str, description: str):
    """Register a task for context awareness"""
    await task_context_awareness.register_task(task_id, description)

async def get_task_context(task_id: str) -> Dict[str, Any]:
    """Get current context for a task"""
    return await task_context_awareness.get_task_context(task_id)

async def enrich_task_data(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich task data with contextual information"""
    return await task_context_awareness.enrich_task_data(task_data)

async def unregister_task(task_id: str):
    """Unregister a task from context awareness"""
    await task_context_awareness.unregister_task(task_id)