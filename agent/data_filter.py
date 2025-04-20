"""
Data Filter Module
Provides data filtering and preprocessing capabilities for the task agent.
"""
import logging
from typing import Dict, List, Any, Optional
import re

class DataFilter:
    """
    Handles data filtering and preprocessing for the task agent.
    """
    
    def __init__(self, load_sensitive_patterns=False, enable_ml_detection=False):
        """
        Initialize the data filter.
        
        Args:
            load_sensitive_patterns (bool): Flag to load sensitive patterns from config file
            enable_ml_detection (bool): Flag to enable machine learning detection
        """
        self.logger = logging.getLogger(__name__)
        self.load_sensitive_patterns = load_sensitive_patterns
        self.enable_ml_detection = enable_ml_detection
        
    def filter_sensor_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter and preprocess sensor data.
        
        Args:
            data: Raw sensor data dictionary
            
        Returns:
            Filtered and preprocessed data dictionary
        """
        filtered_data = {}
        
        try:
            # Filter screen data
            if 'screen' in data:
                filtered_data['screen'] = self._filter_screen_data(data['screen'])
                
            # Filter process data
            if 'process' in data:
                filtered_data['process'] = self._filter_process_data(data['process'])
                
            # Filter file data
            if 'file' in data:
                filtered_data['file'] = self._filter_file_data(data['file'])
                
        except Exception as e:
            self.logger.error(f"Error filtering sensor data: {e}")
            
        return filtered_data
        
    def _filter_screen_data(self, screen_data: Dict) -> Dict:
        """Filter and preprocess screen data."""
        filtered = {}
        
        if 'text' in screen_data:
            # Clean and normalize text
            filtered['text'] = self._clean_text(screen_data['text'])
            
        if 'has_images' in screen_data:
            filtered['has_images'] = screen_data['has_images']
            
        if 'has_videos' in screen_data:
            filtered['has_videos'] = screen_data['has_videos']
            
        return filtered
        
    def _filter_process_data(self, process_data: Dict) -> Dict:
        """Filter and preprocess process data."""
        filtered = {}
        
        if 'active_app' in process_data:
            filtered['active_app'] = self._clean_text(process_data['active_app'])
            
        if 'active_window_title' in process_data:
            filtered['active_window_title'] = self._clean_text(process_data['active_window_title'])
            
        if 'running_apps' in process_data:
            filtered['running_apps'] = [self._clean_text(app) for app in process_data['running_apps']]
            
        return filtered
        
    def _filter_file_data(self, file_data: Dict) -> Dict:
        """Filter and preprocess file data."""
        filtered = {}
        
        if 'recent_files' in file_data:
            filtered['recent_files'] = [
                self._clean_file_path(file) for file in file_data['recent_files']
            ]
            
        if 'file_types' in file_data:
            filtered['file_types'] = list(set(file_data['file_types']))
            
        return filtered
        
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
            
        # Remove special characters and normalize spaces
        text = re.sub(r'[^\w\s.,!?-]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
        
    def _clean_file_path(self, path: str) -> str:
        """Clean and normalize file path."""
        if not path:
            return ""
            
        # Normalize path separators
        path = path.replace('\\', '/')
        
        # Remove any leading/trailing whitespace
        path = path.strip()
        
        return path 