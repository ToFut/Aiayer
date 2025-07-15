"""
SensAI.UI2HTMLMemory - Next-Generation UI Memory System
Replaces screen sensors with semantic UI tree extraction and vector memory storage.
"""

from .ui_scraper.base_scraper import get_ui_tree
from .html_mapper import ui_node_to_html
from .memory_store import store_ui_snapshot, query_ui_by_text, get_ui_memory
from .ui2html_sensor import UI2HTMLSensor

__version__ = "1.0.0"
__author__ = "SensAI Team"

__all__ = [
    "get_ui_tree",
    "ui_node_to_html", 
    "store_ui_snapshot",
    "query_ui_by_text",
    "get_ui_memory",
    "UI2HTMLSensor"
] 