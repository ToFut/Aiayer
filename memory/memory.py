#!/usr/bin/env python3
"""
Memory Module
Provides conversation and context memory management with vector-based storage.
"""
import json
import logging
import os
from datetime import datetime
from collections import deque
import numpy as np
# Removed sentence_transformers dependency
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class BaseMemory:
    """Base class for vector-based memory storage."""
    
    def __init__(self, max_length=50):
        self.max_length = max_length
        self.vector_model = None
        self.vectors = []
        self.metadata = []
        self._init_vector_model()
        
    def _init_vector_model(self):
        """Initialize the vector model for semantic search."""
        # Vector model disabled, using simple text search instead
        self.vector_model = None
        logger.info("Vector model disabled - using text-based search instead")
            
    def _get_text_for_vectorization(self, item):
        """Extract text content for vectorization."""
        try:
            if isinstance(item, dict):
                text_parts = []
                for key, value in item.items():
                    if isinstance(value, (str, int, float)):
                        text_parts.append(str(value))
                return ' '.join(text_parts)
            return str(item)
        except Exception as e:
            logger.error(f"Error extracting text for vectorization: {e}")
            return ""
            
    def _update_vectors(self, item):
        """Update vector storage with new item."""
        try:
            text = self._get_text_for_vectorization(item)
            if not text:
                return
                
            # Simple text storage instead of vector embeddings
            # Store the text as a list of tokens for simple text search
            tokens = text.lower().split()
            
            # Add to storage
            self.vectors.append(tokens)  # storing tokens instead of vectors
            self.metadata.append({
                'timestamp': datetime.now().isoformat(),
                'original_item': item,
                'text': text
            })
            
            # Keep only the most recent items
            if len(self.vectors) > self.max_length:
                self.vectors = self.vectors[-self.max_length:]
                self.metadata = self.metadata[-self.max_length:]
                
        except Exception as e:
            logger.error(f"Error updating text storage: {e}")
            
    def search(self, query, limit=5):
        """Search memory using text matching instead of vector similarity."""
        try:
            if not self.vectors:
                return []
                
            # Simple text search approach
            query_tokens = query.lower().split()
            
            results = []
            for idx, tokens in enumerate(self.vectors):
                if not tokens:
                    continue
                    
                # Calculate a simple similarity score based on token overlap
                common_tokens = set(query_tokens).intersection(set(tokens))
                if not common_tokens:
                    continue
                    
                # Score based on the percentage of query tokens found
                score = len(common_tokens) / len(query_tokens)
                
                if score >= 0.3:  # Lower threshold for text matching
                    metadata = self.metadata[idx]
                    results.append({
                        'content': metadata.get('text', self._get_text_for_vectorization(metadata['original_item'])),
                        'timestamp': metadata['timestamp'],
                        'score': float(score),
                        'original_item': metadata['original_item']
                    })
            
            # Sort by score (highest first)
            results.sort(key=lambda x: x['score'], reverse=True)
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error in text search: {e}")
            return []

class ConversationMemory(BaseMemory):
    def __init__(self, max_length=50):
        super().__init__(max_length)
        self.memory_file = "memory/conversation_memory.json"
        
    def add(self, message):
        """Add a message to conversation memory."""
        try:
            # Add timestamp if not present
            if 'timestamp' not in message:
                message['timestamp'] = datetime.now().isoformat()
                
            # Update vector storage
            self._update_vectors(message)
            
            # Save to file
            self._save()
            logger.debug(f"Added message to conversation memory: {message.get('type', 'unknown')}")
        except Exception as e:
            logger.error(f"Error adding message to conversation memory: {e}")
            
    def get_recent(self, count=5):
        """Get recent messages."""
        return [m['original_item'] for m in self.metadata[-count:]]
        
    def _save(self):
        """Save conversation memory to file."""
        try:
            os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
            with open(self.memory_file, 'w') as f:
                json.dump({
                    'vectors': self.vectors,  # Now storing token lists instead of numpy arrays
                    'metadata': self.metadata
                }, f)
        except Exception as e:
            logger.error(f"Error saving conversation memory: {e}")
            
    def load(self):
        """Load conversation memory from file."""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                    self.vectors = data.get('vectors', [])
                    self.metadata = data.get('metadata', [])
                    logger.info(f"Loaded {len(self.metadata)} messages from conversation memory")
        except Exception as e:
            logger.error(f"Error loading conversation memory: {e}")

class ContextMemory(BaseMemory):
    def __init__(self, max_history=20):
        super().__init__(max_history)
        self.memory_file = "memory/context_memory.json"
        
    def update(self, context):
        """Update context memory with new context."""
        try:
            # Add timestamp if not present
            if 'timestamp' not in context:
                context['timestamp'] = datetime.now().isoformat()
                
            # Update vector storage
            self._update_vectors(context)
            
            # Save to file
            self._save()
            logger.debug("Updated context memory")
        except Exception as e:
            logger.error(f"Error updating context memory: {e}")
            
    def get_relevant_context(self, query):
        """Get relevant context based on query."""
        try:
            results = self.search(query, limit=1)
            if results:
                return results[0]['original_item']
            return {}
        except Exception as e:
            logger.error(f"Error getting relevant context: {e}")
            return {}
            
    def _save(self):
        """Save context memory to file."""
        try:
            os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
            with open(self.memory_file, 'w') as f:
                json.dump({
                    'vectors': self.vectors,  # Now storing token lists instead of numpy arrays
                    'metadata': self.metadata
                }, f)
        except Exception as e:
            logger.error(f"Error saving context memory: {e}")
            
    def load(self):
        """Load context memory from file."""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                    self.vectors = data.get('vectors', [])
                    self.metadata = data.get('metadata', [])
                    logger.info(f"Loaded {len(self.metadata)} contexts from context memory")
        except Exception as e:
            logger.error(f"Error loading context memory: {e}")

class LongTermMemory(BaseMemory):
    def __init__(self, max_length=1000):
        super().__init__(max_length)
        self.memory_file = "memory/long_term_memory.json"
        
    def add(self, item):
        """Add item to long-term memory."""
        try:
            # Add timestamp if not present
            if 'timestamp' not in item:
                item['timestamp'] = datetime.now().isoformat()
                
            # Update vector storage
            self._update_vectors(item)
            
            # Save to file
            self._save()
            logger.debug("Added item to long-term memory")
        except Exception as e:
            logger.error(f"Error adding item to long-term memory: {e}")
            
    def _save(self):
        """Save long-term memory to file."""
        try:
            os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
            with open(self.memory_file, 'w') as f:
                json.dump({
                    'vectors': self.vectors,  # Now storing token lists instead of numpy arrays
                    'metadata': self.metadata
                }, f)
        except Exception as e:
            logger.error(f"Error saving long-term memory: {e}")
            
    def load(self):
        """Load long-term memory from file."""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                    self.vectors = data.get('vectors', [])
                    self.metadata = data.get('metadata', [])
                    logger.info(f"Loaded {len(self.metadata)} items from long-term memory")
        except Exception as e:
            logger.error(f"Error loading long-term memory: {e}")