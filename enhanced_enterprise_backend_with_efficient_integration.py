#!/usr/bin/env python3
"""
Enhanced Enterprise Backend 8767 with Efficient System Integration
Replaces heavy screen capture with lightweight OS-integrated event monitoring
"""

import asyncio
import json
import logging
import websockets
import time
import subprocess
import requests
import aiohttp
import sys
import os
import numpy as np
from datetime import datetime
from typing import Dict, Any, Set, Optional, Tuple, List
from enum import Enum
from concurrent.futures import ThreadPoolExecutor

# Import our new efficient system bridge
from enhanced_realtime_system_bridge import EnhancedRealtimeSystemBridge, SystemEvent, SystemState

# Import warmup manager for fast LLM responses
try:
    from llm_warmup_manager import get_warmup_manager
    WARMUP_MANAGER_AVAILABLE = True
    print("🔥 LLM Warmup Manager available for fast responses")
except ImportError:
    WARMUP_MANAGER_AVAILABLE = False
    print("⚠️ LLM Warmup Manager not available")

# Add memory module to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory.semantic_search_agent import SemanticSearchAgent, get_context_for_query, add_memory

# Import automation components for Agent mode - prioritize fast handler
ENHANCED_AUTOMATION_AVAILABLE = False
try:
    from fast_universal_automation_handler import fast_universal_automation_handler
    AUTOMATION_AVAILABLE = True
    FAST_AUTOMATION_AVAILABLE = True
    UNIVERSAL_AVAILABLE = False  # Fast handler doesn't need universal
    print("⚡ Fast Universal Automation handler loaded for 10-20s responses")
except ImportError as e:
    FAST_AUTOMATION_AVAILABLE = False
    try:
        from universal_intelligent_automation_handler import universal_automation_handler
        AUTOMATION_AVAILABLE = True
        UNIVERSAL_AVAILABLE = True
        print(f"Warning: Fast automation not available, using universal: {e}")
    except ImportError as e2:
        UNIVERSAL_AVAILABLE = False
        try:
            # Import smart fallback handler
            from smart_fallback_automation_handler import smart_fallback_handler
            AUTOMATION_AVAILABLE = True
            print(f"Warning: Universal automation handler not available, using smart fallback: {e}")
        except ImportError as e2:
            try:
                # Final fallback to enhanced automation handler
                from agent_workflow.enhanced_automation_handler import EnhancedAutomationHandler
                ENHANCED_AUTOMATION_AVAILABLE = True
                AUTOMATION_AVAILABLE = True
                print(f"Warning: Smart fallback not available, using enhanced handler: {e2}")
            except ImportError as e3:
                print(f"Warning: No automation handlers available: {e3}")
                ENHANCED_AUTOMATION_AVAILABLE = False
                AUTOMATION_AVAILABLE = False

# Setup enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backend/enhanced_enterprise_8767_efficient.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ChatMode(Enum):
    ASK = "ask"
    SUGGEST = "suggest" 
    AGENT = "agent"
    GENERAL = "general"

