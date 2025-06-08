#!/usr/bin/env python3
"""
File Sensor
Captures file-related data such as file changes, directory contents, and file metadata.
"""
import asyncio
import json
import logging
import os
import sys
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
import hashlib

# Configure logging
os.makedirs('logs/sensors', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sensors/file_sensor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('file_sensor')

class FileSensor:
    """Sensor for capturing file-related data."""
    
    def __init__(self):
        """Initialize the file sensor."""
        self.last_data = None
        self.watched_dirs = set()
        self.file_hashes = {}
        logger.info("File sensor initialized")
    
    async def get_data(self) -> Dict[str, Any]:
        """Get current file data."""
        try:
            # Get file data
            data = {
                'timestamp': datetime.now().isoformat(),
                'watched_directories': self._get_watched_directories(),
                'file_changes': self._detect_file_changes(),
                'directory_contents': self._get_directory_contents(),
                'file_metadata': self._get_file_metadata()
            }
            
            # Update last data
            self.last_data = data
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting file data: {e}")
            logger.error(traceback.format_exc())
            return self.last_data or {
                'timestamp': datetime.now().isoformat(),
                'watched_directories': [],
                'file_changes': [],
                'directory_contents': {},
                'file_metadata': {}
            }
    
    def _get_watched_directories(self) -> list:
        """Get list of watched directories."""
        return list(self.watched_dirs)
    
    def _detect_file_changes(self) -> list:
        """Detect changes in watched files."""
        changes = []
        for directory in self.watched_dirs:
            for root, _, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        # Calculate file hash
                        current_hash = self._calculate_file_hash(file_path)
                        
                        # Check if file has changed
                        if file_path in self.file_hashes:
                            if current_hash != self.file_hashes[file_path]:
                                changes.append({
                                    'path': file_path,
                                    'type': 'modified',
                                    'timestamp': datetime.now().isoformat()
                                })
                        else:
                            changes.append({
                                'path': file_path,
                                'type': 'created',
                                'timestamp': datetime.now().isoformat()
                            })
                        
                        # Update hash
                        self.file_hashes[file_path] = current_hash
                        
                    except Exception as e:
                        logger.error(f"Error detecting changes for {file_path}: {e}")
                        continue
        
        return changes
    
    def _get_directory_contents(self) -> Dict[str, list]:
        """Get contents of watched directories."""
        contents = {}
        for directory in self.watched_dirs:
            try:
                files = []
                for root, _, filenames in os.walk(directory):
                    for filename in filenames:
                        file_path = os.path.join(root, filename)
                        files.append({
                            'path': file_path,
                            'name': filename,
                            'size': os.path.getsize(file_path),
                            'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                        })
                contents[directory] = files
            except Exception as e:
                logger.error(f"Error getting contents for {directory}: {e}")
                contents[directory] = []
        
        return contents
    
    def _get_file_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Get metadata for watched files."""
        metadata = {}
        for directory in self.watched_dirs:
            for root, _, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        stat = os.stat(file_path)
                        metadata[file_path] = {
                            'size': stat.st_size,
                            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            'accessed': datetime.fromtimestamp(stat.st_atime).isoformat(),
                            'permissions': oct(stat.st_mode)[-3:],
                            'owner': stat.st_uid,
                            'group': stat.st_gid
                        }
                    except Exception as e:
                        logger.error(f"Error getting metadata for {file_path}: {e}")
                        continue
        
        return metadata
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of a file."""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return ""
    
    def add_watch_directory(self, directory: str) -> bool:
        """Add a directory to watch."""
        try:
            if os.path.isdir(directory):
                self.watched_dirs.add(directory)
                logger.info(f"Added directory to watch: {directory}")
                return True
            else:
                logger.error(f"Directory does not exist: {directory}")
                return False
        except Exception as e:
            logger.error(f"Error adding watch directory {directory}: {e}")
            return False
    
    def remove_watch_directory(self, directory: str) -> bool:
        """Remove a directory from watch."""
        try:
            if directory in self.watched_dirs:
                self.watched_dirs.remove(directory)
                logger.info(f"Removed directory from watch: {directory}")
                return True
            else:
                logger.warning(f"Directory not being watched: {directory}")
                return False
        except Exception as e:
            logger.error(f"Error removing watch directory {directory}: {e}")
            return False