#!/usr/bin/env python3
"""
Intelligent Event-Driven System
Replace polling with intelligent event subscription and processing
"""

import asyncio
import logging
import time
import json
from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
import weakref

# Import our system components
from system_integrated_monitor import SystemIntegratedMonitor, SystemEvent, EventType
from accessibility_ui_detector import AccessibilityUIDetector, UIElement, UIElementType
from application_integration_framework import ApplicationIntegrationFramework, ApplicationState

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventPriority(Enum):
    CRITICAL = 1    # System crashes, security issues
    HIGH = 2       # User input, window changes
    MEDIUM = 3     # UI updates, application state changes
    LOW = 4        # Background processes, maintenance

class ProcessingStrategy(Enum):
    IMMEDIATE = "immediate"     # Process right away
    BATCHED = "batched"        # Batch with similar events
    THROTTLED = "throttled"    # Rate limit processing
    DEBOUNCED = "debounced"    # Wait for event burst to end

@dataclass
class IntelligentEvent:
    """Enhanced event with processing metadata"""
    source_event: SystemEvent
    priority: EventPriority
    processing_strategy: ProcessingStrategy
    context: Dict[str, Any]
    related_events: List[str] = None
    processing_deadline: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3

class EventProcessor:
    """Intelligent event processor with different strategies"""
    
    def __init__(self):
        self.processing_strategies = {
            ProcessingStrategy.IMMEDIATE: self._process_immediate,
            ProcessingStrategy.BATCHED: self._process_batched,
            ProcessingStrategy.THROTTLED: self._process_throttled,
            ProcessingStrategy.DEBOUNCED: self._process_debounced
        }
        
        # Event queues for different strategies
        self.immediate_queue = asyncio.Queue()
        self.batched_events = defaultdict(list)
        self.throttled_events = {}
        self.debounced_events = {}
        
        # Processing metrics
        self.events_processed = 0
        self.processing_times = deque(maxlen=1000)
        self.error_count = 0
        
        # Rate limiting
        self.last_processing_time = {}
        self.processing_rates = {
            EventType.UI_ELEMENT_CHANGED: 10,  # 10 events per second max
            EventType.WINDOW_MOVED: 5,         # 5 events per second max
            EventType.TEXT_CHANGED: 20,        # 20 events per second max
        }
    
    async def process_event(self, event: IntelligentEvent) -> bool:
        """Process event using appropriate strategy"""
        start_time = time.time()
        
        try:
            strategy = event.processing_strategy
            processor = self.processing_strategies.get(strategy)
            
            if processor:
                success = await processor(event)
                
                # Update metrics
                processing_time = time.time() - start_time
                self.processing_times.append(processing_time)
                self.events_processed += 1
                
                return success
            else:
                logger.error(f"Unknown processing strategy: {strategy}")
                return False
                
        except Exception as e:
            logger.error(f"Event processing error: {e}")
            self.error_count += 1
            
            # Retry logic
            if event.retry_count < event.max_retries:
                event.retry_count += 1
                await asyncio.sleep(0.1 * event.retry_count)  # Exponential backoff
                return await self.process_event(event)
            
            return False
    
    async def _process_immediate(self, event: IntelligentEvent) -> bool:
        """Process event immediately"""
        logger.debug(f"⚡ Immediate processing: {event.source_event.event_type}")
        
        # Add to immediate queue for processing
        await self.immediate_queue.put(event)
        return True
    
    async def _process_batched(self, event: IntelligentEvent) -> bool:
        """Batch similar events together"""
        event_type = event.source_event.event_type
        self.batched_events[event_type].append(event)
        
        # Process batch when it reaches threshold or timeout
        if len(self.batched_events[event_type]) >= 10:  # Batch size threshold
            await self._flush_batch(event_type)
        
        return True
    
    async def _process_throttled(self, event: IntelligentEvent) -> bool:
        """Rate limit event processing"""
        event_type = event.source_event.event_type
        current_time = time.time()
        
        # Check rate limit
        last_time = self.last_processing_time.get(event_type, 0)
        min_interval = 1.0 / self.processing_rates.get(event_type, 10)
        
        if current_time - last_time < min_interval:
            # Store for later processing
            self.throttled_events[event_type] = event
            return True
        
        # Process now
        self.last_processing_time[event_type] = current_time
        await self.immediate_queue.put(event)
        return True
    
    async def _process_debounced(self, event: IntelligentEvent) -> bool:
        """Debounce rapid events"""
        event_type = event.source_event.event_type
        
        # Cancel previous debounced event
        if event_type in self.debounced_events:
            self.debounced_events[event_type].cancel()
        
        # Schedule new debounced processing
        self.debounced_events[event_type] = asyncio.create_task(
            self._debounced_delay(event, 0.5)  # 500ms debounce
        )
        
        return True
    
    async def _debounced_delay(self, event: IntelligentEvent, delay: float):
        """Delay processing for debouncing"""
        await asyncio.sleep(delay)
        await self.immediate_queue.put(event)
    
    async def _flush_batch(self, event_type: EventType):
        """Flush batched events"""
        if event_type in self.batched_events:
            events = self.batched_events[event_type]
            if events:
                logger.debug(f"📦 Flushing batch of {len(events)} {event_type} events")
                
                # Create combined event
                combined_event = events[-1]  # Use latest event as base
                combined_event.context['batched_events'] = [e.source_event for e in events]
                
                await self.immediate_queue.put(combined_event)
                self.batched_events[event_type].clear()
    
    async def start_processing_loops(self):
        """Start background processing loops"""
        asyncio.create_task(self._immediate_processing_loop())
        asyncio.create_task(self._batch_flush_loop())
        asyncio.create_task(self._throttle_flush_loop())
    
    async def _immediate_processing_loop(self):
        """Process immediate events"""
        while True:
            try:
                event = await self.immediate_queue.get()
                # Actual event processing logic here
                logger.debug(f"Processing: {event.source_event.event_type}")
                
                # Mark task as done
                self.immediate_queue.task_done()
                
            except Exception as e:
                logger.error(f"Immediate processing loop error: {e}")
    
    async def _batch_flush_loop(self):
        """Periodically flush batched events"""
        while True:
            await asyncio.sleep(1.0)  # Flush every second
            
            for event_type in list(self.batched_events.keys()):
                if self.batched_events[event_type]:
                    await self._flush_batch(event_type)
    
    async def _throttle_flush_loop(self):
        """Process throttled events"""
        while True:
            await asyncio.sleep(0.1)  # Check every 100ms
            
            current_time = time.time()
            
            for event_type, event in list(self.throttled_events.items()):
                last_time = self.last_processing_time.get(event_type, 0)
                min_interval = 1.0 / self.processing_rates.get(event_type, 10)
                
                if current_time - last_time >= min_interval:
                    self.last_processing_time[event_type] = current_time
                    await self.immediate_queue.put(event)
                    del self.throttled_events[event_type]

