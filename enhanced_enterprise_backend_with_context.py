#!/usr/bin/env python3
"""
Enhanced Enterprise Backend 8767 with Contextual Memory Integration
Provides fully contextual AI responses using semantic search across all modes
Now with efficient OS-integrated system monitoring (replaces heavy screen capture)
"""

import asyncio
import json
import logging
import websockets
import time
import subprocess
import requests
import aiohttp
from aiohttp import web
import sys
import os
import numpy as np
import cv2
from datetime import datetime
from typing import Dict, Any, Set, Optional, Tuple, List
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import uuid
from agent_workflow.enhanced_automation_handler import EnhancedAutomationHandler
from fixed_universal_automation_handler import fixed_handle_universal_automation
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
# --- ADD: Import Hybrid Plan Creator ---
from llm_plan_creator import plan_creator

# Setup enhanced logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backend/enhanced_enterprise_8767.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize input controller only once at module level
input_controller = None
try:
    from agent_workflow.input_controller import InputController
    input_controller = InputController()
    logger.info("✅ Input controller initialized (safe mode)")
except Exception as e:
    logger.error(f"Failed to initialize input controller: {e}")
    # Try alternative initialization
    try:
        import sys
        sys.path.append('.')
        from agent_workflow.input_controller import InputController
        input_controller = InputController()
        logger.info("✅ Input controller initialized (alternative method)")
    except Exception as e2:
        logger.error(f"Failed to initialize input controller with alternative method: {e2}")
        input_controller = None

# Import efficient system bridge (replaces screen capture)
try:
    from enhanced_realtime_system_bridge import EnhancedRealtimeSystemBridge, SystemEvent, SystemState
    EFFICIENT_SYSTEM_AVAILABLE = True
    logger.info("🚀 Efficient system bridge available - no more screen capture overhead!")
except ImportError:
    EFFICIENT_SYSTEM_AVAILABLE = False
    logger.warning("⚠️ Efficient system bridge not available, falling back to screen capture")

# Import warmup manager for fast LLM responses
try:
    from llm_warmup_manager import get_warmup_manager
    WARMUP_MANAGER_AVAILABLE = True
    logger.info("🔥 LLM Warmup Manager available for fast responses")
except ImportError:
    WARMUP_MANAGER_AVAILABLE = False
    logger.warning("⚠️ LLM Warmup Manager not available")

# Add memory module to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from memory.semantic_search_agent import SemanticSearchAgent, get_context_for_query, add_memory
    SEMANTIC_SEARCH_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import semantic search: {e}")
    SEMANTIC_SEARCH_AVAILABLE = False

# Initialize automation handlers with proper error handling
ENHANCED_AUTOMATION_AVAILABLE = False
FAST_AUTOMATION_AVAILABLE = False
UNIVERSAL_AVAILABLE = False
REAL_AGENT_AUTOMATION_AVAILABLE = False
AUTOMATION_AVAILABLE = False

# Try Real Agent Automation Handler first
try:
    from real_agent_automation_handler import RealAgentAutomationHandler
    REAL_AGENT_AUTOMATION_AVAILABLE = True
    AUTOMATION_AVAILABLE = True
    logger.info("✅ Real Agent Automation Handler enabled")
except ImportError as e:
    logger.warning(f"⚠️ Real Agent Automation Handler not available: {e}")

# Try Enhanced Automation Handler as fallback
if not REAL_AGENT_AUTOMATION_AVAILABLE:
    try:
        from agent_workflow.enhanced_automation_handler import EnhancedAutomationHandler
        ENHANCED_AUTOMATION_AVAILABLE = True
        AUTOMATION_AVAILABLE = True
        logger.info("✅ Enhanced Automation Handler enabled (fallback)")
    except ImportError as e:
        logger.warning(f"⚠️ Enhanced Automation Handler not available: {e}")

# Try Universal Intelligent Automation Handler
universal_automation_handler = None
try:
    from universal_intelligent_automation_handler import UniversalIntelligentAutomationHandler
    UNIVERSAL_AVAILABLE = True
    if universal_automation_handler is None:
        universal_automation_handler = UniversalIntelligentAutomationHandler()
    logger.info("✅ Universal Intelligent Automation Handler loaded")
except ImportError as e:
    logger.warning(f"⚠️ Universal handler not available: {e}")

# Import brain router
try:
    from brain.core.brain_router import get_brain_router
    BRAIN_ROUTER_AVAILABLE = True
    logger.info("🧠 Brain Router available for intelligent mode handling")
except ImportError as e:
    logger.error(f"Failed to import brain router: {e}")
    BRAIN_ROUTER_AVAILABLE = False

class ChatMode(str, Enum):
    AGENT = "Agent"
    ASK = "Ask" 
    SUGGEST = "Suggest"
    GENERAL = "General"

# Shared dictionary for pending plans across all instances
shared_pending_plans = {}

