# Folder Reading and Summarization Integration Guide

This document explains how to integrate the folder reading and summarization capabilities into the SensAI/Aiayer system.

## Overview

The folder reading system allows users to:
1. Read and summarize directory contents
2. Search for specific files or content within directories
3. Ask questions about folder contents

## Components

The implementation consists of two main components:

1. **FolderReader** (`folder_reader.py`): Core functionality for reading, analyzing, and summarizing folders
2. **AssistantFolderReader** (`assistant_folder_reader.py`): Integration layer for natural language processing and request handling

## Integration with Backend

To integrate with the backend system, follow these steps:

### 1. Register the Handler

Add the folder reading handler to your backend server:

```python
# In your backend server file (e.g., enhanced_enterprise_backend.py)
from assistant_folder_reader import handle_folder_request

# Add to your message handlers
def handle_message(message):
    # Existing message handling code...
    
    # Add folder reading capabilities
    if message.get('type') == 'folder_request' or 'read folder' in message.get('content', '').lower():
        response = handle_folder_request(message.get('content'))
        return {
            'type': 'folder_response',
            'content': response
        }
```

### 2. Add to Brain Router

If using the brain router architecture, register the folder reader handler:

```python
# In brain_router.py or similar file
from assistant_folder_reader import AssistantFolderReader

class BrainRouter:
    def __init__(self):
        # Existing initialization...
        self.folder_reader = AssistantFolderReader()
    
    def route_message(self, message):
        # Check for folder-related intents
        if self._is_folder_request(message):
            return self.folder_reader.handle_natural_language_request(message['content'])
        
        # Existing routing logic...
    
    def _is_folder_request(self, message):
        content = message.get('content', '').lower()
        folder_keywords = [
            'read folder', 'read directory', 'summarize folder',
            'show files in', 'list files in', 'what files are in',
            'search folder', 'search directory', 'find files in'
        ]
        
        return any(keyword in content for keyword in folder_keywords)
```

### 3. Permissions Setup

Create a permissions system for folder access:

```python
# In config.yaml or similar configuration file
folder_access:
  allowed_paths:
    - '~/Desktop'
    - '~/Documents'
    - './data'
  disallowed_paths:
    - '~/private'
    - '/etc'
    - '/var'
```

## Example Usage

### Natural Language Requests:

1. "Summarize the files in my Documents folder"
2. "Search for Python files in ~/Desktop/projects"
3. "What kind of files are in my Downloads folder?"
4. "Find all documents related to 'budget' in ~/Documents"

### Structured Requests:

```json
{
  "action": "read",
  "folder_path": "~/Desktop",
  "detail_level": "high",
  "include_content": true,
  "recursive": true
}
```

```json
{
  "action": "search",
  "folder_path": "~/Documents",
  "query": "budget 2023",
  "limit": 5
}
```

## Security Considerations

1. **Path Validation**: Always validate and sanitize folder paths
2. **Access Restrictions**: Implement a whitelist of allowed directories
3. **Resource Limits**: Set timeouts and size limits for folder scanning
4. **Error Handling**: Properly handle and log access errors without exposing sensitive information
5. **User Confirmation**: For sensitive operations, request explicit user confirmation

## Error Handling

The system handles common errors:
- Non-existent directories
- Permission issues
- File reading errors
- Invalid requests

Errors are logged and returned with clear messages that don't expose system details.

## Performance Optimization

For large directories:
- Use the `--no-content` flag to skip content analysis
- Set appropriate depth with `--no-recursive` for top-level only
- Use lower detail levels for faster summaries
- Implement caching for frequently accessed folders