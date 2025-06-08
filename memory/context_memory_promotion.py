#!/usr/bin/env python3
"""
Context Memory Promotion Utility

Analyzes contextual memory to identify valuable insights and promotes
them to long-term memory for permanent storage.
"""
import os
import json
import logging
import asyncio
import time
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

class ContextMemoryPromotion:
    """Identifies and promotes valuable contextual memories to long-term storage"""
    
    def __init__(self, memory_system, promotion_interval: int = 300, 
                 significance_threshold: float = 0.6):
        """
        Initialize the context memory promotion utility
        
        Args:
            memory_system: Reference to the memory system
            promotion_interval: Seconds between promotion runs (default: 5 min)
            significance_threshold: Threshold for considering contextual data significant
        """
        self.memory_system = memory_system
        self.promotion_interval = promotion_interval
        self.significance_threshold = significance_threshold
        self.running = False
        self.last_promotion = 0
        self.promotion_stats = {
            "total_runs": 0,
            "promoted_items": 0,
            "last_run": None
        }
        self.storage_path = "memory/memory/context_promotion_stats.json"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        
        logger.info(f"Context memory promotion initialized with "
                   f"interval={promotion_interval}s, "
                   f"significance_threshold={significance_threshold}")
    
    async def start(self):
        """Start the context promotion process"""
        if self.running:
            logger.warning("Context promotion process already running")
            return False
            
        try:
            self.running = True
            logger.info("Starting context memory promotion process")
            
            # Start promotion loop
            asyncio.create_task(self._promotion_loop())
            return True
        except Exception as e:
            logger.error(f"Error starting context memory promotion: {e}")
            logger.error(traceback.format_exc())
            self.running = False
            return False
    
    async def stop(self):
        """Stop the promotion process"""
        try:
            self.running = False
            logger.info("Stopping context memory promotion process")
            
            # Save stats
            await self._save_stats()
            return True
        except Exception as e:
            logger.error(f"Error stopping context memory promotion: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def _save_stats(self):
        """Save promotion stats to file"""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.promotion_stats, f, indent=2)
            logger.info(f"Saved promotion stats to {self.storage_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving promotion stats: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def _promotion_loop(self):
        """Main promotion loop that runs periodically"""
        try:
            while self.running:
                # Check if it's time to promote
                current_time = time.time()
                if current_time - self.last_promotion >= self.promotion_interval:
                    logger.info("Starting scheduled context memory promotion")
                    await self.promote_contextual_memories()
                    self.last_promotion = current_time
                
                # Wait for next check
                await asyncio.sleep(30)  # Check every 30 seconds
                
        except asyncio.CancelledError:
            logger.info("Promotion loop cancelled")
        except Exception as e:
            logger.error(f"Error in promotion loop: {e}")
            logger.error(traceback.format_exc())
    
    async def promote_contextual_memories(self) -> Dict[str, Any]:
        """Identify and promote valuable contextual memories to long-term storage."""
        try:
            processed_count = 0
            promoted_count = 0
            
            # Get context memory from memory system
            context_memory = self.memory_system.context_memory
            if not context_memory:
                logger.warning("No context memory found to promote")
                return {
                    "processed": 0,
                    "promoted": 0,
                    "error": "No context memory found"
                }
            
            # Process by_timestamp section first (most recent memories)
            if 'by_timestamp' in context_memory and isinstance(context_memory['by_timestamp'], dict):
                timestamp_memories = context_memory['by_timestamp']
                logger.info(f"Processing {len(timestamp_memories)} contextual memories by timestamp")
                
                # Sort by timestamp (newest first)
                sorted_timestamps = sorted(timestamp_memories.keys(), reverse=True)
                
                for timestamp in sorted_timestamps:
                    memory = timestamp_memories[timestamp]
                    processed_count += 1
                    
                    # Evaluate memory for promotion
                    should_promote = await self._evaluate_for_promotion(memory)
                    
                    if should_promote:
                        # Prepare memory for long-term storage
                        ltm_memory = await self._prepare_for_long_term(memory)
                        
                        # Add to long-term memory
                        memory_id = await self.memory_system.add_to_long_term_memory(ltm_memory)
                        if memory_id:
                            promoted_count += 1
                            logger.info(f"Promoted contextual memory to long-term: {memory_id}")
            
            # Process sensor data sections
            if 'sensor_data' in context_memory and isinstance(context_memory['sensor_data'], dict):
                for sensor_type, sensor_memories in context_memory['sensor_data'].items():
                    if not isinstance(sensor_memories, dict):
                        continue
                        
                    logger.info(f"Processing {len(sensor_memories)} {sensor_type} contextual memories")
                    
                    for memory_id, memory in sensor_memories.items():
                        # Skip if already processed via by_timestamp
                        if 'by_timestamp' in context_memory and any(m.get('memory_id') == memory_id for m in context_memory['by_timestamp'].values()):
                            continue
                            
                        processed_count += 1
                        
                        # Evaluate memory for promotion
                        should_promote = await self._evaluate_for_promotion(memory)
                        
                        if should_promote:
                            # Prepare memory for long-term storage
                            ltm_memory = await self._prepare_for_long_term(memory)
                            
                            # Add to long-term memory
                            ltm_id = await self.memory_system.add_to_long_term_memory(ltm_memory)
                            if ltm_id:
                                promoted_count += 1
                                logger.info(f"Promoted {sensor_type} contextual memory to long-term: {ltm_id}")
            
            # Save memory state after promotion
            try:
                self.memory_system._save_memory_state()
            except Exception as save_error:
                logger.error(f"Error saving memory state after promotion: {save_error}")
            
            return {
                "processed": processed_count,
                "promoted": promoted_count,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error promoting contextual memories: {e}")
            logger.error(traceback.format_exc())
            return {
                "processed": processed_count,
                "promoted": promoted_count,
                "error": str(e)
            }
    
    async def _get_context_memory(self) -> Dict[str, Any]:
        """Get the current context memory data"""
        try:
            if hasattr(self.memory_system, 'context_memory'):
                return self.memory_system.context_memory
            return {}
        except Exception as e:
            logger.error(f"Error getting context memory: {e}")
            return {}
    
    async def _evaluate_for_promotion(self, memory: Dict[str, Any]) -> bool:
        """
        Evaluate whether a contextual memory should be promoted to long-term
        
        Args:
            memory: The memory item to evaluate
            
        Returns:
            Boolean indicating whether to promote this memory
        """
        try:
            # Skip if not a valid memory object
            if not isinstance(memory, dict):
                return False
            
            # Calculate significance score
            significance = 0.0
            
            # Explicit significance flag has highest priority
            if memory.get('is_significant', False):
                significance += 0.4
            
            # Memory with application workflow data is significant
            if 'application' in memory and isinstance(memory['application'], dict):
                app_data = memory['application']
                if app_data.get('workflow_stage'):
                    significance += 0.3
                if app_data.get('name'):
                    significance += 0.1
            
            # Memory with visual or LLAVA context is significant
            if memory.get('visual_context') or memory.get('llava_description'):
                significance += 0.3
            
            # Memory with insights is significant
            if 'insights' in memory and isinstance(memory['insights'], list):
                insight_count = len(memory['insights'])
                if insight_count > 0:
                    significance += min(0.3, 0.05 * insight_count)
            
            # Memory with activity summary is significant
            if memory.get('activity_summary') or memory.get('context_understanding'):
                significance += 0.2
            
            # Memory with semantic meaning is significant
            if memory.get('semantic_summary'):
                significance += 0.2
            
            # Memory with UI element data is significant
            if 'screen_elements' in memory and isinstance(memory['screen_elements'], list):
                if len(memory['screen_elements']) > 0:
                    significance += 0.1
            
            # Memory with relationship data is significant
            if 'memory_connections' in memory and isinstance(memory['memory_connections'], list):
                if len(memory['memory_connections']) > 0:
                    significance += 0.2
            
            # Memory about communication (email, messages) is significant
            if memory.get('email_data') or memory.get('message_data'):
                significance += 0.3
            
            # Memory with high cognitive importance is significant
            if memory.get('cognitive_memory', {}).get('memory_importance') in ['high', 'critical']:
                significance += 0.4
            
            # Check final significance against threshold
            return significance >= self.significance_threshold
            
        except Exception as e:
            logger.error(f"Error evaluating memory for promotion: {e}")
            return False
    
    async def _prepare_for_long_term(self, memory: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare contextual memory for long-term storage by enhancing metadata
        
        Args:
            memory: The contextual memory to prepare
            
        Returns:
            Enhanced memory object suitable for long-term storage
        """
        try:
            # Create a copy to avoid modifying the original
            ltm_memory = memory.copy()
            
            # Add promotion metadata
            ltm_memory['promoted_from'] = 'context_memory'
            ltm_memory['promoted_at'] = datetime.now().isoformat()
            
            # Generate a new memory_id for long-term storage
            ltm_memory['memory_id'] = f"ltm_ctx_{int(time.time() * 1000)}"
            
            # Reference the original context memory ID if available
            if 'memory_id' in memory:
                ltm_memory['original_memory_id'] = memory['memory_id']
            
            # Add memory type for proper categorization
            ltm_memory['memory_type'] = 'long_term'
            
            # Add importance metadata for memory value calculation
            ltm_memory['importance_score'] = 0.8  # High importance by default for promoted items
            
            # Keep track of content source
            if 'sensor_type' in memory:
                ltm_memory['content_source'] = memory['sensor_type']
            
            # Add source application context if available
            if 'application' in memory and isinstance(memory['application'], dict):
                app_name = memory['application'].get('name', 'Unknown')
                ltm_memory['source_application'] = app_name
            
            # Add semantic tags if possible
            if 'insights' in memory and isinstance(memory['insights'], list):
                semantic_tags = []
                for insight in memory['insights']:
                    if isinstance(insight, dict) and 'content' in insight:
                        tag = insight['content'].split(':')[0] if ':' in insight['content'] else insight['content']
                        semantic_tags.append(tag)
                    elif isinstance(insight, str):
                        tag = insight.split(':')[0] if ':' in insight else insight
                        semantic_tags.append(tag)
                
                if semantic_tags:
                    ltm_memory['semantic_tags'] = semantic_tags
            
            return ltm_memory
            
        except Exception as e:
            logger.error(f"Error preparing memory for long-term: {e}")
            return memory  # Return original if preparation fails