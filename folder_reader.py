#!/usr/bin/env python3
"""
Folder Reader Module

Provides functionality to read, analyze, and summarize folder contents.
Can be used as a standalone tool or integrated with other components.
"""
import os
import json
import logging
import argparse
import sys
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/folder_reader.log')
    ]
)
logger = logging.getLogger(__name__)

# Import existing components
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.folder_summarizer import FolderSummarizer
from memory.enhanced_semantic_search import EnhancedSemanticSearch

class FolderReader:
    """
    Reads and analyzes folder contents, providing both summary and search capabilities.
    """
    
    def __init__(self):
        """Initialize the folder reader."""
        self.folder_summarizer = FolderSummarizer()
        self.semantic_search = EnhancedSemanticSearch(embedding_dim=384, use_hybrid=True)
        logger.info("Folder reader initialized")
    
    def read_folder(self, folder_path: str, detail_level: str = "medium", 
                   include_content: bool = True, recursive: bool = True) -> Dict[str, Any]:
        """
        Read and analyze a folder, returning a comprehensive summary.
        
        Args:
            folder_path: Path to the folder to read
            detail_level: Level of detail in the summary ('low', 'medium', 'high')
            include_content: Whether to analyze file content
            recursive: Whether to include subfolders
            
        Returns:
            Dictionary with folder summary and formatted text summary
        """
        # Ensure the folder path exists
        if not os.path.exists(folder_path):
            return {"error": f"Folder path does not exist: {folder_path}"}
        
        if not os.path.isdir(folder_path):
            return {"error": f"Path is not a directory: {folder_path}"}
        
        try:
            # Get structured summary data
            summary = self.folder_summarizer.summarize_folder(
                folder_path, 
                include_content=include_content,
                recursive=recursive
            )
            
            # Generate human-readable text summary
            text_summary = self.folder_summarizer.generate_summary_text(
                summary, 
                detail_level=detail_level
            )
            
            # Combine results
            result = {
                "summary": summary,
                "text_summary": text_summary
            }
            
            logger.info(f"Successfully read folder: {folder_path}")
            return result
            
        except Exception as e:
            error_msg = f"Error reading folder {folder_path}: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}
    
    def search_files(self, folder_path: str, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Search for files in a folder that match the query.
        
        Args:
            folder_path: Path to the folder to search
            query: Search query
            limit: Maximum number of results to return
            
        Returns:
            Dictionary with search results and formatted text
        """
        try:
            # Get search results
            results = self.folder_summarizer.search_folder_content(
                folder_path=folder_path,
                query=query,
                limit=limit
            )
            
            # Format results as text
            text_results = []
            text_results.append(f"Search Results for '{query}' in {folder_path}:")
            text_results.append("")
            
            if results:
                for i, result in enumerate(results):
                    text_results.append(f"{i+1}. {result.get('file_name', 'Unnamed file')} (Score: {result.get('score', 0):.2f})")
                    text_results.append(f"   Path: {result.get('relative_path', 'Unknown path')}")
                    if "snippet" in result:
                        text_results.append(f"   Preview: {result['snippet']}")
                    text_results.append("")
            else:
                text_results.append("No matching files found.")
            
            formatted_text = "\n".join(text_results)
            
            return {
                "results": results,
                "text_results": formatted_text,
                "count": len(results)
            }
            
        except Exception as e:
            error_msg = f"Error searching folder {folder_path}: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}
    
    def answer_question(self, folder_path: str, question: str) -> Dict[str, Any]:
        """
        Answer a question about folder contents by searching and analyzing relevant files.
        
        Args:
            folder_path: Path to the folder to analyze
            question: Question to answer about the folder contents
            
        Returns:
            Dictionary with answer and supporting information
        """
        try:
            # First, get a general folder summary
            summary = self.read_folder(folder_path, detail_level="medium", include_content=True)
            
            # Then search for relevant files
            search_results = self.search_files(folder_path, question, limit=5)
            
            # Compile information for the answer
            answer_components = []
            
            # Add folder overview
            if "text_summary" in summary:
                overview = summary["text_summary"].split("\n\n")[0]  # First paragraph
                answer_components.append(f"Folder Overview: {overview}")
            
            # Add relevant files
            if "results" in search_results and search_results["results"]:
                answer_components.append("Relevant files:")
                for result in search_results["results"]:
                    answer_components.append(f"- {result.get('file_name', 'Unnamed file')}: {result.get('snippet', 'No preview available')[:200]}...")
            
            # Create comprehensive answer
            answer = {
                "folder_path": folder_path,
                "question": question,
                "answer_text": "\n\n".join(answer_components),
                "folder_summary": summary.get("summary", {}),
                "search_results": search_results.get("results", [])
            }
            
            return answer
            
        except Exception as e:
            error_msg = f"Error answering question about folder {folder_path}: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description="Read, analyze, and search folder contents")
    parser.add_argument("action", choices=["read", "search", "ask"], help="Action to perform")
    parser.add_argument("folder_path", help="Path to the folder to read or search")
    parser.add_argument("--query", help="Search query or question (required for search and ask actions)")
    parser.add_argument("--detail", choices=["low", "medium", "high"], default="medium", help="Detail level for summary")
    parser.add_argument("--no-content", action="store_true", help="Skip content analysis")
    parser.add_argument("--no-recursive", action="store_true", help="Don't include subfolders")
    parser.add_argument("--output", help="Output file for JSON results (optional)")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of search results")
    
    args = parser.parse_args()
    
    # Create folder reader
    folder_reader = FolderReader()
    
    # Perform requested action
    if args.action == "read":
        # Read and summarize folder
        result = folder_reader.read_folder(
            args.folder_path,
            detail_level=args.detail,
            include_content=not args.no_content,
            recursive=not args.no_recursive
        )
        
        # Print text summary
        if "text_summary" in result:
            print(result["text_summary"])
        elif "error" in result:
            print(f"Error: {result['error']}")
        
    elif args.action == "search":
        # Validate search query
        if not args.query:
            print("Error: --query parameter is required for search action")
            sys.exit(1)
        
        # Search folder contents
        result = folder_reader.search_files(
            args.folder_path,
            args.query,
            limit=args.limit
        )
        
        # Print results
        if "text_results" in result:
            print(result["text_results"])
        elif "error" in result:
            print(f"Error: {result['error']}")
    
    elif args.action == "ask":
        # Validate question
        if not args.query:
            print("Error: --query parameter is required for ask action")
            sys.exit(1)
        
        # Answer question about folder
        result = folder_reader.answer_question(
            args.folder_path,
            args.query
        )
        
        # Print answer
        if "answer_text" in result:
            print(result["answer_text"])
        elif "error" in result:
            print(f"Error: {result['error']}")
    
    # Save JSON output if requested
    if args.output and (("summary" in result) or ("results" in result) or ("answer_text" in result)):
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Detailed results saved to {args.output}")

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"Error: {str(e)}")