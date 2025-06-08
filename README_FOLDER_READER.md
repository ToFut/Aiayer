# SensAI Folder Reader

This component enables SensAI to read, analyze, and summarize folders on your computer. It integrates with the existing memory and LLM systems to provide intelligent folder analysis capabilities.

## Features

- **Folder Summarization**: Get detailed summaries of folder contents, including file types, sizes, and content analysis
- **File Search**: Find files in folders based on content and filenames using semantic search
- **Question Answering**: Ask questions about folder contents and get intelligent answers
- **Natural Language Interface**: Interact with the system using natural language commands
- **Security Controls**: Granular permissions system to control which folders can be accessed

## Getting Started

### Basic Usage

Use the folder reader directly from the command line:

```bash
# Summarize a folder
python folder_reader.py read ~/Documents

# Search a folder for specific content
python folder_reader.py search ~/Projects/MyProject --query "budget calculation"

# Ask a question about a folder
python folder_reader.py ask ~/Downloads --query "What are the largest files?"
```

### Using the Assistant Integration

When interacting with SensAI through chat, you can use natural language to access folder functionality:

- "Summarize my Downloads folder"
- "Find all Python files in my Projects directory"
- "What kind of files are in my Documents folder?"
- "Search for budget documents in ~/Documents"
- "Show me the largest files on my Desktop"

## Configuration

Folder access permissions are configured in `config/folder_access.yaml`. This file controls which directories the system can access, along with other settings like file size limits and scan timeouts.

The default configuration allows access to common user directories (Desktop, Documents, Downloads) while blocking sensitive system directories.

### Customizing Permissions

Edit the configuration file to add or remove allowed paths:

```yaml
allowed_paths:
  - '~/Desktop'       # User's desktop
  - '~/Documents'     # User's documents
  - '~/Downloads'     # User's downloads
  - './'              # Current working directory
  - '/path/to/your/custom/folder'  # Add your custom paths here

disallowed_paths:
  - '/etc'            # System configuration
  - '/var'            # Variable system data
  - '~/.ssh'          # SSH keys
  - '~/.config'       # User configuration
```

## Integration with Brain Router

The folder reader integrates with the brain router system to enable natural language folder interactions within the chat interface. The integration automatically detects folder-related queries and routes them to the appropriate handler.

To manually trigger folder mode, use:

```
folder summarize ~/Documents
folder search ~/Desktop for python files
folder ask ~/Downloads "what are the largest video files?"
```

## Security Considerations

- The system only accesses directories explicitly allowed in the configuration
- Sensitive system directories are blocked by default
- File content analysis is limited to specific text file types
- Maximum file size and folder scan limits prevent resource exhaustion
- All file operations are read-only by default

## Advanced Usage

### Programmatic API

```python
from folder_reader import FolderReader

# Initialize
reader = FolderReader()

# Summarize a folder
result = reader.read_folder(
    folder_path="~/Documents/Projects",
    detail_level="high",
    include_content=True,
    recursive=True
)

# Search for files
search_results = reader.search_files(
    folder_path="~/Documents",
    query="budget 2023",
    limit=10
)

# Ask a question
answer = reader.answer_question(
    folder_path="~/Downloads",
    question="What types of files take up the most space?"
)
```

### Processing Structured Requests

```python
from assistant_folder_reader import AssistantFolderReader

# Initialize
assistant = AssistantFolderReader()

# Process a structured request
result = assistant.process_request({
    "action": "read",
    "folder_path": "~/Documents",
    "detail_level": "medium",
    "include_content": True,
    "recursive": True
})
```

## Troubleshooting

### Common Issues

1. **Permission Errors**: Make sure the requested folder is in the allowed_paths in configuration
2. **Performance Issues**: For large folders, use `--no-content` and `--no-recursive` to speed up scanning
3. **Timeout Errors**: Increase the scan_timeout value in the configuration
4. **Memory Errors**: Decrease max_file_size or max_files_per_scan in configuration

## Limitations

- Binary file content analysis is not supported
- Very large directories may timeout or use excessive resources
- Some text encodings might not be properly detected
- Performance depends on disk speed and file sizes
- File content analysis is limited to text-based files