#!/usr/bin/env python3
"""
SuggestionAgent - Integrates with existing backend SuggestionDetector.

This agent connects to the backend suggestion engine and provides intelligent
suggestions based on LLM responses and screen context analysis.
"""

import asyncio
import json
import logging
import sys
import time
from typing import Any, Dict, List, Optional, Set
import websockets
from pathlib import Path

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from execution.core.agent_base import AgentBase, AgentConfig, AgentCapability
from execution.memory.agent_memory import AgentMemory, MemoryType
from llm_suggestion_detector import SuggestionDetector, process_ws_message

logger = logging.getLogger(__name__)


class SuggestionAgent(AgentBase):
    """
    Enterprise-grade suggestion agent that integrates with backend SuggestionDetector.
    
    Features:
    - Direct integration with existing SuggestionDetector
    - WebSocket communication with backend
    - Context-aware suggestion generation
    - Memory integration for learning
    - Real-time suggestion processing
    - Support for all 4 chat modes (Agent/Ask/Suggest/General)
    """
    
    def __init__(self, config: AgentConfig, memory: AgentMemory, 
                 backend_ws_url: str = "ws://localhost:8765"):
        """Initialize the suggestion agent."""
        super().__init__(config)
        
        self.memory = memory
        self.backend_ws_url = backend_ws_url
        self.suggestion_detector = SuggestionDetector(confidence_threshold=0.7)
        
        # WebSocket connection to backend
        self.ws_connection: Optional[websockets.WebSocketServerProtocol] = None
        self.connection_task: Optional[asyncio.Task] = None
        
        # Suggestion processing
        self.active_suggestions: Dict[str, Dict[str, Any]] = {}
        self.suggestion_history: List[Dict[str, Any]] = []
        self.suggestion_callbacks: List[callable] = []
        
        # Chat mode handling
        self.current_mode = "Ask"  # Default mode
        self.mode_handlers = {
            "Agent": self._handle_agent_mode,
            "Ask": self._handle_ask_mode, 
            "Suggest": self._handle_suggest_mode,
            "General": self._handle_general_mode
        }
        
        # Performance tracking
        self.suggestions_generated = 0
        self.suggestions_accepted = 0
        self.suggestions_rejected = 0
        
        logger.info("SuggestionAgent initialized with backend integration")
    
    async def initialize(self) -> None:
        """Initialize the suggestion agent."""
        try:
            # Connect to backend WebSocket
            await self._connect_to_backend()
            
            # Register with backend
            await self._register_with_backend()
            
            # Start suggestion processing
            self.connection_task = asyncio.create_task(self._backend_message_handler())
            
            self.logger.info("SuggestionAgent initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize SuggestionAgent: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            # Cancel connection task
            if self.connection_task:
                self.connection_task.cancel()
            
            # Close WebSocket connection
            if self.ws_connection:
                await self.ws_connection.close()
            
            # Store final statistics in memory
            self.memory.store_memory(MemoryType.PERFORMANCE_METRIC, {
                'agent_type': 'SuggestionAgent',
                'suggestions_generated': self.suggestions_generated,
                'suggestions_accepted': self.suggestions_accepted,
                'suggestions_rejected': self.suggestions_rejected,
                'acceptance_rate': self.suggestions_accepted / max(1, self.suggestions_generated),
                'session_duration': time.time() - self.start_time
            })
            
            self.logger.info("SuggestionAgent cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    async def _connect_to_backend(self) -> None:
        """Connect to backend WebSocket server."""
        max_retries = 5
        retry_delay = 2.0
        
        for attempt in range(max_retries):
            try:
                self.ws_connection = await websockets.connect(
                    self.backend_ws_url,
                    timeout=10.0
                )
                self.logger.info(f"Connected to backend: {self.backend_ws_url}")
                return
                
            except Exception as e:
                self.logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise ConnectionError(f"Failed to connect to backend after {max_retries} attempts")
    
    async def _register_with_backend(self) -> None:
        """Register with backend as suggestion agent."""
        if not self.ws_connection:
            raise RuntimeError("No backend connection")
        
        registration_message = {
            "type": "register",
            "payload": {
                "client_type": "suggestion_agent",
                "agent_id": self.agent_id,
                "capabilities": [cap.value for cap in self.config.capabilities],
                "version": "1.0.0"
            }
        }
        
        await self.ws_connection.send(json.dumps(registration_message))
        self.logger.info("Registered with backend")
    
    async def _backend_message_handler(self) -> None:
        """Handle messages from backend WebSocket."""
        try:
            async for message in self.ws_connection:
                try:
                    data = json.loads(message)
                    await self._process_backend_message(data)
                    
                except json.JSONDecodeError:
                    self.logger.error(f"Invalid JSON message: {message}")
                except Exception as e:
                    self.logger.error(f"Error processing backend message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            self.logger.warning("Backend connection closed")
        except Exception as e:
            self.logger.error(f"Error in backend message handler: {e}")
    
    async def _process_backend_message(self, data: Dict[str, Any]) -> None:
        """Process message from backend."""
        msg_type = data.get("type")
        payload = data.get("payload", {})
        
        if msg_type == "llm_response":
            # Process LLM response for suggestions
            await self._process_llm_response(payload)
            
        elif msg_type == "query_response":
            # Handle query response based on current mode
            await self._handle_mode_response(payload)
            
        elif msg_type == "suggestion_feedback":
            # Handle user feedback on suggestions
            await self._handle_suggestion_feedback(payload)
            
        elif msg_type == "context_update":
            # Handle context updates
            await self._handle_context_update(payload)
            
        else:
            self.logger.debug(f"Unhandled backend message type: {msg_type}")
    
    async def _process_llm_response(self, response_data: Dict[str, Any]) -> None:
        """Process LLM response and detect suggestions."""
        try:
            # Use existing SuggestionDetector
            processed_message = await process_ws_message(response_data)
            
            # Check if suggestion was detected
            if processed_message.get("isSuggestion"):
                await self._handle_detected_suggestion(processed_message)
            
        except Exception as e:
            self.logger.error(f"Error processing LLM response: {e}")
    
    async def _handle_detected_suggestion(self, suggestion_data: Dict[str, Any]) -> None:
        """Handle detected suggestion from LLM response."""
        suggestion_id = f"suggestion_{int(time.time() * 1000)}"
        
        # Enhanced suggestion with context
        enhanced_suggestion = {
            "suggestion_id": suggestion_id,
            "timestamp": time.time(),
            "mode": self.current_mode,
            "agent_id": self.agent_id,
            **suggestion_data
        }
        
        # Store in active suggestions
        self.active_suggestions[suggestion_id] = enhanced_suggestion
        
        # Store in memory
        self.memory.store_memory(MemoryType.SYSTEM_EVENT, {
            "event_type": "suggestion_generated",
            "suggestion_id": suggestion_id,
            "suggestion_data": enhanced_suggestion,
            "mode": self.current_mode
        }, tags={"suggestion", self.current_mode.lower()})
        
        # Update metrics
        self.suggestions_generated += 1
        
        # Notify callbacks
        await self._notify_suggestion_callbacks(enhanced_suggestion)
        
        # Send to frontend
        await self._send_suggestion_to_frontend(enhanced_suggestion)
        
        self.logger.info(f"Generated suggestion: {suggestion_id}")
    
    # ========== Chat Mode Handlers ==========
    
    async def _handle_mode_response(self, response_data: Dict[str, Any]) -> None:
        """Handle response based on current chat mode."""
        handler = self.mode_handlers.get(self.current_mode)
        if handler:
            await handler(response_data)
        else:
            self.logger.warning(f"No handler for mode: {self.current_mode}")
    
    async def _handle_agent_mode(self, response_data: Dict[str, Any]) -> None:
        """Handle Agent mode - proactive task execution suggestions."""
        # Agent mode should provide step-by-step execution plans
        if "steps" in response_data or "plan" in response_data:
            # This is a task execution plan
            await self._create_execution_suggestion(response_data)
        else:
            # Regular response, check for suggestions
            await self._process_llm_response(response_data)
    
    async def _handle_ask_mode(self, response_data: Dict[str, Any]) -> None:
        """Handle Ask mode - contextual information responses."""
        # Ask mode focuses on information retrieval
        # Check if response contains actionable suggestions
        suggestion_confidence = self.suggestion_detector.detect_suggestion(
            response_data.get("content", response_data.get("response", ""))
        )[1]
        
        if suggestion_confidence > 0.5:
            await self._process_llm_response(response_data)
    
    async def _handle_suggest_mode(self, response_data: Dict[str, Any]) -> None:
        """Handle Suggest mode - always look for suggestions."""
        # Suggest mode is most aggressive in finding suggestions
        await self._process_llm_response(response_data)
        
        # Also generate proactive suggestions based on context
        await self._generate_proactive_suggestions(response_data)
    
    async def _handle_general_mode(self, response_data: Dict[str, Any]) -> None:
        """Handle General mode - minimal context, basic suggestions only."""
        # General mode has lower threshold for suggestions
        original_threshold = self.suggestion_detector.confidence_threshold
        self.suggestion_detector.confidence_threshold = 0.8  # Higher threshold
        
        try:
            await self._process_llm_response(response_data)
        finally:
            self.suggestion_detector.confidence_threshold = original_threshold
    
    async def _create_execution_suggestion(self, response_data: Dict[str, Any]) -> None:
        """Create execution suggestion for Agent mode."""
        suggestion_id = f"execution_{int(time.time() * 1000)}"
        
        execution_suggestion = {
            "suggestion_id": suggestion_id,
            "type": "execution_plan",
            "timestamp": time.time(),
            "mode": "Agent",
            "content": response_data.get("content", ""),
            "steps": response_data.get("steps", []),
            "plan": response_data.get("plan", {}),
            "confidence": 0.9,  # High confidence for execution plans
            "isSuggestion": True,
            "buttons": [
                {"id": "execute", "label": "Execute Plan", "primary": True},
                {"id": "modify", "label": "Modify", "primary": False},
                {"id": "cancel", "label": "Cancel", "primary": False}
            ]
        }
        
        self.active_suggestions[suggestion_id] = execution_suggestion
        await self._send_suggestion_to_frontend(execution_suggestion)
        
        self.logger.info(f"Created execution suggestion: {suggestion_id}")
    
    async def _generate_proactive_suggestions(self, response_data: Dict[str, Any]) -> None:
        """Generate proactive suggestions based on context."""
        # This would integrate with screen analysis and context
        # For now, we'll create a placeholder for future enhancement
        proactive_suggestion = {
            "suggestion_id": f"proactive_{int(time.time() * 1000)}",
            "type": "proactive",
            "timestamp": time.time(),
            "mode": "Suggest",
            "content": "Based on your current screen, I can help with automating repetitive tasks.",
            "confidence": 0.6,
            "isSuggestion": True,
            "buttons": [
                {"id": "analyze", "label": "Analyze Screen", "primary": True},
                {"id": "dismiss", "label": "Not Now", "primary": False}
            ]
        }
        
        await self._send_suggestion_to_frontend(proactive_suggestion)
    
    # ========== Core Task Processing ==========
    
    async def process_task(self, task_data: Dict[str, Any]) -> Any:
        """Process a task - main agent method."""
        task_type = task_data.get("action", "unknown")
        
        if task_type == "analyze_response":
            # Analyze an LLM response for suggestions
            response_content = task_data.get("parameters", {}).get("response", "")
            is_suggestion, confidence, suggestion_data = self.suggestion_detector.detect_suggestion(response_content)
            
            return {
                "is_suggestion": is_suggestion,
                "confidence": confidence,
                "suggestion_data": suggestion_data
            }
            
        elif task_type == "set_mode":
            # Change chat mode
            new_mode = task_data.get("parameters", {}).get("mode", "Ask")
            old_mode = self.current_mode
            self.current_mode = new_mode
            
            self.logger.info(f"Mode changed: {old_mode} -> {new_mode}")
            
            return {
                "old_mode": old_mode,
                "new_mode": new_mode,
                "success": True
            }
            
        elif task_type == "handle_suggestion_feedback":
            # Handle user feedback on suggestions
            return await self._process_suggestion_feedback(task_data.get("parameters", {}))
            
        else:
            self.logger.warning(f"Unknown task type: {task_type}")
            return {"error": f"Unknown task type: {task_type}"}
    
    async def _process_suggestion_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process user feedback on suggestions."""
        suggestion_id = feedback_data.get("suggestion_id")
        action = feedback_data.get("action")  # "accept", "reject", "modify"
        
        if suggestion_id not in self.active_suggestions:
            return {"error": "Suggestion not found"}
        
        suggestion = self.active_suggestions[suggestion_id]
        
        # Update metrics
        if action == "accept":
            self.suggestions_accepted += 1
        elif action == "reject":
            self.suggestions_rejected += 1
        
        # Store feedback in memory
        self.memory.store_memory(MemoryType.USER_INTERACTION, {
            "event_type": "suggestion_feedback",
            "suggestion_id": suggestion_id,
            "action": action,
            "suggestion_data": suggestion,
            "timestamp": time.time()
        }, tags={"feedback", action, self.current_mode.lower()})
        
        # Move to history
        self.suggestion_history.append({
            **suggestion,
            "feedback_action": action,
            "feedback_timestamp": time.time()
        })
        
        # Remove from active suggestions
        del self.active_suggestions[suggestion_id]
        
        self.logger.info(f"Processed feedback for suggestion {suggestion_id}: {action}")
        
        return {
            "suggestion_id": suggestion_id,
            "action": action,
            "success": True
        }
    
    # ========== Communication ==========
    
    async def _send_suggestion_to_frontend(self, suggestion: Dict[str, Any]) -> None:
        """Send suggestion to frontend."""
        if not self.ws_connection:
            self.logger.warning("No backend connection to send suggestion")
            return
        
        message = {
            "type": "suggestion",
            "payload": suggestion
        }
        
        try:
            await self.ws_connection.send(json.dumps(message))
            self.logger.debug(f"Sent suggestion to frontend: {suggestion['suggestion_id']}")
        except Exception as e:
            self.logger.error(f"Failed to send suggestion to frontend: {e}")
    
    async def _notify_suggestion_callbacks(self, suggestion: Dict[str, Any]) -> None:
        """Notify registered callbacks about new suggestions."""
        for callback in self.suggestion_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(suggestion)
                else:
                    callback(suggestion)
            except Exception as e:
                self.logger.error(f"Error in suggestion callback: {e}")
    
    def add_suggestion_callback(self, callback: callable) -> None:
        """Add a callback for suggestion events."""
        self.suggestion_callbacks.append(callback)
    
    def remove_suggestion_callback(self, callback: callable) -> None:
        """Remove a suggestion callback."""
        if callback in self.suggestion_callbacks:
            self.suggestion_callbacks.remove(callback)
    
    # ========== Context Handling ==========
    
    async def _handle_context_update(self, context_data: Dict[str, Any]) -> None:
        """Handle context updates from backend."""
        # Store context snapshot in memory
        self.memory.store_memory(MemoryType.CONTEXT_SNAPSHOT, context_data)
        
        # Check if context suggests new opportunities for suggestions
        if self.current_mode == "Suggest":
            await self._analyze_context_for_suggestions(context_data)
    
    async def _analyze_context_for_suggestions(self, context_data: Dict[str, Any]) -> None:
        """Analyze context for potential suggestions."""
        # This would integrate with screen analysis
        # Placeholder for future enhancement with LLAVA integration
        pass
    
    async def _handle_suggestion_feedback(self, feedback_data: Dict[str, Any]) -> None:
        """Handle suggestion feedback from user."""
        await self._process_suggestion_feedback(feedback_data)
    
    # ========== Health and Monitoring ==========
    
    async def health_check(self) -> bool:
        """Perform health check."""
        # Check WebSocket connection
        if not self.ws_connection or self.ws_connection.closed:
            self.logger.warning("Backend connection lost")
            return False
        
        # Check suggestion detector
        if not self.suggestion_detector:
            return False
        
        return True
    
    async def handle_unhealthy_state(self) -> None:
        """Handle unhealthy state by attempting reconnection."""
        self.logger.info("Attempting to recover from unhealthy state")
        
        try:
            # Reconnect to backend
            await self._connect_to_backend()
            await self._register_with_backend()
            
            # Restart message handler
            if self.connection_task:
                self.connection_task.cancel()
            self.connection_task = asyncio.create_task(self._backend_message_handler())
            
            self.logger.info("Recovery successful")
            
        except Exception as e:
            self.logger.error(f"Recovery failed: {e}")
    
    # ========== Statistics ==========
    
    def get_suggestion_statistics(self) -> Dict[str, Any]:
        """Get comprehensive suggestion statistics."""
        total_suggestions = self.suggestions_generated
        acceptance_rate = self.suggestions_accepted / max(1, total_suggestions)
        rejection_rate = self.suggestions_rejected / max(1, total_suggestions)
        
        return {
            "total_suggestions": total_suggestions,
            "accepted_suggestions": self.suggestions_accepted,
            "rejected_suggestions": self.suggestions_rejected,
            "acceptance_rate": acceptance_rate,
            "rejection_rate": rejection_rate,
            "active_suggestions": len(self.active_suggestions),
            "suggestion_history": len(self.suggestion_history),
            "current_mode": self.current_mode,
            "backend_connected": self.ws_connection and not self.ws_connection.closed
        }