class EventClassifier:
    """Classify events and determine processing strategy"""
    
    def __init__(self):
        # Event classification rules
        self.priority_rules = {
            EventType.APPLICATION_LAUNCHED: EventPriority.HIGH,
            EventType.APPLICATION_TERMINATED: EventPriority.HIGH,
            EventType.WINDOW_FOCUSED: EventPriority.HIGH,
            EventType.WINDOW_CREATED: EventPriority.MEDIUM,
            EventType.WINDOW_DESTROYED: EventPriority.MEDIUM,
            EventType.UI_ELEMENT_APPEARED: EventPriority.MEDIUM,
            EventType.UI_ELEMENT_CHANGED: EventPriority.LOW,
            EventType.WINDOW_MOVED: EventPriority.LOW,
            EventType.WINDOW_RESIZED: EventPriority.LOW,
        }
        
        self.strategy_rules = {
            EventType.APPLICATION_LAUNCHED: ProcessingStrategy.IMMEDIATE,
            EventType.APPLICATION_TERMINATED: ProcessingStrategy.IMMEDIATE,
            EventType.WINDOW_FOCUSED: ProcessingStrategy.IMMEDIATE,
            EventType.UI_ELEMENT_CHANGED: ProcessingStrategy.THROTTLED,
            EventType.WINDOW_MOVED: ProcessingStrategy.DEBOUNCED,
            EventType.WINDOW_RESIZED: ProcessingStrategy.DEBOUNCED,
            EventType.TEXT_CHANGED: ProcessingStrategy.BATCHED,
        }
    
    def classify_event(self, event: SystemEvent) -> IntelligentEvent:
        """Classify system event into intelligent event"""
        
        # Determine priority
        priority = self.priority_rules.get(event.event_type, EventPriority.MEDIUM)
        
        # Determine processing strategy
        strategy = self.strategy_rules.get(event.event_type, ProcessingStrategy.IMMEDIATE)
        
        # Build context
        context = {
            'source': 'system_monitor',
            'app_specific': self._is_app_specific_event(event),
            'user_initiated': self._is_user_initiated_event(event),
            'requires_response': self._requires_response(event)
        }
        
        # Set processing deadline for high priority events
        deadline = None
        if priority == EventPriority.CRITICAL:
            deadline = time.time() + 0.1  # 100ms for critical events
        elif priority == EventPriority.HIGH:
            deadline = time.time() + 0.5  # 500ms for high priority
        
        return IntelligentEvent(
            source_event=event,
            priority=priority,
            processing_strategy=strategy,
            context=context,
            processing_deadline=deadline
        )
    
    def _is_app_specific_event(self, event: SystemEvent) -> bool:
        """Check if event is specific to an application"""
        return event.source_app and event.source_app != "Unknown"
    
    def _is_user_initiated_event(self, event: SystemEvent) -> bool:
        """Check if event was initiated by user action"""
        user_events = [
            EventType.WINDOW_FOCUSED,
            EventType.USER_INPUT,
            EventType.MENU_OPENED
        ]
        return event.event_type in user_events
    
    def _requires_response(self, event: SystemEvent) -> bool:
        """Check if event requires immediate response"""
        response_events = [
            EventType.APPLICATION_LAUNCHED,
            EventType.WINDOW_FOCUSED,
            EventType.UI_ELEMENT_APPEARED
        ]
        return event.event_type in response_events

