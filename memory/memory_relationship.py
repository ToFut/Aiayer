#!/usr/bin/env python3
"""
Memory Relationship Module

This module implements enhanced relationship tracking between memory items.
It allows for creating, querying, and analyzing relationships between memory entities
to provide more meaningful context and understanding.
"""
import logging
import time
import json
import os
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple
import asyncio

# Configure logging
logger = logging.getLogger(__name__)

class MemoryRelationship:
    """Represents a relationship between two memory items"""
    
    def __init__(self, source_id: str, target_id: str, relationship_type: str, 
                 strength: float = 1.0, properties: Dict[str, Any] = None):
        self.source_id = source_id
        self.target_id = target_id
        self.relationship_type = relationship_type
        self.strength = strength  # Relationship strength (0.0 to 1.0)
        self.properties = properties or {}
        self.created_at = datetime.now().isoformat()
        self.last_activated = self.created_at
        self.activation_count = 1
    
    def activate(self, strength_modifier: float = 0.0):
        """Activate this relationship, increasing its strength"""
        self.activation_count += 1
        self.last_activated = datetime.now().isoformat()
        
        # Increase strength but keep within bounds
        self.strength = min(1.0, self.strength + strength_modifier)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "type": self.relationship_type,
            "strength": self.strength,
            "properties": self.properties,
            "created_at": self.created_at,
            "last_activated": self.last_activated,
            "activation_count": self.activation_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryRelationship':
        """Create from dictionary representation"""
        relationship = cls(
            source_id=data["source_id"],
            target_id=data["target_id"],
            relationship_type=data["type"],
            strength=data["strength"],
            properties=data["properties"]
        )
        relationship.created_at = data["created_at"]
        relationship.last_activated = data["last_activated"]
        relationship.activation_count = data["activation_count"]
        return relationship


