#!/usr/bin/env python3
"""
Enhanced Complete AI System with Proactive Task Identification
Integrates UI2HTML analysis with automatic task suggestion
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import sys
from pathlib import Path

# Add Aiayer to path
sys.path.insert(0, str(Path(__file__).parent.parent))

@dataclass
class ProactiveSuggestion:
    """Represents a proactive task suggestion"""
    id: str
    title: str
    description: str
    action_type: str
    confidence: float
    priority: int
    estimated_time: float
    category: str
    icon: str
    automation_steps: List[Dict[str, Any]]

class EnhancedCompleteAISystem:
    """Enhanced AI system with proactive task identification"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ui_detector = None
        self.smart_planner = None
        self.brain_router = None
        self.memory_manager = None
        self.proactive_identifier = None
        self.rpa_bridge = None
        self.stats = {
            'ui_analyses': 0,
            'proactive_suggestions': 0,
            'executions': 0,
            'memory_operations': 0,
            'avg_response_time': 0.0
        }
    
    async def initialize(self):
        """Initialize all system components"""
        try:
            self.logger.info("🤖 Enhanced Complete AI System initializing...")
            
            # Initialize UI understanding components
            await self._initialize_ui_components()
            
            # Initialize AI planning components
            await self._initialize_planning_components()
            
            # Initialize proactive task identifier
            await self._initialize_proactive_identifier()
            
            # Initialize RPA bridge
            await self._initialize_rpa_bridge()
            
            self.logger.info("✅ Enhanced Complete AI System initialized successfully!")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize enhanced system: {e}")
            raise
    
    async def _initialize_ui_components(self):
        """Initialize UI understanding components"""
        try:
            # Initialize neural UI detector
            from neural_ui_detector import NeuralUIDetector
            self.ui_detector = NeuralUIDetector()
            
            # Initialize UI2HTML sensor
            from sensai_ui2html import UI2HTMLSensor
            self.ui2html_sensor = UI2HTMLSensor()
            
            self.logger.info("📦 UI Understanding components initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize UI components: {e}")
    
    async def _initialize_planning_components(self):
        """Initialize AI planning components"""
        try:
            # Initialize smart planner
            from universal_smart_planner import UniversalSmartPlanner
            self.smart_planner = UniversalSmartPlanner()
            
            # Initialize brain router
            from brain.core.brain_router import get_brain_router
            self.brain_router = await get_brain_router()
            
            # Initialize memory manager
            from memory.task_memory_manager import initialize as init_memory
            self.memory_manager = await init_memory()
            
            self.logger.info("🧠 AI Planning components initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize planning components: {e}")
    
    async def _initialize_proactive_identifier(self):
        """Initialize proactive task identifier"""
        try:
            from proactive_task_identifier import initialize_proactive_identifier
            await initialize_proactive_identifier()
            
            # Import the proactive identifier
            from proactive_task_identifier import proactive_identifier
            self.proactive_identifier = proactive_identifier
            
            self.logger.info("🎯 Proactive Task Identifier initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize proactive identifier: {e}")
    
    async def _initialize_rpa_bridge(self):
        """Initialize RPA bridge"""
        try:
            from integration.rpa_ai_bridge import RPAAIBridge
            self.rpa_bridge = RPAAIBridge()
            await self.rpa_bridge.initialize()
            
            self.logger.info("🔗 RPA Bridge initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize RPA bridge: {e}")
    
    async def understand_ui_and_suggest_tasks(self) -> Dict[str, Any]:
        """Understand current UI and proactively suggest tasks"""
        start_time = time.time()
        
        try:
            self.logger.info("🔍 Starting UI understanding and proactive task identification...")
            
            # Step 1: Capture UI state
            ui_state = await self._capture_ui_state()
            
            # Step 2: Analyze UI with neural detector
            neural_analysis = await self._analyze_ui_neural()
            
            # Step 3: Extract UI2HTML data
            ui2html_data = await self._extract_ui2html_data()
            
            # Step 4: Identify proactive tasks
            proactive_tasks = await self._identify_proactive_tasks(ui2html_data)
            
            # Step 5: Combine all analyses
            comprehensive_analysis = {
                'ui_state': ui_state,
                'neural_analysis': neural_analysis,
                'ui2html_data': ui2html_data,
                'proactive_tasks': proactive_tasks,
                'timestamp': time.time(),
                'analysis_time': time.time() - start_time
            }
            
            # Step 6: Store in memory
            await self._store_analysis(comprehensive_analysis)
            
            # Update stats
            self.stats['ui_analyses'] += 1
            self.stats['proactive_suggestions'] += len(proactive_tasks)
            
            self.logger.info(f"✅ UI analysis complete: {len(proactive_tasks)} proactive tasks identified")
            
            return comprehensive_analysis
            
        except Exception as e:
            self.logger.error(f"Error in UI understanding: {e}")
            return {
                'error': str(e),
                'ui_state': {},
                'proactive_tasks': []
            }
    
    async def _capture_ui_state(self) -> Dict[str, Any]:
        """Capture current UI state"""
        try:
            # Get active applications
            active_apps = await self._get_active_applications()
            
            # Get current window info
            current_window = await self._get_current_window()
            
            return {
                'active_applications': active_apps,
                'current_window': current_window,
                'timestamp': time.time()
            }
            
        except Exception as e:
            self.logger.error(f"Error capturing UI state: {e}")
            return {}
    
    async def _analyze_ui_neural(self) -> Dict[str, Any]:
        """Analyze UI using neural detector"""
        try:
            if self.ui_detector:
                result = await self.ui_detector.detect_elements()
                return {
                    'elements': result.elements,
                    'confidence': result.confidence,
                    'processing_time': result.processing_time
                }
            else:
                return {'elements': [], 'confidence': 0.0, 'processing_time': 0.0}
                
        except Exception as e:
            self.logger.error(f"Error in neural UI analysis: {e}")
            return {'elements': [], 'confidence': 0.0, 'processing_time': 0.0}
    
    async def _extract_ui2html_data(self) -> Dict[str, Any]:
        """Extract UI2HTML data"""
        try:
            if self.ui2html_sensor:
                html_data = await self.ui2html_sensor.capture_ui_tree()
                return {
                    'html_tree': html_data,
                    'elements': html_data.get('elements', []),
                    'structure': html_data.get('structure', {})
                }
            else:
                return {'html_tree': {}, 'elements': [], 'structure': {}}
                
        except Exception as e:
            self.logger.error(f"Error extracting UI2HTML data: {e}")
            return {'html_tree': {}, 'elements': [], 'structure': {}}
    
    async def _identify_proactive_tasks(self, ui2html_data: Dict[str, Any]) -> List[ProactiveSuggestion]:
        """Identify proactive tasks from UI2HTML data"""
        try:
            if self.proactive_identifier:
                # Get task suggestions
                suggestions = await self.proactive_identifier.get_task_suggestions(ui2html_data)
                
                # Convert to ProactiveSuggestion objects
                proactive_tasks = []
                for suggestion in suggestions:
                    task = ProactiveSuggestion(
                        id=suggestion['id'],
                        title=suggestion['title'],
                        description=suggestion['title'],
                        action_type=suggestion['action'],
                        confidence=suggestion['confidence'],
                        priority=suggestion['priority'],
                        estimated_time=suggestion['estimated_time'],
                        category=suggestion['category'],
                        icon=suggestion['icon'],
                        automation_steps=[{
                            'action': suggestion['action'],
                            'target': 'ui_element',
                            'type': suggestion['category']
                        }]
                    )
                    proactive_tasks.append(task)
                
                return proactive_tasks
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"Error identifying proactive tasks: {e}")
            return []
    
    async def _get_active_applications(self) -> List[Dict[str, Any]]:
        """Get list of active applications"""
        try:
            # Use RPA bridge to get active apps
            if self.rpa_bridge:
                apps = await self.rpa_bridge.get_active_applications()
                return apps
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting active applications: {e}")
            return []
    
    async def _get_current_window(self) -> Dict[str, Any]:
        """Get current window information"""
        try:
            # Use RPA bridge to get current window
            if self.rpa_bridge:
                window = await self.rpa_bridge.get_current_window()
                return window
            else:
                return {}
                
        except Exception as e:
            self.logger.error(f"Error getting current window: {e}")
            return {}
    
    async def _store_analysis(self, analysis: Dict[str, Any]):
        """Store analysis results in memory"""
        try:
            if self.memory_manager:
                await self.memory_manager.store_ui_analysis(analysis)
                self.stats['memory_operations'] += 1
                
        except Exception as e:
            self.logger.error(f"Error storing analysis: {e}")
    
    async def execute_proactive_task(self, task: ProactiveSuggestion) -> Dict[str, Any]:
        """Execute a proactive task"""
        start_time = time.time()
        
        try:
            self.logger.info(f"⚡ Executing proactive task: {task.title}")
            
            # Create execution plan
            plan = await self.smart_planner.create_universal_plan(
                task.description, 
                f"proactive_{task.id}"
            )
            
            # Execute via RPA bridge
            if self.rpa_bridge:
                result = await self.rpa_bridge.execute_automation_plan(plan)
            else:
                result = {'success': False, 'error': 'RPA bridge not available'}
            
            # Store execution result
            execution_result = {
                'task_id': task.id,
                'task_title': task.title,
                'success': result.get('success', False),
                'execution_time': time.time() - start_time,
                'result_message': result.get('message', ''),
                'timestamp': time.time()
            }
            
            # Store in memory
            if self.memory_manager:
                await self.memory_manager.store_execution_result(execution_result)
            
            # Update stats
            self.stats['executions'] += 1
            
            self.logger.info(f"✅ Task execution completed: {execution_result['success']}")
            
            return execution_result
            
        except Exception as e:
            self.logger.error(f"Error executing proactive task: {e}")
            return {
                'task_id': task.id,
                'success': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    async def get_proactive_dashboard(self) -> Dict[str, Any]:
        """Get proactive task dashboard data"""
        try:
            # Get latest UI analysis
            analysis = await self.understand_ui_and_suggest_tasks()
            
            # Get recent executions
            recent_executions = []
            if self.memory_manager:
                recent_executions = await self.memory_manager.get_recent_executions(limit=10)
            
            # Get system stats
            system_stats = self.get_system_stats()
            
            return {
                'current_ui': analysis.get('ui_state', {}),
                'proactive_tasks': analysis.get('proactive_tasks', []),
                'recent_executions': recent_executions,
                'system_stats': system_stats,
                'last_analysis': analysis.get('timestamp', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting proactive dashboard: {e}")
            return {
                'current_ui': {},
                'proactive_tasks': [],
                'recent_executions': [],
                'system_stats': self.get_system_stats(),
                'last_analysis': 0
            }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system performance statistics"""
        return {
            'ui_analyses': self.stats['ui_analyses'],
            'proactive_suggestions': self.stats['proactive_suggestions'],
            'executions': self.stats['executions'],
            'memory_operations': self.stats['memory_operations'],
            'avg_response_time': self.stats['avg_response_time']
        }

# Global instance
enhanced_system = EnhancedCompleteAISystem()

async def initialize_enhanced_system():
    """Initialize the enhanced complete AI system"""
    await enhanced_system.initialize()

async def get_proactive_analysis():
    """Get proactive UI analysis and task suggestions"""
    return await enhanced_system.understand_ui_and_suggest_tasks()

async def execute_proactive_task(task: ProactiveSuggestion):
    """Execute a proactive task"""
    return await enhanced_system.execute_proactive_task(task)

async def get_proactive_dashboard():
    """Get proactive task dashboard"""
    return await enhanced_system.get_proactive_dashboard() 