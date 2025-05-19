"""
Safe JSON utilities for memory system.
Provides safer JSON serialization/deserialization.
"""
import json
import logging
from typing import Any, Dict, Union, Optional

logger = logging.getLogger(__name__)

def safe_load(json_str: str, fallback: Optional[Any] = None) -> Any:
    """
    Safely load JSON from string.
    
    Args:
        json_str: JSON string to load
        fallback: Value to return if loading fails
        
    Returns:
        Parsed JSON data or fallback value
    """
    try:
        return json.loads(json_str)
    except Exception as e:
        logger.error(f"Error loading JSON: {e}")
        return fallback

def safe_dump(data: Any, indent: Optional[int] = None, fallback: str = "{}") -> str:
    """
    Safely dump object to JSON string.
    
    Args:
        data: Object to serialize to JSON
        indent: Indentation level for pretty printing
        fallback: String to return if serialization fails
        
    Returns:
        JSON string or fallback string
    """
    try:
        return json.dumps(data, indent=indent, default=_json_serialize)
    except Exception as e:
        logger.error(f"Error dumping JSON: {e}")
        return fallback

def safe_dumps(data: Any, indent: Optional[int] = None, fallback: str = "{}") -> str:
    """Alias for safe_dump."""
    return safe_dump(data, indent, fallback)

def _json_serialize(obj: Any) -> Any:
    """Custom JSON serializer for handling non-serializable objects."""
    try:
        # Handle common non-serializable types
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        elif hasattr(obj, 'isoformat'):
            return obj.isoformat()
        elif hasattr(obj, '__str__'):
            return str(obj)
        else:
            return repr(obj)
    except Exception:
        return str(obj)