class MemoryRelationshipTracker:
    """Tracks and manages relationships between memory items"""
    
    def __init__(self, storage_path: str = "memory/memory/relationships.json"):
        self.storage_path = storage_path
        self.relationships = {}  # source_id -> target_id -> relationship
        self.reverse_index = {}  # target_id -> set of source_ids
        self.type_index = {}  # relationship_type -> set of (source_id, target_id)
        self.last_save_time = 0
        self.save_interval = 60  # Save every 60 seconds
        self.initialized = False
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
    
    async def initialize(self):
        """Initialize the relationship tracker"""
        if self.initialized:
            return True
            
        try:
            # Load existing relationships if available
            if os.path.exists(self.storage_path):
                await self._load_relationships()
            
            # Start save task
            asyncio.create_task(self._save_periodically())
            
            self.initialized = True
            logger.info(f"Memory relationship tracker initialized with {len(self.relationships)} sources")
            return True
        except Exception as e:
            logger.error(f"Error initializing memory relationship tracker: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def _load_relationships(self):
        """Load relationships from storage"""
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            # Process relationship data
            for rel_data in data.get("relationships", []):
                try:
                    relationship = MemoryRelationship.from_dict(rel_data)
                    self._add_relationship_to_indices(relationship)
                    logger.debug(f"Loaded relationship: {relationship.source_id} -> {relationship.target_id} ({relationship.relationship_type})")
                except Exception as e:
                    logger.error(f"Error loading relationship: {e}")
                    
            logger.info(f"Loaded {len(self.relationships)} relationships from {self.storage_path}")
        except Exception as e:
            logger.error(f"Error loading relationships from {self.storage_path}: {e}")
            logger.error(traceback.format_exc())
    
    async def _save_relationships(self):
        """Save relationships to storage"""
        try:
            # Collect all relationships
            all_relationships = []
            for source_dict in self.relationships.values():
                for relationship in source_dict.values():
                    all_relationships.append(relationship.to_dict())
            
            # Save to file
            with open(self.storage_path, 'w') as f:
                json.dump({
                    "last_updated": datetime.now().isoformat(),
                    "count": len(all_relationships),
                    "relationships": all_relationships
                }, f, indent=2)
            
            self.last_save_time = time.time()
            logger.info(f"Saved {len(all_relationships)} relationships to {self.storage_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving relationships to {self.storage_path}: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def _save_periodically(self):
        """Save relationships periodically"""
        while True:
            try:
                await asyncio.sleep(self.save_interval)
                current_time = time.time()
                if current_time - self.last_save_time >= self.save_interval:
                    await self._save_relationships()
            except asyncio.CancelledError:
                # Final save before exiting
                await self._save_relationships()
                break
            except Exception as e:
                logger.error(f"Error in periodic save: {e}")
                logger.error(traceback.format_exc())
    
    def _add_relationship_to_indices(self, relationship: MemoryRelationship):
        """Add a relationship to all indices"""
        source_id = relationship.source_id
        target_id = relationship.target_id
        rel_type = relationship.relationship_type
        
        # Create source dictionary if needed
        if source_id not in self.relationships:
            self.relationships[source_id] = {}
        
        # Store relationship
        self.relationships[source_id][target_id] = relationship
        
        # Update reverse index
        if target_id not in self.reverse_index:
            self.reverse_index[target_id] = set()
        self.reverse_index[target_id].add(source_id)
        
        # Update type index
        if rel_type not in self.type_index:
            self.type_index[rel_type] = set()
        self.type_index[rel_type].add((source_id, target_id))
    
    async def add_relationship(self, source_id: str, target_id: str, relationship_type: str, 
                              strength: float = 1.0, properties: Dict[str, Any] = None) -> MemoryRelationship:
        """
        Add a new relationship between two memory items
        
        Args:
            source_id: ID of the source memory item
            target_id: ID of the target memory item
            relationship_type: Type of relationship (e.g., "contains", "related_to", "caused_by")
            strength: Strength of the relationship (0.0 to 1.0)
            properties: Additional properties of the relationship
            
        Returns:
            The created relationship object
        """
        try:
            # Check if relationship already exists
            if source_id in self.relationships and target_id in self.relationships[source_id]:
                # Update existing relationship
                relationship = self.relationships[source_id][target_id]
                relationship.activate(0.1)  # Reinforce relationship
                relationship.relationship_type = relationship_type  # Update type
                relationship.properties.update(properties or {})  # Update properties
                logger.info(f"Updated relationship: {source_id} -> {target_id} ({relationship_type})")
            else:
                # Create new relationship
                relationship = MemoryRelationship(
                    source_id=source_id,
                    target_id=target_id,
                    relationship_type=relationship_type,
                    strength=strength,
                    properties=properties
                )
                
                # Add to indices
                self._add_relationship_to_indices(relationship)
                logger.info(f"Added new relationship: {source_id} -> {target_id} ({relationship_type})")
            
            return relationship
        
        except Exception as e:
            logger.error(f"Error adding relationship: {e}")
            logger.error(traceback.format_exc())
            return None
    
    async def get_relationships_from(self, source_id: str, 
                                    relationship_type: Optional[str] = None, 
                                    min_strength: float = 0.0) -> List[MemoryRelationship]:
        """
        Get all relationships from a source memory item
        
        Args:
            source_id: ID of the source memory item
            relationship_type: Optional filter by relationship type
            min_strength: Minimum relationship strength to include
            
        Returns:
            List of relationship objects
        """
        try:
            if source_id not in self.relationships:
                return []
                
            relationships = []
            for relationship in self.relationships[source_id].values():
                # Apply filters
                if relationship_type and relationship.relationship_type != relationship_type:
                    continue
                if relationship.strength < min_strength:
                    continue
                    
                relationships.append(relationship)
                
            # Sort by strength (strongest first)
            relationships.sort(key=lambda r: r.strength, reverse=True)
            return relationships
        
        except Exception as e:
            logger.error(f"Error getting relationships from {source_id}: {e}")
            logger.error(traceback.format_exc())
            return []
    
    async def get_relationships_to(self, target_id: str, 
                                 relationship_type: Optional[str] = None, 
                                 min_strength: float = 0.0) -> List[MemoryRelationship]:
        """
        Get all relationships to a target memory item
        
        Args:
            target_id: ID of the target memory item
            relationship_type: Optional filter by relationship type
            min_strength: Minimum relationship strength to include
            
        Returns:
            List of relationship objects
        """
        try:
            if target_id not in self.reverse_index:
                return []
                
            relationships = []
            for source_id in self.reverse_index[target_id]:
                relationship = self.relationships[source_id][target_id]
                
                # Apply filters
                if relationship_type and relationship.relationship_type != relationship_type:
                    continue
                if relationship.strength < min_strength:
                    continue
                    
                relationships.append(relationship)
                
            # Sort by strength (strongest first)
            relationships.sort(key=lambda r: r.strength, reverse=True)
            return relationships
        
        except Exception as e:
            logger.error(f"Error getting relationships to {target_id}: {e}")
            logger.error(traceback.format_exc())
            return []
    
    async def get_relationships_by_type(self, relationship_type: str, min_strength: float = 0.0) -> List[MemoryRelationship]:
        """
        Get all relationships of a specific type
        
        Args:
            relationship_type: Type of relationship to find
            min_strength: Minimum relationship strength to include
            
        Returns:
            List of relationship objects
        """
        try:
            if relationship_type not in self.type_index:
                return []
                
            relationships = []
            for source_id, target_id in self.type_index[relationship_type]:
                relationship = self.relationships[source_id][target_id]
                
                # Apply strength filter
                if relationship.strength < min_strength:
                    continue
                    
                relationships.append(relationship)
                
            # Sort by strength (strongest first)
            relationships.sort(key=lambda r: r.strength, reverse=True)
            return relationships
        
        except Exception as e:
            logger.error(f"Error getting relationships of type {relationship_type}: {e}")
            logger.error(traceback.format_exc())
            return []
    
    async def get_related_items(self, memory_id: str, max_distance: int = 2, 
                              min_strength: float = 0.3) -> List[Dict[str, Any]]:
        """
        Get all memory items related to a given item using graph traversal
        
        Args:
            memory_id: ID of the memory item
            max_distance: Maximum relationship distance to traverse
            min_strength: Minimum relationship strength to include
            
        Returns:
            List of related memory items with their relationship path
        """
        try:
            # Keep track of visited items and their paths
            visited = set()
            results = []
            
            # Queue for BFS traversal: (memory_id, distance, path)
            queue = [(memory_id, 0, [])]
            
            while queue:
                current_id, distance, path = queue.pop(0)
                
                # Skip if already visited or exceeds max distance
                if current_id in visited or distance > max_distance:
                    continue
                    
                # Mark as visited
                visited.add(current_id)
                
                # If not the starting node, add to results
                if distance > 0:
                    results.append({
                        "memory_id": current_id,
                        "distance": distance,
                        "path": path
                    })
                
                # Don't traverse further if at max distance
                if distance >= max_distance:
                    continue
                
                # Get outgoing relationships
                outgoing = await self.get_relationships_from(current_id, min_strength=min_strength)
                for rel in outgoing:
                    if rel.target_id not in visited:
                        # Create new path with this relationship
                        new_path = path + [{
                            "from": current_id,
                            "to": rel.target_id,
                            "type": rel.relationship_type,
                            "strength": rel.strength
                        }]
                        queue.append((rel.target_id, distance + 1, new_path))
                
                # Get incoming relationships
                incoming = await self.get_relationships_to(current_id, min_strength=min_strength)
                for rel in incoming:
                    if rel.source_id not in visited:
                        # Create new path with this relationship
                        new_path = path + [{
                            "from": rel.source_id,
                            "to": current_id,
                            "type": rel.relationship_type,
                            "strength": rel.strength
                        }]
                        queue.append((rel.source_id, distance + 1, new_path))
            
            # Sort by distance (closest first) and then by path strength
            results.sort(key=lambda r: (r["distance"], -sum(step["strength"] for step in r["path"])))
            return results
        
        except Exception as e:
            logger.error(f"Error getting related items for {memory_id}: {e}")
            logger.error(traceback.format_exc())
            return []
    
    async def get_common_connections(self, memory_id1: str, memory_id2: str, 
                                  max_distance: int = 2) -> List[Dict[str, Any]]:
        """
        Find common connections between two memory items
        
        Args:
            memory_id1: ID of the first memory item
            memory_id2: ID of the second memory item
            max_distance: Maximum relationship distance to traverse
            
        Returns:
            List of common connections with their relationship paths
        """
        try:
            # Get related items for both memory items
            related1 = await self.get_related_items(memory_id1, max_distance)
            related2 = await self.get_related_items(memory_id2, max_distance)
            
            # Extract memory IDs from both sets
            ids1 = {r["memory_id"] for r in related1}
            ids2 = {r["memory_id"] for r in related2}
            
            # Find common IDs
            common_ids = ids1.intersection(ids2)
            
            # Exclude the original memory IDs
            common_ids.discard(memory_id1)
            common_ids.discard(memory_id2)
            
            # Prepare result
            common_connections = []
            for memory_id in common_ids:
                # Find data in both related sets
                data1 = next(r for r in related1 if r["memory_id"] == memory_id)
                data2 = next(r for r in related2 if r["memory_id"] == memory_id)
                
                common_connections.append({
                    "memory_id": memory_id,
                    "path_from_1": data1["path"],
                    "path_from_2": data2["path"],
                    "combined_distance": data1["distance"] + data2["distance"]
                })
            
            # Sort by combined distance
            common_connections.sort(key=lambda c: c["combined_distance"])
            return common_connections
        
        except Exception as e:
            logger.error(f"Error finding common connections between {memory_id1} and {memory_id2}: {e}")
            logger.error(traceback.format_exc())
            return []
    
    async def decay_relationships(self, decay_factor: float = 0.05, min_age_days: int = 7):
        """
        Apply decay to relationship strengths based on age and activation
        
        Args:
            decay_factor: Amount to decay (0.0 to 1.0)
            min_age_days: Minimum age in days for decay to apply
            
        Returns:
            Number of relationships decayed
        """
        try:
            count = 0
            now = datetime.now()
            
            # Process all relationships
            for source_dict in self.relationships.values():
                for relationship in list(source_dict.values()):
                    # Calculate age in days
                    last_activated = datetime.fromisoformat(relationship.last_activated)
                    age_days = (now - last_activated).days
                    
                    # Apply decay if old enough
                    if age_days >= min_age_days:
                        # More decay for older relationships
                        actual_decay = min(0.9, decay_factor * (age_days / min_age_days))
                        
                        # Apply decay
                        relationship.strength = max(0.1, relationship.strength - actual_decay)
                        count += 1
            
            logger.info(f"Decayed {count} relationships")
            return count
        
        except Exception as e:
            logger.error(f"Error decaying relationships: {e}")
            logger.error(traceback.format_exc())
            return 0
    
    async def infer_relationships(self, min_confidence: float = 0.7) -> List[Dict[str, Any]]:
        """
        Infer potential new relationships based on existing relationships
        
        Args:
            min_confidence: Minimum confidence for inference (0.0 to 1.0)
            
        Returns:
            List of inferred relationships
        """
        try:
            inferred = []
            
            # Find transitive relationships (A->B and B->C suggests A->C)
            for source_id, source_dict in self.relationships.items():
                for middle_id, rel1 in source_dict.items():
                    # Only consider strong relationships
                    if rel1.strength < min_confidence:
                        continue
                        
                    # Check if middle_id has outgoing relationships
                    if middle_id in self.relationships:
                        for target_id, rel2 in self.relationships[middle_id].items():
                            # Only consider strong relationships
                            if rel2.strength < min_confidence:
                                continue
                                
                            # Skip if source_id and target_id are the same
                            if source_id == target_id:
                                continue
                                
                            # Skip if relationship already exists
                            if target_id in source_dict:
                                continue
                                
                            # Calculate confidence
                            confidence = rel1.strength * rel2.strength
                            if confidence >= min_confidence:
                                # Determine relationship type based on existing relationships
                                rel_type = "related_to"  # Default
                                
                                # If rel1 and rel2 have same type, use that type
                                if rel1.relationship_type == rel2.relationship_type:
                                    rel_type = rel1.relationship_type
                                    
                                # Create inferred relationship
                                inferred.append({
                                    "source_id": source_id,
                                    "target_id": target_id,
                                    "relationship_type": rel_type,
                                    "confidence": confidence,
                                    "inference_path": [rel1.to_dict(), rel2.to_dict()]
                                })
            
            # Sort by confidence
            inferred.sort(key=lambda r: r["confidence"], reverse=True)
            
            logger.info(f"Inferred {len(inferred)} potential new relationships")
            return inferred
        
        except Exception as e:
            logger.error(f"Error inferring relationships: {e}")
            logger.error(traceback.format_exc())
            return []
    
    async def apply_inferred_relationships(self, min_confidence: float = 0.8) -> int:
        """
        Apply inferred relationships to the relationship tracker
        
        Args:
            min_confidence: Minimum confidence required to create relationship
            
        Returns:
            Number of relationships created
        """
        try:
            inferred = await self.infer_relationships(min_confidence)
            count = 0
            
            for inference in inferred:
                # Create relationship
                relationship = await self.add_relationship(
                    source_id=inference["source_id"],
                    target_id=inference["target_id"],
                    relationship_type=inference["relationship_type"],
                    strength=inference["confidence"],
                    properties={"inferred": True, "created_at": datetime.now().isoformat()}
                )
                
                if relationship:
                    count += 1
            
            logger.info(f"Applied {count} inferred relationships")
            return count
        
        except Exception as e:
            logger.error(f"Error applying inferred relationships: {e}")
            logger.error(traceback.format_exc())
            return 0
    
    async def analyze_connectivity(self) -> Dict[str, Any]:
        """
        Analyze the connectivity of the relationship graph
        
        Returns:
            Dictionary with connectivity metrics
        """
        try:
            # Count memory items
            memory_items = set()
            for source_id in self.relationships:
                memory_items.add(source_id)
                for target_id in self.relationships[source_id]:
                    memory_items.add(target_id)
            
            # Count relationships by type
            relationship_counts = {}
            for rel_type, pairs in self.type_index.items():
                relationship_counts[rel_type] = len(pairs)
            
            # Find most connected items
            item_connections = {}
            for source_id in self.relationships:
                outgoing = len(self.relationships[source_id])
                item_connections[source_id] = outgoing
                
            sorted_items = sorted(item_connections.items(), key=lambda x: x[1], reverse=True)
            top_items = sorted_items[:10] if len(sorted_items) > 10 else sorted_items
            
            return {
                "memory_item_count": len(memory_items),
                "relationship_count": sum(relationship_counts.values()),
                "relationship_types": relationship_counts,
                "most_connected": top_items
            }
        
        except Exception as e:
            logger.error(f"Error analyzing connectivity: {e}")
            logger.error(traceback.format_exc())
            return {}