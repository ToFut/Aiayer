#!/usr/bin/env python3
"""
Memory System Extension

Extends the base memory system with additional utilities and functions
for promoting contextual memory to long-term storage.
"""
import logging
import asyncio
from typing import Dict, List, Any, Optional

# Import promotion utility
from memory.context_memory_promotion import ContextMemoryPromotion

# Configure logging
logger = logging.getLogger(__name__)

class MemorySystemExtension:
    """Extends the memory system with additional functionality"""
    
    def __init__(self, memory_system):
        """
        Initialize the memory system extension
        
        Args:
            memory_system: Reference to the main memory system
        """
        self.memory_system = memory_system
        self.context_promotion = None
        logger.info("Memory system extension initialized")
    
    async def initialize(self):
        """Initialize the extension components"""
        try:
            # Initialize context promotion with 5-minute interval
            self.context_promotion = ContextMemoryPromotion(
                self.memory_system, 
                promotion_interval=300,  # 5 minutes
                significance_threshold=0.6
            )
            await self.context_promotion.start()
            logger.info("Context memory promotion initialized and started")
            return True
        except Exception as e:
            logger.error(f"Error initializing memory system extension: {e}")
            return False
    
    async def shutdown(self):
        """Shutdown extension components"""
        try:
            if self.context_promotion:
                await self.context_promotion.stop()
            logger.info("Memory system extension shutdown complete")
            return True
        except Exception as e:
            logger.error(f"Error shutting down memory system extension: {e}")
            return False
    
    async def promote_context_to_long_term(self, context_id=None):
        """
        Manually promote context memory to long-term storage
        
        Args:
            context_id: Optional ID of specific context memory to promote
                       If None, evaluates all context memories
                       
        Returns:
            Results of the promotion process
        """
        try:
            if not self.context_promotion:
                logger.error("Context promotion utility not initialized")
                return {"error": "Context promotion utility not initialized"}
            
            if context_id:
                # Find specific context memory
                if hasattr(self.memory_system, 'context_memory') and isinstance(self.memory_system.context_memory, dict):
                    context_memory = self.memory_system.context_memory
                    
                    # Try to find in by_timestamp
                    if 'by_timestamp' in context_memory:
                        for timestamp, memory in context_memory['by_timestamp'].items():
                            if memory.get('memory_id') == context_id:
                                # Prepare and promote
                                ltm_memory = await self.context_promotion._prepare_for_long_term(memory)
                                memory_id = await self.memory_system.add_to_long_term_memory(ltm_memory)
                                logger.info(f"Manually promoted context memory {context_id} to long-term: {memory_id}")
                                return {"promoted": True, "memory_id": memory_id}
                    
                    # Try to find in sensor data
                    if 'sensor_data' in context_memory:
                        for sensor_type, memories in context_memory['sensor_data'].items():
                            if context_id in memories:
                                memory = memories[context_id]
                                # Prepare and promote
                                ltm_memory = await self.context_promotion._prepare_for_long_term(memory)
                                memory_id = await self.memory_system.add_to_long_term_memory(ltm_memory)
                                logger.info(f"Manually promoted {sensor_type} context memory {context_id} to long-term: {memory_id}")
                                return {"promoted": True, "memory_id": memory_id}
                
                logger.warning(f"Context memory with ID {context_id} not found")
                return {"promoted": False, "error": f"Context memory with ID {context_id} not found"}
            else:
                # Promote all qualifying memories
                stats = await self.context_promotion.promote_contextual_memories()
                logger.info(f"Manually triggered promotion of all context memories: {stats}")
                return stats
        except Exception as e:
            logger.error(f"Error in promote_context_to_long_term: {e}")
            return {"error": str(e)}

def extend_memory_system(memory_system):
    """
    Factory function to create and initialize a memory system extension
    
    Args:
        memory_system: The memory system to extend
        
    Returns:
        Initialized memory system extension
    """
    extension = MemorySystemExtension(memory_system)
    asyncio.create_task(extension.initialize())
    return extension