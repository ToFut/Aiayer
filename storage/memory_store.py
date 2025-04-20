import lmdb
import protobuf
from cryptography.fernet import Fernet
import faiss
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer

class MemoryStore:
    """Secure and efficient local storage for conversation memory"""
    
    def __init__(self, 
                 data_dir: str = "data",
                 encryption_key: Optional[bytes] = None,
                 max_memory_size: int = 1024 * 1024 * 1024,  # 1GB
                 ttl_days: int = 30):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize encryption
        self.encryption_key = encryption_key or Fernet.generate_key()
        self.fernet = Fernet(self.encryption_key)
        
        # Initialize LMDB
        self.env = lmdb.open(
            str(self.data_dir / "memory.lmdb"),
            map_size=max_memory_size,
            max_dbs=3  # conversations, metadata, vectors
        )
        
        # Initialize SQLite for structured data
        self.db_path = self.data_dir / "memory.db"
        self._init_sqlite()
        
        # Initialize FAISS for vector storage
        self.vector_dim = 384  # all-MiniLM-L6-v2 dimension
        self.index = faiss.IndexFlatL2(self.vector_dim)
        self.vector_ids = []
        
        # Initialize sentence transformer
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        
        self.logger = logging.getLogger(__name__)
        self.ttl_days = ttl_days
        
    def _init_sqlite(self):
        """Initialize SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    content BLOB NOT NULL,
                    created_at TIMESTAMP,
                    last_accessed TIMESTAMP,
                    ttl TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            # Create metadata table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            
            conn.commit()
            
    def _encrypt(self, data: bytes) -> bytes:
        """Encrypt data using Fernet"""
        return self.fernet.encrypt(data)
        
    def _decrypt(self, data: bytes) -> bytes:
        """Decrypt data using Fernet"""
        return self.fernet.decrypt(data)
        
    def _serialize(self, data: Any) -> bytes:
        """Serialize data using Protobuf"""
        # TODO: Implement proper Protobuf serialization
        return json.dumps(data).encode()
        
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize data using Protobuf"""
        # TODO: Implement proper Protobuf deserialization
        return json.loads(data.decode())
        
    async def store_conversation(self, 
                               conversation_id: str,
                               content: Dict,
                               metadata: Optional[Dict] = None) -> None:
        """Store a conversation with encryption and compression"""
        try:
            # Serialize and encrypt content
            serialized = self._serialize(content)
            encrypted = self._encrypt(serialized)
            
            # Calculate TTL
            ttl = datetime.now() + timedelta(days=self.ttl_days)
            
            # Store in SQLite
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO conversations 
                    (id, content, created_at, last_accessed, ttl, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    conversation_id,
                    encrypted,
                    datetime.now(),
                    datetime.now(),
                    ttl,
                    json.dumps(metadata) if metadata else None
                ))
                conn.commit()
                
            # Update vector index if content contains text
            if 'text' in content:
                self._update_vector_index(conversation_id, content['text'])
                
        except Exception as e:
            self.logger.error(f"Error storing conversation: {e}")
            raise
            
    async def retrieve_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Retrieve a conversation with decryption"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT content, metadata FROM conversations 
                    WHERE id = ? AND ttl > ?
                """, (conversation_id, datetime.now()))
                
                result = cursor.fetchone()
                if not result:
                    return None
                    
                encrypted, metadata = result
                
                # Decrypt and deserialize
                decrypted = self._decrypt(encrypted)
                content = self._deserialize(decrypted)
                
                # Update last accessed
                cursor.execute("""
                    UPDATE conversations 
                    SET last_accessed = ? 
                    WHERE id = ?
                """, (datetime.now(), conversation_id))
                conn.commit()
                
                return {
                    'content': content,
                    'metadata': json.loads(metadata) if metadata else None
                }
                
        except Exception as e:
            self.logger.error(f"Error retrieving conversation: {e}")
            return None
            
    def _update_vector_index(self, conversation_id: str, text: str):
        """Update FAISS index with new text"""
        try:
            # Generate embedding
            embedding = self.encoder.encode([text])[0]
            
            # Add to index
            self.index.add(np.array([embedding], dtype=np.float32))
            self.vector_ids.append(conversation_id)
            
        except Exception as e:
            self.logger.error(f"Error updating vector index: {e}")
            
    async def search_conversations(self, query: str, limit: int = 5) -> List[Dict]:
        """Search conversations using semantic similarity"""
        try:
            # Generate query embedding
            query_embedding = self.encoder.encode([query])[0]
            
            # Search FAISS index
            distances, indices = self.index.search(
                np.array([query_embedding], dtype=np.float32),
                limit
            )
            
            # Retrieve conversations
            results = []
            for idx, distance in zip(indices[0], distances[0]):
                if idx < len(self.vector_ids):
                    conversation_id = self.vector_ids[idx]
                    conversation = await self.retrieve_conversation(conversation_id)
                    if conversation:
                        results.append({
                            'conversation': conversation,
                            'similarity': 1.0 / (1.0 + distance)  # Convert distance to similarity
                        })
                        
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching conversations: {e}")
            return []
            
    async def cleanup(self):
        """Clean up expired conversations"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete expired conversations
                cursor.execute("""
                    DELETE FROM conversations 
                    WHERE ttl <= ?
                """, (datetime.now(),))
                
                # Get deleted IDs
                deleted_ids = [row[0] for row in cursor.execute("""
                    SELECT id FROM conversations 
                    WHERE ttl <= ?
                """, (datetime.now(),))]
                
                # Remove from vector index
                for conv_id in deleted_ids:
                    if conv_id in self.vector_ids:
                        idx = self.vector_ids.index(conv_id)
                        self.vector_ids.pop(idx)
                        # TODO: Remove from FAISS index
                        
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error cleaning up: {e}")
            
    async def export_data(self, output_path: str):
        """Export data for backup"""
        try:
            output_path = Path(output_path)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Export SQLite database
            import shutil
            shutil.copy2(self.db_path, output_path / "memory.db")
            
            # Export LMDB
            shutil.copytree(
                str(self.data_dir / "memory.lmdb"),
                str(output_path / "memory.lmdb"),
                dirs_exist_ok=True
            )
            
            # Export encryption key
            with open(output_path / "key.txt", "wb") as f:
                f.write(self.encryption_key)
                
        except Exception as e:
            self.logger.error(f"Error exporting data: {e}")
            raise
            
    async def import_data(self, input_path: str):
        """Import data from backup"""
        try:
            input_path = Path(input_path)
            
            # Import SQLite database
            import shutil
            shutil.copy2(input_path / "memory.db", self.db_path)
            
            # Import LMDB
            shutil.copytree(
                str(input_path / "memory.lmdb"),
                str(self.data_dir / "memory.lmdb"),
                dirs_exist_ok=True
            )
            
            # Import encryption key
            with open(input_path / "key.txt", "rb") as f:
                self.encryption_key = f.read()
                self.fernet = Fernet(self.encryption_key)
                
        except Exception as e:
            self.logger.error(f"Error importing data: {e}")
            raise 