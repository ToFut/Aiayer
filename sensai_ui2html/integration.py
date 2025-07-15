#!/usr/bin/env python3
"""
Integration module for replacing existing screen sensors with UI2HTML
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

# Use absolute imports instead of relative
from ui2html_sensor import UI2HTMLSensor

logger = logging.getLogger(__name__)

class ScreenSensorReplacement:
    """
    Drop-in replacement for existing screen sensors.
    Provides the same interface but with enhanced capabilities.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the screen sensor replacement.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.sensor = UI2HTMLSensor(config)
        self.sensor_type = "ui2html_screen_sensor"
        self.is_active = False
        
        logger.info("Screen sensor replacement initialized")
    
    def start(self) -> bool:
        """Start the sensor."""
        try:
            self.is_active = self.sensor.start()
            return self.is_active
        except Exception as e:
            logger.error(f"Failed to start sensor: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop the sensor."""
        try:
            self.is_active = not self.sensor.stop()
            return not self.is_active
        except Exception as e:
            logger.error(f"Failed to stop sensor: {e}")
            return False
    
    def capture_screen(self, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Capture screen (UI) data.
        
        Args:
            metadata: Additional metadata
            
        Returns:
            Screen data dictionary
        """
        try:
            snapshot = self.sensor.capture_snapshot(metadata)
            
            # Convert to expected format
            screen_data = {
                "timestamp": datetime.now().isoformat(),
                "sensor_type": self.sensor_type,
                "ui_tree": snapshot.get("ui_tree", {}),
                "html_content": snapshot.get("html_content", ""),
                "element_count": snapshot.get("element_count", 0),
                "snapshot_id": snapshot.get("snapshot_id", ""),
                "metadata": metadata or {}
            }
            
            return screen_data
            
        except Exception as e:
            logger.error(f"Error capturing screen: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "sensor_type": self.sensor_type,
                "error": str(e),
                "ui_tree": {},
                "html_content": "",
                "element_count": 0
            }
    
    def get_sensor_info(self) -> Dict[str, Any]:
        """Get sensor information."""
        info = self.sensor.get_sensor_info()
        info["sensor_type"] = self.sensor_type
        info["is_active"] = self.is_active
        return info
    
    def query_ui_memory(self, query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Query UI memory by text.
        
        Args:
            query_text: Text to search for
            n_results: Number of results
            
        Returns:
            List of matching snapshots
        """
        return self.sensor.query_memory(query_text, n_results)

# Compatibility functions
def create_screen_sensor(config: Optional[Dict[str, Any]] = None) -> ScreenSensorReplacement:
    """
    Create a screen sensor replacement.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        ScreenSensorReplacement instance
    """
    return ScreenSensorReplacement(config)

def capture_screen(metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Capture screen data.
    
    Args:
        metadata: Additional metadata
        
    Returns:
        Screen data dictionary
    """
    sensor = ScreenSensorReplacement()
    sensor.start()
    data = sensor.capture_screen(metadata)
    sensor.stop()
    return data

# Export for easy import
__all__ = [
    "ScreenSensorReplacement",
    "create_screen_sensor", 
    "capture_screen"
] 