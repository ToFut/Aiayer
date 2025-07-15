#!/usr/bin/env python3
"""
Base UI Scraper - Cross-platform UI tree extraction
"""

import platform
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def get_ui_tree() -> Dict[str, Any]:
    """
    Get the current UI tree based on the platform.
    
    Returns:
        Dict containing the UI tree structure
    """
    system = platform.system()
    
    if system == "Darwin":  # macOS
        try:
            from .mac_scraper import scrape_macos_ui
            return scrape_macos_ui()
        except ImportError as e:
            logger.error(f"macOS scraper not available: {e}")
            return _get_fallback_ui_tree()
    elif system == "Windows":
        try:
            from .win_scraper import scrape_windows_ui
            return scrape_windows_ui()
        except ImportError as e:
            logger.error(f"Windows scraper not available: {e}")
            return _get_fallback_ui_tree()
    else:
        logger.warning(f"Unsupported platform: {system}")
        return _get_fallback_ui_tree()

def _get_fallback_ui_tree() -> Dict[str, Any]:
    """
    Fallback UI tree when platform-specific scrapers are not available.
    """
    return {
        "name": "fallback_root",
        "type": "Window",
        "id": "fallback_root",
        "bounds": [0, 0, 1920, 1080],
        "children": [
            {
                "name": "Fallback UI Element",
                "type": "Text",
                "id": "fallback_text",
                "bounds": [100, 100, 300, 150],
                "children": []
            }
        ]
    } 