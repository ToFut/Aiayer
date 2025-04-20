import faiss
import sqlite3
import json
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer
from datetime import datetime

class KnowledgeStore:
    """Efficient storage for knowledge base with vector search"""
    
    def __init__(self, 
                 data_dir: str = "data",
                 max_memory_size: int = 1024 * 1024 * 1024):  # 1GB
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize SQLite
        self.db_path = self.data_dir / "knowledge.db"
        self._init_sqlite()
        
        # Initialize FAISS
        self.vector_dim = 384  # all-MiniLM-L6-v2 dimension
        self.index = faiss.IndexFlatL2(self.vector_dim)
        self.vector_ids = []
        
        # Initialize sentence transformer
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        
        self.logger = logging.getLogger(__name__)
        
    def _init_sqlite(self):
        """Initialize SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create knowledge table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    context TEXT,
                    category TEXT,
                    confidence FLOAT,
                    created_at TIMESTAMP,
                    last_accessed TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    source TEXT,
                    metadata TEXT
                )
            """)
            
            # Create relationships table for knowledge graph
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS relationships (
                    source_id TEXT,
                    target_id TEXT,
                    relationship_type TEXT,
                    confidence FLOAT,
                    created_at TIMESTAMP,
                    PRIMARY KEY (source_id, target_id, relationship_type),
                    FOREIGN KEY (source_id) REFERENCES knowledge(id),
                    FOREIGN KEY (target_id) REFERENCES knowledge(id)
                )
            """)
            
            conn.commit()
            
    async def store(self, 
                   content: str,
                   context: Optional[Dict] = None,
                   category: Optional[str] = None,
                   confidence: float = 1.0,
                   source: Optional[str] = None,
                   metadata: Optional[Dict] = None) -> str:
        """Store knowledge with vector indexing"""
        try:
            # Generate unique ID
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            # Store in SQLite
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO knowledge 
                    (id, content, context, category, confidence, created_at, last_accessed, source, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    content_hash,
                    content,
                    json.dumps(context) if context else None,
                    category,
                    confidence,
                    datetime.now(),
                    datetime.now(),
                    source,
                    json.dumps(metadata) if metadata else None
                ))
                conn.commit()
                
            # Update vector index
            self._update_vector_index(content_hash, content)
            
            return content_hash
            
        except Exception as e:
            self.logger.error(f"Error storing knowledge: {e}")
            raise
            
    def _update_vector_index(self, id: str, content: str):
        """Update FAISS index with new content"""
        try:
            # Generate embedding
            embedding = self.encoder.encode([content])[0]
            
            # Add to index
            self.index.add(np.array([embedding], dtype=np.float32))
            self.vector_ids.append(id)
            
        except Exception as e:
            self.logger.error(f"Error updating vector index: {e}")
            
    async def retrieve(self, id: str) -> Optional[Dict]:
        """Retrieve knowledge by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT content, context, category, confidence, source, metadata
                    FROM knowledge WHERE id = ?
                """, (id,))
                
                result = cursor.fetchone()
                if not result:
                    return None
                    
                content, context, category, confidence, source, metadata = result
                
                # Update access count
                cursor.execute("""
                    UPDATE knowledge 
                    SET access_count = access_count + 1,
                        last_accessed = ?
                    WHERE id = ?
                """, (datetime.now(), id))
                conn.commit()
                
                return {
                    'content': content,
                    'context': json.loads(context) if context else None,
                    'category': category,
                    'confidence': confidence,
                    'source': source,
                    'metadata': json.loads(metadata) if metadata else None
                }
                
        except Exception as e:
            self.logger.error(f"Error retrieving knowledge: {e}")
            return None
            
    async def search(self, query: str, limit: int = 5) -> List[Dict]:
        """Search knowledge using semantic similarity"""
        try:
            # Generate query embedding
            query_embedding = self.encoder.encode([query])[0]
            
            # Search FAISS index
            distances, indices = self.index.search(
                np.array([query_embedding], dtype=np.float32),
                limit
            )
            
            # Retrieve knowledge
            results = []
            for idx, distance in zip(indices[0], distances[0]):
                if idx < len(self.vector_ids):
                    knowledge_id = self.vector_ids[idx]
                    knowledge = await self.retrieve(knowledge_id)
                    if knowledge:
                        results.append({
                            'knowledge': knowledge,
                            'similarity': 1.0 / (1.0 + distance)  # Convert distance to similarity
                        })
                        
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching knowledge: {e}")
            return []
            
    async def add_relationship(self, 
                             source_id: str,
                             target_id: str,
                             relationship_type: str,
                             confidence: float = 1.0):
        """Add relationship between knowledge items"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO relationships 
                    (source_id, target_id, relationship_type, confidence, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    source_id,
                    target_id,
                    relationship_type,
                    confidence,
                    datetime.now()
                ))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error adding relationship: {e}")
            
    async def get_relationships(self, 
                              id: str,
                              relationship_type: Optional[str] = None) -> List[Dict]:
        """Get relationships for a knowledge item"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if relationship_type:
                    cursor.execute("""
                        SELECT target_id, relationship_type, confidence
                        FROM relationships
                        WHERE source_id = ? AND relationship_type = ?
                    """, (id, relationship_type))
                else:
                    cursor.execute("""
                        SELECT target_id, relationship_type, confidence
                        FROM relationships
                        WHERE source_id = ?
                    """, (id,))
                    
                results = []
                for row in cursor.fetchall():
                    target_id, rel_type, confidence = row
                    target = await self.retrieve(target_id)
                    if target:
                        results.append({
                            'target': target,
                            'relationship_type': rel_type,
                            'confidence': confidence
                        })
                        
                return results
                
        except Exception as e:
            self.logger.error(f"Error getting relationships: {e}")
            return []
            
    async def update_confidence(self, id: str, confidence: float):
        """Update confidence score for knowledge"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE knowledge
                    SET confidence = ?
                    WHERE id = ?
                """, (confidence, id))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error updating confidence: {e}")
            
    async def get_statistics(self) -> Dict:
        """Get knowledge base statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get total entries
                cursor.execute("SELECT COUNT(*) FROM knowledge")
                total_entries = cursor.fetchone()[0]
                
                # Get categories
                cursor.execute("SELECT category, COUNT(*) FROM knowledge GROUP BY category")
                categories = dict(cursor.fetchall())
                
                # Get average confidence
                cursor.execute("SELECT AVG(confidence) FROM knowledge")
                avg_confidence = cursor.fetchone()[0]
                
                # Get relationship types
                cursor.execute("SELECT relationship_type, COUNT(*) FROM relationships GROUP BY relationship_type")
                relationships = dict(cursor.fetchall())
                
                return {
                    'total_entries': total_entries,
                    'categories': categories,
                    'average_confidence': avg_confidence,
                    'relationships': relationships
                }
                
        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            return {} 