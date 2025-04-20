import json
import os
import logging
from typing import Dict, List, Optional
from datetime import datetime
import hashlib
import sqlite3
from pathlib import Path

class KnowledgeBase:
    """Knowledge base for storing and retrieving information"""
    
    def __init__(self, db_path: str = "knowledge.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_db()
        
    def _init_db(self):
        """Initialize the SQLite database"""
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
                    access_count INTEGER DEFAULT 0
                )
            """)
            
            # Create embeddings table for semantic search
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    id TEXT PRIMARY KEY,
                    embedding BLOB,
                    FOREIGN KEY (id) REFERENCES knowledge(id)
                )
            """)
            
            conn.commit()
            
    async def store(self, content: str, context: Optional[Dict] = None, 
                   category: Optional[str] = None, confidence: float = 1.0) -> str:
        """Store new knowledge with context"""
        try:
            # Generate unique ID
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Store knowledge
                cursor.execute("""
                    INSERT OR REPLACE INTO knowledge 
                    (id, content, context, category, confidence, created_at, last_accessed)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    content_hash,
                    content,
                    json.dumps(context) if context else None,
                    category,
                    confidence,
                    datetime.now(),
                    datetime.now()
                ))
                
                conn.commit()
                
            return content_hash
            
        except Exception as e:
            self.logger.error(f"Error storing knowledge: {e}")
            raise
            
    async def retrieve(self, query: str, limit: int = 5) -> List[Dict]:
        """Retrieve relevant knowledge based on query"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Simple keyword search for now
                # TODO: Implement semantic search using embeddings
                cursor.execute("""
                    SELECT id, content, context, confidence, last_accessed, access_count
                    FROM knowledge
                    WHERE content LIKE ?
                    ORDER BY confidence DESC, access_count DESC
                    LIMIT ?
                """, (f"%{query}%", limit))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'id': row[0],
                        'content': row[1],
                        'context': json.loads(row[2]) if row[2] else None,
                        'confidence': row[3],
                        'last_accessed': row[4],
                        'access_count': row[5]
                    })
                    
                    # Update access count
                    cursor.execute("""
                        UPDATE knowledge
                        SET access_count = access_count + 1,
                            last_accessed = ?
                        WHERE id = ?
                    """, (datetime.now(), row[0]))
                
                conn.commit()
                return results
                
        except Exception as e:
            self.logger.error(f"Error retrieving knowledge: {e}")
            return []
            
    async def update_confidence(self, id: str, confidence: float):
        """Update confidence score for a knowledge entry"""
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
            
    async def delete(self, id: str):
        """Delete knowledge entry"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM knowledge WHERE id = ?", (id,))
                cursor.execute("DELETE FROM embeddings WHERE id = ?", (id,))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error deleting knowledge: {e}")
            
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
                
                return {
                    'total_entries': total_entries,
                    'categories': categories,
                    'average_confidence': avg_confidence
                }
                
        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            return {} 