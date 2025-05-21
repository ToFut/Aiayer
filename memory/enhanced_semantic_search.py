"""
Enhanced Semantic Search Module

Provides vector-based semantic search capabilities with hybrid retrieval
to find relevant information across all memory types.
"""
import numpy as np
import logging
import time
from typing import Dict, List, Any, Tuple, Optional, Union
from datetime import datetime
import json
import os
import re
from collections import Counter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedSemanticSearch:
    """
    Enhanced semantic search implementation using vector embeddings and hybrid retrieval.
    Compatible with all memory types: short-term, long-term, context, and conscious memory.
    """
    
    def __init__(self, embedding_dim=384, use_hybrid=True):
        """
        Initialize the enhanced semantic search module.
        
        Args:
            embedding_dim: Dimension of the vector embeddings
            use_hybrid: Whether to use hybrid retrieval (vector + token-based)
        """
        self.embedding_dim = embedding_dim
        self.use_hybrid = use_hybrid
        self.memory_vectors = {}  # Store for memory item vectors
        self.memory_items = {}    # Store for original memory items
        self.token_index = {}     # Inverted index for token-based search
        self.vector_count = 0
        self.max_vectors = 10000  # Maximum vectors to store
        
        # Try to create a mock embedding function since we can't import heavy ML libraries
        self.embedding_fn = self._create_mock_embedding_function()
        
        logger.info(f"Enhanced semantic search initialized with embedding dim: {embedding_dim}")
        logger.info(f"Hybrid retrieval enabled: {use_hybrid}")
    
    def _create_mock_embedding_function(self):
        """
        Create a mock embedding function that produces deterministic vectors
        based on text features. This simulates a real embedding model without
        requiring heavy dependencies.
        
        In a production system, this would be replaced with a proper embedding model
        like SentenceTransformers, OpenAI embeddings, or similar.
        """
        def mock_embedding(text):
            """Generate a mock embedding vector that captures some text features"""
            if not text:
                return np.zeros(self.embedding_dim)
            
            # Create a more sophisticated mock embedding that captures some semantic features
            # This is still a mock, but tries to create vectors that will cluster similar content
            
            # Convert to lowercase and tokenize
            text = text.lower()
            tokens = re.findall(r'\w+', text)
            
            # Initialize embedding vector with a deterministic hash of the text
            text_hash = hash(text) % 10000
            rng = np.random.RandomState(text_hash)
            embedding = rng.randn(self.embedding_dim) * 0.1
            
            # Enhance with token-based features
            token_set = set(tokens)
            for i, token in enumerate(tokens):
                # Modify specific dimensions based on token hash
                token_hash = hash(token) % self.embedding_dim
                embedding[token_hash % self.embedding_dim] += 0.5
                
                # Add positional influence (words at start/end are often more important)
                position_factor = 1.0 - (i / max(len(tokens), 1))
                embedding[(token_hash + 1) % self.embedding_dim] += 0.3 * position_factor
                
                # Enhance common semantic dimensions for specific word categories
                if token in ['how', 'why', 'what', 'when', 'who']:  # Question words
                    embedding[0:20] += 0.2
                elif token in ['not', 'no', 'never', 'without']:    # Negation
                    embedding[20:40] += 0.2
                elif re.match(r'^\d+$', token):                     # Numbers
                    embedding[40:60] += 0.2
                elif token in ['important', 'critical', 'urgent']:  # Importance
                    embedding[60:80] += 0.3
            
            # Normalize vector to unit length
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
                
            return embedding
            
        return mock_embedding
    
    def add_to_index(self, item: Dict[str, Any], memory_type: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Add a memory item to the search index.
        
        Args:
            item: The memory item to add
            memory_type: Type of memory ('short_term', 'long_term', 'context', 'conscious')
            metadata: Optional metadata about the item
        
        Returns:
            item_id: Unique ID for the indexed item
        """
        try:
            # Extract text content for vectorization
            text = self._extract_text(item)
            if not text:
                logger.warning(f"Empty text content in item, skipping indexing: {item.get('id', 'unknown')}")
                return None
                
            # Generate a unique ID if not present
            item_id = item.get('id', f"{memory_type}_{int(time.time() * 1000)}_{len(self.memory_items)}")
            
            # Create vector embedding
            vector = self.embedding_fn(text)
            
            # Store the vector and original item
            self.memory_vectors[item_id] = {
                'vector': vector,
                'timestamp': item.get('timestamp', datetime.now().isoformat()),
                'memory_type': memory_type,
                'metadata': metadata or {}
            }
            
            # Store the original item
            self.memory_items[item_id] = item
            
            # Add to token index for hybrid search
            if self.use_hybrid:
                self._add_to_token_index(item_id, text)
            
            # Limit the number of vectors
            self._enforce_vector_limit()
            
            self.vector_count += 1
            if self.vector_count % 100 == 0:
                logger.info(f"Added {self.vector_count} items to vector index")
                
            return item_id
            
        except Exception as e:
            logger.error(f"Error adding item to index: {e}")
            return None
    
    def _extract_text(self, item: Dict[str, Any]) -> str:
        """
        Extract usable text from a memory item for vectorization.
        Enhanced with application-specific awareness.
        """
        text_parts = []
        
        # Extract application-specific data with high priority
        if 'application' in item and isinstance(item['application'], dict):
            app_data = item['application']
            app_info = []
            
            if app_data.get('name'):
                app_info.append(f"Application: {app_data['name']}")
            if app_data.get('view'):
                app_info.append(f"View: {app_data['view']}")
            if app_data.get('workflow_stage'):
                app_info.append(f"Task: {app_data['workflow_stage']}")
                
            if app_info:
                text_parts.append(' | '.join(app_info))
        
        # Extract email data with high priority
        if 'email_data' in item and isinstance(item['email_data'], dict):
            email_info = []
            email_data = item['email_data']
            
            if email_data.get('from'):
                email_info.append(f"From: {email_data['from']}")
            if email_data.get('to'):
                email_info.append(f"To: {email_data['to']}")
            if email_data.get('subject'):
                email_info.append(f"Subject: {email_data['subject']}")
                
            if email_info:
                text_parts.append('Email: ' + ' | '.join(email_info))
        
        # Extract form data with high priority
        if 'form_data' in item and isinstance(item['form_data'], dict):
            if 'form_fields' in item['form_data'] and item['form_data']['form_fields']:
                form_fields = item['form_data']['form_fields']
                if isinstance(form_fields, list):
                    text_parts.append('Form fields: ' + ', '.join(form_fields[:5]))
        
        # Extract content field (primary text)
        if 'content' in item and item['content']:
            text_parts.append(str(item['content']))
        
        # Extract message content
        if 'message_content' in item and item['message_content']:
            text_parts.append(str(item['message_content']))
        
        # Extract screen text for context
        if 'screen_content' in item and item['screen_content']:
            # Limit long screen content
            screen_content = str(item['screen_content'])
            if len(screen_content) > 1000:
                screen_content = screen_content[:1000]
            text_parts.append(screen_content)
        
        # Extract window title
        if 'window_title' in item and item['window_title']:
            text_parts.append(str(item['window_title']))
        elif 'window' in item and item['window']:
            text_parts.append(str(item['window']))
        
        # Extract visual context for improved understanding
        if 'visual_context' in item and item['visual_context']:
            text_parts.append(str(item['visual_context']))
        
        # Extract text from sensor_states
        if 'sensor_states' in item and isinstance(item['sensor_states'], dict):
            # Screen sensor text
            if 'screen' in item['sensor_states']:
                screen_data = item['sensor_states']['screen']
                if isinstance(screen_data, dict) and 'window_info' in screen_data:
                    text_parts.append(str(screen_data['window_info']))
            
            # Process sensor - active applications
            if 'process' in item['sensor_states'] and isinstance(item['sensor_states']['process'], dict):
                process_data = item['sensor_states']['process']
                if 'active_processes' in process_data and process_data['active_processes']:
                    text_parts.append(' '.join(str(p) for p in process_data['active_processes'][:10]))
        
        # Extract active apps/windows for context
        if 'active_apps' in item and item['active_apps']:
            if isinstance(item['active_apps'], list):
                text_parts.append(' '.join(str(app) for app in item['active_apps'][:10]))
            else:
                text_parts.append(str(item['active_apps']))
        
        # Concatenate all parts with spaces, but give more weight to application-specific info
        # by placing it at both the beginning and end of the text
        result_text = ' '.join(text_parts)
        
        # For very long texts, truncate to a reasonable size to avoid embedding issues
        if len(result_text) > 5000:
            result_text = result_text[:5000]
            
        return result_text
    
    def _add_to_token_index(self, item_id: str, text: str) -> None:
        """Add item to token-based inverted index for hybrid search."""
        # Tokenize and add to inverted index
        tokens = re.findall(r'\w+', text.lower())
        
        for token in tokens:
            if token not in self.token_index:
                self.token_index[token] = set()
            self.token_index[token].add(item_id)
    
    def _enforce_vector_limit(self) -> None:
        """Ensure vector count stays below maximum limit."""
        if len(self.memory_vectors) > self.max_vectors:
            # Sort by timestamp and keep only the most recent
            sorted_items = sorted(
                self.memory_vectors.items(),
                key=lambda x: x[1].get('timestamp', ''),
                reverse=True
            )
            
            # Keep only max_vectors items
            items_to_keep = dict(sorted_items[:self.max_vectors])
            items_to_remove = set(self.memory_vectors.keys()) - set(items_to_keep.keys())
            
            # Remove excess items
            for item_id in items_to_remove:
                self.memory_vectors.pop(item_id, None)
                self.memory_items.pop(item_id, None)
                
                # Clean up token index
                for token_items in self.token_index.values():
                    if item_id in token_items:
                        token_items.remove(item_id)
            
            logger.info(f"Pruned vector index to {len(self.memory_vectors)} items")
    
    def search(self, query: str, limit: int = 5, memory_types: List[str] = None, 
               min_score: float = 0.5, application_context: str = None) -> List[Dict[str, Any]]:
        """
        Search for relevant memory items using vector similarity with application context awareness.
        
        Args:
            query: The search query
            limit: Maximum number of results to return
            memory_types: Types of memory to search (None for all)
            min_score: Minimum similarity score threshold
            application_context: Optional application context to enhance relevance
        
        Returns:
            List of memory items with score and metadata
        """
        try:
            if not query:
                return []
            
            # Default to all memory types if not specified
            if not memory_types:
                memory_types = ['short_term', 'long_term', 'context', 'conscious']
            
            # Enhance query with application context if provided
            enhanced_query = query
            if application_context:
                enhanced_query = f"{query} {application_context}"
                logger.info(f"Enhanced query with application context: {enhanced_query[:50]}...")
            
            # Generate vector embedding for enhanced query
            query_vector = self.embedding_fn(enhanced_query)
            
            # Search results - vector-based
            vector_results = self._vector_search(query_vector, memory_types, limit*2)
            
            # If hybrid search enabled, also do token-based search
            if self.use_hybrid:
                token_results = self._token_search(enhanced_query, memory_types, limit*2)
                # Combine results with score normalization
                combined_results = self._combine_search_results(vector_results, token_results)
            else:
                combined_results = vector_results
            
            # Filter by minimum score and take top results
            filtered_results = [
                result for result in combined_results 
                if result.get('score', 0) >= min_score
            ]
            
            # Sort by score (highest first) and limit results
            filtered_results.sort(key=lambda x: x.get('score', 0), reverse=True)
            
            # Application-aware re-ranking if context provided
            if application_context:
                # Boost scores for items that match the application context
                app_terms = set(application_context.lower().split())
                for result in filtered_results:
                    item_id = result.get('id')
                    original_item = self.memory_items.get(item_id, {})
                    
                    # Check for application-specific data in the item
                    if 'application' in original_item:
                        # Significant boost for items from the same application
                        app_name = original_item['application'].get('name', '').lower()
                        if app_name and any(term in app_name for term in app_terms):
                            result['score'] *= 1.5  # 50% boost for matching application
                            
                        # Boost for items with workflow stage info
                        if original_item['application'].get('workflow_stage'):
                            result['score'] *= 1.2  # 20% boost for workflow stage info
                    
                    # Also check email and form data if relevant to the application context
                    if 'email' in application_context.lower() and 'email_data' in original_item:
                        result['score'] *= 1.3  # 30% boost for email data
                    
                    if 'form' in application_context.lower() and 'form_data' in original_item:
                        result['score'] *= 1.3  # 30% boost for form data
                
                # Re-sort after boosting
                filtered_results.sort(key=lambda x: x.get('score', 0), reverse=True)
            
            # Apply limit after all processing
            limited_results = filtered_results[:limit]
            
            # Prepare final results
            final_results = []
            for result in limited_results:
                item_id = result.get('id')
                original_item = self.memory_items.get(item_id, {})
                
                final_results.append({
                    'content': self._extract_text(original_item),
                    'score': result.get('score', 0),
                    'id': item_id,
                    'source': result.get('memory_type', 'unknown'),
                    'timestamp': original_item.get('timestamp', ''),
                    'original_item': original_item,
                    # Add application context if available
                    'application_context': original_item.get('application', {}).get('name', '') if 'application' in original_item else ''
                })
            
            logger.info(f"Search for '{query[:30]}...' found {len(final_results)} results.")
            return final_results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def _vector_search(self, query_vector: np.ndarray, memory_types: List[str], 
                       limit: int) -> List[Dict[str, Any]]:
        """Perform vector-based semantic search."""
        results = []
        
        # Calculate similarity for all vectors of specified memory types
        for item_id, item_data in self.memory_vectors.items():
            # Filter by memory type
            if item_data.get('memory_type') not in memory_types:
                continue
            
            # Calculate cosine similarity
            item_vector = item_data.get('vector')
            if item_vector is not None:
                similarity = np.dot(query_vector, item_vector)
                
                # Add to results
                results.append({
                    'id': item_id,
                    'score': float(similarity),
                    'memory_type': item_data.get('memory_type')
                })
        
        # Sort by similarity (highest first)
        results.sort(key=lambda x: x.get('score', 0), reverse=True)
        return results[:limit]
    
    def _token_search(self, query: str, memory_types: List[str], limit: int) -> List[Dict[str, Any]]:
        """Perform token-based search for hybrid retrieval."""
        # Tokenize query
        query_tokens = set(re.findall(r'\w+', query.lower()))
        if not query_tokens:
            return []
        
        # Calculate BM25-like scores
        item_scores = {}
        
        for token in query_tokens:
            if token in self.token_index:
                # Get items containing this token
                item_ids = self.token_index[token]
                
                for item_id in item_ids:
                    # Check memory type
                    if item_id in self.memory_vectors and self.memory_vectors[item_id].get('memory_type') in memory_types:
                        if item_id not in item_scores:
                            item_scores[item_id] = 0
                        
                        # Increase score for this item containing the token
                        # We could implement full BM25 with term frequencies and doc lengths here
                        item_scores[item_id] += 1
        
        # Normalize scores and prepare results
        results = []
        max_score = max(item_scores.values()) if item_scores else 1
        
        for item_id, score in item_scores.items():
            # Normalize score to [0,1] range
            normalized_score = score / max_score
            
            results.append({
                'id': item_id,
                'score': normalized_score,
                'memory_type': self.memory_vectors.get(item_id, {}).get('memory_type', 'unknown')
            })
        
        # Sort by score
        results.sort(key=lambda x: x.get('score', 0), reverse=True)
        return results[:limit]
    
    def _combine_search_results(self, vector_results: List[Dict[str, Any]], 
                                token_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Combine vector and token search results with weighted scores."""
        # Use a weighted combination of scores
        vector_weight = 0.7  # Vector search gets higher weight
        token_weight = 0.3   # Token-based search gets lower weight
        
        # Build a dictionary of combined results
        combined_scores = {}
        
        # Add vector results
        for result in vector_results:
            item_id = result.get('id')
            combined_scores[item_id] = {
                'id': item_id,
                'score': result.get('score', 0) * vector_weight,
                'memory_type': result.get('memory_type', 'unknown')
            }
        
        # Add token results
        for result in token_results:
            item_id = result.get('id')
            if item_id in combined_scores:
                # Item exists in both results, add weighted token score
                combined_scores[item_id]['score'] += result.get('score', 0) * token_weight
            else:
                # Item only in token results
                combined_scores[item_id] = {
                    'id': item_id,
                    'score': result.get('score', 0) * token_weight,
                    'memory_type': result.get('memory_type', 'unknown')
                }
        
        # Convert back to list
        return list(combined_scores.values())
    
    def clear(self) -> None:
        """Clear all indexed data."""
        self.memory_vectors = {}
        self.memory_items = {}
        self.token_index = {}
        self.vector_count = 0
        logger.info("Cleared all indexed memory data")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the indexed data."""
        memory_type_counts = {}
        for item_data in self.memory_vectors.values():
            memory_type = item_data.get('memory_type', 'unknown')
            memory_type_counts[memory_type] = memory_type_counts.get(memory_type, 0) + 1
        
        return {
            'total_items': len(self.memory_vectors),
            'memory_types': memory_type_counts,
            'token_index_size': len(self.token_index),
            'embedding_dim': self.embedding_dim,
            'hybrid_search': self.use_hybrid
        }

# Global instance
enhanced_search = EnhancedSemanticSearch()