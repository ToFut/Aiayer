#!/usr/bin/env python3
"""
Memory Store - ChromaDB-based vector storage for UI snapshots
"""

import logging
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Global ChromaDB client
_chroma_client = None
_collection = None

def get_chroma_client():
    """Get or create ChromaDB client."""
    global _chroma_client
    if _chroma_client is None:
        try:
            import chromadb
            _chroma_client = chromadb.PersistentClient(path="./chroma_db")
            logger.info("ChromaDB client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            return None
    return _chroma_client

def get_collection():
    """Get or create the UI snapshots collection."""
    global _collection
    if _collection is None:
        client = get_chroma_client()
        if client:
            try:
                _collection = client.get_or_create_collection(
                    name="ui_snapshots",
                    metadata={"description": "UI snapshots for semantic querying"}
                )
                logger.info("UI snapshots collection ready")
            except Exception as e:
                logger.error(f"Failed to get collection: {e}")
                return None
    return _collection

def store_ui_snapshot(ui_tree: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> str:
    """
    Store a UI snapshot in the vector database.
    
    Args:
        ui_tree: UI tree dictionary
        metadata: Additional metadata for the snapshot
        
    Returns:
        Snapshot ID
    """
    try:
        collection = get_collection()
        if not collection:
            logger.error("No collection available")
            return None
        
        # Convert UI tree to HTML
        from html_mapper import ui_node_to_html
        html_content = ui_node_to_html(ui_tree)
        
        # Create document text for embedding
        document_text = extract_text_from_ui_tree(ui_tree)
        
        # Generate snapshot ID
        snapshot_id = f"snapshot_{int(time.time() * 1000)}"
        
        # Prepare metadata
        snapshot_metadata = {
            "timestamp": datetime.now().isoformat(),
            "ui_tree": json.dumps(ui_tree),
            "html_content": html_content,
            "element_count": count_elements(ui_tree)
        }
        if metadata:
            snapshot_metadata.update(metadata)
        
        # Store in ChromaDB
        collection.add(
            documents=[document_text],
            metadatas=[snapshot_metadata],
            ids=[snapshot_id]
        )
        
        logger.info(f"Stored UI snapshot: {snapshot_id}")
        return snapshot_id
        
    except Exception as e:
        logger.error(f"Error storing UI snapshot: {e}")
        return None

def query_ui_by_text(query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
    """
    Query UI snapshots by text similarity.
    
    Args:
        query_text: Text to search for
        n_results: Number of results to return
        
    Returns:
        List of matching snapshots
    """
    try:
        collection = get_collection()
        if not collection:
            logger.error("No collection available")
            return []
        
        # Query ChromaDB
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        
        # Format results
        formatted_results = []
        if results['ids'] and results['ids'][0]:
            for i, snapshot_id in enumerate(results['ids'][0]):
                result = {
                    "id": snapshot_id,
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i] if results['distances'] else None
                }
                formatted_results.append(result)
        
        logger.info(f"Found {len(formatted_results)} results for query: {query_text}")
        return formatted_results
        
    except Exception as e:
        logger.error(f"Error querying UI snapshots: {e}")
        return []

def get_ui_memory(snapshot_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a specific UI snapshot by ID.
    
    Args:
        snapshot_id: ID of the snapshot to retrieve
        
    Returns:
        Snapshot data or None if not found
    """
    try:
        collection = get_collection()
        if not collection:
            logger.error("No collection available")
            return None
        
        # Get snapshot by ID
        results = collection.get(ids=[snapshot_id])
        
        if results['ids'] and results['ids'][0]:
            return {
                "id": results['ids'][0],
                "metadata": results['metadatas'][0],
                "document": results['documents'][0] if results['documents'] else None
            }
        
        logger.warning(f"Snapshot not found: {snapshot_id}")
        return None
        
    except Exception as e:
        logger.error(f"Error retrieving UI snapshot: {e}")
        return None

def extract_text_from_ui_tree(ui_tree: Dict[str, Any]) -> str:
    """
    Extract text content from UI tree for embedding.
    
    Args:
        ui_tree: UI tree dictionary
        
    Returns:
        Text content string
    """
    text_parts = []
    
    def safe_str(value):
        """Safely convert any value to string, handling Objective-C types."""
        if value is None:
            return ""
        try:
            # Handle Objective-C types and other non-standard types
            if hasattr(value, '__str__'):
                return str(value)
            else:
                return repr(value)
        except Exception:
            return ""
    
    def extract_node_text(node):
        # Add node name and value - ensure they are strings
        if node.get("name"):
            name = safe_str(node["name"])
            if name:
                text_parts.append(name)
        if node.get("value"):
            value = safe_str(node["value"])
            if value:
                text_parts.append(value)
        
        # Recursively process children
        for child in node.get("children", []):
            extract_node_text(child)
    
    extract_node_text(ui_tree)
    return " ".join(text_parts)

def count_elements(ui_tree: Dict[str, Any]) -> int:
    """
    Count total number of elements in UI tree.
    
    Args:
        ui_tree: UI tree dictionary
        
    Returns:
        Element count
    """
    count = 1  # Count current node
    
    # Count children
    for child in ui_tree.get("children", []):
        count += count_elements(child)
    
    return count

def list_snapshots(limit: int = 50) -> List[Dict[str, Any]]:
    """
    List recent UI snapshots.
    
    Args:
        limit: Maximum number of snapshots to return
        
    Returns:
        List of snapshot metadata
    """
    try:
        collection = get_collection()
        if not collection:
            logger.error("No collection available")
            return []
        
        # Get all snapshots
        results = collection.get(limit=limit)
        
        snapshots = []
        if results['ids']:
            for i, snapshot_id in enumerate(results['ids']):
                snapshot = {
                    "id": snapshot_id,
                    "metadata": results['metadatas'][i],
                    "document": results['documents'][i] if results['documents'] else None
                }
                snapshots.append(snapshot)
        
        # Sort by timestamp (newest first)
        snapshots.sort(key=lambda x: x['metadata'].get('timestamp', ''), reverse=True)
        
        return snapshots
        
    except Exception as e:
        logger.error(f"Error listing snapshots: {e}")
        return [] 