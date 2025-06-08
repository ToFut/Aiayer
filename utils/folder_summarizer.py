#!/usr/bin/env python3
"""
Folder Summarizer Module

Provides functionality to analyze and summarize folder contents.
Uses existing memory and semantic search capabilities.
"""
import os
import time
import json
import logging
import sys
import re
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional, Union
import threading

# Import enhanced semantic search for content analysis
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from memory.enhanced_semantic_search import EnhancedSemanticSearch

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# File type categories
FILE_CATEGORIES = {
    'documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.md', '.markdown'],
    'spreadsheets': ['.xls', '.xlsx', '.csv', '.ods', '.tsv'],
    'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.webp'],
    'audio': ['.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac'],
    'video': ['.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm'],
    'code': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h', '.rb', '.php', '.go', '.rs', '.ts', '.swift'],
    'archives': ['.zip', '.rar', '.tar', '.gz', '.7z'],
    'executables': ['.exe', '.app', '.dmg', '.msi', '.bat', '.sh'],
}

class FolderSummarizer:
    """
    Analyzes and summarizes folder contents.
    Provides detailed information about file types, sizes, and content.
    """
    
    def __init__(self):
        """Initialize the folder summarizer."""
        self.semantic_search = EnhancedSemanticSearch(embedding_dim=384, use_hybrid=True)
        self.file_cache = {}  # Cache for file content
        self.max_file_size = 10 * 1024 * 1024  # 10MB max file size for content analysis
        self.max_cache_size = 100  # Maximum number of files to keep in cache
        
        # Create cache directory for folder summarizer
        os.makedirs('cache/folder_summarizer', exist_ok=True)
        
        logger.info("Folder summarizer initialized")
    
    def summarize_folder(self, folder_path: str, include_content: bool = True, 
                         recursive: bool = True, file_types: List[str] = None) -> Dict[str, Any]:
        """
        Generate a comprehensive summary of a folder.
        
        Args:
            folder_path: Path to the folder to summarize
            include_content: Whether to analyze file content (for text files)
            recursive: Whether to include subfolders
            file_types: List of file extensions to include (None for all)
            
        Returns:
            Dictionary with folder summary information
        """
        # Verify folder exists
        if not os.path.exists(folder_path):
            logger.error(f"Folder path does not exist: {folder_path}")
            return {"error": f"Folder path does not exist: {folder_path}"}
        
        if not os.path.isdir(folder_path):
            logger.error(f"Path is not a directory: {folder_path}")
            return {"error": f"Path is not a directory: {folder_path}"}
        
        try:
            # Start timing
            start_time = time.time()
            
            # Initialize summary structure
            summary = {
                "folder_name": os.path.basename(folder_path),
                "folder_path": folder_path,
                "total_size": 0,
                "total_files": 0,
                "total_folders": 0,
                "file_types": {},
                "largest_files": [],
                "newest_files": [],
                "category_breakdown": {},
                "content_summary": {},
                "timestamp": datetime.now().isoformat()
            }
            
            # Initialize category counters
            for category in FILE_CATEGORIES:
                summary["category_breakdown"][category] = {
                    "count": 0,
                    "size": 0,
                    "extensions": {}
                }
            
            # Add "other" category
            summary["category_breakdown"]["other"] = {
                "count": 0,
                "size": 0,
                "extensions": {}
            }
            
            # Traverse the directory
            for root, dirs, files in os.walk(folder_path):
                # Skip if non-recursive and not in the root directory
                if not recursive and root != folder_path:
                    continue
                
                # Count folders
                summary["total_folders"] += len(dirs)
                
                # Process files
                for filename in files:
                    file_path = os.path.join(root, filename)
                    
                    # Skip if file doesn't match requested types
                    if file_types:
                        _, ext = os.path.splitext(filename.lower())
                        if ext not in file_types:
                            continue
                    
                    try:
                        # Get file stats
                        stats = os.stat(file_path)
                        file_size = stats.st_size
                        file_mtime = stats.st_mtime
                        
                        # Get file extension
                        _, ext = os.path.splitext(filename.lower())
                        
                        # Update summary
                        summary["total_files"] += 1
                        summary["total_size"] += file_size
                        
                        # Track file types
                        if ext not in summary["file_types"]:
                            summary["file_types"][ext] = {
                                "count": 0,
                                "size": 0
                            }
                        summary["file_types"][ext]["count"] += 1
                        summary["file_types"][ext]["size"] += file_size
                        
                        # Track file categories
                        category_found = False
                        for category, extensions in FILE_CATEGORIES.items():
                            if ext in extensions:
                                summary["category_breakdown"][category]["count"] += 1
                                summary["category_breakdown"][category]["size"] += file_size
                                
                                if ext not in summary["category_breakdown"][category]["extensions"]:
                                    summary["category_breakdown"][category]["extensions"][ext] = {
                                        "count": 0,
                                        "size": 0
                                    }
                                summary["category_breakdown"][category]["extensions"][ext]["count"] += 1
                                summary["category_breakdown"][category]["extensions"][ext]["size"] += file_size
                                
                                category_found = True
                                break
                        
                        # If no category matched, add to "other"
                        if not category_found:
                            summary["category_breakdown"]["other"]["count"] += 1
                            summary["category_breakdown"]["other"]["size"] += file_size
                            
                            if ext not in summary["category_breakdown"]["other"]["extensions"]:
                                summary["category_breakdown"]["other"]["extensions"][ext] = {
                                    "count": 0,
                                    "size": 0
                                }
                            summary["category_breakdown"]["other"]["extensions"][ext]["count"] += 1
                            summary["category_breakdown"]["other"]["extensions"][ext]["size"] += file_size
                        
                        # Track largest files
                        file_info = {
                            "name": filename,
                            "path": file_path,
                            "size": file_size,
                            "modified": datetime.fromtimestamp(file_mtime).isoformat()
                        }
                        
                        # Keep top 10 largest files
                        summary["largest_files"].append(file_info)
                        summary["largest_files"].sort(key=lambda x: x["size"], reverse=True)
                        if len(summary["largest_files"]) > 10:
                            summary["largest_files"] = summary["largest_files"][:10]
                        
                        # Keep top 10 newest files
                        summary["newest_files"].append(file_info)
                        summary["newest_files"].sort(key=lambda x: x["modified"], reverse=True)
                        if len(summary["newest_files"]) > 10:
                            summary["newest_files"] = summary["newest_files"][:10]
                            
                        # Analyze content for text files if requested
                        if include_content and self._is_text_file(file_path, ext) and file_size < self.max_file_size:
                            self._analyze_file_content(file_path, summary)
                    
                    except (PermissionError, FileNotFoundError) as e:
                        logger.warning(f"Could not access file {file_path}: {e}")
                    except Exception as e:
                        logger.error(f"Error processing file {file_path}: {e}")
            
            # Generate content summary if we have analyzed files
            if "content_summary" in summary and "analyzed_files" in summary["content_summary"]:
                if summary["content_summary"]["analyzed_files"]:
                    summary["content_summary"]["topics"] = self._extract_topics(summary["content_summary"]["analyzed_files"])
            
            # Calculate time taken
            summary["processing_time"] = time.time() - start_time
            
            logger.info(f"Folder summary completed for {folder_path}: {summary['total_files']} files, {summary['total_folders']} folders")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating folder summary: {e}")
            return {"error": f"Error generating folder summary: {str(e)}"}
    
    def _is_text_file(self, file_path: str, ext: str) -> bool:
        """Determine if a file is a text file that can be analyzed."""
        # Common text file extensions
        text_extensions = [
            '.txt', '.md', '.py', '.js', '.html', '.css', '.java', '.c', '.cpp', 
            '.h', '.rb', '.php', '.go', '.rs', '.json', '.xml', '.yaml', '.yml',
            '.sh', '.bat', '.ps1', '.csv', '.tsv', '.log', '.conf', '.ini'
        ]
        
        if ext in text_extensions:
            return True
        
        # For other files, try to peek at content
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                # Simple binary check - if chunk contains null bytes, likely binary
                if b'\x00' in chunk:
                    return False
                
                # Try to decode as UTF-8
                try:
                    chunk.decode('utf-8')
                    return True
                except UnicodeDecodeError:
                    return False
        except:
            return False
    
    def _analyze_file_content(self, file_path: str, summary: Dict[str, Any]) -> None:
        """Analyze the content of a text file for the summary."""
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Initialize content summary if needed
            if "content_summary" not in summary:
                summary["content_summary"] = {}
            
            # Initialize analyzed_files list if needed
            if "analyzed_files" not in summary["content_summary"]:
                summary["content_summary"]["analyzed_files"] = []
            
            # Create file entry with basic info and content snippet
            file_entry = {
                "path": file_path,
                "name": os.path.basename(file_path),
                "lines": content.count('\n') + 1,
                "words": len(re.findall(r'\w+', content)),
                "snippet": content[:500] + ('...' if len(content) > 500 else '')
            }
            
            # Add to semantic search index
            item_id = self.semantic_search.add_to_index(
                {"content": content, "id": file_path},
                memory_type="folder_summary",
                metadata={"file_path": file_path}
            )
            
            if item_id:
                file_entry["indexed"] = True
                
            # Add to analyzed files
            summary["content_summary"]["analyzed_files"].append(file_entry)
            
        except Exception as e:
            logger.warning(f"Could not analyze content of {file_path}: {e}")
    
    def _extract_topics(self, analyzed_files: List[Dict[str, Any]]) -> List[str]:
        """
        Extract common topics from analyzed files.
        Simple implementation - in a real system, this would use more sophisticated NLP.
        """
        # Simple word frequency analysis
        word_counts = {}
        
        if not analyzed_files:
            return []
            
        for file_entry in analyzed_files:
            if file_entry and "snippet" in file_entry:
                try:
                    words = re.findall(r'\b[a-zA-Z]{3,15}\b', file_entry["snippet"].lower())
                    for word in words:
                        if word not in word_counts:
                            word_counts[word] = 0
                        word_counts[word] += 1
                except Exception as e:
                    logger.warning(f"Error extracting topics: {e}")
        
        # Filter common stopwords
        stopwords = {'the', 'and', 'is', 'in', 'to', 'of', 'a', 'for', 'on', 'with', 'as', 'this', 'that', 'by', 'an'}
        for word in stopwords:
            word_counts.pop(word, None)
        
        # Get top words
        top_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        return [word for word, count in top_words]
    
    def search_folder_content(self, folder_path: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for content within a folder using semantic search.
        
        Args:
            folder_path: Path to the folder to search
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching files with relevance scores
        """
        try:
            # Use enhanced semantic search
            results = self.semantic_search.search(
                query=query,
                limit=limit,
                memory_types=["folder_summary"],
                min_score=0.3
            )
            
            # Filter results to only include files from the specified folder
            folder_results = []
            for result in results:
                file_path = result.get("id", "")
                if file_path.startswith(folder_path):
                    # Add file info
                    result["file_name"] = os.path.basename(file_path)
                    result["relative_path"] = os.path.relpath(file_path, folder_path)
                    folder_results.append(result)
            
            return folder_results
            
        except Exception as e:
            logger.error(f"Error searching folder content: {e}")
            return []
    
    def generate_summary_text(self, summary: Dict[str, Any], detail_level: str = "medium") -> str:
        """
        Generate a human-readable text summary from the structured summary data.
        
        Args:
            summary: The structured summary dictionary
            detail_level: Level of detail ('low', 'medium', 'high')
            
        Returns:
            Formatted text summary
        """
        if "error" in summary:
            return f"Error: {summary['error']}"
        
        # Build the summary text
        lines = []
        
        # Header
        lines.append(f"Folder Summary: {summary['folder_name']}")
        lines.append(f"Path: {summary['folder_path']}")
        lines.append("")
        
        # Basic stats
        lines.append("Basic Statistics:")
        lines.append(f"- Total files: {summary['total_files']}")
        lines.append(f"- Total folders: {summary['total_folders']}")
        lines.append(f"- Total size: {self._format_size(summary['total_size'])}")
        lines.append("")
        
        # File categories
        lines.append("File Categories:")
        for category, data in summary["category_breakdown"].items():
            if data["count"] > 0:
                lines.append(f"- {category.capitalize()}: {data['count']} files ({self._format_size(data['size'])})")
                
                # Add extension details for medium and high detail levels
                if detail_level in ["medium", "high"] and len(data["extensions"]) > 0:
                    for ext, ext_data in data["extensions"].items():
                        lines.append(f"  - {ext}: {ext_data['count']} files ({self._format_size(ext_data['size'])})")
        lines.append("")
        
        # Largest files for medium and high detail levels
        if detail_level in ["medium", "high"] and summary["largest_files"]:
            lines.append("Largest Files:")
            for file in summary["largest_files"][:5]:  # Show top 5
                lines.append(f"- {file['name']} ({self._format_size(file['size'])})")
            lines.append("")
        
        # Newest files for medium and high detail levels
        if detail_level in ["medium", "high"] and summary["newest_files"]:
            lines.append("Most Recently Modified Files:")
            for file in summary["newest_files"][:5]:  # Show top 5
                modified = datetime.fromisoformat(file['modified']).strftime('%Y-%m-%d %H:%M:%S')
                lines.append(f"- {file['name']} (Modified: {modified})")
            lines.append("")
        
        # Content summary for high detail level
        if detail_level == "high" and "content_summary" in summary and "topics" in summary["content_summary"]:
            lines.append("Content Analysis:")
            if summary["content_summary"]["topics"]:
                lines.append(f"- Common topics: {', '.join(summary['content_summary']['topics'][:10])}")
            if "analyzed_files" in summary["content_summary"]:
                lines.append(f"- Analyzed {len(summary['content_summary']['analyzed_files'])} text files")
            lines.append("")
        
        # Processing info
        lines.append(f"Summary generated on {datetime.fromisoformat(summary['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Processing time: {summary['processing_time']:.2f} seconds")
        
        return "\n".join(lines)
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    def clear_cache(self) -> None:
        """Clear the semantic search cache."""
        self.semantic_search.clear()
        self.file_cache = {}
        logger.info("Folder summarizer cache cleared")

def main():
    """Main function for standalone usage."""
    import argparse
    parser = argparse.ArgumentParser(description="Summarize folder contents")
    parser.add_argument("folder_path", help="Path to the folder to summarize")
    parser.add_argument("--no-content", action="store_true", help="Skip content analysis")
    parser.add_argument("--no-recursive", action="store_true", help="Don't include subfolders")
    parser.add_argument("--detail", choices=["low", "medium", "high"], default="medium", help="Detail level for summary text")
    parser.add_argument("--output", help="Output file for JSON summary (optional)")
    parser.add_argument("--search", help="Search query (optional)")
    args = parser.parse_args()
    
    # Create summarizer
    summarizer = FolderSummarizer()
    
    # If search query provided
    if args.search:
        print(f"Searching for '{args.search}' in {args.folder_path}...")
        results = summarizer.search_folder_content(args.folder_path, args.search)
        if results:
            print(f"Found {len(results)} results:")
            for i, result in enumerate(results):
                print(f"{i+1}. {result['file_name']} (Score: {result['score']:.2f})")
                print(f"   Path: {result['relative_path']}")
                if "content" in result:
                    print(f"   Preview: {result['content'][:100]}...")
                print()
        else:
            print("No results found.")
        return
    
    # Generate summary
    print(f"Generating summary for {args.folder_path}...")
    summary = summarizer.summarize_folder(
        args.folder_path,
        include_content=not args.no_content,
        recursive=not args.no_recursive
    )
    
    # Print text summary
    text_summary = summarizer.generate_summary_text(summary, detail_level=args.detail)
    print(text_summary)
    
    # Save JSON if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"Detailed summary saved to {args.output}")

if __name__ == "__main__":
    main()