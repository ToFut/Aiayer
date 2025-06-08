#!/usr/bin/env python3
"""
Example usage of the folder reader system.
This script demonstrates the various capabilities of the folder reader system.
"""
import os
import json
import sys
from typing import Dict, Any

# Import the folder reader components
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from folder_reader import FolderReader
from assistant_folder_reader import AssistantFolderReader

def print_section(title):
    """Print a section title."""
    print("\n" + "=" * 50)
    print(f" {title} ".center(50))
    print("=" * 50 + "\n")

def print_json(data):
    """Print JSON data in a readable format."""
    print(json.dumps(data, indent=2))
    print()

def example_direct_folder_reading():
    """Example of direct folder reading."""
    print_section("Direct Folder Reading")
    
    folder_reader = FolderReader()
    
    # Example 1: Read Desktop folder with medium detail
    desktop_path = os.path.expanduser("~/Desktop")
    print(f"Reading {desktop_path} with medium detail...\n")
    
    result = folder_reader.read_folder(
        folder_path=desktop_path,
        detail_level="medium",
        include_content=True,
        recursive=True
    )
    
    if "text_summary" in result:
        print(result["text_summary"])
    else:
        print_json(result)

def example_folder_searching():
    """Example of searching folder contents."""
    print_section("Folder Content Searching")
    
    folder_reader = FolderReader()
    
    # Example 2: Search Documents folder for "report"
    docs_path = os.path.expanduser("~/Documents")
    search_term = "report"
    
    print(f"Searching for '{search_term}' in {docs_path}...\n")
    
    result = folder_reader.search_files(
        folder_path=docs_path,
        query=search_term,
        limit=5
    )
    
    if "text_results" in result:
        print(result["text_results"])
    else:
        print_json(result)

def example_asking_questions():
    """Example of asking questions about folder contents."""
    print_section("Asking Questions About Folders")
    
    folder_reader = FolderReader()
    
    # Example 3: Ask a question about Downloads folder
    downloads_path = os.path.expanduser("~/Downloads")
    question = "What are the largest files in this folder?"
    
    print(f"Question: '{question}' about {downloads_path}...\n")
    
    result = folder_reader.answer_question(
        folder_path=downloads_path,
        question=question
    )
    
    if "answer_text" in result:
        print(result["answer_text"])
    else:
        print_json(result)

def example_natural_language_requests():
    """Example of processing natural language requests."""
    print_section("Natural Language Requests")
    
    assistant_reader = AssistantFolderReader()
    
    # Example 4: Process natural language requests
    requests = [
        "Summarize my Desktop folder",
        "Find all Python files in my Documents folder",
        "What kind of files are in my Downloads folder?",
        "Show me the largest files in ~/Desktop"
    ]
    
    for i, request in enumerate(requests, 1):
        print(f"Request {i}: {request}\n")
        
        result = assistant_reader.handle_natural_language_request(request)
        
        # Show relevant part of the response
        if "text_summary" in result:
            print(result["text_summary"])
        elif "text_results" in result:
            print(result["text_results"])
        elif "answer_text" in result:
            print(result["answer_text"])
        else:
            print_json(result)
        
        print("-" * 50 + "\n")

def example_structured_requests():
    """Example of processing structured requests."""
    print_section("Structured API Requests")
    
    assistant_reader = AssistantFolderReader()
    
    # Example 5: Process structured API requests
    requests = [
        {
            "action": "read",
            "folder_path": "~/Desktop",
            "detail_level": "high",
            "include_content": True
        },
        {
            "action": "search",
            "folder_path": "~/Documents",
            "query": "project plan",
            "limit": 3
        },
        {
            "action": "ask",
            "folder_path": "~/Downloads",
            "query": "What's the distribution of file types?"
        }
    ]
    
    for i, request in enumerate(requests, 1):
        print(f"Request {i}: {json.dumps(request, indent=2)}\n")
        
        result = assistant_reader.process_request(request)
        
        # Show relevant part of the response
        if "text_summary" in result:
            print(result["text_summary"])
        elif "text_results" in result:
            print(result["text_results"])
        elif "answer_text" in result:
            print(result["answer_text"])
        else:
            print_json(result)
        
        print("-" * 50 + "\n")

def run_examples():
    """Run all examples."""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Run examples
    try:
        example_direct_folder_reading()
        example_folder_searching()
        example_asking_questions()
        example_natural_language_requests()
        example_structured_requests()
    except Exception as e:
        print(f"Error running examples: {str(e)}")

if __name__ == "__main__":
    print_section("Folder Reader System Examples")
    
    print("""
This script demonstrates the various capabilities of the folder reader system:

1. Direct folder reading and summarization
2. Searching folder contents
3. Asking questions about folders
4. Processing natural language requests
5. Processing structured API requests

Each example will show both the request and the response.
    """)
    
    run_examples()