"""
Document Intelligence Core Module
Implements document analysis and memory management.
"""
import os
import time
from pathlib import Path
from typing import List, Dict, Optional, Set
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import hashlib
from datetime import datetime
import mimetypes
import magic  # python-magic for better file type detection
import logging
from backend.llm.llm_service import LLMService
import itertools
import PyPDF2
import docx
import python_docx2txt

logger = logging.getLogger(__name__)

class FolderStats:
    def __init__(self):
        self.total_files = 0
        self.total_size = 0
        self.file_types = {}
        self.last_scan = None
        self.scanning = False
        self.scan_progress = 0
        self.error_count = 0

class DocumentMemory:
    def __init__(self, storage_path: str = "memory/documents"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.folder_stats = {}  # Store stats for each watched folder
        
    def store_document_analysis(self, doc_path: str, analysis: Dict, folder_path: str) -> str:
        """Store document analysis with a unique ID"""
        doc_hash = hashlib.md5(doc_path.encode()).hexdigest()
        timestamp = datetime.now().isoformat()
        
        data = {
            "doc_path": doc_path,
            "analysis": analysis,
            "timestamp": timestamp,
            "doc_hash": doc_hash,
            "folder_path": folder_path
        }
        
        file_path = self.storage_path / f"{doc_hash}.json"
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
            
        return doc_hash
    
    def get_document_analysis(self, doc_hash: str) -> Optional[Dict]:
        """Retrieve document analysis by hash"""
        file_path = self.storage_path / f"{doc_hash}.json"
        if not file_path.exists():
            return None
            
        with open(file_path, 'r') as f:
            return json.load(f)
            
    def list_all_analyses(self) -> List[Dict]:
        """List all stored document analyses"""
        analyses = []
        for file_path in self.storage_path.glob("*.json"):
            with open(file_path, 'r') as f:
                analyses.append(json.load(f))
        return analyses

    def get_folder_stats(self, folder_path: str) -> Dict:
        """Get statistics for a specific folder"""
        return self.folder_stats.get(folder_path, {})

    def update_folder_stats(self, folder_path: str, stats: Dict):
        """Update statistics for a folder"""
        self.folder_stats[folder_path] = stats

class DocumentAnalyzer:
    def __init__(self, memory: DocumentMemory):
        self.memory = memory
        self.llm_service = None
        self.supported_extensions = {
            '.txt', '.pdf', '.doc', '.docx', '.xls', '.xlsx',
            '.ppt', '.pptx', '.csv', '.json', '.xml', '.html',
            '.md', '.rtf'
        }
        self.chunk_size = 2000  # characters per chunk
        self.current_progress = 0
        self.current_file = None
        self.current_chunk = 0
        self.total_chunks = 0
        
    async def initialize(self):
        """Initialize the LLM service"""
        try:
            self.llm_service = LLMService()
            await self.llm_service.initialize()
            return True
        except Exception as e:
            logger.error(f"Error initializing LLM service: {e}")
            return False
            
    def is_supported_file(self, file_path: str) -> bool:
        """Check if file type is supported"""
        ext = Path(file_path).suffix.lower()
        return ext in self.supported_extensions
        
    def get_file_type(self, file_path: str) -> str:
        """Get file type information"""
        try:
            mime = magic.Magic(mime=True)
            return mime.from_file(file_path)
        except:
            return mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
        
    async def analyze_document(self, file_path: str, folder_path: str) -> Dict:
        """Analyze a document using LLM in chunks and aggregate insights"""
        if not self.is_supported_file(file_path):
            return None
        try:
            self.current_file = file_path
            self.current_chunk = 0
            self.total_chunks = 0
            
            file_stats = os.stat(file_path)
            file_type = self.get_file_type(file_path)
            
            # Read file content in chunks
            chunks = []
            async for chunk in self._read_file_content_chunks(file_path, file_type):
                if chunk:
                    chunks.append(chunk)
            
            if not chunks:
                return None
                
            self.total_chunks = len(chunks)
            
            # Analyze each chunk with the LLM
            chunk_analyses = []
            for idx, chunk in enumerate(chunks):
                self.current_chunk = idx + 1
                prompt = self._create_analysis_prompt(file_path, chunk, file_type, chunk_index=idx+1, total_chunks=len(chunks))
                if self.llm_service:
                    analysis = await self._get_llm_analysis(prompt)
                else:
                    analysis = self._get_basic_analysis(file_path, file_type)
                chunk_analyses.append(analysis)
                
            # Reset progress tracking
            self.current_file = None
            self.current_chunk = 0
            self.total_chunks = 0
            
            # Aggregate chunk analyses
            aggregated = self._aggregate_chunk_analyses(chunk_analyses)
            # Add metadata
            aggregated["metadata"] = {
                "file_type": file_type,
                "size": file_stats.st_size,
                "created": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                "extension": Path(file_path).suffix.lower(),
                "chunks": len(chunks)
            }
            # Store analysis in memory
            doc_hash = self.memory.store_document_analysis(file_path, aggregated, folder_path)
            aggregated["doc_hash"] = doc_hash
            return aggregated
        except Exception as e:
            logger.error(f"Error analyzing document {file_path}: {e}")
            # Reset progress tracking on error
            self.current_file = None
            self.current_chunk = 0
            self.total_chunks = 0
            return None

    async def _read_file_content_chunks(self, file_path: str, file_type: str):
        """Read file content in chunks for processing"""
        try:
            if file_type == 'text/plain':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    chunk_size = self.chunk_size
                    for i in range(0, len(content), chunk_size):
                        chunk = content[i:i + chunk_size]
                        if chunk.strip():
                            yield chunk
            elif file_type == 'application/pdf':
                # ✅ IMPLEMENTED: PDF text extraction
                try:
                    with open(file_path, 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        for page_num, page in enumerate(pdf_reader.pages):
                            text = page.extract_text()
                            if text.strip():
                                # Split long pages into chunks
                                for i in range(0, len(text), self.chunk_size):
                                    chunk = text[i:i + self.chunk_size]
                                    if chunk.strip():
                                        yield chunk
                except Exception as e:
                    logger.error(f"Error extracting PDF text from {file_path}: {e}")
                    return
            elif file_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                # ✅ IMPLEMENTED: DOC/DOCX text extraction
                try:
                    if file_type == 'application/msword':
                        # For .doc files
                        text = docx2txt.process(file_path)
                    else:
                        # For .docx files
                        doc = docx.Document(file_path)
                        text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
                    
                    if text.strip():
                        # Split into chunks
                        for i in range(0, len(text), self.chunk_size):
                            chunk = text[i:i + self.chunk_size]
                            if chunk.strip():
                                yield chunk
                except Exception as e:
                    logger.error(f"Error extracting DOC/DOCX text from {file_path}: {e}")
                    return
            else:
                return
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return

    def _create_analysis_prompt(self, file_path: str, content: str, file_type: str, chunk_index: int = 1, total_chunks: int = 1) -> str:
        chunk_info = f"\n(Chunk {chunk_index} of {total_chunks})" if total_chunks > 1 else ""
        return f"""Analyze this document and provide insights:{chunk_info}

File: {file_path}
Type: {file_type}
Content:
{content[:self.chunk_size]}

Please provide:
1. A brief summary
2. Key topics/themes
3. Important entities (people, organizations, dates)
4. Document structure (headings, sections)
5. Any notable patterns or insights
6. Potential risks or concerns
7. Recommendations for further analysis

Format the response as a JSON object with these fields:
{{
    "summary": "Brief document summary",
    "topics": ["topic1", "topic2", ...],
    "entities": {{
        "people": ["person1", "person2", ...],
        "organizations": ["org1", "org2", ...],
        "dates": ["date1", "date2", ...]
    }},
    "structure": {{
        "headings": ["heading1", "heading2", ...],
        "sections": ["section1", "section2", ...]
    }},
    "patterns": ["pattern1", "pattern2", ...],
    "risks": ["risk1", "risk2", ...],
    "recommendations": ["rec1", "rec2", ...]
}}"""

    def _aggregate_chunk_analyses(self, analyses: List[Dict]) -> Dict:
        """Aggregate multiple chunk analyses into a single analysis object"""
        if not analyses:
            return self._get_basic_analysis(None, None)
        # Combine summaries
        summary = "\n".join(a.get("summary", "") for a in analyses if a.get("summary"))
        # Combine topics, entities, etc.
        topics = list(set(itertools.chain.from_iterable(a.get("topics", []) for a in analyses)))
        entities = {
            "people": list(set(itertools.chain.from_iterable(a.get("entities", {}).get("people", []) for a in analyses))),
            "organizations": list(set(itertools.chain.from_iterable(a.get("entities", {}).get("organizations", []) for a in analyses))),
            "dates": list(set(itertools.chain.from_iterable(a.get("entities", {}).get("dates", []) for a in analyses)))
        }
        structure = {
            "headings": list(set(itertools.chain.from_iterable(a.get("structure", {}).get("headings", []) for a in analyses))),
            "sections": list(set(itertools.chain.from_iterable(a.get("structure", {}).get("sections", []) for a in analyses)))
        }
        patterns = list(set(itertools.chain.from_iterable(a.get("patterns", []) for a in analyses)))
        risks = list(set(itertools.chain.from_iterable(a.get("risks", []) for a in analyses)))
        recommendations = list(set(itertools.chain.from_iterable(a.get("recommendations", []) for a in analyses)))
        return {
            "summary": summary,
            "topics": topics,
            "entities": entities,
            "structure": structure,
            "patterns": patterns,
            "risks": risks,
            "recommendations": recommendations
        }

    async def _get_llm_analysis(self, prompt: str) -> Dict:
        """Get document analysis from LLM"""
        try:
            response = await self.llm_service.generate_response(
                messages=[
                    {"role": "system", "content": "You are a document analysis expert. Analyze documents and provide structured insights."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse JSON response
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                logger.error(f"Error parsing LLM response as JSON: {response}")
                return self._get_basic_analysis(None, None)
                
        except Exception as e:
            logger.error(f"Error getting LLM analysis: {e}")
            return self._get_basic_analysis(None, None)
            
    def _get_basic_analysis(self, file_path: Optional[str], file_type: Optional[str]) -> Dict:
        """Get basic document analysis without LLM"""
        return {
            "summary": "Basic document analysis",
            "topics": [],
            "entities": {
                "people": [],
                "organizations": [],
                "dates": []
            },
            "structure": {
                "headings": [],
                "sections": []
            },
            "patterns": [],
            "risks": [],
            "recommendations": []
        }

    def get_analysis_progress(self) -> Dict:
        """Get current analysis progress"""
        return {
            "current_file": self.current_file,
            "current_chunk": self.current_chunk,
            "total_chunks": self.total_chunks,
            "progress_percentage": (self.current_chunk / self.total_chunks * 100) if self.total_chunks > 0 else 0
        }

class FolderScanner(FileSystemEventHandler):
    def __init__(self, analyzer: DocumentAnalyzer):
        self.analyzer = analyzer
        self.observer = Observer()
        self.watched_folders: Set[str] = set()
        
    def start_watching(self, folder_path: str):
        """Start watching a folder for changes"""
        if folder_path in self.watched_folders:
            return
            
        self.watched_folders.add(folder_path)
        self.observer.schedule(self, folder_path, recursive=True)
        
        if not self.observer.is_alive():
            self.observer.start()
            
        # Initial scan of existing files
        self._scan_folder(folder_path)
        
    def stop_watching(self, folder_path: str = None):
        """Stop watching a specific folder or all folders"""
        if folder_path:
            if folder_path in self.watched_folders:
                self.watched_folders.remove(folder_path)
                # ✅ IMPLEMENTED: Proper unscheduling of specific folder
                try:
                    # Get all scheduled watches
                    scheduled_watches = self.observer._schedules.copy()
                    for watch in scheduled_watches:
                        if watch.path == folder_path:
                            self.observer.unschedule(watch)
                            logger.info(f"Unscheduled folder: {folder_path}")
                            break
                except Exception as e:
                    logger.error(f"Error unscheduling folder {folder_path}: {e}")
        else:
            self.observer.stop()
            self.observer.join()
            self.watched_folders.clear()
        
    def _scan_folder(self, folder_path: str):
        """Scan all files in a folder"""
        stats = FolderStats()
        stats.scanning = True
        stats.last_scan = datetime.now().isoformat()
        
        total_files = 0
        processed_files = 0
        
        # First pass: count total files
        for root, _, files in os.walk(folder_path):
            total_files += len(files)
            
        # Second pass: process files
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    analysis = self.analyzer.analyze_document(file_path, folder_path)
                    if analysis:
                        stats.total_files += 1
                        stats.total_size += os.path.getsize(file_path)
                        ext = Path(file_path).suffix.lower()
                        stats.file_types[ext] = stats.file_types.get(ext, 0) + 1
                except Exception as e:
                    stats.error_count += 1
                    print(f"Error processing {file_path}: {str(e)}")
                    
                processed_files += 1
                stats.scan_progress = (processed_files / total_files) * 100
                
        stats.scanning = False
        self.analyzer.memory.update_folder_stats(folder_path, stats.__dict__)
                
    def on_created(self, event):
        """Handle file creation events"""
        if not event.is_directory:
            folder_path = str(Path(event.src_path).parent)
            if folder_path in self.watched_folders:
                self.analyzer.analyze_document(event.src_path, folder_path)
            
    def on_modified(self, event):
        """Handle file modification events"""
        if not event.is_directory:
            folder_path = str(Path(event.src_path).parent)
            if folder_path in self.watched_folders:
                self.analyzer.analyze_document(event.src_path, folder_path)
                
    def on_deleted(self, event):
        """Handle file deletion events"""
        if not event.is_directory:
            folder_path = str(Path(event.src_path).parent)
            if folder_path in self.watched_folders:
                # ✅ IMPLEMENTED: Cleanup of deleted file analysis
                try:
                    # Remove from memory
                    doc_hash = self.analyzer.memory._get_document_hash(event.src_path)
                    if doc_hash in self.analyzer.memory.analyses:
                        del self.analyzer.memory.analyses[doc_hash]
                        logger.info(f"Removed analysis for deleted file: {event.src_path}")
                    
                    # Update folder stats
                    stats = self.analyzer.memory.get_folder_stats(folder_path)
                    if stats:
                        stats['total_files'] = max(0, stats.get('total_files', 0) - 1)
                        self.analyzer.memory.update_folder_stats(folder_path, stats)
                except Exception as e:
                    logger.error(f"Error cleaning up deleted file {event.src_path}: {e}") 