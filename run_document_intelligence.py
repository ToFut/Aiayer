"""
Document Intelligence System Runner
This script initializes and runs the complete document intelligence system.
"""
import os
import sys
import logging
from pathlib import Path
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

# Import our components
from sensors.folder_scanner_sensor import FolderScannerSensor
from document_intelligence.core import DocumentMemory, DocumentAnalyzer
from backend.llm.llm_service import LLMService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('document_intelligence.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Document Intelligence System")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
document_memory = DocumentMemory()
document_analyzer = DocumentAnalyzer(document_memory)
folder_scanner = FolderScannerSensor()

# Mount static files
app.mount("/static", StaticFiles(directory="document_intelligence/web/dashboard/static"), name="static")

# API Routes
@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """Serve the dashboard HTML"""
    with open("document_intelligence/web/dashboard/templates/document_intelligence.html") as f:
        return f.read()

@app.get("/api/folders")
async def get_folders():
    """Get list of watched folders"""
    return folder_scanner.watched_folders

@app.post("/api/folders")
async def add_folder(folder_data: dict):
    """Add a new folder to watch"""
    try:
        success = folder_scanner.start_watching(folder_data["path"])
        if success:
            return {"status": "success", "message": f"Started watching folder: {folder_data['path']}"}
        else:
            raise HTTPException(status_code=400, detail="Failed to add folder")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/folders/{folder_path}")
async def remove_folder(folder_path: str):
    """Stop watching a folder"""
    try:
        success = folder_scanner.stop_watching(folder_path)
        if success:
            return {"status": "success", "message": f"Stopped watching folder: {folder_path}"}
        else:
            raise HTTPException(status_code=400, detail="Failed to remove folder")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents/extensions")
async def get_supported_extensions():
    """Get list of supported file extensions"""
    return list(folder_scanner.supported_extensions)

@app.get("/api/stats")
async def get_stats():
    """Get folder statistics"""
    return folder_scanner.current_state["folder_stats"]

@app.get("/api/analysis/{doc_hash}")
async def get_document_analysis(doc_hash: str):
    """Get document analysis by hash"""
    analysis = folder_scanner.get_document_analysis(doc_hash)
    if analysis:
        return analysis
    raise HTTPException(status_code=404, detail="Document analysis not found")

@app.get("/api/automation")
async def get_automation_suggestions():
    """Get automation suggestions based on document analysis"""
    # ✅ IMPLEMENTED: Automation suggestions
    try:
        suggestions = []
        
        # Get recent document analyses
        recent_analyses = document_memory.list_all_analyses()
        
        # Analyze patterns and generate suggestions
        for analysis in recent_analyses[-10:]:  # Last 10 analyses
            doc_path = analysis.get('doc_path', '')
            doc_type = analysis.get('file_type', '')
            content = analysis.get('content', {})
            
            # Generate suggestions based on document type and content
            if doc_type == 'application/pdf':
                if 'invoice' in doc_path.lower() or 'bill' in doc_path.lower():
                    suggestions.append({
                        'type': 'automation',
                        'title': 'Invoice Processing',
                        'description': 'Automate invoice data extraction and payment processing',
                        'confidence': 0.85,
                        'action': 'extract_invoice_data',
                        'target_file': doc_path
                    })
            
            elif doc_type in ['text/plain', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                # Check for repetitive tasks in documents
                if content.get('patterns', []):
                    suggestions.append({
                        'type': 'automation',
                        'title': 'Document Template Creation',
                        'description': 'Create templates for frequently used document formats',
                        'confidence': 0.75,
                        'action': 'create_template',
                        'target_file': doc_path
                    })
            
            # Check for file organization opportunities
            if len(recent_analyses) > 5:
                suggestions.append({
                    'type': 'organization',
                    'title': 'File Organization',
                    'description': 'Organize files by type, date, or project',
                    'confidence': 0.8,
                    'action': 'organize_files',
                    'target_folder': os.path.dirname(doc_path)
                })
        
        # Add general suggestions based on system usage
        suggestions.extend([
            {
                'type': 'backup',
                'title': 'Automatic Backup',
                'description': 'Set up automatic backup for important documents',
                'confidence': 0.9,
                'action': 'setup_backup'
            },
            {
                'type': 'search',
                'title': 'Enhanced Search',
                'description': 'Create searchable index of all documents',
                'confidence': 0.85,
                'action': 'create_search_index'
            }
        ])
        
        return {
            "suggestions": suggestions,
            "total_count": len(suggestions),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating automation suggestions: {e}")
        return {
            "suggestions": [],
            "error": str(e),
            "total_count": 0
        }

@app.post("/api/folders/files")
async def add_folder_files(request: Request):
    """Accept a list of file paths from the frontend and log/process them."""
    data = await request.json()
    files = data.get("files", [])
    logger.info(f"Received files for folder add: {files}")
    # Here you could process the file list, e.g., reconstruct folder structure, or trigger analysis
    return {"status": "ok", "received_files": files}

async def initialize_system():
    """Initialize all system components"""
    try:
        # Initialize LLM service
        llm_service = LLMService()
        await llm_service.initialize()
        
        # Initialize document analyzer
        await document_analyzer.initialize()
        
        # Initialize folder scanner
        await folder_scanner.initialize()
        
        logger.info("Document Intelligence System initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing system: {e}")
        return False

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    await initialize_system()

def main():
    """Run the application"""
    # Create necessary directories
    Path("memory/documents").mkdir(parents=True, exist_ok=True)
    Path("logs").mkdir(exist_ok=True)
    
    # Run the FastAPI application
    uvicorn.run(
        "run_document_intelligence:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

if __name__ == "__main__":
    main() 