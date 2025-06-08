#!/usr/bin/env python3
"""
Folder Reader Handler - Brain Router Integration

Provides folder reading capabilities to the Brain Router system.
"""
import os
import sys
import json
import logging
import yaml
import time
import asyncio
from typing import Dict, Any, List, Optional, Union

# Import from parent directories
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from assistant_folder_reader import AssistantFolderReader
from brain.core.brain_router import BrainResponse, ChatRequest, ChatMode

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load folder access permissions
def load_folder_permissions():
    """Load folder access permissions from config file."""
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                  "config", "folder_access.yaml")
        
        if not os.path.exists(config_path):
            logger.warning(f"Folder access config not found at {config_path}, using defaults")
            return {
                "allowed_paths": ["~/Desktop", "~/Documents", "~/Downloads", "./"],
                "disallowed_paths": ["/etc", "/var", "~/.ssh", "~/.config"],
                "settings": {
                    "max_file_size": 10 * 1024 * 1024,  # 10MB
                    "max_files_per_scan": 1000,
                    "scan_timeout": 60
                }
            }
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        logger.info(f"Loaded folder access permissions: {len(config.get('allowed_paths', []))} allowed paths, {len(config.get('disallowed_paths', []))} disallowed paths")
        return config
        
    except Exception as e:
        logger.error(f"Error loading folder permissions: {e}")
        # Return safe defaults
        return {
            "allowed_paths": ["~/Desktop", "~/Documents", "./"],
            "disallowed_paths": ["/etc", "/var", "~/.ssh"],
            "settings": {
                "max_file_size": 5 * 1024 * 1024,  # 5MB
                "max_files_per_scan": 500,
                "scan_timeout": 30
            }
        }

# Load permissions at module initialization
FOLDER_PERMISSIONS = load_folder_permissions()

class FolderReaderHandler:
    """
    Handles folder reading requests integrated with the Brain Router.
    """
    
    def __init__(self):
        """Initialize the folder reader handler."""
        self.folder_reader = AssistantFolderReader()
        self.permissions = FOLDER_PERMISSIONS
        logger.info("Folder reader handler initialized")
    
    def _is_path_allowed(self, folder_path: str) -> bool:
        """Check if a folder path is allowed by permissions."""
        # Expand user paths like ~ to absolute paths
        folder_path = os.path.expanduser(folder_path)
        folder_path = os.path.abspath(folder_path)
        
        # Check against disallowed paths
        for disallowed in self.permissions.get("disallowed_paths", []):
            disallowed = os.path.expanduser(disallowed)
            disallowed = os.path.abspath(disallowed)
            if folder_path == disallowed or folder_path.startswith(disallowed + os.sep):
                logger.warning(f"Access denied to disallowed path: {folder_path}")
                return False
        
        # Check against allowed paths
        for allowed in self.permissions.get("allowed_paths", []):
            allowed = os.path.expanduser(allowed)
            allowed = os.path.abspath(allowed)
            if folder_path == allowed or folder_path.startswith(allowed + os.sep):
                return True
        
        logger.warning(f"Access denied to non-allowed path: {folder_path}")
        return False
    
    def _sanitize_path(self, folder_path: str) -> str:
        """Sanitize and normalize folder path."""
        # Expand user paths
        folder_path = os.path.expanduser(folder_path)
        
        # Remove any potential dangerous elements
        folder_path = os.path.normpath(folder_path)
        
        return folder_path
    
    async def handle_folder_request(self, request: ChatRequest) -> BrainResponse:
        """
        Handle a folder reader request from the brain router.
        
        Args:
            request: Chat request from brain router
            
        Returns:
            Brain response with folder information
        """
        start_time = time.time()
        query = request.query.strip()
        
        try:
            # Process the natural language request
            folder_result = self.folder_reader.handle_natural_language_request(query)
            
            # Check if there was an error in processing
            if "error" in folder_result:
                return BrainResponse(
                    success=False,
                    response=f"📁 **Folder Reader Error**\n\n{folder_result['error']}",
                    mode_used=request.mode,
                    processing_time=time.time() - start_time,
                    resources_used=["storage"],
                    confidence=0.0,
                    metadata={"error": folder_result["error"]}
                )
            
            # Check folder access permissions
            folder_path = folder_result.get("request", {}).get("folder_path", "")
            if folder_path and not self._is_path_allowed(folder_path):
                return BrainResponse(
                    success=False,
                    response=f"📁 **Access Denied**\n\nI don't have permission to access the folder: {folder_path}",
                    mode_used=request.mode,
                    processing_time=time.time() - start_time,
                    resources_used=["storage"],
                    confidence=0.0,
                    metadata={"error": "access_denied"}
                )
            
            # Format the response based on action type
            if "text_summary" in folder_result:
                response_text = f"📁 **Folder Summary**\n\n{folder_result['text_summary']}"
            elif "text_results" in folder_result:
                response_text = f"🔍 **Search Results**\n\n{folder_result['text_results']}"
            elif "answer_text" in folder_result:
                response_text = f"❓ **Folder Analysis**\n\n{folder_result['answer_text']}"
            else:
                # Generic success response
                action_type = folder_result.get("request", {}).get("action", "processed")
                response_text = f"✅ **Folder {action_type.capitalize()} Complete**\n\nSuccessfully processed folder: {folder_path}"
            
            # Return the formatted response
            return BrainResponse(
                success=True,
                response=response_text,
                mode_used=request.mode,
                processing_time=time.time() - start_time,
                resources_used=["storage", "memory"],
                confidence=0.9,
                metadata={
                    "folder_path": folder_path,
                    "action": folder_result.get("request", {}).get("action", "unknown")
                }
            )
            
        except Exception as e:
            logger.error(f"Error handling folder request: {e}")
            return BrainResponse(
                success=False,
                response=f"📁 **Folder Reader Error**\n\nI encountered an error processing your folder request: {str(e)}",
                mode_used=request.mode,
                processing_time=time.time() - start_time,
                resources_used=[],
                confidence=0.0,
                metadata={"error": str(e)}
            )

