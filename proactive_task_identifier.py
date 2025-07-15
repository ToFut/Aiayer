#!/usr/bin/env python3
"""
Proactive Task Identifier
Automatically identifies potential tasks from UI2HTML analysis
without waiting for user input
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path
import sys

# Add Aiayer to path
sys.path.insert(0, str(Path(__file__).parent))

@dataclass
class ProactiveTask:
    """Represents a proactively identified task"""
    task_id: str
    description: str
    action_type: str
    target_element: Optional[str]
    confidence: float
    priority: int  # 1-5, 5 being highest
    estimated_time: float
    context: Dict[str, Any]
    automation_steps: List[Dict[str, Any]]

class ProactiveTaskIdentifier:
    """Identifies potential tasks from UI2HTML analysis"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.task_patterns = self._load_task_patterns()
        self.context_analyzer = None
        self.memory_manager = None
        
    def _load_task_patterns(self) -> Dict[str, List[Dict]]:
        """Load patterns for identifying potential tasks"""
        return {
            "navigation": [
                {"pattern": "menu", "actions": ["click", "navigate"], "priority": 3},
                {"pattern": "button", "actions": ["click", "activate"], "priority": 4},
                {"pattern": "link", "actions": ["click", "navigate"], "priority": 3},
                {"pattern": "tab", "actions": ["switch", "navigate"], "priority": 3},
            ],
            "input": [
                {"pattern": "input", "actions": ["type", "fill"], "priority": 4},
                {"pattern": "textarea", "actions": ["type", "fill"], "priority": 4},
                {"pattern": "search", "actions": ["search", "query"], "priority": 5},
                {"pattern": "form", "actions": ["submit", "fill"], "priority": 4},
            ],
            "interaction": [
                {"pattern": "checkbox", "actions": ["toggle", "check"], "priority": 3},
                {"pattern": "radio", "actions": ["select", "choose"], "priority": 3},
                {"pattern": "dropdown", "actions": ["select", "choose"], "priority": 3},
                {"pattern": "slider", "actions": ["adjust", "set"], "priority": 2},
            ],
            "file_operations": [
                {"pattern": "file", "actions": ["open", "save", "upload"], "priority": 4},
                {"pattern": "folder", "actions": ["browse", "navigate"], "priority": 3},
                {"pattern": "download", "actions": ["download", "save"], "priority": 4},
            ],
            "system": [
                {"pattern": "close", "actions": ["close", "exit"], "priority": 2},
                {"pattern": "minimize", "actions": ["minimize", "hide"], "priority": 1},
                {"pattern": "maximize", "actions": ["maximize", "expand"], "priority": 1},
                {"pattern": "settings", "actions": ["configure", "setup"], "priority": 3},
            ]
        }
    
    async def initialize(self):
        """Initialize the proactive task identifier"""
        try:
            # Initialize context analyzer
            from agent.context_analyzer import ContextAnalyzer
            self.context_analyzer = ContextAnalyzer()
            
            # Initialize memory manager
            from memory.task_memory_manager import initialize as init_memory
            self.memory_manager = await init_memory()
            
            self.logger.info("Proactive Task Identifier initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize: {e}")
    
    async def identify_proactive_tasks(self, ui_html_data: Dict[str, Any]) -> List[ProactiveTask]:
        """Identify potential tasks from UI2HTML analysis"""
        try:
            self.logger.info("🔍 Analyzing UI for proactive tasks...")
            
            tasks = []
            
            # Extract UI elements from HTML data
            ui_elements = self._extract_ui_elements(ui_html_data)
            
            # Analyze context and current state
            context = await self._analyze_context(ui_html_data)
            
            # Identify tasks by element type
            element_tasks = await self._identify_element_tasks(ui_elements, context)
            tasks.extend(element_tasks)
            
            # Identify tasks by application context
            app_tasks = await self._identify_application_tasks(ui_html_data, context)
            tasks.extend(app_tasks)
            
            # Identify tasks by user behavior patterns
            behavior_tasks = await self._identify_behavior_tasks(context)
            tasks.extend(behavior_tasks)
            
            # Identify tasks by system state
            system_tasks = await self._identify_system_tasks(ui_html_data, context)
            tasks.extend(system_tasks)
            
            # Sort by priority and confidence
            tasks.sort(key=lambda x: (x.priority, x.confidence), reverse=True)
            
            # Limit to top tasks
            top_tasks = tasks[:10]
            
            self.logger.info(f"🎯 Identified {len(top_tasks)} proactive tasks")
            
            return top_tasks
            
        except Exception as e:
            self.logger.error(f"Error identifying proactive tasks: {e}")
            return []
    
    def _extract_ui_elements(self, ui_html_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract UI elements from HTML data"""
        elements = []
        
        try:
            # Extract from different possible data structures
            if 'elements' in ui_html_data:
                elements = ui_html_data['elements']
            elif 'ui_elements' in ui_html_data:
                elements = ui_html_data['ui_elements']
            elif 'nodes' in ui_html_data:
                elements = ui_html_data['nodes']
            else:
                # Try to parse as HTML
                elements = self._parse_html_elements(ui_html_data)
                
        except Exception as e:
            self.logger.error(f"Error extracting UI elements: {e}")
            
        return elements
    
    def _parse_html_elements(self, html_data: Any) -> List[Dict[str, Any]]:
        """Parse HTML data to extract UI elements"""
        elements = []
        
        try:
            if isinstance(html_data, str):
                # Parse HTML string
                import re
                
                # Find common UI element patterns
                patterns = {
                    'button': r'<button[^>]*>(.*?)</button>',
                    'input': r'<input[^>]*>',
                    'link': r'<a[^>]*>(.*?)</a>',
                    'div': r'<div[^>]*>(.*?)</div>',
                    'span': r'<span[^>]*>(.*?)</span>',
                }
                
                for element_type, pattern in patterns.items():
                    matches = re.findall(pattern, html_data, re.IGNORECASE | re.DOTALL)
                    for match in matches:
                        elements.append({
                            'type': element_type,
                            'text': match.strip() if isinstance(match, str) else '',
                            'attributes': self._extract_attributes(match)
                        })
                        
        except Exception as e:
            self.logger.error(f"Error parsing HTML elements: {e}")
            
        return elements
    
    def _extract_attributes(self, element_text: str) -> Dict[str, str]:
        """Extract attributes from HTML element"""
        attributes = {}
        try:
            import re
            attr_pattern = r'(\w+)=["\']([^"\']*)["\']'
            matches = re.findall(attr_pattern, element_text)
            for name, value in matches:
                attributes[name] = value
        except Exception:
            pass
        return attributes
    
    async def _analyze_context(self, ui_html_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze current context and state"""
        context = {
            'active_applications': [],
            'current_window': None,
            'user_activity': 'idle',
            'system_state': 'normal',
            'recent_actions': [],
            'common_patterns': []
        }
        
        try:
            # Extract application information
            if 'active_applications' in ui_html_data:
                context['active_applications'] = ui_html_data['active_applications']
            
            # Get recent actions from memory
            if self.memory_manager:
                recent = await self.memory_manager.get_recent_actions(limit=5)
                context['recent_actions'] = recent
            
            # Analyze user behavior patterns
            if self.context_analyzer:
                patterns = await self.context_analyzer.analyze_patterns(ui_html_data)
                context['common_patterns'] = patterns
                
        except Exception as e:
            self.logger.error(f"Error analyzing context: {e}")
            
        return context
    
    async def _identify_element_tasks(self, elements: List[Dict], context: Dict) -> List[ProactiveTask]:
        """Identify tasks based on UI elements"""
        tasks = []
        
        for element in elements:
            element_type = element.get('type', '').lower()
            element_text = element.get('text', '').lower()
            
            # Check against task patterns
            for category, patterns in self.task_patterns.items():
                for pattern in patterns:
                    if (pattern['pattern'] in element_type or 
                        pattern['pattern'] in element_text):
                        
                        for action in pattern['actions']:
                            task = ProactiveTask(
                                task_id=f"{action}_{element_type}_{len(tasks)}",
                                description=f"{action.title()} {element_text or element_type}",
                                action_type=action,
                                target_element=element_text or element_type,
                                confidence=0.7,
                                priority=pattern['priority'],
                                estimated_time=1.0,
                                context=context,
                                automation_steps=[{
                                    'action': action,
                                    'target': element_text or element_type,
                                    'type': element_type
                                }]
                            )
                            tasks.append(task)
        
        return tasks
    
    async def _identify_application_tasks(self, ui_html_data: Dict, context: Dict) -> List[ProactiveTask]:
        """Identify tasks based on application context"""
        tasks = []
        
        try:
            active_apps = context.get('active_applications', [])
            
            for app in active_apps:
                app_name = app.get('name', '').lower()
                
                # Application-specific task patterns
                app_tasks = {
                    'calculator': [
                        {'action': 'calculate', 'description': 'Perform calculation', 'priority': 4},
                        {'action': 'clear', 'description': 'Clear calculator', 'priority': 2},
                    ],
                    'textedit': [
                        {'action': 'type', 'description': 'Type text', 'priority': 4},
                        {'action': 'save', 'description': 'Save document', 'priority': 3},
                        {'action': 'format', 'description': 'Format text', 'priority': 3},
                    ],
                    'safari': [
                        {'action': 'navigate', 'description': 'Navigate to website', 'priority': 4},
                        {'action': 'search', 'description': 'Search web', 'priority': 4},
                        {'action': 'bookmark', 'description': 'Bookmark page', 'priority': 2},
                    ],
                    'finder': [
                        {'action': 'browse', 'description': 'Browse files', 'priority': 3},
                        {'action': 'search', 'description': 'Search files', 'priority': 4},
                        {'action': 'organize', 'description': 'Organize files', 'priority': 3},
                    ]
                }
                
                for app_pattern, app_task_list in app_tasks.items():
                    if app_pattern in app_name:
                        for task_info in app_task_list:
                            task = ProactiveTask(
                                task_id=f"{task_info['action']}_{app_name}_{len(tasks)}",
                                description=task_info['description'],
                                action_type=task_info['action'],
                                target_element=app_name,
                                confidence=0.8,
                                priority=task_info['priority'],
                                estimated_time=2.0,
                                context=context,
                                automation_steps=[{
                                    'action': task_info['action'],
                                    'target': app_name,
                                    'type': 'application'
                                }]
                            )
                            tasks.append(task)
                            
        except Exception as e:
            self.logger.error(f"Error identifying application tasks: {e}")
            
        return tasks
    
    async def _identify_behavior_tasks(self, context: Dict) -> List[ProactiveTask]:
        """Identify tasks based on user behavior patterns"""
        tasks = []
        
        try:
            recent_actions = context.get('recent_actions', [])
            common_patterns = context.get('common_patterns', [])
            
            # Analyze patterns and suggest related tasks
            if recent_actions:
                last_action = recent_actions[0]
                
                # Suggest follow-up actions
                follow_up_tasks = {
                    'open': [
                        {'action': 'interact', 'description': 'Interact with opened application', 'priority': 4},
                        {'action': 'configure', 'description': 'Configure application settings', 'priority': 3},
                    ],
                    'type': [
                        {'action': 'save', 'description': 'Save typed content', 'priority': 4},
                        {'action': 'format', 'description': 'Format content', 'priority': 3},
                    ],
                    'search': [
                        {'action': 'filter', 'description': 'Filter search results', 'priority': 3},
                        {'action': 'sort', 'description': 'Sort results', 'priority': 3},
                    ]
                }
                
                for action_type, suggestions in follow_up_tasks.items():
                    if action_type in last_action.get('action', '').lower():
                        for suggestion in suggestions:
                            task = ProactiveTask(
                                task_id=f"followup_{suggestion['action']}_{len(tasks)}",
                                description=suggestion['description'],
                                action_type=suggestion['action'],
                                target_element=None,
                                confidence=0.6,
                                priority=suggestion['priority'],
                                estimated_time=1.5,
                                context=context,
                                automation_steps=[{
                                    'action': suggestion['action'],
                                    'target': 'current_context',
                                    'type': 'followup'
                                }]
                            )
                            tasks.append(task)
                            
        except Exception as e:
            self.logger.error(f"Error identifying behavior tasks: {e}")
            
        return tasks
    
    async def _identify_system_tasks(self, ui_html_data: Dict, context: Dict) -> List[ProactiveTask]:
        """Identify system-level tasks"""
        tasks = []
        
        try:
            # System maintenance tasks
            system_tasks = [
                {'action': 'screenshot', 'description': 'Take screenshot', 'priority': 2},
                {'action': 'cleanup', 'description': 'Clean up temporary files', 'priority': 1},
                {'action': 'organize', 'description': 'Organize desktop', 'priority': 2},
                {'action': 'backup', 'description': 'Create backup', 'priority': 1},
            ]
            
            for task_info in system_tasks:
                task = ProactiveTask(
                    task_id=f"system_{task_info['action']}_{len(tasks)}",
                    description=task_info['description'],
                    action_type=task_info['action'],
                    target_element='system',
                    confidence=0.5,
                    priority=task_info['priority'],
                    estimated_time=3.0,
                    context=context,
                    automation_steps=[{
                        'action': task_info['action'],
                        'target': 'system',
                        'type': 'system'
                    }]
                )
                tasks.append(task)
                
        except Exception as e:
            self.logger.error(f"Error identifying system tasks: {e}")
            
        return tasks
    
    async def get_task_suggestions(self, ui_html_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get formatted task suggestions for display"""
        tasks = await self.identify_proactive_tasks(ui_html_data)
        
        suggestions = []
        for task in tasks:
            suggestions.append({
                'id': task.task_id,
                'title': task.description,
                'action': task.action_type,
                'confidence': task.confidence,
                'priority': task.priority,
                'estimated_time': task.estimated_time,
                'category': self._categorize_task(task),
                'icon': self._get_task_icon(task)
            })
        
        return suggestions
    
    def _categorize_task(self, task: ProactiveTask) -> str:
        """Categorize task for better organization"""
        if task.action_type in ['click', 'navigate', 'switch']:
            return 'navigation'
        elif task.action_type in ['type', 'fill', 'search']:
            return 'input'
        elif task.action_type in ['toggle', 'select', 'adjust']:
            return 'interaction'
        elif task.action_type in ['open', 'save', 'upload']:
            return 'file_operations'
        else:
            return 'system'
    
    def _get_task_icon(self, task: ProactiveTask) -> str:
        """Get appropriate icon for task"""
        icons = {
            'navigation': '🔄',
            'input': '⌨️',
            'interaction': '👆',
            'file_operations': '📁',
            'system': '⚙️'
        }
        return icons.get(self._categorize_task(task), '🎯')

# Global instance
proactive_identifier = ProactiveTaskIdentifier()

async def initialize_proactive_identifier():
    """Initialize the proactive task identifier"""
    await proactive_identifier.initialize()

async def identify_proactive_tasks(ui_html_data: Dict[str, Any]) -> List[ProactiveTask]:
    """Identify proactive tasks from UI2HTML data"""
    return await proactive_identifier.identify_proactive_tasks(ui_html_data)

async def get_task_suggestions(ui_html_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get formatted task suggestions"""
    return await proactive_identifier.get_task_suggestions(ui_html_data) 