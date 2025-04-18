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
class VectorKnowledgeBase(KnowledgeBase):
    """
    Knowledge base with semantic search capabilities.
    Note: This requires additional dependencies:
    - sentence-transformers
    - numpy
    - faiss-cpu or faiss-gpu
    """
    
    def __init__(self, storage_path: Optional[str] = None, embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize vector knowledge base.
        
        Args:
            storage_path: Path to store knowledge base files
            embedding_model: Model name for sentence-transformers
        """
        super().__init__(storage_path)
        self.logger.info("Vector knowledge base initialized - semantic search capabilities available")
        self.embedding_model_name = embedding_model
        self.vector_index = None
        self.vector_data = {}
        
        # Lazy init - we'll load the embedding model and build the index on first use
        self._embedding_model = None
        self._index_built = False
    
    def _get_embedding_model(self):
        """Lazy-load the embedding model."""
        if self._embedding_model is None:
            try:
                # This import is conditional since these are optional dependencies
                from sentence_transformers import SentenceTransformer
                self._embedding_model = SentenceTransformer(self.embedding_model_name)
                self.logger.info(f"Loaded embedding model: {self.embedding_model_name}")
            except ImportError:
                self.logger.error("sentence-transformers is required for VectorKnowledgeBase")
                raise
        return self._embedding_model
    
    def _build_index(self):
        """Build or rebuild the vector index."""
        try:
            import numpy as np
            import faiss
            
            # Get all text values for indexing
            texts = []
            keys = []
            
            for key, value in self.data.items():
                if isinstance(value, str):
                    texts.append(value)
                    keys.append(key)
                elif isinstance(value, dict) and "text" in value:
                    texts.append(value["text"])
                    keys.append(key)
            
            if not texts:
                self.logger.warning("No text entries to index")
                return
            
            # Get embeddings
            model = self._get_embedding_model()
            embeddings = model.encode(texts)
            
            # Build index
            dimension = embeddings.shape[1]
            index = faiss.IndexFlatL2(dimension)
            index.add(np.array(embeddings).astype('float32'))
            
            # Store index and data mapping
            self.vector_index = index
            self.vector_data = {i: keys[i] for i in range(len(keys))}
            self._index_built = True
            
            self.logger.info(f"Built vector index with {len(texts)} entries")
        except ImportError:
            self.logger.error("faiss-cpu is required for vector search")
            raise
        except Exception as e:
            self.logger.error(f"Error building vector index: {e}")
    
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
        
        # Mark index as needing rebuild
        if result:
            self._index_built = False
        
        return result
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search the knowledge base semantically.
        
        Args:
            query: Text to search for
            top_k: Number of results to return
            
        Returns:
            List of matching entries with scores and metadata
        """
        try:
            import numpy as np
            
            # Build/rebuild index if needed
            if not self._index_built or self.vector_index is None:
                self._build_index()
            
            if not self._index_built:
                return []
            
            # Get query embedding
            model = self._get_embedding_model()
            query_embedding = model.encode([query])
            
            # Search index
            distances, indices = self.vector_index.search(
                np.array(query_embedding).astype('float32'), 
                min(top_k, len(self.vector_data))
            )
            
            # Format results
            results = []
            for i, idx in enumerate(indices[0]):
                if idx >= 0 and idx < len(self.vector_data):
                    key = self.vector_data[idx]
                    data = self.data.get(key)
                    metadata = self.metadata.get(key, {})
                    
                    # Check if expired
                    expires_at = metadata.get("expires_at")
                    if expires_at and time.time() > expires_at:
                        continue
                    
                    results.append({
                        "key": key,
                        "data": data,
                        "score": float(1.0 / (1.0 + distances[0][i])),  # Convert distance to similarity score
                        "category": metadata.get("category"),
                        "created_at": metadata.get("created_at")
                    })
            
            return results
        except Exception as e:
            self.logger.error(f"Error performing vector search: {e}")
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