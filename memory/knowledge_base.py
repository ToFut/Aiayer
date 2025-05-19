"""
Knowledge Base Module (Optional)
For storing and retrieving long-term information beyond conversation memory.
"""
import os
import json
import time
import logging
from typing import Dict, List, Any, Optional, Union


class KnowledgeBase:
    """
    Simple key-value storage for persistent information.
    Can be extended with vector storage for semantic search.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize the knowledge base.
        
        Args:
            storage_path: Path to store knowledge base files. If None, uses a default path.
        """
        self.logger = logging.getLogger(__name__)
        
        if storage_path is None:
            home_dir = os.path.expanduser("~")
            storage_path = os.path.join(home_dir, ".local_assistant", "knowledge")
        
        self.storage_path = storage_path
        self.data: Dict[str, Any] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}
        
        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Load existing knowledge base if available
        self._load()
    
    def _load(self) -> None:
        """Load knowledge base from disk."""
        data_file = os.path.join(self.storage_path, "knowledge.json")
        metadata_file = os.path.join(self.storage_path, "metadata.json")
        
        try:
            if os.path.exists(data_file):
                with open(data_file, 'r') as f:
                    self.data = json.load(f)
                self.logger.info(f"Loaded knowledge base with {len(self.data)} entries")
            
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    self.metadata = json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading knowledge base: {e}")
            self.data = {}
            self.metadata = {}
    
    def _save(self) -> None:
        """Save knowledge base to disk."""
        data_file = os.path.join(self.storage_path, "knowledge.json")
        metadata_file = os.path.join(self.storage_path, "metadata.json")
        
        try:
            with open(data_file, 'w') as f:
                json.dump(self.data, f, indent=2)
            
            with open(metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
            
            self.logger.debug("Knowledge base saved to disk")
        except Exception as e:
            self.logger.error(f"Error saving knowledge base: {e}")
    
    def store(self, key: str, value: Any, category: Optional[str] = None, 
              ttl: Optional[int] = None) -> bool:
        """
        Store a value in the knowledge base.
        
        Args:
            key: Unique identifier for this knowledge
            value: The data to store
            category: Optional category for organizing knowledge
            ttl: Time to live in seconds (None = no expiration)
            
        Returns:
            bool: True if storage succeeded
        """
        try:
            # Store the actual data
            self.data[key] = value
            
            # Store metadata
            self.metadata[key] = {
                "created_at": time.time(),
                "updated_at": time.time(),
                "category": category,
                "expires_at": time.time() + ttl if ttl else None
            }
            
            # Save to disk
            self._save()
            return True
        except Exception as e:
            self.logger.error(f"Error storing knowledge '{key}': {e}")
            return False
    
    def retrieve(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a value from the knowledge base.
        
        Args:
            key: The identifier to look up
            default: Value to return if key not found
            
        Returns:
            The stored value or default
        """
        # Check if key exists
        if key not in self.data:
            return default
        
        # Check if expired
        if key in self.metadata:
            expires_at = self.metadata[key].get("expires_at")
            if expires_at and time.time() > expires_at:
                # Delete expired entry
                self.delete(key)
                return default
            
            # Update last accessed time
            self.metadata[key]["accessed_at"] = time.time()
        
        return self.data[key]
    
    def delete(self, key: str) -> bool:
        """
        Delete an entry from the knowledge base.
        
        Args:
            key: The identifier to delete
            
        Returns:
            bool: True if deletion succeeded
        """
        try:
            if key in self.data:
                del self.data[key]
            
            if key in self.metadata:
                del self.metadata[key]
            
            self._save()
            return True
        except Exception as e:
            self.logger.error(f"Error deleting knowledge '{key}': {e}")
            return False
    
    def list_by_category(self, category: str) -> List[str]:
        """
        List all keys in a specific category.
        
        Args:
            category: Category to filter by
            
        Returns:
            List of keys in the category
        """
        result = []
        for key, meta in self.metadata.items():
            if meta.get("category") == category:
                # Check if expired
                expires_at = meta.get("expires_at")
                if expires_at and time.time() > expires_at:
                    continue
                result.append(key)
        return result
    
    def clear(self) -> bool:
        """
        Clear all knowledge base entries.
        
        Returns:
            bool: True if operation succeeded
        """
        try:
            self.data = {}
            self.metadata = {}
            self._save()
            return True
        except Exception as e:
            self.logger.error(f"Error clearing knowledge base: {e}")
            return False
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the knowledge base.
        
        Returns:
            dict: Summary information
        """
        categories = {}
        expired = 0
        total = len(self.metadata)
        
        for key, meta in self.metadata.items():
            category = meta.get("category", "uncategorized")
            
            # Check if expired
            expires_at = meta.get("expires_at")
            if expires_at and time.time() > expires_at:
                expired += 1
                continue
            
            # Count by category
            if category not in categories:
                categories[category] = 0
            categories[category] += 1
        
        return {
            "total_entries": total,
            "active_entries": total - expired,
            "expired_entries": expired,
            "categories": categories
        }
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from the knowledge base.
        
        Returns:
            int: Number of entries removed
        """
        expired_keys = []
        
        # Find expired entries
        for key, meta in self.metadata.items():
            expires_at = meta.get("expires_at")
            if expires_at and time.time() > expires_at:
                expired_keys.append(key)
        
        # Delete them
        for key in expired_keys:
            self.delete(key)
        
        self.logger.info(f"Cleaned up {len(expired_keys)} expired knowledge base entries")
        return len(expired_keys)


# Optional: Vector-based semantic search extension
# This requires additional dependencies like sentence-transformers
class TextSearchKnowledgeBase(KnowledgeBase):
    """
    Knowledge base with text-based search capabilities.
    This is a replacement for VectorKnowledgeBase that doesn't require 
    sentence-transformers or other heavy dependencies.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize text search knowledge base.
        
        Args:
            storage_path: Path to store knowledge base files
        """
        super().__init__(storage_path)
        self.logger.info("Text search knowledge base initialized")
        self.text_index = {}  # Key -> tokenized content
        
    def _tokenize_text(self, text: str) -> List[str]:
        """Convert text to tokens for search."""
        if not isinstance(text, str):
            return []
        # Simple tokenization - split on whitespace and convert to lowercase
        return text.lower().split()
    
    def _update_index(self):
        """Update the text search index."""
        try:
            self.text_index = {}
            
            # Index all text content
            for key, value in self.data.items():
                if isinstance(value, str):
                    self.text_index[key] = self._tokenize_text(value)
                elif isinstance(value, dict) and "text" in value:
                    self.text_index[key] = self._tokenize_text(value["text"])
            
            self.logger.info(f"Built text index with {len(self.text_index)} entries")
        except Exception as e:
            self.logger.error(f"Error building text index: {e}")
    
    def store(self, key: str, value: Any, category: Optional[str] = None, 
              ttl: Optional[int] = None) -> bool:
        """
        Store a value with automatic indexing for text content.
        
        Args:
            key: Unique identifier for this knowledge
            value: The data to store
            category: Optional category for organizing knowledge
            ttl: Time to live in seconds (None = no expiration)
            
        Returns:
            bool: True if storage succeeded
        """
        result = super().store(key, value, category, ttl)
        
        # Update index with new content
        if result:
            if isinstance(value, str):
                self.text_index[key] = self._tokenize_text(value)
            elif isinstance(value, dict) and "text" in value:
                self.text_index[key] = self._tokenize_text(value["text"])
        
        return result
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search the knowledge base using text matching.
        
        Args:
            query: Text to search for
            top_k: Number of results to return
            
        Returns:
            List of matching entries with scores and metadata
        """
        try:
            # Make sure index is up to date
            if not self.text_index:
                self._update_index()
            
            # Tokenize query
            query_tokens = self._tokenize_text(query)
            if not query_tokens:
                return []
            
            # Calculate text similarity for each entry
            scored_results = []
            for key, tokens in self.text_index.items():
                # Skip if key is no longer in data (might have been deleted)
                if key not in self.data:
                    continue
                    
                # Check if expired
                metadata = self.metadata.get(key, {})
                expires_at = metadata.get("expires_at")
                if expires_at and time.time() > expires_at:
                    continue
                
                # Calculate text similarity (token overlap)
                if not tokens:
                    continue
                    
                # Find common tokens
                common_tokens = set(query_tokens).intersection(set(tokens))
                if not common_tokens:
                    continue
                
                # Score based on percentage of query tokens found
                score = len(common_tokens) / len(query_tokens)
                
                if score >= 0.3:  # Minimum relevance threshold
                    scored_results.append({
                        "key": key,
                        "data": self.data.get(key),
                        "score": float(score),
                        "category": metadata.get("category"),
                        "created_at": metadata.get("created_at")
                    })
            
            # Sort by score (descending)
            scored_results.sort(key=lambda x: x["score"], reverse=True)
            
            return scored_results[:top_k]
        except Exception as e:
            self.logger.error(f"Error performing text search: {e}")
            return []


# For testing if run directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test basic knowledge base
    kb = KnowledgeBase()
    
    # Store some test data
    kb.store("test1", "This is a test entry", category="test")
    kb.store("test2", {"text": "This is a structured entry", "value": 42}, category="test")
    kb.store("temp1", "This entry will expire soon", category="temporary", ttl=5)
    
    # Retrieve and print data
    print("Retrieved test1:", kb.retrieve("test1"))
    print("Retrieved test2:", kb.retrieve("test2"))
    print("Retrieved non-existent:", kb.retrieve("nonexistent", "Default value"))
    
    # List and summarize
    print("Test category entries:", kb.list_by_category("test"))
    print("Knowledge base summary:", kb.get_summary())
    
    # Test expiration
    print("Temp entry before expiry:", kb.retrieve("temp1"))
    print("Waiting for expiration...")
    time.sleep(6)
    print("Temp entry after expiry:", kb.retrieve("temp1"))
    
    # Clean up
    kb.clear()
    print("After clearing:", kb.get_summary())
    
    # Uncomment to test vector search (requires additional dependencies)
    """
    print("\nTesting Vector Knowledge Base")
    vkb = VectorKnowledgeBase()
    
    # Store some test data
    vkb.store("doc1", "Python is a programming language that lets you work quickly and integrate systems effectively.", category="programming")
    vkb.store("doc2", "Machine learning is a type of artificial intelligence that allows software applications to become more accurate at predicting outcomes.", category="ai")
    vkb.store("doc3", "Natural language processing helps computers communicate with humans in their own language.", category="ai")
    
    # Search
    print("Search results for 'python programming':")
    for result in vkb.search("python programming"):
        print(f"  - {result['key']} (Score: {result['score']:.2f}): {result['data']}")
    
    print("\nSearch results for 'artificial intelligence':")
    for result in vkb.search("artificial intelligence"):
        print(f"  - {result['key']} (Score: {result['score']:.2f}): {result['data']}")
    
    # Clean up
    vkb.clear()
    """