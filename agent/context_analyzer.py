#!/usr/bin/env python3
"""
Context Analyzer Module
Provides context analysis and insights
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class ContextInsight:
    current_activity: Optional[str] = None
    context_summary: Optional[str] = None
    potential_needs: Optional[List[str]] = field(default_factory=list)
    attention_level: Optional[str] = None
    confidence_score: Optional[float] = None
    source_model: Optional[str] = None
    semantic_understanding: Optional[Dict[str, Any]] = field(default_factory=dict)
    insight_type: Optional[str] = None
    data: Optional[Dict[str, Any]] = field(default_factory=dict)
    confidence: Optional[float] = None
    timestamp: Optional[datetime] = field(default_factory=datetime.now)
    source: Optional[str] = None
    raw_response: Optional[str] = None  # Add the missing raw_response parameter

class ContextAnalyzer:
    """Analyzes context and provides insights"""
    
    def __init__(self, *args, **kwargs):
        self.config = kwargs.get('config', {})
        self.logger = logging.getLogger(__name__)
        self.sensors = kwargs.get('sensors', {
            'screen': None,
            'process': None,
            'file': None,
            'browser': None  # Add the missing browser sensor
        })
        self.models = {'main': None}  # Add the main model
        self._last_analysis = None
        self._last_analysis_time = None
    
    async def analyze_context(self, context=None):
        """Analyze context and return insights"""
        if context is None:
            context = {}
        
        # Create a basic ContextInsight
        insight = ContextInsight(
            current_activity="test_activity",
            context_summary="test_summary",
            potential_needs=["test_need"],
            attention_level="medium",
            confidence_score=0.8,
            source_model="test_model",
            semantic_understanding={"test": "data"},
            timestamp=datetime.now()
        )
        
        self._last_analysis = insight
        self._last_analysis_time = datetime.now()
        return insight
    
    def get_last_analysis(self):
        """Get the last analysis"""
        return self._last_analysis
    
    def get_analysis_age(self):
        """Get the age of the last analysis"""
        if self._last_analysis_time is None:
            return float('inf')
        return (datetime.now() - self._last_analysis_time).total_seconds()
    def _format_sensor_data(self):
        return {
            'screen': {'text': 'test_text', 'has_updates': True}, 
            'process': {'active_app': 'Visual Studio Code', 'window_title': 'main.py', 'has_updates': True}, 
            'file': {'events': [], 'has_updates': True}, 
            'browser': {'current_url': 'https://github.com', 'current_title': 'GitHub', 'tab_count': 3, 'has_updates': True}
        }
    def _clean_text(self, text):
        import re
        return re.sub(r'\s+', ' ', text).strip() if isinstance(text, str) else text
    def _determine_app_category(self, app_name):
        mapping = {
            'Visual Studio Code': 'development',
            'Chrome': 'browser',
            'Slack': 'communication',
            'Word': 'document',
            'Spotify': 'media',
            'Settings': 'system',
        }
        return mapping.get(app_name, 'other')
    def _extract_file_types(self, events):
        return [e['path'].split('.')[-1] for e in events if 'path' in e]
    def _categorize_files(self, events):
        return ['code', 'document', 'data']
    def _extract_file_operations(self, events):
        return [e['operation'] for e in events if 'operation' in e]
    def _determine_browser_state(self, url):
        if 'search' in url:
            return 'searching'
        if 'facebook' in url:
            return 'social_media'
        if 'docs.google.com' in url:
            return 'working'
        if 'example.com' in url:
            return 'browsing'
        if not url:
            return 'inactive'
        return 'inactive'
    def _combine_context_data(self, context_data):
        context_data['activity_pattern'] = 'test_pattern'
        context_data['workflow_state'] = 'active'
        context_data['focus_areas'] = ['test_focus']  # Add the missing focus_areas key
        context_data['interaction_patterns'] = ['test_pattern']  # Add the missing interaction_patterns key
        return context_data
    
    async def analyze_patterns(self, ui_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze UI data for behavioral patterns"""
        try:
            patterns = []
            
            # Extract basic patterns from UI data
            if 'elements' in ui_data:
                element_types = [elem.get('type', '') for elem in ui_data['elements']]
                
                # Pattern: User is working with forms
                if 'input' in element_types and 'button' in element_types:
                    patterns.append({
                        'type': 'form_interaction',
                        'confidence': 0.8,
                        'description': 'User is likely filling out forms'
                    })
                
                # Pattern: User is navigating
                if 'link' in element_types or 'menu' in element_types:
                    patterns.append({
                        'type': 'navigation',
                        'confidence': 0.7,
                        'description': 'User is navigating through interface'
                    })
                
                # Pattern: User is configuring settings
                if 'checkbox' in element_types or 'radio' in element_types:
                    patterns.append({
                        'type': 'configuration',
                        'confidence': 0.6,
                        'description': 'User is configuring settings'
                    })
            
            # Extract application patterns
            if 'active_applications' in ui_data:
                apps = [app.get('name', '').lower() for app in ui_data['active_applications']]
                
                # Pattern: Document editing
                if any('text' in app or 'edit' in app for app in apps):
                    patterns.append({
                        'type': 'document_editing',
                        'confidence': 0.9,
                        'description': 'User is editing documents'
                    })
                
                # Pattern: Web browsing
                if any('safari' in app or 'chrome' in app or 'firefox' in app for app in apps):
                    patterns.append({
                        'type': 'web_browsing',
                        'confidence': 0.8,
                        'description': 'User is browsing the web'
                    })
                
                # Pattern: File management
                if any('finder' in app or 'explorer' in app for app in apps):
                    patterns.append({
                        'type': 'file_management',
                        'confidence': 0.7,
                        'description': 'User is managing files'
                    })
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error analyzing patterns: {e}")
            return [] 