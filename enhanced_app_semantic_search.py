#!/usr/bin/env python3
"""
Enhanced App-Specific Semantic Search
Improved semantic search specifically for application-related queries
"""

import json
import re
import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedAppSemanticSearch:
    def __init__(self, memory_file: str = None):
        self.memory_file = memory_file or "/Users/segevbin/Desktop/SensAI/Aiayer/memory/memory_state.json"
        self.app_query_patterns = [
            # Direct app queries
            r'\b(?:what|which|list)\s+(?:apps?|applications?)\s+(?:are|is)?\s*(?:open|running|active|launched|opened)\b',
            r'\b(?:apps?|applications?)\s+(?:are|is)?\s*(?:open|running|active|launched|opened)\b',
            r'\bopen\s+(?:apps?|applications?)\b',
            r'\brunning\s+(?:apps?|applications?)\b',
            r'\bactive\s+(?:apps?|applications?)\b',
            
            # Specific app queries
            r'\bis\s+(\w+)\s+(?:open|running|active|launched|opened)\b',
            r'\b(\w+)\s+(?:open|running|active|launched|opened)\b\s*\?',
            r'\bdo\s+i\s+have\s+(\w+)\s+(?:open|running)\b',
            
            # General system queries
            r'\bwhat\s+(?:am\s+i\s+)?(?:seeing|viewing|looking\s+at)\s+(?:on\s+)?(?:my\s+)?(?:pc|computer|screen)\b',
            r'\bwhat\'?s\s+(?:on\s+)?(?:my\s+)?(?:pc|computer|screen)\b',
            r'\bwhat\'?s\s+(?:opened?|running|active)\s+(?:in|on)\s+(?:my\s+)?(?:pc|computer|system|machine)\b',
            r'\bcurrent\s+(?:apps?|applications?|programs?)\b'
        ]
        
        # Common app name variations
        self.app_aliases = {
            'spotify': ['spotify', 'music'],
            'chrome': ['chrome', 'google chrome', 'browser'],
            'safari': ['safari', 'browser'],
            'cursor': ['cursor', 'code editor', 'editor'],
            'firefox': ['firefox', 'browser'],
            'vs code': ['vscode', 'visual studio code', 'code'],
            'terminal': ['terminal', 'command line', 'shell'],
            'finder': ['finder', 'file manager']
        }
        
    def is_app_related_query(self, query: str) -> bool:
        """Check if the query is asking about applications"""
        query_lower = query.lower().strip()
        
        for pattern in self.app_query_patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                logger.info(f"App query detected with pattern: {pattern}")
                return True
        
        return False
    
    def extract_specific_app_query(self, query: str) -> str:
        """Extract specific app name from query"""
        query_lower = query.lower().strip()
        
        # Look for specific app name patterns
        specific_patterns = [
            r'\bis\s+(\w+)\s+(?:open|running|active|launched|opened)\b',
            r'\b(\w+)\s+(?:open|running|active|launched|opened)\b\s*\?',
            r'\bdo\s+i\s+have\s+(\w+)\s+(?:open|running)\b'
        ]
        
        for pattern in specific_patterns:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                app_name = match.group(1)
                logger.info(f"Specific app query detected: {app_name}")
                return app_name
                
        return None
    
    def get_current_apps_from_memory(self) -> Dict[str, Any]:
        """Extract current applications from memory"""
        try:
            with open(self.memory_file, 'r') as f:
                memory_data = json.load(f)
            
            current_apps = []
            app_details = {}
            
            # Look in short_term memory for current applications
            if 'short_term' in memory_data and memory_data['short_term']:
                latest_entry = memory_data['short_term'][0]  # Most recent entry
                
                if 'user_activity' in latest_entry and 'current_applications' in latest_entry['user_activity']:
                    current_apps = latest_entry['user_activity']['current_applications']
                    
                    # Get additional context
                    app_details = {
                        'primary_app': latest_entry['user_activity'].get('application_used', 'Unknown'),
                        'primary_activity': latest_entry['user_activity'].get('primary_activity', 'Unknown'),
                        'productivity_score': latest_entry['user_activity'].get('productivity_score', 0),
                        'system_metrics': latest_entry['user_activity'].get('system_metrics', {}),
                        'workflow_stage': latest_entry.get('context_analysis', {}).get('workflow_stage', 'Unknown'),
                        'timestamp': latest_entry.get('timestamp', 'Unknown')
                    }
            
            logger.info(f"Retrieved {len(current_apps)} apps from memory")
            
            return {
                'apps': current_apps,
                'details': app_details,
                'total_count': len(current_apps)
            }
            
        except Exception as e:
            logger.error(f"Error reading memory file: {e}")
            return {'apps': [], 'details': {}, 'total_count': 0}
    
    def check_specific_app_status(self, app_name: str, current_apps: List[str]) -> Dict[str, Any]:
        """Check if a specific app is running"""
        app_name_lower = app_name.lower()
        
        # Check direct match
        for app in current_apps:
            if app_name_lower in app.lower():
                return {
                    'found': True,
                    'exact_name': app,
                    'status': 'running'
                }
        
        # Check aliases
        for canonical_name, aliases in self.app_aliases.items():
            if app_name_lower in aliases:
                for app in current_apps:
                    if canonical_name.lower() in app.lower():
                        return {
                            'found': True,
                            'exact_name': app,
                            'canonical_name': canonical_name,
                            'status': 'running'
                        }
        
        return {
            'found': False,
            'status': 'not_running'
        }
    
    def generate_app_response_context(self, query: str) -> str:
        """Generate enhanced context for app-related queries"""
        is_app_query = self.is_app_related_query(query)
        
        if not is_app_query:
            return ""
        
        app_data = self.get_current_apps_from_memory()
        current_apps = app_data['apps']
        details = app_data['details']
        
        if not current_apps:
            return "CURRENT APPS: No application data available in memory."
        
        # Check for specific app query
        specific_app = self.extract_specific_app_query(query)
        
        if specific_app:
            app_status = self.check_specific_app_status(specific_app, current_apps)
            
            if app_status['found']:
                return f"""SPECIFIC APP STATUS: {specific_app.title()} is CURRENTLY RUNNING as '{app_status['exact_name']}'.

COMPLETE APP LIST: {', '.join(current_apps)}
PRIMARY APP: {details.get('primary_app', 'Unknown')}
ACTIVITY: {details.get('primary_activity', 'Unknown')}
TOTAL APPS: {len(current_apps)}"""
            else:
                return f"""SPECIFIC APP STATUS: {specific_app.title()} is NOT currently running.

CURRENT RUNNING APPS: {', '.join(current_apps)}
TOTAL APPS: {len(current_apps)}"""
        else:
            # General app list query
            # Format apps in a clear list
            app_list = []
            for i, app in enumerate(current_apps, 1):
                if app == details.get('primary_app'):
                    app_list.append(f"{i}. {app} (PRIMARY)")
                else:
                    app_list.append(f"{i}. {app}")
            
            app_list_str = '\n'.join(app_list)
            
            return f"""CURRENT APPLICATIONS ({len(current_apps)} total):

{app_list_str}

PRIMARY APP: {details.get('primary_app', 'Unknown')}
ACTIVITY: {details.get('primary_activity', 'Unknown')} ({details.get('workflow_stage', 'unknown')} stage)
PRODUCTIVITY: {details.get('productivity_score', 0):.1f}/1.0
CPU: {details.get('system_metrics', {}).get('cpu_percent', 0):.1f}%
MEMORY: {details.get('system_metrics', {}).get('memory_percent', 0):.1f}%
LAST UPDATE: {details.get('timestamp', 'Unknown')}"""

# Test function
def test_app_semantic_search():
    """Test the enhanced app semantic search"""
    search = EnhancedAppSemanticSearch()
    
    test_queries = [
        "what apps are open?",
        "what applications are running?",
        "is spotify opened?",
        "is chrome running?",
        "what am i seeing in my PC?",
        "current apps",
        "list open applications"
    ]
    
    print("Testing Enhanced App Semantic Search:")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        is_app_query = search.is_app_related_query(query)
        print(f"Is app query: {is_app_query}")
        
        if is_app_query:
            context = search.generate_app_response_context(query)
            print(f"Generated context:\n{context}")
        
        print("-" * 40)

if __name__ == "__main__":
    test_app_semantic_search()