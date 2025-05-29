#!/usr/bin/env python3
"""
Memory System
Handles context and memory management for the chat system.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MemorySystem:
    def __init__(self):
        self.initialized = False
        self.memory = []
        self.max_memory_items = 100
        
    async def initialize(self) -> bool:
        """Initialize the memory system."""
        try:
            self.initialized = True
            logger.info("Memory system initialized")
            return True
        except Exception as e:
            logger.error(f"Error initializing memory system: {e}")
            return False
            
    async def get_context_summary(self, query: Optional[str] = None, limit: int = 3) -> List[Dict[str, Any]]:
        """Get relevant context for a query."""
        try:
            if not self.initialized:
                raise RuntimeError("Memory system not initialized")
                
            logger.info(f"Current memory size: {len(self.memory)}")
            logger.info(f"Memory contents: {json.dumps(self.memory, indent=2)}")
                
            # If no query provided, return the most recent items
            if not query:
                return self.memory[-limit:]
                
            # For now, just return the most recent items
            # In a real implementation, this would use semantic search to find relevant context
            recent_items = self.memory[-limit:]
            
            # Format the items for the LLM
            formatted_items = []
            for item in recent_items:
                if isinstance(item, dict):
                    content = item.get('content', '')
                    if content:
                        formatted_items.append({
                            'role': item.get('role', 'user'),
                            'content': content
                        })
            
            logger.info(f"Retrieved {len(formatted_items)} context items")
            return formatted_items
            
        except Exception as e:
            logger.error(f"Error getting context summary: {e}")
            raise
            
    async def add_to_context_memory(self, item: Dict[str, Any]) -> bool:
        """Add an item to the context memory."""
        try:
            if not self.initialized:
                raise RuntimeError("Memory system not initialized")
                
            # Add timestamp if not present
            if 'timestamp' not in item:
                item['timestamp'] = datetime.now().isoformat()
                
            logger.info(f"Adding item to memory: {json.dumps(item, indent=2)}")
                
            # Add to memory
            self.memory.append(item)
            
            # Trim memory if it gets too large
            if len(self.memory) > self.max_memory_items:
                self.memory = self.memory[-self.max_memory_items:]
                
            logger.info(f"Added item to context memory. Memory size: {len(self.memory)}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding to context memory: {e}")
            raise
            
    def get_latest_context_summary(self) -> Dict[str, Any]:
        """Get the latest context summary from memory"""
        try:
            if not self.initialized:
                logger.warning("Memory system not initialized when getting latest context summary")
                return {}
                
            # If no memory items, return empty context
            if not self.memory:
                return {}
                
            # Get the most recent memory items
            recent_items = self.memory[-3:]  # Last 3 items
            
            # Extract key information for context summary
            current_activity = {}
            recent_actions = []
            user_intent = ""
            current_task = ""
            related_insights = []
            
            # Process recent items to extract relevant context
            for item in recent_items:
                if isinstance(item, dict):
                    # Add to recent actions
                    if 'content' in item and 'role' in item:
                        recent_actions.append({
                            'role': item.get('role', 'user'),
                            'content': item.get('content', '')[:100],  # Truncate long content
                            'timestamp': item.get('timestamp', datetime.now().isoformat())
                        })
                    
                    # If it's a user message, use it to infer user intent and current task
                    if item.get('role') == 'user' and not user_intent and 'content' in item:
                        user_intent = item.get('content', '')[:200]  # Use truncated content as intent
                        current_task = f"Responding to: {user_intent[:50]}..."  # Simplified task description
            
            # Build the context summary
            context_summary = {
                'current_activity': current_activity,
                'recent_actions': recent_actions,
                'user_intent': user_intent,
                'current_task': current_task,
                'related_insights': related_insights,
                'last_updated': datetime.now().isoformat()
            }
            
            logger.info(f"Generated context summary with {len(recent_actions)} recent actions")
            return context_summary
            
        except Exception as e:
            logger.error(f"Error getting latest context summary: {e}")
            return {}
    
    async def cleanup(self):
        """Cleanup resources used by the memory system."""
        try:
            self.initialized = False
            self.memory = []
            logger.info("Memory system cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up memory system: {e}") 