class IntelligentEventDrivenSystem:
    """Main intelligent event-driven system"""
    
    def __init__(self):
        # Core components
        self.system_monitor = SystemIntegratedMonitor()
        self.accessibility_detector = AccessibilityUIDetector()
        self.app_framework = ApplicationIntegrationFramework()
        
        # Event processing
        self.event_classifier = EventClassifier()
        self.event_processor = EventProcessor()
        
        # Event handlers
        self.event_handlers: Dict[EventType, List[Callable]] = defaultdict(list)
        
        # System state
        self.current_state = {
            'active_applications': {},
            'ui_elements': {},
            'system_context': {},
            'last_user_action': None
        }
        
        # Performance metrics
        self.start_time = time.time()
        self.total_events = 0
        
    async def initialize(self) -> bool:
        """Initialize the intelligent event-driven system"""
        logger.info("🚀 Initializing Intelligent Event-Driven System...")
        
        # Initialize components
        success = True
        
        # Initialize accessibility detector
        if await self.accessibility_detector.initialize():
            logger.info("✅ Accessibility detector initialized")
        else:
            logger.warning("⚠️  Accessibility detector initialization failed")
            success = False
        
        # Add event handlers
        self.system_monitor.add_event_handler(self._handle_system_event)
        
        # Start event processing
        await self.event_processor.start_processing_loops()
        
        # Start system monitoring
        if await self.system_monitor.start_monitoring():
            logger.info("✅ System monitoring started")
        else:
            logger.error("❌ System monitoring failed")
            success = False
        
        if success:
            logger.info("🎉 Intelligent Event-Driven System ready!")
            logger.info("📡 Monitoring: Apps, Windows, UI Elements, User Actions")
            logger.info("🧠 Processing: Intelligent, Efficient, Real-time")
        
        return success
    
    def register_event_handler(self, event_type: EventType, handler: Callable):
        """Register handler for specific event type"""
        self.event_handlers[event_type].append(handler)
        logger.info(f"📝 Registered handler for {event_type.value}")
    
    async def _handle_system_event(self, event: SystemEvent):
        """Handle incoming system events"""
        self.total_events += 1
        
        # Classify event
        intelligent_event = self.event_classifier.classify_event(event)
        
        # Update system state
        await self._update_system_state(event)
        
        # Process event
        await self.event_processor.process_event(intelligent_event)
        
        # Notify registered handlers
        handlers = self.event_handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(intelligent_event)
                else:
                    handler(intelligent_event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")
    
    async def _update_system_state(self, event: SystemEvent):
        """Update internal system state based on event"""
        
        if event.event_type == EventType.APPLICATION_LAUNCHED:
            self.current_state['active_applications'][event.source_app] = {
                'launch_time': event.timestamp,
                'windows': []
            }
        
        elif event.event_type == EventType.APPLICATION_TERMINATED:
            if event.source_app in self.current_state['active_applications']:
                del self.current_state['active_applications'][event.source_app]
        
        elif event.event_type == EventType.WINDOW_FOCUSED:
            self.current_state['system_context']['active_window'] = {
                'app': event.source_app,
                'title': event.window_title,
                'timestamp': event.timestamp
            }
        
        elif event.event_type == EventType.USER_INPUT:
            self.current_state['last_user_action'] = {
                'type': 'input',
                'timestamp': event.timestamp,
                'context': event.element_info
            }
    
    async def get_current_context(self) -> Dict[str, Any]:
        """Get current system context for AI decision making"""
        
        # Get current UI elements
        ui_elements = await self.accessibility_detector.get_current_ui_elements()
        
        # Get application states
        app_states = await self.app_framework.detect_and_integrate_applications()
        
        # Combine into comprehensive context
        context = {
            'timestamp': time.time(),
            'system_state': self.current_state,
            'ui_elements': [asdict(element) for element in ui_elements],
            'applications': [asdict(state) for state in app_states],
            'performance_metrics': {
                'uptime': time.time() - self.start_time,
                'total_events': self.total_events,
                'events_processed': self.event_processor.events_processed,
                'processing_errors': self.event_processor.error_count,
                'avg_processing_time': sum(self.event_processor.processing_times) / 
                                     len(self.event_processor.processing_times) 
                                     if self.event_processor.processing_times else 0
            }
        }
        
        return context
    
    async def execute_intelligent_action(self, action: str, target: Dict[str, Any], 
                                       context: Dict[str, Any]) -> bool:
        """Execute action with full system context"""
        logger.info(f"🎯 Executing intelligent action: {action}")
        
        try:
            # Find appropriate application integrator
            app_name = target.get('app_name')
            if app_name:
                app_state = await self.app_framework.get_application_by_name(app_name)
                if app_state:
                    # Execute through application framework
                    return await self.app_framework.execute_application_action(
                        app_state.pid, action, target
                    )
            
            # Fallback to accessibility-based action
            ui_elements = await self.accessibility_detector.get_current_ui_elements()
            
            # Find target element
            target_element = None
            if 'element_text' in target:
                matching_elements = await self.accessibility_detector.find_elements_by_text(
                    target['element_text']
                )
                if matching_elements:
                    target_element = matching_elements[0]
            
            if target_element and action == "click":
                # Use system APIs to click the element
                # This would integrate with platform-specific clicking
                logger.info(f"✅ Clicked element: {target_element.title}")
                return True
            
        except Exception as e:
            logger.error(f"Intelligent action execution error: {e}")
        
        return False
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        uptime = time.time() - self.start_time
        
        return {
            'uptime_seconds': uptime,
            'total_events_received': self.total_events,
            'events_processed': self.event_processor.events_processed,
            'processing_errors': self.event_processor.error_count,
            'events_per_second': self.total_events / uptime if uptime > 0 else 0,
            'average_processing_time': sum(self.event_processor.processing_times) / 
                                     len(self.event_processor.processing_times) 
                                     if self.event_processor.processing_times else 0,
            'active_integrations': len(self.app_framework.active_integrations),
            'system_monitoring_active': self.system_monitor.running
        }

# Example usage and demonstration
async def main():
    """Demonstrate intelligent event-driven system"""
    system = IntelligentEventDrivenSystem()
    
    # Example event handlers
    async def on_app_launched(event: IntelligentEvent):
        logger.info(f"🚀 App launched: {event.source_event.source_app}")
    
    async def on_window_focused(event: IntelligentEvent):
        logger.info(f"🔍 Window focused: {event.source_event.window_title}")
    
    # Register handlers
    system.register_event_handler(EventType.APPLICATION_LAUNCHED, on_app_launched)
    system.register_event_handler(EventType.WINDOW_FOCUSED, on_window_focused)
    
    # Initialize system
    success = await system.initialize()
    
    if success:
        logger.info("🔄 Running intelligent event monitoring for 30 seconds...")
        
        # Monitor for 30 seconds
        await asyncio.sleep(30)
        
        # Show performance metrics
        metrics = system.get_performance_metrics()
        logger.info("📊 Performance Metrics:")
        for key, value in metrics.items():
            logger.info(f"  {key}: {value}")
        
        # Get current context
        context = await system.get_current_context()
        logger.info(f"📱 Current context: {len(context['ui_elements'])} UI elements, "
                   f"{len(context['applications'])} applications")
    
    else:
        logger.error("❌ Failed to initialize intelligent event-driven system")

if __name__ == "__main__":
    asyncio.run(main())