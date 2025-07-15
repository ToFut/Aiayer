#!/usr/bin/env python3
"""
UI2HTML Sensor - Next-generation replacement for screen sensors
"""

import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

# Use absolute imports instead of relative
from ui_scraper.base_scraper import get_ui_tree
from html_mapper import ui_node_to_html
from memory_store import store_ui_snapshot, query_ui_by_text, get_ui_memory, list_snapshots

logger = logging.getLogger(__name__)

class UI2HTMLSensor:
    """
    Next-generation UI sensor that extracts semantic UI trees and stores them in vector memory.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the UI2HTML sensor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.sensor_type = "ui2html"
        self.last_snapshot_id = None
        self.snapshot_count = 0
        self.is_active = False
        
        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        
        logger.info("UI2HTML Sensor initialized")
    
    def start(self) -> bool:
        """
        Start the sensor.
        
        Returns:
            True if started successfully
        """
        try:
            self.is_active = True
            logger.info("UI2HTML Sensor started")
            return True
        except Exception as e:
            logger.error(f"Failed to start sensor: {e}")
            return False
    
    def stop(self) -> bool:
        """
        Stop the sensor.
        
        Returns:
            True if stopped successfully
        """
        try:
            self.is_active = False
            logger.info("UI2HTML Sensor stopped")
            return True
        except Exception as e:
            logger.error(f"Failed to stop sensor: {e}")
            return False
    
    def capture_snapshot(self, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Capture a UI snapshot and store it in memory.
        
        Args:
            metadata: Additional metadata for the snapshot
            
        Returns:
            Snapshot data dictionary
        """
        try:
            if not self.is_active:
                logger.warning("Sensor not active, cannot capture snapshot")
                return {}
            
            # Get UI tree
            ui_tree = get_ui_tree()
            
            # Convert to HTML
            html_content = ui_node_to_html(ui_tree)
            
            # Store in memory
            snapshot_id = store_ui_snapshot(ui_tree, metadata)
            
            if snapshot_id:
                self.last_snapshot_id = snapshot_id
                self.snapshot_count += 1
                
                snapshot_data = {
                    "snapshot_id": snapshot_id,
                    "timestamp": datetime.now().isoformat(),
                    "ui_tree": ui_tree,
                    "html_content": html_content,
                    "element_count": self._count_elements(ui_tree),
                    "sensor_type": self.sensor_type
                }
                
                logger.info(f"Captured snapshot {snapshot_id} with {snapshot_data['element_count']} elements")
                return snapshot_data
            else:
                logger.error("Failed to store snapshot")
                return {}
                
        except Exception as e:
            logger.error(f"Error capturing snapshot: {e}")
            return {}
    
    def query_memory(self, query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Query UI memory by text.
        
        Args:
            query_text: Text to search for
            n_results: Number of results to return
            
        Returns:
            List of matching snapshots
        """
        try:
            results = query_ui_by_text(query_text, n_results)
            logger.info(f"Query '{query_text}' returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Error querying memory: {e}")
            return []
    
    def get_last_snapshot(self) -> Optional[Dict[str, Any]]:
        """
        Get the last captured snapshot.
        
        Returns:
            Last snapshot data or None
        """
        if self.last_snapshot_id:
            return get_ui_memory(self.last_snapshot_id)
        return None
    
    def list_recent_snapshots(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        List recent snapshots.
        
        Args:
            limit: Maximum number of snapshots to return
            
        Returns:
            List of recent snapshots
        """
        try:
            return list_snapshots(limit)
        except Exception as e:
            logger.error(f"Error listing snapshots: {e}")
            return []
    
    def get_sensor_info(self) -> Dict[str, Any]:
        """
        Get sensor information.
        
        Returns:
            Sensor information dictionary
        """
        return {
            "sensor_type": self.sensor_type,
            "is_active": self.is_active,
            "snapshot_count": self.snapshot_count,
            "last_snapshot_id": self.last_snapshot_id,
            "config": self.config
        }
    
    def _count_elements(self, ui_tree: Dict[str, Any]) -> int:
        """
        Count elements in UI tree.
        
        Args:
            ui_tree: UI tree dictionary
            
        Returns:
            Element count
        """
        count = 1
        for child in ui_tree.get("children", []):
            count += self._count_elements(child)
        return count

# Compatibility functions for existing system
def create_ui2html_sensor(config: Optional[Dict[str, Any]] = None) -> UI2HTMLSensor:
    """
    Create a new UI2HTML sensor instance.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        UI2HTMLSensor instance
    """
    return UI2HTMLSensor(config)

def capture_ui_snapshot(metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Capture a UI snapshot using the default sensor.
    
    Args:
        metadata: Additional metadata
        
    Returns:
        Snapshot data
    """
    sensor = UI2HTMLSensor()
    sensor.start()
    snapshot = sensor.capture_snapshot(metadata)
    sensor.stop()
    return snapshot

def query_ui_memory(query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
    """
    Query UI memory by text.
    
    Args:
        query_text: Text to search for
        n_results: Number of results
        
    Returns:
        List of matching snapshots
    """
    sensor = UI2HTMLSensor()
    return sensor.query_memory(query_text, n_results) 