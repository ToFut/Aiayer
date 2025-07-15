#!/bin/bash

# Enable error handling
set -e
set -o pipefail

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Create project structure
log "Creating project structure..."

# Create main directories
mkdir -p document_intelligence/web/dashboard/templates
mkdir -p document_intelligence/web/dashboard/static/js
mkdir -p document_intelligence/web/dashboard/static/css
mkdir -p sensors
mkdir -p backend/llm
mkdir -p memory/documents
mkdir -p logs

# Create __init__.py files
touch document_intelligence/__init__.py
touch document_intelligence/web/__init__.py
touch document_intelligence/web/dashboard/__init__.py
touch sensors/__init__.py
touch backend/__init__.py
touch backend/llm/__init__.py

# Create backend/llm/llm_service.py if it doesn't exist
if [ ! -f "backend/llm/llm_service.py" ]; then
    log "Creating LLM service file..."
    cat > backend/llm/llm_service.py << 'EOL'
"""
LLM Service Module
Handles interactions with the Language Model.
"""
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.initialized = False
        
    async def initialize(self) -> bool:
        """Initialize the LLM service"""
        try:
            # TODO: Add actual LLM initialization
            self.initialized = True
            return True
        except Exception as e:
            logger.error(f"Error initializing LLM service: {e}")
            return False
            
    async def generate_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate a response from the LLM"""
        if not self.initialized:
            raise RuntimeError("LLM service not initialized")
            
        try:
            # TODO: Add actual LLM interaction
            return "Sample response"
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return ""
EOL
fi

# Create sensors/folder_scanner_sensor.py if it doesn't exist
if [ ! -f "sensors/folder_scanner_sensor.py" ]; then
    log "Creating folder scanner sensor file..."
    cat > sensors/folder_scanner_sensor.py << 'EOL'
"""
Folder Scanner Sensor Module
Implements folder scanning and monitoring capabilities.
"""
import os
import time
import logging
import hashlib
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
import mimetypes
import magic
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from document_intelligence.core import DocumentMemory, DocumentAnalyzer

logger = logging.getLogger(__name__)

class FolderScannerSensor(FileSystemEventHandler):
    """Sensor for scanning and monitoring folders for document analysis."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize folder scanner sensor with optional config."""
        self.config = config or {}
        self.watched_folders: Set[str] = set()
        self.observer = Observer()
        self.current_state = {
            "timestamp": time.time(),
            "watched_folders": [],
            "folder_stats": {},
            "scanning": False,
            "scan_progress": 0,
            "error_count": 0
        }
        self.supported_extensions = {
            '.txt', '.pdf', '.doc', '.docx', '.xls', '.xlsx',
            '.ppt', '.pptx', '.csv', '.json', '.xml', '.html',
            '.md', '.rtf'
        }
        
        # Initialize document memory and analyzer
        self.document_memory = DocumentMemory()
        self.document_analyzer = DocumentAnalyzer(self.document_memory)
        
        logger.info("Folder scanner sensor initialized")
    
    async def initialize(self) -> bool:
        """Initialize the sensor with proper error handling and retries."""
        try:
            logger.info("Folder scanner sensor initialization started")
            if not self.observer.is_alive():
                self.observer.start()
            return True
        except Exception as e:
            logger.error(f"Error initializing folder scanner sensor: {e}")
            return False
    
    def start_watching(self, folder_path: str) -> bool:
        """Start watching a folder for changes."""
        try:
            if not os.path.isdir(folder_path):
                logger.error(f"Directory does not exist: {folder_path}")
                return False
                
            if folder_path in self.watched_folders:
                logger.warning(f"Already watching folder: {folder_path}")
                return True
                
            self.watched_folders.add(folder_path)
            self.observer.schedule(self, folder_path, recursive=True)
            
            if not self.observer.is_alive():
                self.observer.start()
                
            # Initial scan of existing files
            self._scan_folder(folder_path)
            logger.info(f"Started watching folder: {folder_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting folder watch {folder_path}: {e}")
            return False
    
    def stop_watching(self, folder_path: Optional[str] = None) -> bool:
        """Stop watching a specific folder or all folders."""
        try:
            if folder_path:
                if folder_path in self.watched_folders:
                    self.watched_folders.remove(folder_path)
                    # TODO: Implement proper unscheduling of specific folder
                    logger.info(f"Stopped watching folder: {folder_path}")
            else:
                self.observer.stop()
                self.observer.join()
                self.watched_folders.clear()
                logger.info("Stopped watching all folders")
            return True
        except Exception as e:
            logger.error(f"Error stopping folder watch: {e}")
            return False
    
    def _scan_folder(self, folder_path: str) -> None:
        """Scan all files in a folder."""
        try:
            stats = {
                "total_files": 0,
                "total_size": 0,
                "file_types": {},
                "last_scan": datetime.now().isoformat(),
                "scanning": True,
                "scan_progress": 0,
                "error_count": 0,
                "analyzed_files": 0,
                "analysis_errors": 0
            }
            
            total_files = sum(1 for _ in self._walk_files(folder_path))
            processed_files = 0
            
            for file_path in self._walk_files(folder_path):
                try:
                    if self._is_supported_file(file_path):
                        file_size = os.path.getsize(file_path)
                        file_type = self._get_file_type(file_path)
                        
                        stats["total_files"] += 1
                        stats["total_size"] += file_size
                        stats["file_types"][file_type] = stats["file_types"].get(file_type, 0) + 1
                        
                        # Analyze document with LLM
                        try:
                            analysis = self.document_analyzer.analyze_document(file_path, folder_path)
                            if analysis:
                                stats["analyzed_files"] += 1
                            else:
                                stats["analysis_errors"] += 1
                        except Exception as e:
                            logger.error(f"Error analyzing document {file_path}: {e}")
                            stats["analysis_errors"] += 1
                            
                except Exception as e:
                    stats["error_count"] += 1
                    logger.error(f"Error processing {file_path}: {e}")
                
                processed_files += 1
                stats["scan_progress"] = (processed_files / total_files) * 100
                
            stats["scanning"] = False
            self.current_state["folder_stats"][folder_path] = stats
            self.document_memory.update_folder_stats(folder_path, stats)
            logger.info(f"Completed scanning folder: {folder_path}")
            
        except Exception as e:
            logger.error(f"Error scanning folder {folder_path}: {e}")
    
    def _walk_files(self, folder_path: str):
        """Walk through all files in a folder."""
        for root, _, files in os.walk(folder_path):
            for file in files:
                yield os.path.join(root, file)
    
    def _is_supported_file(self, file_path: str) -> bool:
        """Check if the file type is supported for analysis."""
        ext = Path(file_path).suffix.lower()
        return ext in self.supported_extensions
    
    def _get_file_type(self, file_path: str) -> str:
        """Get detailed file type information."""
        try:
            mime = magic.Magic(mime=True)
            file_type = mime.from_file(file_path)
            return file_type
        except:
            return mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
    
    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory:
            folder_path = str(Path(event.src_path).parent)
            if folder_path in self.watched_folders:
                self._scan_folder(folder_path)
    
    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory:
            folder_path = str(Path(event.src_path).parent)
            if folder_path in self.watched_folders:
                self._scan_folder(folder_path)
    
    def on_deleted(self, event):
        """Handle file deletion events."""
        if not event.is_directory:
            folder_path = str(Path(event.src_path).parent)
            if folder_path in self.watched_folders:
                self._scan_folder(folder_path)
    
    def get_current_data(self) -> Dict[str, Any]:
        """Get current folder scanner state."""
        self.current_state.update({
            "timestamp": time.time(),
            "watched_folders": list(self.watched_folders)
        })
        return self.current_state
    
    def get_folder_stats(self, folder_path: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific folder."""
        return self.current_state["folder_stats"].get(folder_path)
    
    def get_supported_extensions(self) -> Set[str]:
        """Get list of supported file extensions."""
        return self.supported_extensions
        
    def get_document_analysis(self, doc_hash: str) -> Optional[Dict]:
        """Get document analysis by hash."""
        return self.document_memory.get_document_analysis(doc_hash)
        
    def list_all_analyses(self) -> List[Dict]:
        """List all stored document analyses."""
        return self.document_memory.list_all_analyses()
EOL
fi

log "Project structure setup complete!" 