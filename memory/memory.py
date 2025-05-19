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
from sentence_transformers import SentenceTransformer
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
        try:
            self.vector_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Vector model initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing vector model: {e}")
            self.vector_model = None
            
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
            if not self.vector_model:
                return
                
            text = self._get_text_for_vectorization(item)
            if not text:
                return
                
            # Generate vector embedding
            vector = self.vector_model.encode(text)
            
            # Add to vector storage
            self.vectors.append(vector)
            self.metadata.append({
                'timestamp': datetime.now().isoformat(),
                'original_item': item
            })
            
            # Keep only the most recent vectors
            if len(self.vectors) > self.max_length:
                self.vectors = self.vectors[-self.max_length:]
                self.metadata = self.metadata[-self.max_length:]
                
        except Exception as e:
            logger.error(f"Error updating vectors: {e}")
            
    def search(self, query, limit=5):
        """Search memory using vector similarity."""
        try:
            if not self.vector_model or not self.vectors:
                return []
                
            # Generate query vector
            query_vector = self.vector_model.encode(query)
            
            # Calculate similarities
            vectors = np.array(self.vectors)
            similarities = cosine_similarity([query_vector], vectors)[0]
            
            # Get top matches
            top_indices = np.argsort(similarities)[-limit:][::-1]
            
            results = []
            for idx in top_indices:
                similarity = similarities[idx]
                if similarity >= 0.7:  # Similarity threshold
                    metadata = self.metadata[idx]
                    results.append({
                        'content': self._get_text_for_vectorization(metadata['original_item']),
                        'timestamp': metadata['timestamp'],
                        'score': float(similarity),
                        'original_item': metadata['original_item']
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
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
                    'vectors': [v.tolist() for v in self.vectors],
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
                    self.vectors = [np.array(v) for v in data.get('vectors', [])]
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
                    'vectors': [v.tolist() for v in self.vectors],
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
                    self.vectors = [np.array(v) for v in data.get('vectors', [])]
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
                    'vectors': [v.tolist() for v in self.vectors],
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
                    self.vectors = [np.array(v) for v in data.get('vectors', [])]
                    self.metadata = data.get('metadata', [])
                    logger.info(f"Loaded {len(self.metadata)} items from long-term memory")
        except Exception as e:
            logger.error(f"Error loading long-term memory: {e}")