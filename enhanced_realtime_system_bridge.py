#!/usr/bin/env python3
"""
Enhanced Real-time System Bridge
===============================

This module bridges the new efficient OS-integrated system components with the existing
SensAI enterprise backend, replacing the inefficient PIL screen capture approach with
true system integration.

Key Philosophy Change:
- FROM: External observer capturing screens (heavy, inefficient)
- TO: Living within the system as integrated participant (lightweight, efficient)

Author: Claude
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
import platform
import threading
from concurrent.futures import ThreadPoolExecutor

# Import our new efficient system components
from system_integrated_monitor import SystemIntegratedMonitor
from accessibility_ui_detector import AccessibilityUIDetector
from application_integration_framework import ApplicationIntegrationFramework
from intelligent_event_driven_system import IntelligentEventDrivenSystem

# Import existing SensAI components
import websockets
from memory.memory_system import MemorySystem

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SystemEvent:
    """Represents a system event with context and metadata"""
    event_type: str
    timestamp: float
    application: str
    window_title: str
    ui_elements: List[Dict[str, Any]]
    context: Dict[str, Any]
    priority: int
    action_suggestions: List[str]

@dataclass
class SystemState:
    """Current system state snapshot"""
    active_application: str
    focused_window: str
    visible_ui_elements: List[Dict[str, Any]]
    running_processes: List[str]
    recent_events: List[SystemEvent]
    user_context: Dict[str, Any]

class EnhancedRealtimeSystemBridge:
    """
    Bridge between new efficient system components and existing SensAI backend.
    
    This replaces the heavy screen capture approach with lightweight system integration:
    - OS-level event monitoring instead of screen polling
    - Direct UI element access via accessibility APIs
    - Application-specific integration hooks
    - Intelligent event-driven processing
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.is_running = False
        self.connected_clients = set()
        self.current_system_state = None
        
        # Initialize efficient system components
        self.system_monitor = SystemIntegratedMonitor()
        self.ui_detector = AccessibilityUIDetector()
        self.app_integrator = ApplicationIntegrationFramework()
        self.event_processor = IntelligentEventDrivenSystem()
        
        # Initialize memory system for context
        self.memory_system = MemorySystem()
        
        # Event queues for different priority levels
        self.high_priority_queue = asyncio.Queue()
        self.normal_priority_queue = asyncio.Queue()
        self.background_queue = asyncio.Queue()
        
        # Performance metrics
        self.performance_metrics = {
            'events_processed': 0,
            'avg_processing_time': 0.0,
            'memory_usage': 0,
            'cpu_usage': 0.0,
            'last_update': time.time()
        }
        
        # Event subscribers (existing SensAI components)
        self.event_subscribers: Dict[str, List[Callable]] = {
            'ui_change': [],
            'app_switch': [],
            'user_action': [],
            'system_state': [],
            'performance_alert': []
        }
        
        logger.info("EnhancedRealtimeSystemBridge initialized - living in the system, not capturing it")
    
    async def start(self):
        """Start the enhanced real-time system bridge"""
        logger.info("Starting enhanced real-time system bridge...")
        self.is_running = True
        
        # Start all system components
        await self.system_monitor.start_monitoring()
        await self.ui_detector.start()
        await self.app_integrator.start()
        await self.event_processor.start()
        
        # Start background tasks
        tasks = [
            asyncio.create_task(self._event_processing_loop()),
            asyncio.create_task(self._system_state_monitoring()),
            asyncio.create_task(self._performance_monitoring()),
            asyncio.create_task(self._memory_integration_loop()),
            asyncio.create_task(self._websocket_server())
        ]
        
        # Register event handlers with system components
        self._register_event_handlers()
        
        logger.info("Enhanced real-time system bridge started successfully")
        await asyncio.gather(*tasks)
    
    async def stop(self):
        """Stop the enhanced real-time system bridge"""
        logger.info("Stopping enhanced real-time system bridge...")
        self.is_running = False
        
        # Stop all system components
        await self.system_monitor.stop()
        await self.ui_detector.stop()
        await self.app_integrator.stop()
        await self.event_processor.stop()
        
        logger.info("Enhanced real-time system bridge stopped")
    
    def _register_event_handlers(self):
        """Register event handlers with system components"""
        # Register with system monitor
        self.system_monitor.add_event_handler('window_changed', self._handle_window_change)
        self.system_monitor.add_event_handler('application_launched', self._handle_app_launch)
        self.system_monitor.add_event_handler('application_terminated', self._handle_app_terminate)
        
        # Register with UI detector
        self.ui_detector.add_event_handler('ui_element_added', self._handle_ui_element_change)
        self.ui_detector.add_event_handler('ui_element_removed', self._handle_ui_element_change)
        self.ui_detector.add_event_handler('ui_element_modified', self._handle_ui_element_change)
        
        # Register with application integrator
        self.app_integrator.add_event_handler('user_action', self._handle_user_action)
        self.app_integrator.add_event_handler('content_change', self._handle_content_change)
        
        logger.info("Event handlers registered with system components")
    
    async def _handle_window_change(self, event_data: Dict[str, Any]):
        """Handle window change events from system monitor"""
        event = SystemEvent(
            event_type='window_change',
            timestamp=time.time(),
            application=event_data.get('application', 'unknown'),
            window_title=event_data.get('window_title', ''),
            ui_elements=await self._get_current_ui_elements(),
            context=event_data,
            priority=2,  # High priority for window changes
            action_suggestions=await self._generate_action_suggestions(event_data)
        )
        
        await self.high_priority_queue.put(event)
        await self._notify_subscribers('app_switch', event)
    
    async def _handle_app_launch(self, event_data: Dict[str, Any]):
        """Handle application launch events"""
        event = SystemEvent(
            event_type='app_launch',
            timestamp=time.time(),
            application=event_data.get('application', 'unknown'),
            window_title='',
            ui_elements=[],
            context=event_data,
            priority=2,
            action_suggestions=[]
        )
        
        await self.normal_priority_queue.put(event)
        await self._notify_subscribers('system_state', event)
    
    async def _handle_app_terminate(self, event_data: Dict[str, Any]):
        """Handle application termination events"""
        event = SystemEvent(
            event_type='app_terminate',
            timestamp=time.time(),
            application=event_data.get('application', 'unknown'),
            window_title='',
            ui_elements=[],
            context=event_data,
            priority=1,
            action_suggestions=[]
        )
        
        await self.normal_priority_queue.put(event)
        await self._notify_subscribers('system_state', event)
    
    async def _handle_ui_element_change(self, event_data: Dict[str, Any]):
        """Handle UI element change events"""
        event = SystemEvent(
            event_type='ui_change',
            timestamp=time.time(),
            application=event_data.get('application', 'unknown'),
            window_title=event_data.get('window_title', ''),
            ui_elements=[event_data.get('element', {})],
            context=event_data,
            priority=3,  # Highest priority for UI changes
            action_suggestions=await self._generate_ui_action_suggestions(event_data)
        )
        
        await self.high_priority_queue.put(event)
        await self._notify_subscribers('ui_change', event)
    
    async def _handle_user_action(self, event_data: Dict[str, Any]):
        """Handle user action events from application integrator"""
        event = SystemEvent(
            event_type='user_action',
            timestamp=time.time(),
            application=event_data.get('application', 'unknown'),
            window_title=event_data.get('window_title', ''),
            ui_elements=await self._get_current_ui_elements(),
            context=event_data,
            priority=2,
            action_suggestions=[]
        )
        
        await self.normal_priority_queue.put(event)
        await self._notify_subscribers('user_action', event)
    
    async def _handle_content_change(self, event_data: Dict[str, Any]):
        """Handle content change events"""
        event = SystemEvent(
            event_type='content_change',
            timestamp=time.time(),
            application=event_data.get('application', 'unknown'),
            window_title=event_data.get('window_title', ''),
            ui_elements=[],
            context=event_data,
            priority=1,
            action_suggestions=[]
        )
        
        await self.background_queue.put(event)
    
    async def _get_current_ui_elements(self) -> List[Dict[str, Any]]:
        """Get current UI elements from accessibility detector"""
        try:
            elements = await self.ui_detector.get_ui_elements()
            return elements[:10]  # Limit to top 10 for performance
        except Exception as e:
            logger.error(f"Error getting UI elements: {e}")
            return []
    
    async def _generate_action_suggestions(self, event_data: Dict[str, Any]) -> List[str]:
        """Generate intelligent action suggestions based on context"""
        app = event_data.get('application', '')
        window_title = event_data.get('window_title', '')
        
        suggestions = []
        
        # Browser-specific suggestions
        if 'safari' in app.lower() or 'chrome' in app.lower() or 'firefox' in app.lower():
            if 'google' in window_title.lower():
                suggestions.extend(['search_suggestion', 'navigate_results'])
            elif 'youtube' in window_title.lower():
                suggestions.extend(['video_control', 'search_videos'])
        
        # Terminal-specific suggestions
        elif 'terminal' in app.lower() or 'iterm' in app.lower():
            suggestions.extend(['command_completion', 'directory_navigation'])
        
        # IDE-specific suggestions
        elif any(ide in app.lower() for ide in ['code', 'xcode', 'intellij', 'pycharm']):
            suggestions.extend(['code_completion', 'debug_assistance', 'file_navigation'])
        
        return suggestions
    
    async def _generate_ui_action_suggestions(self, event_data: Dict[str, Any]) -> List[str]:
        """Generate UI-specific action suggestions"""
        element = event_data.get('element', {})
        element_type = element.get('type', '')
        
        suggestions = []
        
        if element_type == 'button':
            suggestions.append('click_action')
        elif element_type == 'textfield':
            suggestions.extend(['text_input', 'auto_complete'])
        elif element_type == 'menu':
            suggestions.append('menu_navigation')
        elif element_type == 'link':
            suggestions.append('link_navigation')
        
        return suggestions
    
    async def _event_processing_loop(self):
        """Main event processing loop with priority-based handling"""
        while self.is_running:
            try:
                # Process high priority events first
                if not self.high_priority_queue.empty():
                    event = await self.high_priority_queue.get()
                    await self._process_event(event)
                
                # Then normal priority events
                elif not self.normal_priority_queue.empty():
                    event = await self.normal_priority_queue.get()
                    await self._process_event(event)
                
                # Finally background events
                elif not self.background_queue.empty():
                    event = await self.background_queue.get()
                    await self._process_event(event)
                
                else:
                    # No events to process, brief sleep
                    await asyncio.sleep(0.01)
                    
            except Exception as e:
                logger.error(f"Error in event processing loop: {e}")
                await asyncio.sleep(0.1)
    
    async def _process_event(self, event: SystemEvent):
        """Process a system event and update system state"""
        start_time = time.time()
        
        try:
            # Process event through intelligent event processor
            processed_event = await self.event_processor.process_event(asdict(event))
            
            # Update current system state
            await self._update_system_state(event)
            
            # Store in memory system for context
            await self._store_event_in_memory(event)
            
            # Send to connected WebSocket clients
            await self._broadcast_event(processed_event)
            
            # Update performance metrics
            processing_time = time.time() - start_time
            self._update_performance_metrics(processing_time)
            
            self.performance_metrics['events_processed'] += 1
            
        except Exception as e:
            logger.error(f"Error processing event: {e}")
    
    async def _update_system_state(self, event: SystemEvent):
        """Update the current system state based on event"""
        if not self.current_system_state:
            self.current_system_state = SystemState(
                active_application='',
                focused_window='',
                visible_ui_elements=[],
                running_processes=[],
                recent_events=[],
                user_context={}
            )
        
        # Update based on event type
        if event.event_type in ['window_change', 'app_launch']:
            self.current_system_state.active_application = event.application
            self.current_system_state.focused_window = event.window_title
        
        if event.ui_elements:
            self.current_system_state.visible_ui_elements = event.ui_elements
        
        # Keep last 10 events for context
        self.current_system_state.recent_events.append(event)
        if len(self.current_system_state.recent_events) > 10:
            self.current_system_state.recent_events.pop(0)
    
    async def _store_event_in_memory(self, event: SystemEvent):
        """Store event in memory system for context and learning"""
        try:
            memory_data = {
                'type': 'system_event',
                'event_type': event.event_type,
                'application': event.application,
                'window_title': event.window_title,
                'timestamp': event.timestamp,
                'context': event.context,
                'action_suggestions': event.action_suggestions
            }
            
            await self.memory_system.store_context(
                context_type='system_event',
                data=memory_data,
                metadata={'priority': event.priority}
            )
            
        except Exception as e:
            logger.error(f"Error storing event in memory: {e}")
    
    async def _system_state_monitoring(self):
        """Monitor and update system state periodically"""
        while self.is_running:
            try:
                # Get running processes
                running_processes = await self.system_monitor.get_running_applications()
                
                if self.current_system_state:
                    self.current_system_state.running_processes = running_processes
                
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in system state monitoring: {e}")
                await asyncio.sleep(10)
    
    async def _performance_monitoring(self):
        """Monitor system performance and resource usage"""
        while self.is_running:
            try:
                import psutil
                
                # Update performance metrics
                self.performance_metrics.update({
                    'memory_usage': psutil.virtual_memory().percent,
                    'cpu_usage': psutil.cpu_percent(),
                    'last_update': time.time()
                })
                
                # Alert if performance degrades
                if (self.performance_metrics['memory_usage'] > 80 or 
                    self.performance_metrics['cpu_usage'] > 80):
                    await self._notify_subscribers('performance_alert', self.performance_metrics)
                
                await asyncio.sleep(10)  # Monitor every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")
                await asyncio.sleep(30)
    
    async def _memory_integration_loop(self):
        """Integrate with memory system for contextual awareness"""
        while self.is_running:
            try:
                if self.current_system_state:
                    # Store current system state in memory
                    await self.memory_system.store_context(
                        context_type='system_state',
                        data=asdict(self.current_system_state),
                        metadata={'timestamp': time.time()}
                    )
                
                await asyncio.sleep(30)  # Store state every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in memory integration: {e}")
                await asyncio.sleep(60)
    
    async def _websocket_server(self):
        """WebSocket server for real-time communication with SensAI backend"""
        async def handle_client(websocket, path):
            self.connected_clients.add(websocket)
            logger.info(f"Client connected: {websocket.remote_address}")
            
            try:
                # Send current system state to new client
                if self.current_system_state:
                    await websocket.send(json.dumps({
                        'type': 'system_state',
                        'data': asdict(self.current_system_state)
                    }))
                
                # Listen for client messages
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        await self._handle_client_message(websocket, data)
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON from client: {message}")
                        
            except websockets.exceptions.ConnectionClosed:
                logger.info(f"Client disconnected: {websocket.remote_address}")
            finally:
                self.connected_clients.discard(websocket)
        
        # Start WebSocket server on port 8768 (different from existing backend)
        start_server = websockets.serve(handle_client, "localhost", 8768)
        logger.info("WebSocket server started on ws://localhost:8768")
        await start_server
    
    async def _handle_client_message(self, websocket, data: Dict[str, Any]):
        """Handle messages from connected clients"""
        message_type = data.get('type')
        
        if message_type == 'execute_action':
            # Execute action through application integrator
            action = data.get('action')
            parameters = data.get('parameters', {})
            
            try:
                result = await self.app_integrator.execute_action(action, parameters)
                await websocket.send(json.dumps({
                    'type': 'action_result',
                    'success': True,
                    'result': result
                }))
            except Exception as e:
                await websocket.send(json.dumps({
                    'type': 'action_result',
                    'success': False,
                    'error': str(e)
                }))
        
        elif message_type == 'get_system_state':
            # Send current system state
            if self.current_system_state:
                await websocket.send(json.dumps({
                    'type': 'system_state',
                    'data': asdict(self.current_system_state)
                }))
        
        elif message_type == 'get_performance_metrics':
            # Send performance metrics
            await websocket.send(json.dumps({
                'type': 'performance_metrics',
                'data': self.performance_metrics
            }))
    
    async def _broadcast_event(self, event_data: Dict[str, Any]):
        """Broadcast event to all connected WebSocket clients"""
        if not self.connected_clients:
            return
        
        message = json.dumps({
            'type': 'system_event',
            'data': event_data
        })
        
        # Send to all connected clients
        disconnected_clients = set()
        for client in self.connected_clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        self.connected_clients -= disconnected_clients
    
    async def _notify_subscribers(self, event_type: str, data: Any):
        """Notify event subscribers"""
        if event_type in self.event_subscribers:
            for callback in self.event_subscribers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    logger.error(f"Error in event subscriber callback: {e}")
    
    def _update_performance_metrics(self, processing_time: float):
        """Update performance metrics with new processing time"""
        current_avg = self.performance_metrics['avg_processing_time']
        events_count = self.performance_metrics['events_processed']
        
        # Calculate new average processing time
        new_avg = ((current_avg * events_count) + processing_time) / (events_count + 1)
        self.performance_metrics['avg_processing_time'] = new_avg
    
    def subscribe_to_events(self, event_type: str, callback: Callable):
        """Subscribe to system events"""
        if event_type not in self.event_subscribers:
            self.event_subscribers[event_type] = []
        self.event_subscribers[event_type].append(callback)
    
    def unsubscribe_from_events(self, event_type: str, callback: Callable):
        """Unsubscribe from system events"""
        if event_type in self.event_subscribers:
            try:
                self.event_subscribers[event_type].remove(callback)
            except ValueError:
                pass
    
    async def get_current_system_state(self) -> Optional[SystemState]:
        """Get current system state"""
        return self.current_system_state
    
    async def execute_system_action(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a system action through the application integrator"""
        try:
            result = await self.app_integrator.execute_action(action, parameters)
            return {'success': True, 'result': result}
        except Exception as e:
            logger.error(f"Error executing system action: {e}")
            return {'success': False, 'error': str(e)}

async def main():
    """Main function for testing the bridge"""
    bridge = EnhancedRealtimeSystemBridge()
    
    # Add some test event subscribers
    def test_ui_change_handler(event):
        print(f"UI Change detected: {event.application} - {event.event_type}")
    
    def test_app_switch_handler(event):
        print(f"App Switch detected: {event.application} - {event.window_title}")
    
    bridge.subscribe_to_events('ui_change', test_ui_change_handler)
    bridge.subscribe_to_events('app_switch', test_app_switch_handler)
    
    try:
        await bridge.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await bridge.stop()

if __name__ == "__main__":
    asyncio.run(main())