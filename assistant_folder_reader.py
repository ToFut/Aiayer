#!/usr/bin/env python3
"""
Assistant Folder Reader

Integrates with the main system to provide folder reading and summarization
capabilities. Allows users to access, search, and analyze directories on their system.
"""
import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/assistant_folder_reader.log')
    ]
)
logger = logging.getLogger(__name__)

# Import folder reader component
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from folder_reader import FolderReader

class AssistantFolderReader:
    """
    Provides folder reading and summarization capabilities for the assistant.
    """
    
    def __init__(self):
        """Initialize the assistant folder reader."""
        self.folder_reader = FolderReader()
        logger.info("Assistant folder reader initialized")
    
    def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a folder reader request from the assistant system.
        
        Args:
            request: Dictionary containing request parameters:
                - action: "read", "search", or "ask"
                - folder_path: Path to the folder
                - query: Search query or question (for search/ask actions)
                - detail_level: Detail level for summaries
                - include_content: Whether to analyze content
                - recursive: Whether to include subfolders
                - limit: Maximum search results
                
        Returns:
            Dictionary with the results of the requested action
        """
        try:
            # Validate request
            if "action" not in request:
                return {"error": "Missing required parameter: action"}
            if "folder_path" not in request:
                return {"error": "Missing required parameter: folder_path"}
            
            action = request["action"]
            folder_path = request["folder_path"]
            
            # Resolve paths like ~ to absolute paths
            folder_path = os.path.expanduser(folder_path)
            
            # Set defaults for optional parameters
            detail_level = request.get("detail_level", "medium")
            include_content = request.get("include_content", True)
            recursive = request.get("recursive", True)
            limit = request.get("limit", 10)
            
            # Process based on action
            if action == "read":
                result = self.folder_reader.read_folder(
                    folder_path=folder_path,
                    detail_level=detail_level,
                    include_content=include_content,
                    recursive=recursive
                )
                
            elif action == "search":
                if "query" not in request:
                    return {"error": "Missing required parameter for search action: query"}
                
                result = self.folder_reader.search_files(
                    folder_path=folder_path,
                    query=request["query"],
                    limit=limit
                )
                
            elif action == "ask":
                if "query" not in request:
                    return {"error": "Missing required parameter for ask action: query"}
                
                result = self.folder_reader.answer_question(
                    folder_path=folder_path,
                    question=request["query"]
                )
                
            else:
                return {"error": f"Invalid action: {action}"}
            
            # Add request parameters to result for reference
            result["request"] = {
                "action": action,
                "folder_path": folder_path
            }
            
            return result
            
        except Exception as e:
            error_msg = f"Error processing folder reader request: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}
    
    def handle_natural_language_request(self, user_input: str) -> Dict[str, Any]:
        """
        Process a natural language request about folders.
        
        Args:
            user_input: Natural language request from the user
            
        Returns:
            Dictionary with the results of the interpreted request
        """
        # Simple keyword-based intent detection
        user_input = user_input.lower()
        
        # Extract folder path - look for quotes or paths
        import re
        folder_path = None
        
        # Look for quoted paths
        path_match = re.search(r'"([^"]+)"', user_input)
        if path_match:
            folder_path = path_match.group(1)
        
        # Look for common path patterns if no quoted path found
        if not folder_path:
            path_match = re.search(r'(?:in|at|from|of|the)\s+([~/\w.]+(?:/[~\w.]+)+)', user_input)
            if path_match:
                folder_path = path_match.group(1)
        
        # If still no path, look for home directory references
        if not folder_path and ('home' in user_input or 'my documents' in user_input or 'desktop' in user_input):
            if 'desktop' in user_input:
                folder_path = '~/Desktop'
            elif 'documents' in user_input:
                folder_path = '~/Documents'
            else:
                folder_path = '~'
        
        # Default to current directory if no path found
        if not folder_path:
            folder_path = '.'
        
        # Determine action
        action = "read"  # Default action
        
        if re.search(r'\b(?:search|find|locate)\b', user_input):
            action = "search"
        elif re.search(r'\b(?:what|how|why|when|who|tell me about|explain)\b', user_input):
            action = "ask"
        
        # Extract query for search/ask actions
        query = None
        if action in ["search", "ask"]:
            # Try to extract query after certain keywords
            for keyword in ["for", "about", "containing", "related to", "what is", "explain"]:
                match = re.search(f"{keyword}\\s+(.+?)(?:\\s+in\\s+|$)", user_input)
                if match:
                    query = match.group(1)
                    break
            
            # If no query found, use the whole input as query
            if not query:
                query = user_input
        
        # Determine detail level
        detail_level = "medium"  # Default
        if re.search(r'\b(?:detailed|in depth|comprehensive|full)\b', user_input):
            detail_level = "high"
        elif re.search(r'\b(?:brief|quick|summary|basic)\b', user_input):
            detail_level = "low"
        
        # Build request
        request = {
            "action": action,
            "folder_path": folder_path,
            "detail_level": detail_level,
            "include_content": not re.search(r'\b(?:no content|skip content)\b', user_input),
            "recursive": not re.search(r'\b(?:no subfolder|skip subfolder|this folder only)\b', user_input),
        }
        
        # Add query for search/ask actions
        if action in ["search", "ask"] and query:
            request["query"] = query
        
        # Process the request
        return self.process_request(request)

# Example usage in a WebSocket or API handler
def handle_folder_request(message_data):
    """Handle a folder request from a client."""
    folder_reader = AssistantFolderReader()
    
    # If natural language input
    if isinstance(message_data, str):
        result = folder_reader.handle_natural_language_request(message_data)
    # If structured request
    else:
        result = folder_reader.process_request(message_data)
    
    return result

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Simple command-line interface for testing
    import argparse
    parser = argparse.ArgumentParser(description="Process folder read/search requests")
    parser.add_argument("input", help="Natural language request or JSON request")
    parser.add_argument("--json", action="store_true", help="Treat input as JSON")
    args = parser.parse_args()
    
    folder_reader = AssistantFolderReader()
    
    if args.json:
        try:
            request = json.loads(args.input)
            result = folder_reader.process_request(request)
        except json.JSONDecodeError:
            result = {"error": "Invalid JSON input"}
    else:
        result = folder_reader.handle_natural_language_request(args.input)
    
    # Pretty print the result
    print(json.dumps(result, indent=2))