class ContextualAIBackend:
    def __init__(self):
        self.contextual_knowledge_initialized = False
        self.connected_clients: Set[str] = set()
        self.sessions: Dict[str, Dict] = {}
        self.start_time = datetime.now()
        self.ollama_available = False
        
        # Initialize brain router if available
        self.brain_router = None
        
        # Initialize semantic search agent if available
        if SEMANTIC_SEARCH_AVAILABLE:
            try:
                self.semantic_agent = SemanticSearchAgent()
                logger.info("✅ Enhanced semantic search agent initialized")
            except Exception as e:
                logger.error(f"Failed to initialize semantic agent: {e}")
                self.semantic_agent = None
        else:
            self.semantic_agent = None
        
        # Initialize pending_plans dictionary
        self.pending_plans = shared_pending_plans
        logger.info("✅ Initialized pending_plans dictionary")
        
        # Initialize system bridge if available
        self.system_bridge = None
        self.current_system_state = None
        self.system_integration_active = False
        
        if EFFICIENT_SYSTEM_AVAILABLE:
            try:
                self.system_bridge = EnhancedRealtimeSystemBridge()
                self.system_integration_active = True
                logger.info("🚀 Efficient system bridge initialized")
            except Exception as e:
                logger.error(f"Failed to initialize system bridge: {e}")
                self.system_integration_active = False
        
        # Initialize screen monitoring
        self.screen_monitoring_active = False
        self.execution_verification_enabled = True
        self.execution_history = []
        self.last_screen_state = None
        self.visual_changes_history = []
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Use the global input controller
        self.input_controller = input_controller
        if self.input_controller is not None:
            logger.info("✅ Input controller initialized successfully")
        else:
            logger.error("❌ Input controller is None - automation will not work!")
        
        # Initialize automation handler
        try:
            self.automation_handler = EnhancedAutomationHandler()
            logger.info("✅ EnhancedAutomationHandler initialized for automation_handler")
        except Exception as e:
            self.automation_handler = None
            logger.warning(f"⚠️ Could not initialize EnhancedAutomationHandler: {e}")
        
        # Initialize optimized LLM-powered plan creator (no fallbacks)
        self.llm_plan_creator = plan_creator
        # --- ADD: Store generated plans for execution ---
        self.generated_plans = {}
        logger.info("✅ ContextualAIBackend initialized successfully")

    async def initialize(self):
        """Initialize async components"""
        # Initialize brain router if available
        if BRAIN_ROUTER_AVAILABLE:
            try:
                self.brain_router = await get_brain_router()
                logger.info("✅ Brain Router initialized asynchronously")
            except Exception as e:
                logger.error(f"Failed to initialize brain router asynchronously: {e}")
                self.brain_router = None
        else:
            logger.warning("⚠️ Brain Router not available - using fallback handlers")
        
        # Initialize the LLM plan creator
        try:
            await self.llm_plan_creator.initialize()
            logger.info("✅ LLM Plan Creator initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM Plan Creator: {e}")
        
    async def _warmup_llm(self):
        """Warm up the LLM with a simple prompt to avoid cold starts"""
        try:
            if hasattr(self.llm_plan_creator, 'llm_service') and hasattr(self.llm_plan_creator.llm_service, 'llm_client'):
                warmup_messages = [{"role": "user", "content": "Hello, are you ready?"}]
                await self.llm_plan_creator.llm_service.llm_client.generate_response(warmup_messages, max_tokens=10)
                logger.info("🔥 LLM warmed up successfully")
        except Exception as e:
            logger.warning(f"⚠️ LLM warmup failed: {e}")
        
    def check_ollama_availability(self) -> bool:
        """Check if Ollama is available on the system"""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=1)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            return False
            
    async def _initialize_contextual_knowledge(self):
        """Initialize contextual knowledge in memory"""
        enterprise_knowledge = [
            "Enterprise AI Backend on port 8767 provides contextual responses across all chat modes",
            "System integrates Ollama LLM with semantic memory for intelligent context-aware responses",
            "Agent mode uses context to understand UI automation patterns and user preferences",
            "Ask mode retrieves relevant information from memory to provide accurate contextual answers",
            "Suggest mode analyzes user patterns and context to provide personalized recommendations",
            "General mode maintains conversation context for natural flowing interactions",
            "All responses are enhanced with memory context for personalized user experience",
            "System learns from every interaction to improve future response quality",
            "Memory system stores conversation history, user preferences, and interaction patterns",
            "Contextual confidence scoring helps determine response accuracy and relevance"
        ]
        
        for knowledge in enterprise_knowledge:
            await add_memory(knowledge, source="enterprise_system", tags={"enterprise", "system_capabilities"})
        
        logger.info("Enterprise contextual knowledge initialized")

    # ==================== TEAMVIEWER-STYLE SCREEN CONTROL METHODS ====================
    
    async def capture_screen_fast(self, region: Optional[Tuple[int, int, int, int]] = None) -> Optional[np.ndarray]:
        """Get system context efficiently (replaces screen capture when system bridge available)"""
        
        # Use efficient system integration when available
        if self.system_integration_active and self.system_bridge:
            try:
                # Get current system state instead of screen capture
                system_state = await self.system_bridge.get_current_system_state()
                
                if system_state:
                    self.current_system_state = system_state
                    # Return system state as "context frame" for compatibility
                    # This is much more efficient than screen capture
                    logger.debug("System context captured via OS integration")
                    return np.array([[1]])  # Dummy array for compatibility
                else:
                    logger.warning("No system state available from bridge")
                    return None
                    
            except Exception as e:
                logger.error(f"System bridge capture failed: {e}")
                # Fall through to screen capture fallback
        
        # Fallback to traditional screen capture if system bridge not available
        if not EFFICIENT_SYSTEM_AVAILABLE:
            logger.warning("Screen capture not available - Efficient system bridge not installed")
            return None
            
        try:
            loop = asyncio.get_event_loop()
            
            def _capture():
                try:
                    if region:
                        # Capture specific region (x, y, width, height)
                        bbox = (region[0], region[1], region[0] + region[2], region[1] + region[3])
                        screenshot = PIL.ImageGrab.grab(bbox=bbox)
                    else:
                        # Full screen capture
                        screenshot = PIL.ImageGrab.grab()
                    
                    return np.array(screenshot)
                except Exception as e:
                    logger.error(f"Screen capture error: {e}")
                    return None
            
            screenshot = await loop.run_in_executor(self.executor, _capture)
            self.last_screen_state = screenshot
            return screenshot
            
        except Exception as e:
            logger.error(f"Fast screen capture failed: {e}")
            return None
    
    async def detect_visual_changes(self, before: np.ndarray, after: np.ndarray, 
                                  threshold: float = 0.1) -> Dict[str, Any]:
        """Detect visual changes between two screenshots (TeamViewer-style verification)"""
        try:
            if before is None or after is None:
                return {'changes_detected': False, 'confidence': 0.0}
            
            # Ensure same dimensions
            if before.shape != after.shape:
                logger.warning("Screenshot dimensions don't match for comparison")
                return {'changes_detected': False, 'confidence': 0.0}
            
            # Calculate difference
            diff = cv2.absdiff(before, after)
            
            # Convert to grayscale for analysis
            if len(diff.shape) == 3:
                gray_diff = cv2.cvtColor(diff, cv2.COLOR_RGB2GRAY)
            else:
                gray_diff = diff
            
            # Calculate change metrics
            total_pixels = gray_diff.size
            changed_pixels = np.sum(gray_diff > 25)  # Threshold for significant change
            change_percentage = changed_pixels / total_pixels
            
            # Debug logging for change detection
            logger.debug(f"Change detection: {changed_pixels}/{total_pixels} pixels changed ({change_percentage:.3%})")
            
            # Find changed regions
            _, thresh = cv2.threshold(gray_diff, 25, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            changed_regions = []
            for contour in contours:
                if cv2.contourArea(contour) > 100:  # Filter small changes
                    x, y, w, h = cv2.boundingRect(contour)
                    changed_regions.append({
                        'x': int(x), 'y': int(y), 'width': int(w), 'height': int(h),
                        'area': int(cv2.contourArea(contour))
                    })
            
            changes_detected = change_percentage > threshold
            
            change_data = {
                'changes_detected': changes_detected,
                'change_percentage': float(change_percentage),
                'changed_pixels': int(changed_pixels),
                'total_pixels': int(total_pixels),
                'changed_regions': changed_regions,
                'confidence': min(1.0, change_percentage / threshold),
                'timestamp': time.time()
            }
            
            # Store in history
            self.visual_changes_history.append(change_data)
            if len(self.visual_changes_history) > 50:  # Keep last 50 changes
                self.visual_changes_history.pop(0)
            
            return change_data
            
        except Exception as e:
            logger.error(f"Visual change detection error: {e}")
            return {'changes_detected': False, 'confidence': 0.0, 'error': str(e)}
    
    async def execute_action_with_verification(self, action: Dict[str, Any], 
                                             websocket=None) -> Dict[str, Any]:
        """Execute action with efficient system verification (replaces visual comparison when possible)"""
        execution_id = f"exec_{int(time.time() * 1000)}"
        
        result = {
            'execution_id': execution_id,
            'action': action,
            'timestamp': time.time(),
            'success': False,
            'verification': {},
            'changes_detected': [],
            'error': None,
            'verification_method': 'system_integration' if self.system_integration_active else 'visual_comparison'
        }
        
        try:
            # 1. Capture pre-execution state (efficient system state vs screen capture)
            if self.execution_verification_enabled:
                logger.info(f"🔍 Capturing pre-execution state for: {action.get('description', 'unknown')}")
                
                if self.system_integration_active and self.system_bridge:
                    # Use efficient system state capture
                    before_state = await self.system_bridge.get_current_system_state()
                else:
                    # Fallback to screen capture
                    before_state = await self.capture_screen_fast()
                
                # Send real-time feedback to overlay
                if websocket:
                    await websocket.send(json.dumps({
                        'type': 'execution_start',
                        'action': action.get('description', 'Unknown action'),
                        'execution_id': execution_id,
                        'verification_method': result['verification_method'],
                        'timestamp': time.time()
                    }))
            
            # 2. Execute the action through system bridge when available
            if self.system_integration_active and self.system_bridge:
                try:
                    # Execute through efficient system bridge
                    execution_result = await self.system_bridge.execute_system_action(
                        action.get('type', 'unknown'),
                        action.get('parameters', {})
                    )
                    execution_success = execution_result.get('success', False)
                except Exception as e:
                    logger.error(f"System bridge execution failed: {e}")
                    # Fallback to traditional automation
                    execution_success = await self._execute_automation_action(action)
            else:
                # Use traditional automation handlers
                execution_success = await self._execute_automation_action(action)
            
            # 3. Post-execution verification
            if self.execution_verification_enabled and before_state is not None:
                await asyncio.sleep(0.2)  # Wait for system to respond
                
                if self.system_integration_active and self.system_bridge:
                    # Use efficient system state comparison
                    after_state = await self.system_bridge.get_current_system_state()
                    
                    if after_state:
                        # Detect system changes (much more efficient than visual diff)
                        changes = await self._detect_system_state_changes(before_state, after_state)
                        result['verification'] = changes
                        result['changes_detected'] = changes.get('change_details', [])
                        
                        # Determine success based on system changes
                        if changes.get('changes_detected', False):
                            result['success'] = True
                            logger.info(f"✅ Action verified via system integration: {len(changes.get('change_details', []))} changes")
                        else:
                            result['success'] = execution_success
                            logger.info("ℹ️ No system changes detected, using execution result")
                    else:
                        result['success'] = execution_success
                else:
                    # Fallback to visual comparison
                    after_state = await self.capture_screen_fast()
                    
                    if after_state is not None and hasattr(before_state, 'shape'):
                        # Detect visual changes (traditional method)
                        changes = await self.detect_visual_changes(before_state, after_state)
                        result['verification'] = changes
                        result['changes_detected'] = changes.get('changed_regions', [])
                        
                        # Determine success based on visual changes
                        if changes.get('changes_detected', False):
                            result['success'] = True
                            logger.info(f"✅ Action verified visually: {changes.get('change_percentage', 0):.1%} screen changed")
                        else:
                            result['success'] = False
                            logger.warning("❌ No visual changes detected - action may have failed")
                    else:
                        result['success'] = execution_success
                
                # Send verification feedback
                if websocket:
                    await websocket.send(json.dumps({
                        'type': 'execution_verification',
                        'execution_id': execution_id,
                        'success': result['success'],
                        'changes': result.get('verification', {}),
                        'verification_method': result['verification_method'],
                        'timestamp': time.time()
                    }))
            else:
                result['success'] = execution_success
            
            # 4. Store execution history
            self.execution_history.append(result)
            if len(self.execution_history) > 100:  # Keep last 100 executions
                self.execution_history.pop(0)
                
        except Exception as e:
            logger.error(f"Action execution with verification failed: {e}")
            result['error'] = str(e)
            result['success'] = False
        
        return result
    
    async def _execute_automation_action(self, action: Dict[str, Any]) -> bool:
        """Execute automation action (integrate with existing automation handlers)"""
        try:
            # Integrate with your existing fast automation handler
            if FAST_AUTOMATION_AVAILABLE and hasattr(universal_automation_handler, 'execute_single_action'):
                return await universal_automation_handler.execute_single_action(action)
            elif self.automation_handler and hasattr(self.automation_handler, 'execute_action'):
                return await self.automation_handler.execute_action(action)
            else:
                # Placeholder for basic action execution
                await asyncio.sleep(0.1)
                return True
        except Exception as e:
            logger.error(f"Automation action execution failed: {e}")
            return False
    
    async def _detect_system_state_changes(self, before_state: 'SystemState', after_state: 'SystemState') -> Dict[str, Any]:
        """Detect changes in system state (replaces visual diff for efficiency)"""
        try:
            changes = {
                'changes_detected': False,
                'confidence': 0.0,
                'change_details': [],
                'timestamp': time.time(),
                'method': 'system_state_comparison'
            }
            
            # Check application changes
            if before_state.active_application != after_state.active_application:
                changes['changes_detected'] = True
                changes['confidence'] = 0.9
                changes['change_details'].append(f'Application changed: {before_state.active_application} -> {after_state.active_application}')
            
            # Check window changes
            if before_state.focused_window != after_state.focused_window:
                changes['changes_detected'] = True
                changes['confidence'] = max(changes['confidence'], 0.8)
                changes['change_details'].append(f'Window changed: {before_state.focused_window} -> {after_state.focused_window}')
            
            # Check UI element changes
            before_elements = len(before_state.visible_ui_elements)
            after_elements = len(after_state.visible_ui_elements)
            
            if abs(before_elements - after_elements) > 0:
                changes['changes_detected'] = True
                changes['confidence'] = max(changes['confidence'], 0.7)
                changes['change_details'].append(f'UI elements changed: {before_elements} -> {after_elements}')
            
            # Check for new events
            before_events = len(before_state.recent_events)
            after_events = len(after_state.recent_events)
            
            if after_events > before_events:
                changes['changes_detected'] = True
                changes['confidence'] = max(changes['confidence'], 0.6)
                changes['change_details'].append(f'New system events: {after_events - before_events}')
            
            # Check running processes changes
            before_processes = set(before_state.running_processes)
            after_processes = set(after_state.running_processes)
            
            new_processes = after_processes - before_processes
            stopped_processes = before_processes - after_processes
            
            if new_processes:
                changes['changes_detected'] = True
                changes['confidence'] = max(changes['confidence'], 0.5)
                changes['change_details'].append(f'New processes: {list(new_processes)[:3]}')  # Limit to 3
            
            if stopped_processes:
                changes['changes_detected'] = True
                changes['confidence'] = max(changes['confidence'], 0.5)
                changes['change_details'].append(f'Stopped processes: {list(stopped_processes)[:3]}')  # Limit to 3
            
            logger.debug(f"System state changes detected: {changes['changes_detected']} with confidence {changes['confidence']}")
            return changes
            
        except Exception as e:
            logger.error(f"Error detecting system state changes: {e}")
            return {
                'changes_detected': False,
                'confidence': 0.0,
                'change_details': [],
                'error': str(e),
                'method': 'system_state_comparison'
            }
    
    async def handle_agent_execution_with_verification(self, data: Dict[str, Any], 
                                                     client_id: str, websocket) -> Dict[str, Any]:
        """Handle enhanced agent execution with TeamViewer-style verification"""
        message = data.get("message", "")
        session_id = data.get("session_id", client_id)
        execution_mode = data.get("execution_mode", "verified")  # "verified", "monitored", "basic"
        
        logger.info(f"🎯 Enhanced Agent Execution: {message} (mode: {execution_mode})")
        
        try:
            # Get context for the query
            context = await get_context_for_query(message, max_context_length=500)
            
            # Check if automation is available (prefer Universal over Fast)
            if UNIVERSAL_AVAILABLE or FAST_AUTOMATION_AVAILABLE:
                logger.info("⚡ Creating automation plan with visual verification")
                
                # Create automation plan using real LLM
                if UNIVERSAL_AVAILABLE:
                    plan_result = await universal_automation_handler.create_universal_automation_plan(message, session_id)
                elif FAST_AUTOMATION_AVAILABLE:
                    plan_result = await universal_automation_handler.create_universal_automation_plan(message, session_id)
                else:
                    plan_result = {"success": False, "response": "No automation handler available"}
                
                if plan_result.get("success", False):
                    # Send plan to client for confirmation
                    plan_response = {
                        "type": "agent_plan_ready",
                        "plan": plan_result,
                        "execution_mode": execution_mode,
                        "requires_confirmation": True,
                        "verification_enabled": self.execution_verification_enabled
                    }
                    
                    await websocket.send(json.dumps(plan_response))
                    
                    # Store plan for execution
                    if not hasattr(self, 'pending_verified_plans'):
                        self.pending_verified_plans = {}
                        
                    plan_id = plan_result.get("plan_id", f"plan_{int(time.time())}")
                    self.pending_verified_plans[plan_id] = {
                        "plan": plan_result,
                        "context": context,
                        "execution_mode": execution_mode,
                        "websocket": websocket,
                        "timestamp": time.time()
                    }
                    
                    return {
                        "success": True,
                        "response": "✅ Enhanced automation plan created with visual verification. Awaiting confirmation.",
                        "plan_id": plan_id,
                        "execution_mode": execution_mode
                    }
                else:
                    return {
                        "success": False,
                        "response": "❌ Failed to create automation plan",
                        "error": plan_result.get("error", "Unknown error")
                    }
            else:
                return {
                    "success": False,
                    "response": "❌ Enhanced agent execution not available - fast automation handler not found",
                    "error": "FAST_AUTOMATION_AVAILABLE is False"
                }
                
        except Exception as e:
            logger.error(f"Enhanced agent execution error: {e}")
            return {
                "success": False,
                "response": f"❌ Enhanced agent execution failed: {str(e)}",
                "error": str(e)
            }
    
    async def _send_execution_progress(self, websocket, client_id, plan_id, progress_data):
        """Send execution progress update to client via WebSocket"""
        if not websocket:
            logger.warning(f"Cannot send progress update - no websocket for plan: {plan_id}")
            return
            
        try:
            await websocket.send(json.dumps({
                "type": "agent_progress",
                "plan_id": plan_id,
                "client_id": client_id,
                "step": progress_data.get("step", 0),
                "message": progress_data.get("message", ""),
                "progress": progress_data.get("progress", 0),
                "timestamp": time.time()
            }))
            
            logger.debug(f"📊 Progress update sent for plan {plan_id}: {progress_data.get('progress')}%")
        except Exception as e:
            logger.error(f"❌ Failed to send progress update: {e}")
    
    async def _send_progress_update(self, client_id, plan_id, progress_data):
        """Legacy method - redirects to _send_execution_progress for compatibility"""
        # Find the websocket for this client
        websocket = None
        for client_session in self.sessions.values():
            if client_session.get("client_id") == client_id:
                websocket = client_session.get("websocket")
                break
        
        # Send progress update using the new method
        await self._send_execution_progress(websocket, client_id, plan_id, progress_data)
    
    

    async def execute_verified_plan(self, plan_id: str, session_id: str = None) -> Dict[str, Any]:
        """Execute a verified plan with comprehensive reasoning and step-by-step completion tracking"""
        try:
            if session_id is None:
                session_id = plan_id

            logger.info(f"🎯 Executing plan {plan_id} for session {session_id}")

            # Initialize execution tracking
            execution_results = []
            steps_completed = 0
            steps_failed = 0
            total_execution_time = 0
            start_time = time.time()

            # Try to load the plan from generated_plans first, then from persistence
            plan = None
            
            # First check if we have the plan in memory
            logger.info(f"🔍 Looking for plan {plan_id} in generated_plans (available: {list(self.generated_plans.keys())})")
            if plan_id in self.generated_plans:
                plan = self.generated_plans[plan_id]
                logger.info(f"✅ Found plan {plan_id} in generated_plans")
            else:
                logger.warning(f"⚠️ Plan {plan_id} not found in generated_plans, checking persistence...")
                # Try to load from persistence
            try:
                from plan_persistence import load_plan
                plan = await load_plan(plan_id)  # Add await here
                if plan:
                    logger.info(f"✅ Loaded plan {plan_id} from persistence")
                    # Also store it in memory for future use
                    self.generated_plans[plan_id] = plan
                    logger.info(f"✅ Stored plan {plan_id} in generated_plans for future use")
                else:
                    logger.warning(f"⚠️ Plan {plan_id} not found in persistence")
            except Exception as e:
                logger.warning(f"⚠️ Could not load plan from persistence: {e}")
            
            # If still no plan, use fallback
            if not plan:
                logger.warning(f"⚠️ Using fallback plan for {plan_id}")
                plan = {
                    "title": "Fallback Test Plan",
                    "description": "Open Safari and search for SEGEV",
                    "steps": [
                        {"description": "Open Safari browser", "action_type": "open_app", "target": "Safari"},
                        {"description": "Enter SEGEV in search bar", "action_type": "type_text", "value": "SEGEV"},
                        {"description": "Click search button", "action_type": "click_element", "target": "search_button"}
                    ]
                }

            total_steps = len(plan.get("steps", []))
            logger.info(f"📋 Plan contains {total_steps} steps to execute")

            # Execute each step with comprehensive tracking
            try:
                # Use the global input controller instead of creating a new one
                if self.input_controller is None:
                    logger.error("❌ Input controller is not available - cannot execute automation")
                    return {
                        "success": False,
                        "plan_id": plan_id,
                        "session_id": session_id,
                        "error": "Input controller not available",
                        "steps_completed": 0,
                        "steps_failed": total_steps,
                        "total_steps": total_steps,
                        "total_execution_time": time.time() - start_time,
                        "execution_results": [],
                        "summary": "❌ Cannot execute plan: Input controller not available"
                    }
                
                logger.info(f"🤖 Using input controller: {type(self.input_controller)}")
                
                for i, step in enumerate(plan.get("steps", []), 1):
                    step_start_time = time.time()
                    step_description = step.get("description", "Unknown step")
                    action_type = step.get("action_type", "click_element")
                    target = step.get("target", "")
                    value = step.get("value", "")
                    
                    logger.info(f"🔄 Executing step {i}/{total_steps}: {step_description}")
                    
                    # Initialize step result
                    step_result = {
                        "step_number": i,
                        "description": step_description,
                        "action_type": action_type,
                        "target": target,
                        "value": value,
                        "start_time": step_start_time,
                        "success": False,
                        "reasoning": "",
                        "error": None,
                        "execution_time": 0
                    }
                    
                    try:
                        # Execute the step based on action type with reasoning
                        logger.info(f"🎯 Executing action: {action_type} with target='{target}' value='{value}'")
                        
                        if action_type == "hotkey":
                            # Handle hotkey combinations like cmd+space
                            hotkey = target if target else "cmd+space"
                            logger.info(f"⌨️ Pressing hotkey: {hotkey}")
                            if hotkey == "cmd+space":
                                # Simulate Cmd+Space for Spotlight on macOS
                                self.input_controller.hotkey("command", "space")
                            else:
                                # For other hotkeys, try to parse and execute
                                keys = hotkey.split("+")
                                # Convert cmd to command for macOS
                                keys = ["command" if key == "cmd" else key for key in keys]
                                self.input_controller.hotkey(*keys)
                            await asyncio.sleep(1)
                            step_result["success"] = True
                            step_result["reasoning"] = f"Successfully pressed hotkey: {hotkey}"
                            
                        elif action_type == "open_app":
                            # Open application using Spotlight on macOS
                            app_name = target if target else "Safari"
                            logger.info(f"🚀 Opening application: {app_name}")
                            # Use Spotlight to open the application
                            self.input_controller.hotkey("command", "space")
                            await asyncio.sleep(0.5)
                            self.input_controller.type_text(app_name)
                            await asyncio.sleep(0.5)
                            self.input_controller.press_key("return")
                            await asyncio.sleep(2)
                            step_result["success"] = True
                            step_result["reasoning"] = f"Successfully opened {app_name} application using Spotlight"
                            
                        elif action_type == "type_text":
                            # Type text
                            text_to_type = value if value else step_description
                            logger.info(f"⌨️ Typing text: '{text_to_type}'")
                            self.input_controller.type_text(text_to_type)
                            await asyncio.sleep(1)
                            step_result["success"] = True
                            step_result["reasoning"] = f"Successfully typed text: '{text_to_type}'"
                            
                        elif action_type == "click_element":
                            # Click element
                            element_name = target if target else "element"
                            logger.info(f"🖱️ Clicking {element_name}")
                            self.input_controller.press_key("return")  # Press Enter as default click
                            await asyncio.sleep(1)
                            step_result["success"] = True
                            step_result["reasoning"] = f"Successfully clicked {element_name}"
                            
                        elif action_type == "press_key":
                            # Press specific key
                            key = target if target else "return"
                            logger.info(f"🔤 Pressing key: {key}")
                            self.input_controller.press_key(key)
                            await asyncio.sleep(1)
                            step_result["success"] = True
                            step_result["reasoning"] = f"Successfully pressed key: {key}"
                            
                        elif action_type == "wait":
                            # Wait for specified duration
                            duration = float(value) if value else 1.0
                            logger.info(f"⏱️ Waiting for {duration} seconds")
                            await asyncio.sleep(duration)
                            step_result["success"] = True
                            step_result["reasoning"] = f"Successfully waited for {duration} seconds"
                            
                        else:
                            # Default action - click
                            logger.info(f"🖱️ Performing default click action for unknown action_type: {action_type}")
                            self.input_controller.click()
                            await asyncio.sleep(1)
                            step_result["success"] = True
                            step_result["reasoning"] = f"Successfully performed default click action for {action_type}"
                        
                        # Update step completion tracking
                        if step_result["success"]:
                            steps_completed += 1
                            logger.info(f"✅ Completed step {i}: {step_description}")
                        else:
                            steps_failed += 1
                            logger.warning(f"❌ Failed step {i}: {step_description}")
                    
                    except Exception as step_error:
                        # Handle step execution error
                        error_msg = str(step_error)
                        logger.error(f"❌ Error executing step {i}: {error_msg}")
                        step_result["success"] = False
                        step_result["error"] = error_msg
                        step_result["reasoning"] = f"Step failed due to error: {error_msg}"
                        steps_failed += 1
                    
                    # Calculate step execution time
                    step_end_time = time.time()
                    step_result["execution_time"] = step_end_time - step_start_time
                    step_result["end_time"] = step_end_time
                    
                    # Add step result to execution results
                    execution_results.append(step_result)
                    
                    # Log step completion with reasoning
                    if step_result["success"]:
                        logger.info(f"✅ Step {i} completed successfully in {step_result['execution_time']:.2f}s: {step_result['reasoning']}")
                    else:
                        logger.error(f"❌ Step {i} failed in {step_result['execution_time']:.2f}s: {step_result['reasoning']}")
                
                # Calculate total execution time
                total_execution_time = time.time() - start_time
                
                # Generate comprehensive execution summary
                success_rate = steps_completed / total_steps if total_steps > 0 else 0
                overall_success = steps_completed == total_steps
                
                # Create detailed summary with reasoning
                summary_reasoning = self._generate_execution_summary(
                    plan_id, steps_completed, total_steps, success_rate, 
                    execution_results, total_execution_time
                )
                
                logger.info(f"🎉 Plan {plan_id} execution completed!")
                logger.info(f"📊 Results: {steps_completed}/{total_steps} steps successful ({success_rate:.1%} success rate)")
                logger.info(f"⏱️ Total execution time: {total_execution_time:.2f} seconds")
                
                return {
                    "success": overall_success,
                    "plan_id": plan_id,
                    "session_id": session_id,
                    "execution_completed": True,
                    "steps_completed": steps_completed,
                    "steps_failed": steps_failed,
                    "total_steps": total_steps,
                    "success_rate": success_rate,
                    "total_execution_time": total_execution_time,
                    "execution_results": execution_results,
                    "summary": summary_reasoning,
                    "detailed_reasoning": self._generate_detailed_reasoning(execution_results)
                }
                
            except Exception as e:
                logger.error(f"❌ Error during plan execution: {e}")
                total_execution_time = time.time() - start_time
                return {
                    "success": False,
                    "plan_id": plan_id,
                    "session_id": session_id,
                    "error": str(e),
                    "steps_completed": steps_completed,
                    "steps_failed": steps_failed,
                    "total_steps": total_steps,
                    "total_execution_time": total_execution_time,
                    "execution_results": execution_results,
                    "summary": f"Plan execution failed due to system error: {str(e)}"
                }

        except Exception as e:
            logger.error(f"❌ Error executing verified plan: {e}")
            return {
                "success": False,
                "response": f"❌ Error executing plan: {str(e)}",
                "error": str(e)
            }
    
    def _generate_execution_summary(self, plan_id: str, steps_completed: int, total_steps: int, 
                                  success_rate: float, execution_results: list, total_time: float) -> str:
        """Generate a comprehensive execution summary with reasoning"""
        summary = f"🎯 **Plan Execution Summary**\n\n"
        summary += f"**Plan ID:** {plan_id}\n"
        summary += f"**Completion:** {steps_completed}/{total_steps} steps ({success_rate:.1%} success rate)\n"
        summary += f"**Total Time:** {total_time:.2f} seconds\n\n"
        
        if success_rate == 1.0:
            summary += "✅ **All steps completed successfully!**\n"
            summary += "The plan was executed completely without any errors.\n"
        elif success_rate > 0.5:
            summary += "⚠️ **Most steps completed successfully**\n"
            summary += f"Some steps failed, but {steps_completed}/{total_steps} were successful.\n"
        else:
            summary += "❌ **Multiple steps failed**\n"
            summary += f"Only {steps_completed}/{total_steps} steps were successful.\n"
        
        return summary
    
    def _generate_detailed_reasoning(self, execution_results: list) -> str:
        """Generate detailed reasoning for each step"""
        detailed_reasoning = "📋 **Step-by-Step Execution Details**\n\n"
        
        for result in execution_results:
            step_num = result["step_number"]
            description = result["description"]
            success = result["success"]
            reasoning = result["reasoning"]
            execution_time = result["execution_time"]
            
            status_emoji = "✅" if success else "❌"
            detailed_reasoning += f"{status_emoji} **Step {step_num}:** {description}\n"
            detailed_reasoning += f"   ⏱️ Time: {execution_time:.2f}s\n"
            detailed_reasoning += f"   💭 Reasoning: {reasoning}\n\n"
        
        return detailed_reasoning
    
    async def _try_agnostic_deep_data_access(self, message: str, mode: str, client_id: str, websocket) -> Dict[str, Any]:
        """Try to handle universal agnostic deep data access for any query
        This is a powerful abstraction that can handle any specific data source
        Returns {"handled": True} if the message was handled, {"handled": False} otherwise
        """
        # Default result - not handled
        result = {"handled": False}
        
        # Only process for certain clear data extraction intents
        lower_message = message.lower()
        
        # Check for system stats queries
        if ("system" in lower_message and ("stats" in lower_message or "status" in lower_message)) or \
           ("what's running" in lower_message) or ("what is running" in lower_message):
            try:
                # Get running processes
                import psutil
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                    if proc.info['cpu_percent'] > 0.1 or proc.info['memory_percent'] > 0.1:
                        processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cpu': proc.info['cpu_percent'],
                            'memory': proc.info['memory_percent']
                        })
                
                # Sort by CPU usage
                processes.sort(key=lambda x: x['cpu'], reverse=True)
                top_processes = processes[:10]  # Top 10 processes
                
                # Format response
                response = "📊 **System Status**\n\n"
                response += "Top processes by CPU usage:\n\n"
                for i, proc in enumerate(top_processes):
                    response += f"{i+1}. {proc['name']} (PID: {proc['pid']}) - CPU: {proc['cpu']:.1f}%, Memory: {proc['memory']:.1f}%\n"
                
                # Send streaming response
                await websocket.send(json.dumps({
                    "type": "chat_response",
                    "mode": mode,
                    "response": response,
                    "client_id": client_id,
                    "timestamp": datetime.now().isoformat(),
                    "deep_data_access": True
                }))
                
                # Mark as handled
                result["handled"] = True
                logger.info(f"✅ Handled system stats query via deep data access")
                
            except Exception as e:
                logger.error(f"❌ Error handling system stats query: {e}")
                # Not handled - fall through to regular processing
        
        # Return result
        return result
    
    async def handle_contextual_chat_request_streaming(self, data: Dict[str, Any], client_id: str, websocket) -> None:
        """Handle chat requests with streaming responses for better UX"""
        try:
            message = data.get('message', '').strip()
            mode = data.get('mode', 'General').title()
            session_id = data.get('session_id', str(uuid.uuid4()))
            
            if not message:
                await websocket.send(json.dumps({
                    "type": "error",
                    "payload": {"message": "Empty message received"},
                    "session_id": session_id
                }))
                return
            
            logger.info(f"🔄 Processing streaming request for {mode} mode: {message[:100]}...")
            
            # Send initial acknowledgment
            await websocket.send(json.dumps({
                "type": "processing_started",
                "payload": {
                    "mode": mode,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                },
                "session_id": session_id
            }))
            
            # Handle different modes with streaming
            if mode == "Agent":
                await self._handle_agent_mode_streaming(message, session_id, websocket)
            elif mode == "Ask":
                await self._handle_ask_mode_streaming(message, session_id, websocket)
            elif mode == "Suggest":
                await self._handle_suggest_mode_streaming(message, session_id, websocket)
            else:
                await self._handle_general_mode_streaming(message, session_id, websocket)
                
        except Exception as e:
            logger.error(f"Error in streaming chat request: {e}")
            await websocket.send(json.dumps({
                "type": "error",
                "payload": {"message": f"Processing error: {str(e)}"},
                "session_id": session_id
            }))

    async def _handle_agent_mode_streaming(self, message: str, session_id: str, websocket):
        """Handle agent mode with streaming plan generation"""
        try:
            # Generate a proper plan ID
            plan_id = f"plan_{int(time.time())}"
            
            # Send plan generation start
            await websocket.send(json.dumps({
                "type": "plan_generation_started",
                "payload": {
                    "message": "Generating automation plan...",
                    "plan_id": plan_id,
                    "timestamp": datetime.now().isoformat()
                },
                "session_id": session_id
            }))
            
            # Stream plan generation
            plan_chunks = []
            async for chunk in self.llm_plan_creator.create_plan_streaming(message):
                plan_chunks.append(chunk)
                
                # Send progress updates
                if "🔄" in chunk or "✅" in chunk or "❌" in chunk:
                    await websocket.send(json.dumps({
                        "type": "plan_generation_progress",
                        "payload": {
                            "progress": chunk,
                                "plan_id": plan_id,
                            "timestamp": datetime.now().isoformat()
                        },
                        "session_id": session_id
                    }))
                elif chunk.startswith('{') and chunk.endswith('}'):
                    # This is the final JSON plan
                    try:
                        plan_data = json.loads(chunk)
                        # Add plan_id to the plan data
                        plan_data["plan_id"] = plan_id
                        plan_data["session_id"] = session_id
                        
                        await websocket.send(json.dumps({
                            "type": "plan_generated",
                            "payload": {
                                "plan": plan_data,
                                    "plan_id": plan_id,
                                "timestamp": datetime.now().isoformat()
                            },
                            "session_id": session_id
                            }))
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse plan JSON: {chunk}")
            
            # Send completion message
            await websocket.send(json.dumps({
                "type": "plan_generation_completed",
                "payload": {
                    "message": "Plan generation completed",
                    "plan_id": plan_id,
                    "timestamp": datetime.now().isoformat()
                },
                "session_id": session_id
            }))
            
        except Exception as e:
            logger.error(f"Error in agent mode streaming: {e}")
            await websocket.send(json.dumps({
                "type": "error",
                "payload": {"message": f"Agent mode error: {str(e)}"},
                "session_id": session_id
            }))

    async def _handle_ask_mode_streaming(self, message: str, session_id: str, websocket):
        """Handle ask mode with streaming responses"""
        try:
            # Send processing start
            await websocket.send(json.dumps({
                "type": "response_generation_started",
                "payload": {
                    "message": "Generating response...",
                    "timestamp": datetime.now().isoformat()
                },
                "session_id": session_id
            }))
            
            # First try deep data access for specific queries
            response = await self._try_agnostic_deep_data_access(message, "Ask", session_id, websocket)
            
            # If not handled by deep data access, use LLM service
            if not response.get("handled", False):
                logger.info(f"🤖 Using LLM service for Ask mode query: {message}")
                
                # Create a prompt for the LLM
                prompt = f"""You are a helpful AI assistant. The user asked: "{message}"

Please provide a helpful and informative response. If this is a request to open something or perform an action, explain how to do it or what the user might be looking for.

Response:"""
                
                try:
                    # Get response from LLM service
                    llm_response = await self.llm_service.generate_response(prompt)
                    
                    # Send the LLM response
                    await websocket.send(json.dumps({
                        "type": "response_generated",
                        "payload": {
                            "response": llm_response,
                            "mode": "Ask",
                            "handled": True
                        },
                        "session_id": session_id
                    }))
                    
                except Exception as llm_error:
                    logger.error(f"LLM service error: {llm_error}")
                    # Fallback response
                    await websocket.send(json.dumps({
                        "type": "response_generated",
                        "payload": {
                            "response": f"I understand you're asking about '{message}'. This appears to be a request to open something in Google. To open a search in Google, you can:\n\n1. Open your web browser\n2. Go to google.com\n3. Type '{message.replace('in Google', '').strip()}' in the search box\n4. Press Enter\n\nWould you like me to help you with anything specific about this?",
                            "mode": "Ask",
                            "handled": True
                        },
                        "session_id": session_id
                    }))
            else:
                # Deep data access handled it, send the response
                await websocket.send(json.dumps({
                    "type": "response_generated",
                    "payload": response,
                    "session_id": session_id
                }))
            
        except Exception as e:
            logger.error(f"Error in ask mode streaming: {e}")
            await websocket.send(json.dumps({
                "type": "error",
                "payload": {"message": f"Ask mode error: {str(e)}"},
                "session_id": session_id
            }))

    async def _handle_suggest_mode_streaming(self, message: str, session_id: str, websocket):
        """Handle suggest mode with streaming responses"""
        try:
            # Send processing start
            await websocket.send(json.dumps({
                "type": "suggestion_generation_started",
                "payload": {
                    "message": "Generating suggestions...",
                    "timestamp": datetime.now().isoformat()
                },
                "session_id": session_id
            }))
            
            # Use LLM service for suggestions
            logger.info(f"🤖 Using LLM service for Suggest mode query: {message}")
            
            # Create a prompt for suggestions
            prompt = f"""You are a helpful AI assistant that provides suggestions and recommendations. The user asked: "{message}"

Please provide helpful suggestions, tips, or recommendations related to their request. Be creative and practical.

Suggestions:"""
            
            try:
                # Get response from LLM service
                llm_response = await self.llm_service.generate_response(prompt)
                
                # Send the LLM response
                await websocket.send(json.dumps({
                    "type": "suggestion_generated",
                    "payload": {
                        "response": llm_response,
                        "mode": "Suggest",
                        "handled": True
                    },
                    "session_id": session_id
                }))
                
            except Exception as llm_error:
                logger.error(f"LLM service error: {llm_error}")
                # Fallback response
                await websocket.send(json.dumps({
                    "type": "suggestion_generated",
                    "payload": {
                        "response": f"Here are some suggestions for '{message}':\n\n1. Try breaking down your request into smaller steps\n2. Consider what specific outcome you're looking for\n3. Think about alternative approaches\n4. Ask for more specific guidance if needed\n\nWould you like me to elaborate on any of these suggestions?",
                        "mode": "Suggest",
                        "handled": True
                    },
                    "session_id": session_id
                }))
            
        except Exception as e:
            logger.error(f"Error in suggest mode streaming: {e}")
            await websocket.send(json.dumps({
                "type": "error",
                "payload": {"message": f"Suggest mode error: {str(e)}"},
                "session_id": session_id
            }))

    async def _handle_general_mode_streaming(self, message: str, session_id: str, websocket):
        """Handle general mode with streaming responses"""
        try:
            # Send processing start
            await websocket.send(json.dumps({
                "type": "response_generation_started",
                "payload": {
                    "message": "Generating response...",
                    "timestamp": datetime.now().isoformat()
                },
                "session_id": session_id
            }))
            
            # Use LLM service for general queries
            logger.info(f"🤖 Using LLM service for General mode query: {message}")
            
            # Create a prompt for general responses
            prompt = f"""You are a helpful AI assistant. The user said: "{message}"

Please provide a helpful and informative response. Be conversational and helpful.

Response:"""
            
            try:
                # Get response from LLM service
                llm_response = await self.llm_service.generate_response(prompt)
                
                # Send the LLM response
                await websocket.send(json.dumps({
                    "type": "response_generated",
                    "payload": {
                        "response": llm_response,
                        "mode": "General",
                        "handled": True
                    },
                    "session_id": session_id
                }))
                
            except Exception as llm_error:
                logger.error(f"LLM service error: {llm_error}")
                # Fallback response
                await websocket.send(json.dumps({
                    "type": "response_generated",
                    "payload": {
                        "response": f"I understand you said: '{message}'. I'm here to help! Could you please clarify what you'd like me to assist you with?",
                        "mode": "General",
                        "handled": True
                    },
                    "session_id": session_id
                }))
            
        except Exception as e:
            logger.error(f"Error in general mode streaming: {e}")
            await websocket.send(json.dumps({
                "type": "error",
                "payload": {"message": f"General mode error: {str(e)}"},
                "session_id": session_id
            }))
            
    async def handle_websocket(self, websocket, path=None):
        """Handle WebSocket connections with proper path parameter support"""
        client_id = f"client_{int(time.time() * 1000)}"
        client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
        
        self.connected_clients.add(client_id)
        logger.info(f"Client connected: {client_id} from {client_ip} on path: {path}")
        
        # Store client info in sessions
        self.sessions[client_id] = {
            "client_id": client_id,
            "connected_at": datetime.now().isoformat(),
            "ip": client_ip,
            "path": path,
            "websocket": websocket
        }
        
        try:
            registered = False
            while True:
                message = await websocket.recv()
                logger.info(f"[WS] Received raw message: {message}")
                try:
                    data = json.loads(message)
                    # --- PATCH: Always set session_id and client_id early ---
                    client_id = data.get('client_id') or str(uuid.uuid4())
                    session_id = data.get('session_id') or client_id
                    msg_type = data.get('type', '')
                    logger.info(f"[WS] Routing message type: {msg_type} from {client_id} | Full data: {data}")

                    # Handle registration (only first message)
                    if msg_type == 'register':
                        if not registered:
                            logger.info(f"[WS] Registration message from {client_id}")
                            await websocket.send(json.dumps({
                                "type": "registration_confirmed",
                                    "client_id": client_id,
                                    "timestamp": datetime.now().isoformat(),
                                "capabilities": [
                                    "plan_execution",
                                    "verification",
                                    "context_tracking"
                                ]
                                }))
                            registered = True
                        else:
                            logger.info(f"[WS] Ignoring duplicate registration from {client_id}")
                        continue
                    # After registration, always route by type
                    if msg_type == 'chat' or msg_type == 'automation_request':
                        user_request = data.get('query', '')
                        plan_result = await self.llm_plan_creator.create_llm_plan(user_request, session_id)
                        if plan_result["success"]:
                            plan_id = plan_result["plan_id"]
                            # --- ADD: Store plan for later execution ---
                            self.generated_plans[plan_id] = plan_result
                            await websocket.send(json.dumps({
                                "type": "plan_created",
                                    "plan_id": plan_id,
                                "plan": plan_result,
                                    "client_id": client_id,
                                    "session_id": session_id,
                                    "timestamp": datetime.now().isoformat(),
                                "success": True
                                }))
                        else:
                            await websocket.send(json.dumps({
                                "type": "plan_error",
                                "error": plan_result.get("response", "Plan creation failed"),
                                    "client_id": client_id,
                                    "session_id": session_id,
                                    "timestamp": datetime.now().isoformat(),
                                "success": False
                                }))
                        continue
                    elif msg_type == 'query':
                        # Handle query messages (including /do_ commands from overlay)
                        try:
                            message = data.get('payload', {}).get('message', '')
                            logger.info(f"Processing query message: {message}")
                            # Check if this is a /do_ command from overlay
                            if message.startswith('/do_'):
                                # Extract action and plan_id from /do_execute plan_id format
                                parts = message.split(' ', 1)
                                if len(parts) == 2:
                                    action = parts[0].replace('/do_', '')
                                    plan_id = parts[1].strip()
                                    logger.info(f"Processing /do_ command: action={action}, plan_id={plan_id}")
                                    if action == 'execute':
                                        # Execute the plan
                                        result = await self.execute_verified_plan(plan_id, session_id)
                                        await websocket.send(json.dumps({
                                            "type": "execution_result",
                                            "plan_id": plan_id,
                                            "action": action,
                                            "result": result,
                                            "client_id": client_id,
                                            "session_id": session_id,
                                            "timestamp": datetime.now().isoformat(),
                                            "success": True
                                        }))
                                    else:
                                        await websocket.send(json.dumps({
                                            "type": "action_result",
                                            "plan_id": plan_id,
                                            "action": action,
                                            "message": f"Action '{action}' not yet implemented",
                                            "client_id": client_id,
                                            "session_id": session_id,
                                            "timestamp": datetime.now().isoformat(),
                                            "success": False
                                        }))
                                else:
                                    await websocket.send(json.dumps({
                                        "type": "error",
                                        "error": f"Invalid /do_ command format: {message}",
                                        "client_id": client_id,
                                        "session_id": session_id,
                                        "timestamp": datetime.now().isoformat(),
                                        "success": False
                                    }))
                            else:
                                # Handle regular query messages - create a plan
                                user_request = data.get('payload', {}).get('message', '')
                                plan_result = await self.llm_plan_creator.create_llm_plan(user_request, session_id)
                                if plan_result["success"]:
                                    plan_id = plan_result["plan_id"]
                                    # Store plan for later execution
                                    self.generated_plans[plan_id] = plan_result
                                    # Create a formatted response for the overlay
                                    formatted_response = f"""🎯 **AUTOMATION EXECUTION PLAN**\n\n🆔 **Plan ID:** {plan_id}\n📋 **Task:** {user_request}\n⏱️ **Estimated Duration:** {plan_result.get('estimated_duration', '15.0')} seconds\n🎯 **Success Probability:** {plan_result.get('success_probability', '80')}%\n🔧 **Complexity:** {plan_result.get('complexity', 'Medium')}\n📝 **Steps:** {len(plan_result.get('steps', []))}+ actions\n\n🚀 **Automation Steps:**\n"""
                                    for i, step in enumerate(plan_result.get('steps', []), 1):
                                        formatted_response += f"{i}. {step.get('description', 'Step')}\n"
                                    formatted_response += f"""\n\n🧠 **Universal Intelligence System**\n✅ **Plan Ready for Execution**\n🔄 **Interactive Controls Available**\n"""
                                    await websocket.send(json.dumps({
                                        "type": "response",
                                        "payload": {
                                            "plan_id": plan_id,
                                            "response": formatted_response,
                                            "plan": plan_result
                                        },
                                        "client_id": client_id,
                                        "session_id": session_id,
                                        "timestamp": datetime.now().isoformat(),
                                        "success": True
                                    }))
                                else:
                                    await websocket.send(json.dumps({
                                        "type": "error",
                                        "error": plan_result.get("response", "Plan creation failed"),
                                        "client_id": client_id,
                                        "session_id": session_id,
                                        "timestamp": datetime.now().isoformat(),
                                        "success": False
                                    }))
                        except Exception as e:
                            logger.error(f"Error handling query message: {e}")
                            await websocket.send(json.dumps({
                                "type": "error",
                                "error": f"Error processing query: {str(e)}",
                                "client_id": client_id,
                                "session_id": session_id,
                                "timestamp": datetime.now().isoformat(),
                                "success": False
                            }))
                        continue
                    elif msg_type == 'chat_request':
                        logger.info(f"Handling chat_request from {client_id}: {data}")
                        try:
                            # Use streaming response for better UX
                            await self.handle_contextual_chat_request_streaming(data, client_id, websocket)
                        except Exception as e:
                            logger.error(f"Error handling chat_request: {e}")
                            await websocket.send(json.dumps({
                                "type": "error",
                                "error": f"Error processing chat request: {str(e)}",
                                    "client_id": client_id,
                                    "session_id": session_id,
                                    "timestamp": datetime.now().isoformat(),
                                "success": False
                                }))
                        continue
                    elif msg_type == 'agent_confirmation':
                        # Handle agent confirmation (DO button)
                        plan_id = data.get('session_id', '')
                        action = data.get('action', '').upper()
                        logger.info(f"Agent confirmation received: plan_id={plan_id}, action={action}")
                        
                        # Execute the plan
                        result = await self.execute_verified_plan(plan_id)
                        await websocket.send(json.dumps(result))
                    elif msg_type == 'button_action':
                        # --- PATCH: Execute plan on button_action/execute ---
                        plan_id = data.get('plan_id')
                        plan = self.generated_plans.get(plan_id)
                        if not plan:
                            await websocket.send(json.dumps({
                                "type": "execution_error",
                                "error": f"Plan not found for plan_id: {plan_id}",
                                    "plan_id": plan_id,
                                    "client_id": client_id,
                                    "session_id": session_id,
                                    "timestamp": datetime.now().isoformat(),
                                "success": False
                                }))
                            continue
                        # --- Execute each step using input controller ---
                        await websocket.send(json.dumps({
                            "type": "execution_started",
                                "plan_id": plan_id,
                                "client_id": client_id,
                                "session_id": session_id,
                                "timestamp": datetime.now().isoformat(),
                            "success": True
                            }))
                        for i, step in enumerate(plan["steps"]):
                            step_type = step.get("action_type")
                            desc = step.get("description", "")
                            try:
                                # Check if input controller is available
                                if self.input_controller is None:
                                    logger.error("❌ Input controller is not initialized!")
                                    await websocket.send(json.dumps({
                                        "type": "execution_error",
                                        "plan_id": plan_id,
                                        "step": i+1,
                                        "description": desc,
                                        "error": "Input controller not initialized",
                                        "timestamp": datetime.now().isoformat(),
                                        "success": False
                                    }))
                                    continue
                                logger.info(f"🎮 Executing step {i+1}: {step_type} - {desc}")
                                # Map step to input controller
                                if step_type == "hotkey":
                                    keys = step.get("target", "").split("+")
                                    logger.info(f"🔥 Executing hotkey: {'+'.join(keys)}")
                                    self.input_controller.hotkey(*[k.strip() for k in keys if k.strip()])
                                elif step_type == "type_text":
                                    text = step.get("value", "")
                                    logger.info(f"⌨️ Typing text: '{text}'")
                                    self.input_controller.type_text(text)
                                elif step_type == "press_key":
                                    key = step.get("key") or step.get("target")
                                    logger.info(f"🔤 Pressing key: {key}")
                                    self.input_controller.press_key(key)
                                elif step_type == "click":
                                    coords = step.get("coordinates")
                                    if coords and isinstance(coords, (list, tuple)) and len(coords) == 2:
                                        logger.info(f"🖱️ Clicking at coordinates: {coords}")
                                        self.input_controller.click(int(coords[0]), int(coords[1]))
                                    else:
                                        logger.info("🖱️ Clicking at current position")
                                        self.input_controller.click()
                                elif step_type == "wait":
                                    duration = float(step.get("duration") or step.get("value") or 1.0)
                                    logger.info(f"⏱️ Waiting for {duration} seconds")
                                    await asyncio.sleep(duration)
                                else:
                                    logger.warning(f"⚠️ Unknown step type: {step_type}")
                                # Send progress update
                                await websocket.send(json.dumps({
                                    "type": "execution_progress",
                                    "plan_id": plan_id,
                                    "step": i+1,
                                    "total_steps": len(plan["steps"]),
                                    "description": desc,
                                    "step_type": step_type,
                                    "timestamp": datetime.now().isoformat(),
                                    "success": True
                                }))
                            except Exception as e:
                                await websocket.send(json.dumps({
                                    "type": "execution_error",
                                    "plan_id": plan_id,
                                    "step": i+1,
                                    "description": desc,
                                    "error": str(e),
                                    "timestamp": datetime.now().isoformat(),
                                    "success": False
                                }))
                        # --- Send completion ---
                        await websocket.send(json.dumps({
                            "type": "execution_completed",
                                "plan_id": plan_id,
                                "client_id": client_id,
                                "session_id": session_id,
                                "timestamp": datetime.now().isoformat(),
                            "success": True
                            }))
                        continue
                    elif msg_type == 'ping':
                        # Handle ping messages
                        await websocket.send(json.dumps({
                            "type": "pong",
                            "timestamp": datetime.now().isoformat()
                            }))
                    elif msg_type == 'sensor_data':
                        # Handle sensor data
                        logger.info(f"Processing sensor data from {client_id}")
                        await websocket.send(json.dumps({
                            "type": "sensor_data_ack",
                            "timestamp": datetime.now().isoformat()
                            }))
                    elif msg_type == 'sensor_data_response':
                        # Handle sensor data responses
                        logger.info(f"Processing sensor data response from {client_id}")
                        await websocket.send(json.dumps({
                            "type": "sensor_data_ack",
                            "timestamp": datetime.now().isoformat()
                            }))
                    elif msg_type == 'heartbeat':
                        # Handle heartbeat messages
                        logger.info(f"Processing heartbeat from {client_id}")
                        await websocket.send(json.dumps({
                            "type": "heartbeat_ack",
                            "timestamp": datetime.now().isoformat()
                            }))
                    elif msg_type == 'execute_plan':
                        # Handle execute_plan messages with comprehensive reasoning
                        plan_id = data.get('plan_id', '')
                        logger.info(f"🎯 Executing plan: {plan_id}")
                        
                        # Send execution started notification
                        await websocket.send(json.dumps({
                            "type": "execution_started",
                            "plan_id": plan_id,
                            "client_id": client_id,
                            "session_id": session_id,
                            "timestamp": datetime.now().isoformat(),
                            "success": True
                        }))
                        
                        try:
                            # Execute the plan using our enhanced method
                            execution_result = await self.execute_verified_plan(plan_id, session_id)
                            
                            # Send detailed execution results
                            await websocket.send(json.dumps({
                                "type": "execution_completed",
                                "plan_id": plan_id,
                                "client_id": client_id,
                                "session_id": session_id,
                                "timestamp": datetime.now().isoformat(),
                                "success": execution_result.get("success", False),
                                "steps_completed": execution_result.get("steps_completed", 0),
                                "steps_failed": execution_result.get("steps_failed", 0),
                                "total_steps": execution_result.get("total_steps", 0),
                                "success_rate": execution_result.get("success_rate", 0),
                                "total_execution_time": execution_result.get("total_execution_time", 0),
                                "summary": execution_result.get("summary", ""),
                                "detailed_reasoning": execution_result.get("detailed_reasoning", ""),
                                "execution_results": execution_result.get("execution_results", [])
                            }))
                            
                            # Log completion
                            if execution_result.get("success", False):
                                logger.info(f"✅ Plan {plan_id} executed successfully with comprehensive reasoning")
                            else:
                                logger.warning(f"⚠️ Plan {plan_id} execution completed with some failures")
                                
                        except Exception as e:
                            logger.error(f"❌ Error executing plan {plan_id}: {e}")
                            await websocket.send(json.dumps({
                                "type": "execution_error",
                                "error": f"Plan execution failed: {str(e)}",
                                "plan_id": plan_id,
                                "client_id": client_id,
                                "session_id": session_id,
                                "timestamp": datetime.now().isoformat(),
                                "success": False
                            }))
                        continue
                    elif msg_type == 'heartbeat_response':
                        # Handle heartbeat responses
                        logger.info(f"Processing heartbeat response from {client_id}")
                        await websocket.send(json.dumps({
                            "type": "heartbeat_ack",
                            "timestamp": datetime.now().isoformat()
                            }))
                    elif "notification" in data or "suggestion" in data or msg_type in ["notification", "suggestion"]:
                        # Forward notifications
                        await websocket.send(message)
                    else:
                        # Generic response for unknown message types
                        await websocket.send(json.dumps({
                            "type": "response",
                            "message": f"Received {msg_type} message",
                            "timestamp": datetime.now().isoformat()
                            }))
                
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from {client_id}: {message[:100]}...")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "error": "Invalid JSON format"
                    }))
                except Exception as e:
                    logger.error(f"Error processing message from {client_id}: {e}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "error": f"Processing error: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"WebSocket error for {client_id}: {e}")
        finally:
            self.connected_clients.discard(client_id)
            if client_id in self.sessions:
                del self.sessions[client_id]