class EnhancedEnterpriseBackendEfficient:
    """
    Enhanced Enterprise Backend with Efficient System Integration
    
    Key Changes from Traditional Approach:
    - Replaces PIL.ImageGrab screen capture with OS-level event monitoring
    - Uses real-time system state instead of polling screenshots
    - Integrates with accessibility APIs for direct UI element access
    - Event-driven architecture for minimal resource usage
    - Maintains TeamViewer-style capabilities without screen capture overhead
    """
    
    def __init__(self):
        self.connected_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.llm_service_url = "http://localhost:11435"
        self.brain_router_url = "http://localhost:8765/brain"
        
        # Initialize efficient system bridge (replaces screen capture)
        self.system_bridge = EnhancedRealtimeSystemBridge()
        self.current_system_state: Optional[SystemState] = None
        self.last_ui_elements: List[Dict[str, Any]] = []
        
        # Performance tracking
        self.response_times = []
        self.context_cache = {}
        self.last_context_update = 0
        
        # Initialize automation handler based on availability
        self.automation_handler = None
        if FAST_AUTOMATION_AVAILABLE:
            self.automation_handler = fast_universal_automation_handler
        elif UNIVERSAL_AVAILABLE:
            self.automation_handler = universal_automation_handler
        elif AUTOMATION_AVAILABLE:
            self.automation_handler = smart_fallback_handler
        elif ENHANCED_AUTOMATION_AVAILABLE:
            self.automation_handler = EnhancedAutomationHandler()
        
        logger.info("Enhanced Enterprise Backend with Efficient Integration initialized")
        logger.info("🚀 System living inside OS - no more screen capture overhead!")
    
    async def start_server(self):
        """Start the enhanced enterprise backend server"""
        logger.info("Starting Enhanced Enterprise Backend on port 8767...")
        
        # Start the efficient system bridge
        logger.info("Starting efficient system bridge...")
        bridge_task = asyncio.create_task(self.system_bridge.start())
        
        # Subscribe to system events
        self._setup_system_event_handlers()
        
        # Initialize enterprise knowledge base
        await self._initialize_enterprise_knowledge()
        
        # Start WebSocket server
        server_task = asyncio.create_task(
            websockets.serve(self.handle_client, "localhost", 8767)
        )
        
        logger.info("✅ Enhanced Enterprise Backend started successfully")
        logger.info("🔗 WebSocket server: ws://localhost:8767")
        logger.info("⚡ System Bridge: ws://localhost:8768")
        logger.info("🧠 Memory-powered contextual responses enabled")
        logger.info("🎯 OS-integrated event monitoring active")
        
        # Run both tasks concurrently
        await asyncio.gather(bridge_task, server_task)
    
    def _setup_system_event_handlers(self):
        """Setup event handlers for the system bridge"""
        # Subscribe to system events that matter for enterprise functionality
        self.system_bridge.subscribe_to_events('ui_change', self._handle_ui_change)
        self.system_bridge.subscribe_to_events('app_switch', self._handle_app_switch)
        self.system_bridge.subscribe_to_events('user_action', self._handle_user_action)
        self.system_bridge.subscribe_to_events('system_state', self._handle_system_state_change)
        
        logger.info("System event handlers registered")
    
    async def _handle_ui_change(self, event: SystemEvent):
        """Handle UI change events from system bridge"""
        # Update our understanding of current UI elements
        self.last_ui_elements = event.ui_elements
        
        # Store in context for memory
        context_data = {
            'type': 'ui_change',
            'application': event.application,
            'window_title': event.window_title,
            'ui_elements': event.ui_elements,
            'timestamp': event.timestamp
        }
        
        # Notify connected clients about UI changes
        await self._broadcast_to_clients({
            'type': 'ui_change',
            'data': context_data
        })
    
    async def _handle_app_switch(self, event: SystemEvent):
        """Handle application switch events"""
        logger.info(f"App switch detected: {event.application} - {event.window_title}")
        
        # Update current system state
        await self._update_current_system_state()
        
        # Store context for memory
        await add_memory(
            f"User switched to {event.application} with window '{event.window_title}'",
            source="system_monitoring",
            tags={"app_switch", "user_behavior"}
        )
        
        # Notify clients
        await self._broadcast_to_clients({
            'type': 'app_switch',
            'data': {
                'application': event.application,
                'window_title': event.window_title,
                'timestamp': event.timestamp
            }
        })
    
    async def _handle_user_action(self, event: SystemEvent):
        """Handle user action events"""
        # Store user actions for context learning
        await add_memory(
            f"User performed action in {event.application}: {event.context}",
            source="user_action_monitoring",
            tags={"user_action", "behavior_pattern"}
        )
    
    async def _handle_system_state_change(self, event: SystemEvent):
        """Handle system state changes"""
        await self._update_current_system_state()
    
    async def _update_current_system_state(self):
        """Update current system state from bridge"""
        self.current_system_state = await self.system_bridge.get_current_system_state()
    
    async def _initialize_enterprise_knowledge(self):
        """Initialize enterprise knowledge base with efficient system capabilities"""
        knowledge_items = [
            "The system uses efficient OS-level integration instead of screen capture for real-time monitoring",
            "UI elements are accessed directly through accessibility APIs for precise interaction",
            "System events are monitored through native OS event streams for minimal overhead",
            "Application integration works through specific hooks rather than external observation",
            "Performance is optimized with event-driven architecture instead of polling",
            "TeamViewer-style capabilities are achieved through system integration, not screen mirroring",
            "Memory system stores context from real system events rather than visual analysis",
            "Cross-platform support includes macOS (Quartz), Windows (UI Automation), and Linux (AT-SPI)",
            "Intelligent event processing prioritizes important system changes",
            "WebSocket integration provides real-time communication between system components"
        ]
        
        for knowledge in knowledge_items:
            await add_memory(knowledge, source="enterprise_system", tags={"enterprise", "efficient_system"})
        
        logger.info("Enterprise efficient system knowledge initialized")
    
    # ==================== EFFICIENT SYSTEM INTERACTION METHODS ====================
    
    async def get_current_system_context(self) -> Dict[str, Any]:
        """Get current system context without screen capture"""
        try:
            # Get current system state from bridge
            system_state = await self.system_bridge.get_current_system_state()
            
            if not system_state:
                return {'error': 'System state not available'}
            
            # Build comprehensive context
            context = {
                'active_application': system_state.active_application,
                'focused_window': system_state.focused_window,
                'visible_ui_elements': system_state.visible_ui_elements[:5],  # Top 5 for performance
                'running_processes': system_state.running_processes[:10],  # Top 10
                'recent_events': [
                    {
                        'type': event.event_type,
                        'app': event.application,
                        'window': event.window_title,
                        'timestamp': event.timestamp
                    }
                    for event in system_state.recent_events[-3:]  # Last 3 events
                ],
                'timestamp': time.time(),
                'system_integration_active': True
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting system context: {e}")
            return {'error': str(e)}
    
    async def execute_action_with_verification(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action with system integration verification (no screen capture needed)"""
        try:
            logger.info(f"Executing action via system integration: {action}")
            
            # Get system state before action
            before_state = await self.get_current_system_context()
            
            # Execute action through system bridge
            result = await self.system_bridge.execute_system_action(action, parameters)
            
            if not result.get('success'):
                return {
                    'success': False,
                    'error': result.get('error', 'Action execution failed'),
                    'action': action,
                    'parameters': parameters
                }
            
            # Brief wait for system to respond
            await asyncio.sleep(0.5)
            
            # Get system state after action
            after_state = await self.get_current_system_context()
            
            # Analyze changes through system events (much more reliable than visual comparison)
            changes_detected = await self._detect_system_changes(before_state, after_state)
            
            # Store action result in memory
            await add_memory(
                f"Executed {action} in {before_state.get('active_application', 'unknown')} - "
                f"Changes detected: {changes_detected.get('changes_detected', False)}",
                source="system_action",
                tags={"automation", "system_action"}
            )
            
            return {
                'success': True,
                'action': action,
                'parameters': parameters,
                'before_state': before_state,
                'after_state': after_state,
                'changes_detected': changes_detected,
                'execution_method': 'system_integration',
                'result': result.get('result')
            }
            
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'action': action,
                'parameters': parameters
            }
    
    async def _detect_system_changes(self, before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
        """Detect system changes through state comparison (replaces visual diff)"""
        changes = {
            'changes_detected': False,
            'confidence': 0.0,
            'change_details': []
        }
        
        try:
            # Check application changes
            if before.get('active_application') != after.get('active_application'):
                changes['changes_detected'] = True
                changes['confidence'] = 0.9
                changes['change_details'].append('Application changed')
            
            # Check window changes
            if before.get('focused_window') != after.get('focused_window'):
                changes['changes_detected'] = True
                changes['confidence'] = max(changes['confidence'], 0.8)
                changes['change_details'].append('Window changed')
            
            # Check UI element changes
            before_elements = len(before.get('visible_ui_elements', []))
            after_elements = len(after.get('visible_ui_elements', []))
            
            if abs(before_elements - after_elements) > 0:
                changes['changes_detected'] = True
                changes['confidence'] = max(changes['confidence'], 0.7)
                changes['change_details'].append(f'UI elements changed: {before_elements} -> {after_elements}')
            
            # Check for new events
            before_events = len(before.get('recent_events', []))
            after_events = len(after.get('recent_events', []))
            
            if after_events > before_events:
                changes['changes_detected'] = True
                changes['confidence'] = max(changes['confidence'], 0.6)
                changes['change_details'].append('New system events detected')
            
            return changes
            
        except Exception as e:
            logger.error(f"Error detecting system changes: {e}")
            return changes
    
    async def get_ui_elements_at_location(self, x: int, y: int) -> List[Dict[str, Any]]:
        """Get UI elements at specific location using accessibility APIs"""
        try:
            # Use system bridge to get UI elements at location
            if self.current_system_state and self.current_system_state.visible_ui_elements:
                # Filter elements by proximity to coordinates
                nearby_elements = []
                for element in self.current_system_state.visible_ui_elements:
                    element_bounds = element.get('bounds', {})
                    if element_bounds:
                        element_x = element_bounds.get('x', 0)
                        element_y = element_bounds.get('y', 0)
                        element_width = element_bounds.get('width', 0)
                        element_height = element_bounds.get('height', 0)
                        
                        # Check if coordinates are within element bounds
                        if (element_x <= x <= element_x + element_width and
                            element_y <= y <= element_y + element_height):
                            nearby_elements.append(element)
                
                return nearby_elements
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting UI elements at location: {e}")
            return []
    
    # ==================== ENHANCED CHAT PROCESSING ====================
    
    async def handle_client(self, websocket, path):
        """Handle WebSocket client connections"""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        self.connected_clients.add(websocket)
        logger.info(f"✅ Client connected: {client_id}")
        
        try:
            # Send current system context to new client
            system_context = await self.get_current_system_context()
            await websocket.send(json.dumps({
                'type': 'system_context',
                'data': system_context
            }))
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    response = await self.process_chat_request(data)
                    await websocket.send(json.dumps(response))
                    
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error from {client_id}: {e}")
                    await websocket.send(json.dumps({
                        'error': 'Invalid JSON format',
                        'message': str(e)
                    }))
                except Exception as e:
                    logger.error(f"Error processing message from {client_id}: {e}")
                    await websocket.send(json.dumps({
                        'error': 'Internal server error',
                        'message': str(e)
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"❌ Client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            self.connected_clients.discard(websocket)
    
    async def process_chat_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process chat request with efficient system context"""
        start_time = time.time()
        
        try:
            message = data.get('message', '')
            mode = data.get('mode', 'general')
            context = data.get('context', {})
            
            # Get current system context (replaces screen capture)
            system_context = await self.get_current_system_context()
            
            # Enhance context with system state
            enhanced_context = {
                **context,
                'system_state': system_context,
                'timestamp': start_time,
                'integration_method': 'efficient_system_bridge'
            }
            
            # Process based on mode
            if mode == ChatMode.AGENT.value and AUTOMATION_AVAILABLE:
                response = await self._handle_agent_mode(message, enhanced_context)
            elif mode == ChatMode.ASK.value:
                response = await self._handle_ask_mode(message, enhanced_context)
            elif mode == ChatMode.SUGGEST.value:
                response = await self._handle_suggest_mode(message, enhanced_context)
            else:
                response = await self._handle_general_mode(message, enhanced_context)
            
            # Add performance metrics
            processing_time = time.time() - start_time
            self.response_times.append(processing_time)
            
            response['performance'] = {
                'processing_time': processing_time,
                'avg_response_time': sum(self.response_times[-10:]) / min(len(self.response_times), 10),
                'system_integration': True,
                'screen_capture_overhead': 0.0  # No screen capture overhead!
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing chat request: {e}")
            return {
                'error': 'Failed to process request',
                'message': str(e),
                'timestamp': time.time()
            }
    
    async def _handle_agent_mode(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent mode with efficient system integration"""
        try:
            logger.info(f"🤖 Agent mode request: {message}")
            
            # Get system context for automation
            system_state = context.get('system_state', {})
            current_app = system_state.get('active_application', 'unknown')
            
            # Use efficient automation handler
            if self.automation_handler:
                if FAST_AUTOMATION_AVAILABLE:
                    result = await self.automation_handler(
                        message, 
                        current_app, 
                        system_context=system_state
                    )
                elif ENHANCED_AUTOMATION_AVAILABLE:
                    result = await self.automation_handler.execute_task(
                        message,
                        context=system_state
                    )
                else:
                    result = await self.automation_handler(
                        message,
                        system_context=system_state
                    )
                
                return {
                    'response': result.get('response', 'Task completed'),
                    'mode': 'agent',
                    'actions_taken': result.get('actions_taken', []),
                    'success': result.get('success', True),
                    'system_integration': True,
                    'context': system_state
                }
            else:
                return {
                    'response': 'Agent automation not available',
                    'mode': 'agent',
                    'success': False,
                    'error': 'No automation handler available'
                }
                
        except Exception as e:
            logger.error(f"Agent mode error: {e}")
            return {
                'response': f'Agent mode error: {str(e)}',
                'mode': 'agent',
                'success': False,
                'error': str(e)
            }
    
    async def _handle_ask_mode(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ask mode with contextual memory"""
        try:
            # Get relevant context from memory
            memory_context = await get_context_for_query(message)
            
            # Include system state in context
            system_state = context.get('system_state', {})
            full_context = f"""
System Context: {json.dumps(system_state, indent=2)}
Memory Context: {memory_context}
User Question: {message}
"""
            
            # Send to brain router for processing
            brain_response = await self._query_brain_router({
                'message': message,
                'mode': 'ask',
                'context': full_context,
                'system_integration': True
            })
            
            response_text = brain_response.get('response', 'I apologize, but I cannot provide a response right now.')
            
            # Store interaction in memory
            await add_memory(
                f"User asked: {message}. Response: {response_text}",
                source="ask_mode",
                tags={"conversation", "ask_mode"}
            )
            
            return {
                'response': response_text,
                'mode': 'ask',
                'context_used': True,
                'system_integration': True,
                'memory_context': memory_context[:200] + "..." if len(memory_context) > 200 else memory_context
            }
            
        except Exception as e:
            logger.error(f"Ask mode error: {e}")
            return {
                'response': f'I encountered an error: {str(e)}',
                'mode': 'ask',
                'error': str(e)
            }
    
    async def _handle_suggest_mode(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle suggest mode with system-aware suggestions"""
        try:
            system_state = context.get('system_state', {})
            current_app = system_state.get('active_application', 'unknown')
            ui_elements = system_state.get('visible_ui_elements', [])
            
            # Generate context-aware suggestions
            suggestion_context = f"""
Current Application: {current_app}
Available UI Elements: {len(ui_elements)} elements
User Input: {message}
System Integration: Active

Generate helpful suggestions based on the current system state.
"""
            
            brain_response = await self._query_brain_router({
                'message': suggestion_context,
                'mode': 'suggest',
                'context': suggestion_context,
                'system_integration': True
            })
            
            suggestions = brain_response.get('response', 'No suggestions available.')
            
            return {
                'response': suggestions,
                'mode': 'suggest',
                'current_app': current_app,
                'ui_elements_count': len(ui_elements),
                'system_integration': True
            }
            
        except Exception as e:
            logger.error(f"Suggest mode error: {e}")
            return {
                'response': f'Suggestion error: {str(e)}',
                'mode': 'suggest',
                'error': str(e)
            }
    
    async def _handle_general_mode(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general chat mode"""
        try:
            brain_response = await self._query_brain_router({
                'message': message,
                'mode': 'general',
                'context': context,
                'system_integration': True
            })
            
            return {
                'response': brain_response.get('response', 'I apologize, but I cannot respond right now.'),
                'mode': 'general',
                'system_integration': True
            }
            
        except Exception as e:
            logger.error(f"General mode error: {e}")
            return {
                'response': f'General chat error: {str(e)}',
                'mode': 'general',
                'error': str(e)
            }
    
    async def _query_brain_router(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Query the brain router for LLM responses"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.brain_router_url,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Brain router error: {response.status}")
                        return {'response': 'Brain router unavailable'}
                        
        except Exception as e:
            logger.error(f"Error querying brain router: {e}")
            return {'response': f'Error connecting to brain router: {str(e)}'}
    
    async def _broadcast_to_clients(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if not self.connected_clients:
            return
        
        message_str = json.dumps(message)
        disconnected_clients = set()
        
        for client in self.connected_clients:
            try:
                await client.send(message_str)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        self.connected_clients -= disconnected_clients

async def main():
    """Main function to start the enhanced enterprise backend"""
    backend = EnhancedEnterpriseBackendEfficient()
    
    try:
        logger.info("🚀 Starting Enhanced Enterprise Backend with Efficient Integration")
        await backend.start_server()
    except KeyboardInterrupt:
        logger.info("🛑 Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
    finally:
        logger.info("🔚 Enhanced Enterprise Backend shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())