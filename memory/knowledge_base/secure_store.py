"""
Secure Knowledge Store Module
Provides encrypted storage using LMDB for persistence and Fernet for encryption.
"""
import os
import json
import time
import logging
import lmdb
import base64
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class SecureKnowledgeStore:
    """
    Secure, efficient knowledge storage using LMDB and encryption
    
    Features:
    - Fast LMDB storage for performance
    - Fernet encryption for sensitive data
    - Automatic TTL (time-to-live) expiration
    - Categorized data organization
    - Memory-efficient compression for large data
    """
    
    def __init__(self, 
                 storage_path: Optional[str] = None,
                 encryption_key: Optional[str] = None,
                 max_db_size: int = 10 * 1024 * 1024 * 1024  # 10GB max size
                ):
        """
        Initialize secure knowledge store.
        
        Args:
            storage_path: Path to store knowledge base files. If None, uses a default path.
            encryption_key: Key for encrypting data. If None, generates a new one.
            max_db_size: Maximum size of LMDB in bytes
        """
        self.logger = logging.getLogger(__name__)
        
        if storage_path is None:
            home_dir = os.path.expanduser("~")
            storage_path = os.path.join(home_dir, ".local_assistant", "secure_knowledge")
        
        self.storage_path = storage_path
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Initialize encryption
        self._setup_encryption(encryption_key)
        
        # Open LMDB environment
        self.env = lmdb.open(
            self.storage_path,
            map_size=max_db_size,  # Max database size
            subdir=True,
            metasync=True,
            sync=True,
            map_async=False,
            mode=0o600  # Secure permissions
        )
        
        self.logger.info(f"Secure knowledge store initialized at {self.storage_path}")
        
        # Run initial cleanup of expired entries
        self.cleanup_expired()
    
    def _setup_encryption(self, encryption_key: Optional[str]) -> None:
        """Set up encryption with provided key or generate a new one."""
        key_file = os.path.join(self.storage_path, ".key")
        
        if encryption_key:
            # Use provided key
            self.encryption_key = self._derive_key(encryption_key)
            
            # Save derived key (encrypted with itself for additional security)
            if not os.path.exists(key_file):
                with open(key_file, 'wb') as f:
                    cipher = Fernet(self.encryption_key)
                    f.write(cipher.encrypt(self.encryption_key))
        
        elif os.path.exists(key_file):
            # Load existing key
            try:
                with open(key_file, 'rb') as f:
                    encrypted_key = f.read()
                
                # We need to derive an initial key to decrypt the stored key
                # This is a bootstrapping process - the actual key is encrypted with itself
                temp_key = self._derive_key("local_assistant_default")
                cipher = Fernet(temp_key)
                
                try:
                    # Try to decrypt with temp key
                    self.encryption_key = cipher.decrypt(encrypted_key)
                except:
                    # If that fails, maybe it's encrypted with itself
                    cipher = Fernet(encrypted_key)
                    self.encryption_key = cipher.decrypt(encrypted_key)
            except Exception as e:
                self.logger.error(f"Error loading encryption key: {e}, generating new one")
                self._generate_new_key(key_file)
        else:
            # Generate new key
            self._generate_new_key(key_file)
    
    def _generate_new_key(self, key_file: str) -> None:
        """Generate a new encryption key and save it."""
        import secrets
        
        # Generate a truly random password
        random_password = secrets.token_hex(32)
        self.encryption_key = self._derive_key(random_password)
        
        # Save derived key (encrypted with itself for additional security)
        with open(key_file, 'wb') as f:
            cipher = Fernet(self.encryption_key)
            f.write(cipher.encrypt(self.encryption_key))
        
        self.logger.info("Generated new encryption key")
    
    def _derive_key(self, password: str) -> bytes:
        """Derive a Fernet key from a password."""
        salt = b'local_assistant_salt'  # Fixed salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def _encrypt(self, data: bytes) -> bytes:
        """Encrypt data using Fernet."""
        cipher = Fernet(self.encryption_key)
        return cipher.encrypt(data)
    
    def _decrypt(self, encrypted_data: bytes) -> bytes:
        """Decrypt data using Fernet."""
        cipher = Fernet(self.encryption_key)
        return cipher.decrypt(encrypted_data)
    
    def _compress(self, data: str) -> bytes:
        """Compress data for storage efficiency."""
        import zlib
        json_bytes = json.dumps(data).encode('utf-8')
        return zlib.compress(json_bytes)
    
    def _decompress(self, compressed_data: bytes) -> Any:
        """Decompress stored data."""
        import zlib
        json_bytes = zlib.decompress(compressed_data)
        return json.loads(json_bytes.decode('utf-8'))
    
    def store(self, key: str, value: Any, category: Optional[str] = None, 
              ttl: Optional[int] = None, encrypt: bool = True) -> bool:
        """
        Store a value in the knowledge base with encryption and compression.
        
        Args:
            key: Unique identifier for this knowledge
            value: The data to store
            category: Optional category for organizing knowledge
            ttl: Time to live in seconds (None = no expiration)
            encrypt: Whether to encrypt the data
            
        Returns:
            bool: True if storage succeeded
        """
        try:
            # Store the actual data
            data_key = f"data:{key}".encode('utf-8')
            
            # Compress and optionally encrypt the data
            compressed_data = self._compress(value)
            stored_data = self._encrypt(compressed_data) if encrypt else compressed_data
            
            # Store metadata
            meta_key = f"meta:{key}".encode('utf-8')
            metadata = {
                "created_at": time.time(),
                "updated_at": time.time(),
                "category": category,
                "encrypted": encrypt,
                "expires_at": time.time() + ttl if ttl else None
            }
            
            # Serialize, compress, and encrypt metadata
            meta_compressed = self._compress(metadata)
            meta_encrypted = self._encrypt(meta_compressed)
            
            # Store both data and metadata in a single transaction
            with self.env.begin(write=True) as txn:
                txn.put(data_key, stored_data)
                txn.put(meta_key, meta_encrypted)
            
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
        try:
            data_key = f"data:{key}".encode('utf-8')
            meta_key = f"meta:{key}".encode('utf-8')
            
            with self.env.begin() as txn:
                # Get metadata first to check expiration and encryption status
                meta_bytes = txn.get(meta_key)
                if not meta_bytes:
                    return default
                
                # Decrypt and decompress metadata
                meta_decrypted = self._decrypt(meta_bytes)
                metadata = self._decompress(meta_decrypted)
                
                # Check if expired
                if metadata.get("expires_at") and time.time() > metadata["expires_at"]:
                    # Delete expired entry
                    with self.env.begin(write=True) as write_txn:
                        write_txn.delete(data_key)
                        write_txn.delete(meta_key)
                    return default
                
                # Retrieve data
                data_bytes = txn.get(data_key)
                if not data_bytes:
                    return default
                
                # Decrypt if needed and decompress
                if metadata.get("encrypted", True):
                    data_decrypted = self._decrypt(data_bytes)
                    result = self._decompress(data_decrypted)
                else:
                    result = self._decompress(data_bytes)
                
                # Update access timestamp in metadata
                metadata["accessed_at"] = time.time()
                meta_compressed = self._compress(metadata)
                meta_encrypted = self._encrypt(meta_compressed)
                
                with self.env.begin(write=True) as write_txn:
                    write_txn.put(meta_key, meta_encrypted)
                
                return result
        except Exception as e:
            self.logger.error(f"Error retrieving knowledge '{key}': {e}")
            return default
    
    def delete(self, key: str) -> bool:
        """
        Delete an entry from the knowledge base.
        
        Args:
            key: The identifier to delete
            
        Returns:
            bool: True if deletion succeeded
        """
        try:
            data_key = f"data:{key}".encode('utf-8')
            meta_key = f"meta:{key}".encode('utf-8')
            
            with self.env.begin(write=True) as txn:
                # Delete both data and metadata
                txn.delete(data_key)
                txn.delete(meta_key)
            
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
        try:
            with self.env.begin() as txn:
                cursor = txn.cursor()
                prefix = b"meta:"
                
                # Only iterate through metadata entries
                cursor.set_range(prefix)
                for key, value in cursor:
                    if not key.startswith(prefix):
                        break
                    
                    # Extract the actual key
                    actual_key = key.decode('utf-8').split(':', 1)[1]
                    
                    try:
                        # Decrypt and decompress metadata
                        meta_decrypted = self._decrypt(value)
                        metadata = self._decompress(meta_decrypted)
                        
                        # Check category and expiration
                        if metadata.get("category") == category:
                            expires_at = metadata.get("expires_at")
                            if not expires_at or time.time() <= expires_at:
                                result.append(actual_key)
                    except Exception as e:
                        self.logger.warning(f"Error processing metadata for {actual_key}: {e}")
            
            return result
        except Exception as e:
            self.logger.error(f"Error listing category '{category}': {e}")
            return []
    
    def list_all_categories(self) -> List[str]:
        """
        List all available categories.
        
        Returns:
            List of unique categories
        """
        categories = set()
        try:
            with self.env.begin() as txn:
                cursor = txn.cursor()
                prefix = b"meta:"
                
                # Only iterate through metadata entries
                cursor.set_range(prefix)
                for key, value in cursor:
                    if not key.startswith(prefix):
                        break
                    
                    try:
                        # Decrypt and decompress metadata
                        meta_decrypted = self._decrypt(value)
                        metadata = self._decompress(meta_decrypted)
                        
                        # Check expiration and add category
                        expires_at = metadata.get("expires_at")
                        if (not expires_at or time.time() <= expires_at) and metadata.get("category"):
                            categories.add(metadata["category"])
                    except Exception as e:
                        # Skip entries with errors
                        continue
            
            return list(categories)
        except Exception as e:
            self.logger.error(f"Error listing categories: {e}")
            return []
    
    def clear(self) -> bool:
        """
        Clear all knowledge base entries.
        
        Returns:
            bool: True if operation succeeded
        """
        try:
            # Close the environment
            self.env.close()
            
            # Delete and recreate the database
            import shutil
            shutil.rmtree(self.storage_path)
            os.makedirs(self.storage_path, exist_ok=True)
            
            # Reopen the environment
            self.env = lmdb.open(
                self.storage_path,
                map_size=10 * 1024 * 1024 * 1024,  # 10GB
                subdir=True,
                metasync=True,
                sync=True,
                map_async=False,
                mode=0o600  # Secure permissions
            )
            
            # Recreate encryption key
            self._setup_encryption(None)
            
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
        total = 0
        
        try:
            with self.env.begin() as txn:
                cursor = txn.cursor()
                prefix = b"meta:"
                
                # Only iterate through metadata entries
                cursor.set_range(prefix)
                for key, value in cursor:
                    if not key.startswith(prefix):
                        break
                    
                    total += 1
                    
                    try:
                        # Decrypt and decompress metadata
                        meta_decrypted = self._decrypt(value)
                        metadata = self._decompress(meta_decrypted)
                        
                        category = metadata.get("category", "uncategorized")
                        
                        # Check if expired
                        expires_at = metadata.get("expires_at")
                        if expires_at and time.time() > expires_at:
                            expired += 1
                            continue
                        
                        # Count by category
                        if category not in categories:
                            categories[category] = 0
                        categories[category] += 1
                    except Exception as e:
                        # Skip entries with errors
                        self.logger.warning(f"Error processing metadata: {e}")
            
            return {
                "total_entries": total,
                "active_entries": total - expired,
                "expired_entries": expired,
                "categories": categories,
                "storage_path": self.storage_path,
                "encrypted": True
            }
        except Exception as e:
            self.logger.error(f"Error getting knowledge base summary: {e}")
            return {
                "error": str(e),
                "total_entries": 0,
                "active_entries": 0,
                "expired_entries": 0,
                "categories": {}
            }
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from the knowledge base.
        
        Returns:
            int: Number of entries removed
        """
        expired_count = 0
        try:
            keys_to_delete = []
            
            # First pass: identify expired entries
            with self.env.begin() as txn:
                cursor = txn.cursor()
                prefix = b"meta:"
                
                cursor.set_range(prefix)
                for key, value in cursor:
                    if not key.startswith(prefix):
                        break
                    
                    try:
                        # Decrypt and decompress metadata
                        meta_decrypted = self._decrypt(value)
                        metadata = self._decompress(meta_decrypted)
                        
                        # Check if expired
                        expires_at = metadata.get("expires_at")
                        if expires_at and time.time() > expires_at:
                            # Extract the actual key
                            actual_key = key.decode('utf-8').split(':', 1)[1]
                            keys_to_delete.append(actual_key)
                    except Exception as e:
                        # Skip entries with errors
                        continue
            
            # Second pass: delete expired entries
            for key in keys_to_delete:
                self.delete(key)
                expired_count += 1
            
            self.logger.info(f"Cleaned up {expired_count} expired knowledge base entries")
            return expired_count
        except Exception as e:
            self.logger.error(f"Error cleaning up expired entries: {e}")
            return 0
    
    def close(self):
        """Close the LMDB environment."""
        try:
            if self.env:
                self.env.close()
                self.logger.info("Knowledge base closed")
        except Exception as e:
            self.logger.error(f"Error closing knowledge base: {e}")


# For testing if run directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test secure knowledge store
    store = SecureKnowledgeStore()
    
    # Store some test data
    store.store("test1", "This is a test entry", category="test")
    store.store("test2", {"text": "This is a structured entry", "value": 42}, category="test")
    store.store("temp1", "This entry will expire soon", category="temporary", ttl=5)
    
    # Retrieve and print data
    print("Retrieved test1:", store.retrieve("test1"))
    print("Retrieved test2:", store.retrieve("test2"))
    print("Retrieved non-existent:", store.retrieve("nonexistent", "Default value"))
    
    # List and summarize
    print("Test category entries:", store.list_by_category("test"))
    print("All categories:", store.list_all_categories())
    print("Knowledge base summary:", store.get_summary())
    
    # Test expiration
    print("Temp entry before expiry:", store.retrieve("temp1"))
    print("Waiting for expiration...")
    time.sleep(6)
    print("Temp entry after expiry:", store.retrieve("temp1"))
    
    # Clean up
    store.close()
    print("Knowledge base closed")