async def start_server():
    """Start the Enhanced Enterprise Backend with Context on port 8767"""
    backend = ContextualAIBackend()
    
    # Create logs directory
    import os
    os.makedirs("logs/backend", exist_ok=True)
    
    ws_port = 8767
    http_port = 8768
    host = "0.0.0.0"  # Listen on all interfaces
    
    logger.info(f"🚀 Starting Enhanced Enterprise Backend with Context...")
    
    try:
        # Initialize brain router asynchronously
        if BRAIN_ROUTER_AVAILABLE:
            try:
                await backend.initialize()
                logger.info("✅ Brain Router initialized asynchronously")
            except Exception as e:
                logger.error(f"Failed to initialize brain router asynchronously: {e}")
        
        # Warm up the LLM
        try:
            logger.info("🔥 Warming up LLM for faster responses...")
            await backend._warmup_llm()
            logger.info("✅ LLM warmup completed")
        except Exception as e:
            logger.warning(f"⚠️ LLM warmup failed: {e}")
        
        # Create HTTP app for REST endpoints
        app = web.Application()
        
        # Add HTTP routes
        async def handle_chat(request):
            """Handle HTTP chat requests"""
            try:
                data = await request.json()
                message = data.get('message', '')
                mode = data.get('mode', 'Agent')
                session_id = data.get('session_id', str(uuid.uuid4()))
                
                logger.info(f"📝 HTTP Chat Request: {message[:100]}... (mode: {mode})")
                
                # Create a mock websocket for response collection
                class MockWebSocket:
                    def __init__(self):
                        self.responses = []
                    
                    async def send(self, data):
                        self.responses.append(data)
                
                mock_ws = MockWebSocket()
                
                # Handle the request based on mode
                if mode == "Agent":
                    await backend._handle_agent_mode_streaming(message, session_id, mock_ws)
                elif mode == "Ask":
                    await backend._handle_ask_mode_streaming(message, session_id, mock_ws)
                elif mode == "Suggest":
                    await backend._handle_suggest_mode_streaming(message, session_id, mock_ws)
                else:
                    await backend._handle_general_mode_streaming(message, session_id, mock_ws)
                
                # Return the final response
                if mock_ws.responses:
                    try:
                        # Try to parse the last JSON response
                        last_response = mock_ws.responses[-1]
                        if isinstance(last_response, str) and last_response.startswith('{'):
                            return web.json_response(json.loads(last_response))
                        else:
                            return web.json_response({
                                "type": "response",
                                "message": "".join(mock_ws.responses),
                                    "session_id": session_id,
                                "timestamp": datetime.now().isoformat()
                            })
                    except:
                        return web.json_response({
                            "type": "response",
                            "message": "".join(mock_ws.responses),
                                "session_id": session_id,
                            "timestamp": datetime.now().isoformat()
                        })
                else:
                    return web.json_response({
                        "type": "error",
                        "message": "No response generated",
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat()
                    })
                    
            except Exception as e:
                logger.error(f"HTTP chat error: {e}")
                return web.json_response({
                    "type": "error",
                    "message": f"Error processing request: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }, status=500)
        
        async def handle_health(request):
            """Health check endpoint"""
            return web.json_response({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "backend": "Enhanced Enterprise Backend with Context",
                "ws_port": ws_port,
                "http_port": http_port
            })
        
        # Add routes
        app.router.add_post('/chat', handle_chat)
        app.router.add_get('/health', handle_health)
        
        # Start HTTP server on different port
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, http_port)
        await site.start()
        
        logger.info(f"✅ HTTP server started on http://{host}:{http_port}")
        
        # Create WebSocket server on original port
        ws_server = await websockets.serve(
            backend.handle_websocket,
            host, 
            ws_port,
            ping_interval=20,
            ping_timeout=10
        )
        
        logger.info(f"✅ WebSocket server started on ws://{host}:{ws_port}")
        logger.info(f"🚀 Enhanced Enterprise Backend started!")
        logger.info(f"🌐 HTTP API: http://localhost:{http_port}/chat")
        logger.info(f"🔌 WebSocket: ws://localhost:{ws_port}")
        
        # Keep the server running
        await asyncio.Future()  # Run forever
        
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        raise

def start_http_status_server():
    class StatusHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/status':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                status = {
                    'status': 'ok',
                    'backend': 'enhanced_enterprise_backend_with_context',
                    'time': datetime.now().isoformat()
                }
                self.wfile.write(json.dumps(status).encode())
            else:
                self.send_response(404)
                self.end_headers()
        def log_message(self, format, *args):
            return  # Suppress default logging

    def run_server():
        server = HTTPServer(('0.0.0.0', 8787), StatusHandler)
        print('HTTP /status endpoint available at http://localhost:8787/status')
        server.serve_forever()

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()

if __name__ == "__main__":
    start_http_status_server()
    try:
        # Ensure the pids directory exists
        import os
        os.makedirs("pids", exist_ok=True)
        
        # Kill any existing process on port 8767 to avoid conflicts
        import subprocess
        subprocess.run("lsof -ti:8767 | xargs kill -9 2>/dev/null || true", shell=True)
        
        # Allow port to be released
        asyncio.run(asyncio.sleep(1))
        
        # Start the server
        asyncio.run(start_server())
    except KeyboardInterrupt:
        logger.info("🛑 Enhanced Enterprise Backend stopped by user")
    except Exception as e:
        logger.error(f"❌ Enhanced Enterprise Backend error: {e}")