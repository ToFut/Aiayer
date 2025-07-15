from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
from pathlib import Path

from .core import DocumentMemory, DocumentAnalyzer, FolderScanner

app = FastAPI(title="Aiayer Document Intelligence API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core components
memory = DocumentMemory()
analyzer = DocumentAnalyzer(memory)
scanner = FolderScanner(analyzer)

class FolderPath(BaseModel):
    path: str

class DocumentAnalysis(BaseModel):
    doc_path: str
    analysis: Dict
    timestamp: str
    doc_hash: str
    folder_path: str

class FolderStats(BaseModel):
    total_files: int
    total_size: int
    file_types: Dict[str, int]
    last_scan: Optional[str]
    scanning: bool
    scan_progress: float
    error_count: int

@app.post("/watch-folder")
async def watch_folder(folder: FolderPath):
    """Start watching a folder for document changes"""
    if not os.path.exists(folder.path):
        raise HTTPException(status_code=404, detail="Folder not found")
        
    try:
        scanner.start_watching(folder.path)
        return {
            "status": "success",
            "message": f"Now watching folder: {folder.path}",
            "stats": memory.get_folder_stats(folder.path)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stop-watching")
async def stop_watching(folder: Optional[FolderPath] = None):
    """Stop watching a specific folder or all folders"""
    try:
        scanner.stop_watching(folder.path if folder else None)
        return {
            "status": "success",
            "message": "Stopped watching folder" if folder else "Stopped watching all folders"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents", response_model=List[DocumentAnalysis])
async def list_documents(folder_path: Optional[str] = None):
    """List all analyzed documents, optionally filtered by folder"""
    documents = memory.list_all_analyses()
    if folder_path:
        documents = [doc for doc in documents if doc["folder_path"] == folder_path]
    return documents

@app.get("/documents/{doc_hash}", response_model=DocumentAnalysis)
async def get_document(doc_hash: str):
    """Get analysis for a specific document"""
    analysis = memory.get_document_analysis(doc_hash)
    if not analysis:
        raise HTTPException(status_code=404, detail="Document not found")
    return analysis

@app.get("/folders", response_model=List[str])
async def list_folders():
    """List all watched folders"""
    return list(scanner.watched_folders)

@app.get("/folders/{folder_path}/stats", response_model=FolderStats)
async def get_folder_stats(folder_path: str):
    """Get statistics for a specific folder"""
    if folder_path not in scanner.watched_folders:
        raise HTTPException(status_code=404, detail="Folder not found")
    return memory.get_folder_stats(folder_path)

@app.post("/analyze-document")
async def analyze_document(file_path: str):
    """Manually trigger analysis of a specific document"""
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    try:
        folder_path = str(Path(file_path).parent)
        analysis = analyzer.analyze_document(file_path, folder_path)
        if not analysis:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/supported-extensions")
async def get_supported_extensions():
    """Get list of supported file extensions"""
    return list(analyzer.supported_extensions)

@app.get("/analysis-progress")
async def get_analysis_progress():
    """Get current document analysis progress"""
    progress = analyzer.get_analysis_progress()
    return progress 