# Create handler instance
folder_reader_handler = FolderReaderHandler()

# Function to integrate with the brain router
async def handle_folder_mode(request: ChatRequest) -> BrainResponse:
    """Handler function to register with the brain router."""
    return await folder_reader_handler.handle_folder_request(request)

# Function to detect folder-related queries
async def is_folder_request(query: str) -> bool:
    """Detect if a query is related to folder reading/searching using LLM."""
    # First try LLM classification
    try:
        # Import the intent classifier
        from brain.handlers.intent_classifier import classify_intent
        
        # Get classification result
        result = await classify_intent(query)
        
        # Check if folder_access is the primary intent
        if result['success'] and result['primary_intent'] == 'folder_access':
            logger.info(f"LLM classified query as folder request: {query}")
            return True
            
        # Check if folder_access is among required capabilities
        if result['success'] and 'folder_access' in result.get('required_capabilities', []):
            logger.info(f"LLM identified folder access capability requirement: {query}")
            return True
            
    except Exception as e:
        logger.warning(f"LLM classification failed, using fallback: {e}")
        
    # Fallback to pattern matching (existing implementation)
    query = query.lower()
    folder_keywords = [
        "read folder", "read directory", "read files in", 
        "summarize folder", "summarize directory", 
        "show files in", "list files in", "what files are in",
        "search folder", "search directory", "find files in",
        "what's in my", "what is in my", "show me what's in",
        "analyze folder", "analyze directory"
    ]
    
    folder_locations = [
        "desktop", "documents", "downloads", "folder", 
        "directory", "path", "files in", "/", "~/"
    ]
    
    # Check if query contains folder-related intent and location
    has_intent = any(keyword in query for keyword in folder_keywords)
    has_location = any(location in query for location in folder_locations)
    
    return has_intent or (has_location and any(action in query for action in ["show", "list", "find", "search", "what", "read", "summarize"]))

# Register with the brain router
def register_with_brain_router(router):
    """Register the folder reader handler with the brain router."""
    try:
        # Import ChatMode from brain_router to ensure it's the correct type
        from brain.core.brain_router import ChatMode
        
        # Try to use existing FOLDER enum if it exists, otherwise create a new one
        try:
            FolderMode = ChatMode.FOLDER  # Use existing enum value if available
        except (AttributeError, ValueError):
            # Create new chat mode for folder operations
            FolderMode = ChatMode("Folder")
        
        # Register the handler
        router.register_handler(FolderMode, handle_folder_mode)
        
        # Success registration
        logger.info("✅ Folder reader handler registered with brain router")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to register folder reader with brain router: {e}")
        return False