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
            
    async def cleanup(self):
        """Cleanup resources used by the memory system."""
        try:
            self.initialized = False
            self.memory = []
            logger.info("Memory system cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up memory system: {e}") 