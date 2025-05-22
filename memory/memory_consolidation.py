#!/usr/bin/env python3
"""
Memory Consolidation Module

This module periodically reviews and consolidates memory contents
to organize information more effectively, remove redundancies,
and identify important patterns.
"""
import os
import json
import logging
import asyncio
import time
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Any, Set, Tuple, Optional
import hashlib

# Import required modules
from memory.memory_system import MemorySystem
from memory.memory_relationship import MemoryRelationshipTracker

# Configure logging
logger = logging.getLogger(__name__)

class MemoryConsolidation:
    """Handles periodic consolidation of memory content"""
    
    def __init__(self, memory_system: MemorySystem, relationship_tracker: MemoryRelationshipTracker,
                 consolidation_interval: int = 3600, similarity_threshold: float = 0.7):
        """
        Initialize the memory consolidation system
        
        Args:
            memory_system: Reference to the memory system
            relationship_tracker: Reference to the relationship tracker
            consolidation_interval: Seconds between consolidation runs (default: 1 hour)
            similarity_threshold: Threshold for considering memories similar (0.0 to 1.0)
        """
        self.memory_system = memory_system
        self.relationship_tracker = relationship_tracker
        self.consolidation_interval = consolidation_interval
        self.similarity_threshold = similarity_threshold
        self.running = False
        self.last_consolidation = 0
        self.consolidation_stats = {
            "total_runs": 0,
            "merged_items": 0,
            "pruned_items": 0,
            "promoted_items": 0,
            "last_run": None
        }
        self.storage_path = "memory/memory/consolidation_stats.json"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        
        logger.info("Memory consolidation initialized with "
                   f"interval={consolidation_interval}s, "
                   f"similarity_threshold={similarity_threshold}")
    
    async def initialize(self):
        """Initialize the consolidation system"""
        try:
            # Load previous stats if available
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    self.consolidation_stats = json.load(f)
                logger.info(f"Loaded consolidation stats from {self.storage_path}")
            
            logger.info("Memory consolidation initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing memory consolidation: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def start(self):
        """Start the consolidation process"""
        if self.running:
            logger.warning("Consolidation process already running")
            return False
            
        try:
            self.running = True
            logger.info("Starting memory consolidation process")
            
            # Start consolidation loop
            asyncio.create_task(self._consolidation_loop())
            return True
        except Exception as e:
            logger.error(f"Error starting memory consolidation: {e}")
            logger.error(traceback.format_exc())
            self.running = False
            return False
    
    async def stop(self):
        """Stop the consolidation process"""
        try:
            self.running = False
            logger.info("Stopping memory consolidation process")
            
            # Save stats
            await self._save_stats()
            return True
        except Exception as e:
            logger.error(f"Error stopping memory consolidation: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def _save_stats(self):
        """Save consolidation stats to file"""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.consolidation_stats, f, indent=2)
            logger.info(f"Saved consolidation stats to {self.storage_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving consolidation stats: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def _consolidation_loop(self):
        """Main consolidation loop that runs periodically"""
        try:
            while self.running:
                # Check if it's time to consolidate
                current_time = time.time()
                if current_time - self.last_consolidation >= self.consolidation_interval:
                    logger.info("Starting scheduled memory consolidation")
                    await self.consolidate_memory()
                    self.last_consolidation = current_time
                
                # Wait for next check
                await asyncio.sleep(60)  # Check every minute
                
        except asyncio.CancelledError:
            logger.info("Consolidation loop cancelled")
        except Exception as e:
            logger.error(f"Error in consolidation loop: {e}")
            logger.error(traceback.format_exc())
    
    async def consolidate_memory(self) -> Dict[str, Any]:
        """
        Perform memory consolidation
        
        Returns:
            Statistics about the consolidation process
        """
        try:
            start_time = time.time()
            logger.info("Beginning memory consolidation process")
            
            # Initialize stats for this run
            stats = {
                "start_time": datetime.now().isoformat(),
                "merged_items": 0,
                "pruned_items": 0,
                "promoted_items": 0
            }
            
            # 1. Identify and merge similar short-term memories
            merged_count = await self._merge_similar_memories()
            stats["merged_items"] = merged_count
            
            # 2. Prune redundant or low-value memories
            pruned_count = await self._prune_low_value_memories()
            stats["pruned_items"] = pruned_count
            
            # 3. Promote important short-term memories to long-term
            promoted_count = await self._promote_important_memories()
            stats["promoted_items"] = promoted_count
            
            # 4. Update memory relationships based on contents
            await self._update_memory_relationships()
            
            # Update overall stats
            self.consolidation_stats["total_runs"] += 1
            self.consolidation_stats["merged_items"] += merged_count
            self.consolidation_stats["pruned_items"] += pruned_count
            self.consolidation_stats["promoted_items"] += promoted_count
            self.consolidation_stats["last_run"] = datetime.now().isoformat()
            
            # Calculate duration
            duration = time.time() - start_time
            stats["duration"] = duration
            logger.info(f"Memory consolidation completed in {duration:.2f}s: "
                        f"merged={merged_count}, pruned={pruned_count}, "
                        f"promoted={promoted_count}")
            
            # Save updated stats
            await self._save_stats()
            
            return stats
            
        except Exception as e:
            logger.error(f"Error during memory consolidation: {e}")
            logger.error(traceback.format_exc())
            return {"error": str(e)}
    
    async def _merge_similar_memories(self) -> int:
        """
        Identify and merge similar memories to reduce redundancy
        
        Returns:
            Number of merged memory items
        """
        try:
            merged_count = 0
            
            # Get all short-term memories
            short_term_memories = await self.memory_system.get_short_term_memories()
            if not short_term_memories:
                logger.info("No short-term memories to merge")
                return 0
                
            # Group memories by sensor type
            memories_by_type = {}
            for memory in short_term_memories:
                sensor_type = memory.get("sensor_type", "unknown")
                if sensor_type not in memories_by_type:
                    memories_by_type[sensor_type] = []
                memories_by_type[sensor_type].append(memory)
            
            # Process each type separately
            for sensor_type, memories in memories_by_type.items():
                # Skip if not enough memories to merge
                if len(memories) < 2:
                    continue
                    
                # Sort by timestamp (newest first)
                memories.sort(key=lambda m: m.get("timestamp", ""), reverse=True)
                
                # Find similar memories
                to_merge = []
                for i, memory1 in enumerate(memories[:-1]):
                    for memory2 in memories[i+1:]:
                        # Skip if already marked for merging
                        if memory2 in [m for group in to_merge for m in group]:
                            continue
                            
                        # Check similarity
                        similarity = await self._calculate_similarity(memory1, memory2)
                        if similarity >= self.similarity_threshold:
                            # Find existing group or create new one
                            found_group = False
                            for group in to_merge:
                                if memory1 in group:
                                    group.append(memory2)
                                    found_group = True
                                    break
                            
                            if not found_group:
                                to_merge.append([memory1, memory2])
                
                # Merge similar memories
                for group in to_merge:
                    if len(group) >= 2:
                        merged_memory = await self._create_merged_memory(group)
                        if merged_memory:
                            # Replace with merged memory
                            await self.memory_system.add_to_short_term_memory(merged_memory)
                            
                            # Remove original memories
                            for memory in group:
                                await self.memory_system.remove_from_short_term_memory(memory.get("memory_id"))
                            
                            merged_count += len(group) - 1
                            logger.info(f"Merged {len(group)} similar {sensor_type} memories")
            
            return merged_count
            
        except Exception as e:
            logger.error(f"Error merging similar memories: {e}")
            logger.error(traceback.format_exc())
            return 0
    
    async def _calculate_similarity(self, memory1: Dict[str, Any], memory2: Dict[str, Any]) -> float:
        """
        Calculate similarity between two memory items
        
        Args:
            memory1: First memory item
            memory2: Second memory item
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        try:
            # Different approaches based on sensor type
            sensor_type = memory1.get("sensor_type")
            
            # Check timestamp proximity (close in time = more similar)
            time1 = datetime.fromisoformat(memory1.get("timestamp", datetime.now().isoformat()))
            time2 = datetime.fromisoformat(memory2.get("timestamp", datetime.now().isoformat()))
            time_diff = abs((time1 - time2).total_seconds())
            time_score = 1.0 if time_diff < 60 else max(0.0, 1.0 - (time_diff / 3600))
            
            if sensor_type == "screen":
                # Compare image hashes if available
                if "image_hash" in memory1 and "image_hash" in memory2:
                    hash1 = memory1["image_hash"]
                    hash2 = memory2["image_hash"]
                    # Calculate Hamming distance between hashes
                    if len(hash1) == len(hash2):
                        hash_similarity = sum(c1 == c2 for c1, c2 in zip(hash1, hash2)) / len(hash1)
                    else:
                        hash_similarity = 0.0
                    
                    # Compare window titles
                    title1 = memory1.get("window_title", "")
                    title2 = memory2.get("window_title", "")
                    title_similarity = 1.0 if title1 == title2 else 0.0
                    
                    # Combine scores (hash has more weight)
                    return 0.6 * hash_similarity + 0.2 * title_similarity + 0.2 * time_score
                
                # Fallback to text comparison
                text1 = memory1.get("screen_content", "")
                text2 = memory2.get("screen_content", "")
                text_similarity = self._text_similarity(text1, text2)
                
                return 0.7 * text_similarity + 0.3 * time_score
                
            elif sensor_type == "process":
                # Compare active applications
                apps1 = set(app.get("name", "") for app in memory1.get("active_apps", []))
                apps2 = set(app.get("name", "") for app in memory2.get("active_apps", []))
                
                # Calculate Jaccard similarity for app sets
                if apps1 or apps2:
                    app_similarity = len(apps1.intersection(apps2)) / len(apps1.union(apps2)) if apps1.union(apps2) else 0.0
                else:
                    app_similarity = 1.0  # Both empty
                
                # Compare active window
                window1 = memory1.get("active_window", "")
                window2 = memory2.get("active_window", "")
                window_similarity = 1.0 if window1 == window2 else 0.0
                
                return 0.5 * app_similarity + 0.3 * window_similarity + 0.2 * time_score
                
            else:
                # Generic content similarity
                content1 = memory1.get("content", "")
                content2 = memory2.get("content", "")
                content_similarity = self._text_similarity(content1, content2)
                
                return 0.7 * content_similarity + 0.3 * time_score
                
        except Exception as e:
            logger.error(f"Error calculating memory similarity: {e}")
            logger.error(traceback.format_exc())
            return 0.0
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two text strings
        
        Args:
            text1: First text string
            text2: Second text string
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Handle empty strings
        if not text1 and not text2:
            return 1.0
        if not text1 or not text2:
            return 0.0
            
        # Convert to sets of words
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    async def _create_merged_memory(self, memories: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Create a merged memory from similar memories
        
        Args:
            memories: List of similar memories to merge
            
        Returns:
            Merged memory item or None if failed
        """
        try:
            if not memories:
                return None
                
            # Use newest memory as base
            base_memory = memories[0]
            sensor_type = base_memory.get("sensor_type", "unknown")
            
            # Create merged memory
            merged = {
                "memory_id": f"merged_{int(time.time() * 1000)}",
                "sensor_type": sensor_type,
                "timestamp": base_memory.get("timestamp"),
                "merged_from": [mem.get("memory_id") for mem in memories],
                "merged_count": len(memories),
                "merged_at": datetime.now().isoformat()
            }
            
            # Copy basic fields from base memory
            for key, value in base_memory.items():
                if key not in merged and key not in ["memory_id", "memory_created"]:
                    merged[key] = value
            
            # Add specialized merging logic based on sensor type
            if sensor_type == "screen":
                # For screen, use the most recent data but note the time span
                time_start = min(datetime.fromisoformat(mem.get("timestamp", datetime.now().isoformat())) 
                               for mem in memories)
                time_end = max(datetime.fromisoformat(mem.get("timestamp", datetime.now().isoformat())) 
                             for mem in memories)
                
                merged["time_span"] = {
                    "start": time_start.isoformat(),
                    "end": time_end.isoformat(),
                    "duration_seconds": (time_end - time_start).total_seconds()
                }
                
            elif sensor_type == "process":
                # For process data, combine active apps across time period
                all_apps = set()
                for mem in memories:
                    apps = [app.get("name", "") for app in mem.get("active_apps", [])]
                    all_apps.update(apps)
                
                # Convert back to list of dictionaries
                merged["active_apps"] = [{"name": app} for app in all_apps if app]
                
                # Mark significant if any of the original memories were
                merged["is_significant"] = any(mem.get("is_significant", False) for mem in memories)
            
            return merged
            
        except Exception as e:
            logger.error(f"Error creating merged memory: {e}")
            logger.error(traceback.format_exc())
            return None
    
    async def _prune_low_value_memories(self) -> int:
        """
        Identify and remove low-value memories
        
        Returns:
            Number of pruned memory items
        """
        try:
            pruned_count = 0
            
            # Get all short-term memories
            short_term_memories = await self.memory_system.get_short_term_memories()
            if not short_term_memories:
                logger.info("No short-term memories to prune")
                return 0
            
            # Identify low-value memories
            to_prune = []
            for memory in short_term_memories:
                # Get memory value score
                value = await self._calculate_memory_value(memory)
                
                # Age-based pruning (older + low value = prune)
                memory_time = datetime.fromisoformat(memory.get("timestamp", datetime.now().isoformat()))
                age_hours = (datetime.now() - memory_time).total_seconds() / 3600
                
                # Combine age and value for pruning decision
                if age_hours > 24 and value < 0.3:  # Low value and at least 24 hours old
                    to_prune.append(memory.get("memory_id"))
                elif age_hours > 72 and value < 0.5:  # Medium-low value and at least 3 days old
                    to_prune.append(memory.get("memory_id"))
                elif age_hours > 168 and value < 0.7:  # Medium value and at least 7 days old
                    to_prune.append(memory.get("memory_id"))
            
            # Prune identified memories
            for memory_id in to_prune:
                if memory_id:
                    await self.memory_system.remove_from_short_term_memory(memory_id)
                    pruned_count += 1
            
            if pruned_count > 0:
                logger.info(f"Pruned {pruned_count} low-value memories")
            
            return pruned_count
            
        except Exception as e:
            logger.error(f"Error pruning low-value memories: {e}")
            logger.error(traceback.format_exc())
            return 0
    
    async def _calculate_memory_value(self, memory: Dict[str, Any]) -> float:
        """
        Calculate the value of a memory item
        
        Args:
            memory: Memory item to evaluate
            
        Returns:
            Value score between 0.0 and 1.0
        """
        try:
            # Start with base value
            value = 0.5
            
            # Significant items have higher value
            if memory.get("is_significant", False):
                value += 0.3
            
            # Consider memory connections (more connections = higher value)
            memory_id = memory.get("memory_id")
            if memory_id:
                outgoing = await self.relationship_tracker.get_relationships_from(memory_id)
                incoming = await self.relationship_tracker.get_relationships_to(memory_id)
                
                # Adjust value based on connection count
                connection_count = len(outgoing) + len(incoming)
                if connection_count > 0:
                    connection_value = min(0.3, 0.05 * connection_count)
                    value += connection_value
            
            # Consider access frequency
            access_count = memory.get("access_count", 0)
            if access_count > 0:
                access_value = min(0.2, 0.02 * access_count)
                value += access_value
            
            # Consider explicit importance
            importance = memory.get("importance", 0.0)
            if importance > 0:
                value += importance * 0.2
            
            # Sensor-specific adjustments
            sensor_type = memory.get("sensor_type")
            if sensor_type == "screen":
                # Screen memories with application context are more valuable
                if memory.get("application"):
                    value += 0.1
                    
                # Screen memories with recognized content are more valuable
                if memory.get("visual_context") and len(memory.get("visual_context", "")) > 20:
                    value += 0.1
                    
            elif sensor_type == "process":
                # Process memories with many active apps are more valuable
                app_count = len(memory.get("active_apps", []))
                if app_count > 5:
                    value += 0.1
            
            # Normalize to 0.0-1.0 range
            return max(0.0, min(1.0, value))
            
        except Exception as e:
            logger.error(f"Error calculating memory value: {e}")
            logger.error(traceback.format_exc())
            return 0.5  # Default to neutral value on error
    
    async def _promote_important_memories(self) -> int:
        """
        Identify and promote important short-term memories to long-term
        
        Returns:
            Number of promoted memory items
        """
        try:
            promoted_count = 0
            
            # Get all short-term memories
            short_term_memories = await self.memory_system.get_short_term_memories()
            if not short_term_memories:
                logger.info("No short-term memories to promote")
                return 0
            
            # Identify important memories
            to_promote = []
            for memory in short_term_memories:
                # Get memory value score
                value = await self._calculate_memory_value(memory)
                
                # Promotion criteria
                if value >= 0.7:  # High value memories
                    to_promote.append(memory)
                elif memory.get("is_significant", False) and value >= 0.5:  # Significant memories with decent value
                    to_promote.append(memory)
            
            # Promote identified memories
            for memory in to_promote:
                memory_id = memory.get("memory_id")
                if memory_id:
                    # Add to long-term memory
                    await self.memory_system.add_to_long_term_memory(memory)
                    promoted_count += 1
            
            if promoted_count > 0:
                logger.info(f"Promoted {promoted_count} important memories to long-term memory")
            
            return promoted_count
            
        except Exception as e:
            logger.error(f"Error promoting important memories: {e}")
            logger.error(traceback.format_exc())
            return 0
    
    async def _update_memory_relationships(self) -> bool:
        """
        Update relationships between memory items based on content
        
        Returns:
            Whether relationships were successfully updated
        """
        try:
            # Decay existing relationships
            await self.relationship_tracker.decay_relationships()
            
            # Apply inferred relationships
            added_count = await self.relationship_tracker.apply_inferred_relationships()
            logger.info(f"Added {added_count} inferred relationships")
            
            # Analyze connectivity
            connectivity = await self.relationship_tracker.analyze_connectivity()
            logger.info(f"Relationship graph: {connectivity.get('memory_item_count', 0)} items, "
                       f"{connectivity.get('relationship_count', 0)} relationships")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating memory relationships: {e}")
            logger.error(traceback.format_exc())
            return False
        
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get consolidation statistics
        
        Returns:
            Dictionary with consolidation statistics
        """
        return self.consolidation_stats

def get_consolidation_system(memory_system: MemorySystem, relationship_tracker: MemoryRelationshipTracker) -> MemoryConsolidation:
    """Factory function to create and initialize a consolidation system"""
    return MemoryConsolidation(memory_system, relationship_tracker)