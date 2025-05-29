"""
Next-Generation Brain Router - The Central Intelligence Hub

This is the main orchestration layer that routes chat modes to appropriate
specialized handlers, manages resources, and ensures optimal performance.
Acts as the "lobby of the brain" managing all cognitive resources.
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor
import weakref

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatMode(Enum):
    AGENT = "Agent"
    ASK = "Ask" 
    SUGGEST = "Suggest"
    GENERAL = "General"

class Priority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

class ResourceType(Enum):
    MEMORY = "memory"
    LLM = "llm"
    SENSORS = "sensors"
    EXECUTION = "execution"
    STORAGE = "storage"

@dataclass
class ResourceRequest:
    """Represents a request for cognitive resources"""
    resource_type: ResourceType
    priority: Priority
    estimated_duration: float
    requirements: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ChatRequest:
    """Incoming chat request with full context"""
    mode: ChatMode
    query: str
    user_id: str
    session_id: str
    timestamp: float
    priority: Priority = Priority.MEDIUM
    context: Dict[str, Any] = field(default_factory=dict)
    resources_needed: List[ResourceRequest] = field(default_factory=list)

@dataclass
class BrainResponse:
    """Standardized response from the brain system"""
    success: bool
    response: str
    mode_used: ChatMode
    processing_time: float
    resources_used: List[str]
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    verification_status: str = "pending"
    execution_plan: Optional[Dict[str, Any]] = None  # ADD EXECUTION PLAN FIELD

class ResourceManager:
    """Manages and allocates cognitive resources efficiently"""
    
    def __init__(self):
        self.resources = {
            ResourceType.MEMORY: {"available": True, "load": 0.0, "max_concurrent": 5},
            ResourceType.LLM: {"available": True, "load": 0.0, "max_concurrent": 3},
            ResourceType.SENSORS: {"available": True, "load": 0.0, "max_concurrent": 10},
            ResourceType.EXECUTION: {"available": True, "load": 0.0, "max_concurrent": 2},
            ResourceType.STORAGE: {"available": True, "load": 0.0, "max_concurrent": 8}
        }
        self.active_requests: Dict[str, ResourceRequest] = {}
        self.resource_locks = {rt: asyncio.Lock() for rt in ResourceType}
        
    async def check_availability(self, requests: List[ResourceRequest]) -> bool:
        """Check if all requested resources are available"""
        for req in requests:
            resource = self.resources.get(req.resource_type)
            if not resource or not resource["available"]:
                return False
            if resource["load"] >= resource["max_concurrent"]:
                return False
        return True
    
    async def allocate_resources(self, requests: List[ResourceRequest], request_id: str) -> bool:
        """Allocate resources for a request"""
        try:
            # Check availability first
            if not await self.check_availability(requests):
                return False
            
            # Lock and allocate each resource
            for req in requests:
                async with self.resource_locks[req.resource_type]:
                    self.resources[req.resource_type]["load"] += 1
                    self.active_requests[f"{request_id}_{req.resource_type.value}"] = req
            
            logger.info(f"Resources allocated for request {request_id}: {[r.resource_type.value for r in requests]}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to allocate resources: {e}")
            await self.release_resources(requests, request_id)
            return False
    
    async def release_resources(self, requests: List[ResourceRequest], request_id: str):
        """Release allocated resources"""
        for req in requests:
            try:
                async with self.resource_locks[req.resource_type]:
                    if self.resources[req.resource_type]["load"] > 0:
                        self.resources[req.resource_type]["load"] -= 1
                    
                    request_key = f"{request_id}_{req.resource_type.value}"
                    if request_key in self.active_requests:
                        del self.active_requests[request_key]
                        
            except Exception as e:
                logger.error(f"Error releasing resource {req.resource_type.value}: {e}")
    
    def get_resource_status(self) -> Dict[str, Any]:
        """Get current resource utilization status"""
        return {
            rt.value: {
                "load": info["load"],
                "max_concurrent": info["max_concurrent"],
                "utilization": (info["load"] / info["max_concurrent"]) * 100,
                "available": info["available"]
            }
            for rt, info in self.resources.items()
        }

class ResponseVerifier:
    """Ensures response quality and accuracy"""
    
    def __init__(self):
        self.verification_rules = {
            ChatMode.AGENT: self._verify_agent_response,
            ChatMode.ASK: self._verify_ask_response,
            ChatMode.SUGGEST: self._verify_suggest_response,
            ChatMode.GENERAL: self._verify_general_response
        }
    
    async def verify_response(self, response: BrainResponse, original_request: ChatRequest) -> BrainResponse:
        """Verify response quality and accuracy"""
        try:
            verifier = self.verification_rules.get(original_request.mode)
            if verifier:
                verification_result = await verifier(response, original_request)
                response.verification_status = verification_result["status"]
                response.confidence = verification_result["confidence"]
                response.metadata.update(verification_result.get("metadata", {}))
            else:
                response.verification_status = "no_verifier"
                
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            response.verification_status = "verification_failed"
            
        return response
    
    async def _verify_agent_response(self, response: BrainResponse, request: ChatRequest) -> Dict[str, Any]:
        """Verify Agent mode responses for task execution quality"""
        # Check if response contains actionable steps
        has_steps = any(word in response.response.lower() for word in ["step", "first", "then", "next", "execute"])
        has_plan = len(response.response.split('\n')) > 1 or len(response.response.split('.')) > 2
        
        confidence = 0.8 if has_steps and has_plan else 0.5
        status = "verified" if confidence > 0.7 else "low_confidence"
        
        return {
            "status": status,
            "confidence": confidence,
            "metadata": {"has_steps": has_steps, "has_plan": has_plan}
        }
    
    async def _verify_ask_response(self, response: BrainResponse, request: ChatRequest) -> Dict[str, Any]:
        """Verify Ask mode responses for contextual accuracy"""
        # Check if response addresses the question directly
        response_length = len(response.response)
        is_substantive = response_length > 50
        is_contextual = "context" in response.response.lower() or "memory" in response.response.lower()
        
        confidence = 0.9 if is_substantive and is_contextual else 0.6
        status = "verified" if confidence > 0.7 else "needs_improvement"
        
        return {
            "status": status,
            "confidence": confidence,
            "metadata": {"is_substantive": is_substantive, "is_contextual": is_contextual}
        }
    
    async def _verify_suggest_response(self, response: BrainResponse, request: ChatRequest) -> Dict[str, Any]:
        """Verify Suggest mode responses for proactive value"""
        # Check if response contains actionable suggestions
        has_suggestions = any(word in response.response.lower() for word in ["suggest", "recommend", "consider", "try"])
        is_proactive = any(word in response.response.lower() for word in ["would", "could", "might", "perhaps"])
        
        confidence = 0.85 if has_suggestions and is_proactive else 0.55
        status = "verified" if confidence > 0.7 else "insufficient_proactivity"
        
        return {
            "status": status,
            "confidence": confidence,
            "metadata": {"has_suggestions": has_suggestions, "is_proactive": is_proactive}
        }
    
    async def _verify_general_response(self, response: BrainResponse, request: ChatRequest) -> Dict[str, Any]:
        """Verify General mode responses for basic quality"""
        # Basic quality checks
        response_length = len(response.response)
        is_coherent = response_length > 10 and not response.response.count("error") > 0
        
        confidence = 0.7 if is_coherent else 0.3
        status = "verified" if confidence > 0.5 else "poor_quality"
        
        return {
            "status": status,
            "confidence": confidence,
            "metadata": {"is_coherent": is_coherent, "length": response_length}
        }

class BrainRouter:
    """
    The Central Intelligence Hub - Routes requests to specialized handlers
    Acts as the "lobby of the brain" managing all cognitive processes
    """
    
    def __init__(self):
        self.resource_manager = ResourceManager()
        self.response_verifier = ResponseVerifier()
        self.mode_handlers: Dict[ChatMode, Callable] = {}
        self.request_queue: asyncio.Queue = asyncio.Queue()
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.performance_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "average_response_time": 0.0,
            "mode_usage": {mode: 0 for mode in ChatMode}
        }
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Initialize default handlers
        self._initialize_handlers()
        
        # Background tasks will be started when the router is used
        self._background_tasks_started = False
        
        logger.info("BrainRouter initialized - The Central Intelligence Hub is online")
    
    def _initialize_handlers(self):
        """Initialize default mode handlers"""
        self.mode_handlers = {
            ChatMode.AGENT: self._handle_agent_mode,
            ChatMode.ASK: self._handle_ask_mode,
            ChatMode.SUGGEST: self._handle_suggest_mode,
            ChatMode.GENERAL: self._handle_general_mode
        }
    
    def register_handler(self, mode: ChatMode, handler: Callable):
        """Register a specialized handler for a chat mode"""
        self.mode_handlers[mode] = handler
        logger.info(f"Registered specialized handler for {mode.value} mode")
    
    async def _ensure_background_tasks(self):
        """Ensure background tasks are started"""
        if not self._background_tasks_started:
            asyncio.create_task(self._process_request_queue())
            asyncio.create_task(self._cleanup_stale_sessions())
            self._background_tasks_started = True

    async def process_request(self, request: ChatRequest) -> BrainResponse:
        """Main entry point - Process incoming chat request"""
        start_time = time.time()
        request_id = f"{request.session_id}_{request.timestamp}"
        
        try:
            # Ensure background tasks are running
            await self._ensure_background_tasks()
            
            logger.info(f"Processing {request.mode.value} request: {request.query[:50]}...")
            
            # Update session context
            await self._update_session_context(request)
            
            # Determine required resources
            await self._analyze_resource_requirements(request)
            
            # Check and allocate resources
            if not await self.resource_manager.allocate_resources(request.resources_needed, request_id):
                return BrainResponse(
                    success=False,
                    response="System is currently at capacity. Please try again in a moment.",
                    mode_used=request.mode,
                    processing_time=time.time() - start_time,
                    resources_used=[],
                    confidence=0.0,
                    verification_status="resource_unavailable"
                )
            
            try:
                # Route to appropriate handler
                handler = self.mode_handlers.get(request.mode)
                if not handler:
                    raise ValueError(f"No handler found for mode: {request.mode.value}")
                
                # Process request
                response = await handler(request)
                
                # Verify response quality
                response = await self.response_verifier.verify_response(response, request)
                
                # Update metrics
                self._update_metrics(request, response, start_time)
                
                logger.info(f"Request processed successfully in {response.processing_time:.2f}s")
                return response
                
            finally:
                # Always release resources
                await self.resource_manager.release_resources(request.resources_needed, request_id)
                
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return BrainResponse(
                success=False,
                response=f"An error occurred while processing your request: {str(e)}",
                mode_used=request.mode,
                processing_time=time.time() - start_time,
                resources_used=[],
                confidence=0.0,
                verification_status="error"
            )
    
    async def _analyze_resource_requirements(self, request: ChatRequest):
        """Analyze and determine required resources for the request"""
        # Base resources needed for each mode
        mode_resources = {
            ChatMode.AGENT: [
                ResourceRequest(ResourceType.MEMORY, Priority.HIGH, 5.0),
                ResourceRequest(ResourceType.LLM, Priority.HIGH, 3.0),
                ResourceRequest(ResourceType.EXECUTION, Priority.MEDIUM, 2.0)
            ],
            ChatMode.ASK: [
                ResourceRequest(ResourceType.MEMORY, Priority.HIGH, 2.0),
                ResourceRequest(ResourceType.LLM, Priority.MEDIUM, 1.5)
            ],
            ChatMode.SUGGEST: [
                ResourceRequest(ResourceType.SENSORS, Priority.HIGH, 1.0),
                ResourceRequest(ResourceType.MEMORY, Priority.MEDIUM, 2.0),
                ResourceRequest(ResourceType.LLM, Priority.MEDIUM, 2.0)
            ],
            ChatMode.GENERAL: [
                ResourceRequest(ResourceType.LLM, Priority.LOW, 1.0)
            ]
        }
        
        request.resources_needed = mode_resources.get(request.mode, [])
    
    async def _update_session_context(self, request: ChatRequest):
        """Update session context and maintain conversation history"""
        session_key = request.session_id
        if session_key not in self.active_sessions:
            self.active_sessions[session_key] = {
                "created_at": time.time(),
                "last_activity": time.time(),
                "request_count": 0,
                "mode_history": [],
                "context": {}
            }
        
        session = self.active_sessions[session_key]
        session["last_activity"] = time.time()
        session["request_count"] += 1
        session["mode_history"].append(request.mode.value)
        session["context"].update(request.context)
    
    def _update_metrics(self, request: ChatRequest, response: BrainResponse, start_time: float):
        """Update performance metrics"""
        self.performance_metrics["total_requests"] += 1
        if response.success:
            self.performance_metrics["successful_requests"] += 1
        
        self.performance_metrics["mode_usage"][request.mode] += 1
        
        # Update average response time
        current_avg = self.performance_metrics["average_response_time"]
        total_requests = self.performance_metrics["total_requests"]
        new_time = time.time() - start_time
        
        self.performance_metrics["average_response_time"] = (
            (current_avg * (total_requests - 1) + new_time) / total_requests
        )
    
    async def _process_request_queue(self):
        """Background task to process queued requests"""
        while True:
            try:
                # This will be used for batch processing and priority queuing
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Queue processing error: {e}")
    
    async def _cleanup_stale_sessions(self):
        """Clean up old inactive sessions"""
        while True:
            try:
                current_time = time.time()
                stale_sessions = []
                
                for session_id, session_data in self.active_sessions.items():
                    if current_time - session_data["last_activity"] > 3600:  # 1 hour
                        stale_sessions.append(session_id)
                
                for session_id in stale_sessions:
                    del self.active_sessions[session_id]
                    logger.info(f"Cleaned up stale session: {session_id}")
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")
    
    # Default mode handlers (to be replaced by specialized implementations)
    async def _handle_agent_mode(self, request: ChatRequest) -> BrainResponse:
        """Handle Agent mode - Universal Task Planning and Execution"""
        try:
            # Import the real agent automation handler (FIXED)
            from real_agent_automation_handler import handle_real_agent_automation
            
            # Use the real automation system with execution plans
            result = await handle_real_agent_automation(request.query, request.session_id)
            
            # Convert to BrainResponse format
            response = BrainResponse(
                success=result.get("success", True),
                response=result.get("response", ""),
                mode_used=request.mode,
                processing_time=result.get("processing_time", 0.0),
                resources_used=["automation", "llm", "memory"],
                confidence=result.get("confidence", 0.8),
                metadata=result.get("metadata", {}),
                execution_plan=result.get("execution_plan", None)  # ADD EXECUTION PLAN
            )
            return response
            
        except ImportError as e:
            logger.warning(f"Improved agent handler not available: {e}, using fallback")
            # Fallback to basic agent mode
            return BrainResponse(
                success=True,
                response=f"🤖 **Agent Mode - Basic Handler**\n\nI understand you want me to help with: \"{request.query}\"\n\nThe advanced universal automation system is currently not available. Please try again or contact support if this issue persists.",
                mode_used=request.mode,
                processing_time=0.5,
                resources_used=["memory", "basic_planning"],
                confidence=0.6,
                metadata={"fallback_mode": True, "error": str(e)}
            )
        except Exception as e:
            logger.error(f"Error in agent mode handler: {e}")
            return BrainResponse(
                success=False,
                response=f"🚨 **Agent Mode Error**\n\nI encountered an error while processing your request: \"{request.query}\"\n\nError: {str(e)}\n\nPlease try rephrasing your request or contact support.",
                mode_used=request.mode,
                processing_time=0.1,
                resources_used=[],
                confidence=0.0,
                metadata={"error": str(e)}
            )
    
    async def _handle_ask_mode(self, request: ChatRequest) -> BrainResponse:
        """Handle Ask mode - Enhanced Memory Integration with Semantic Search"""
        try:
            # Import the enhanced ask mode handler
            from brain.handlers.enhanced_ask_mode_handler import handle_enhanced_ask_mode
            
            # Use the enhanced memory integration system with semantic search
            response = await handle_enhanced_ask_mode(request)
            return response
            
        except ImportError as e:
            logger.warning(f"Enhanced ask handler not available: {e}, using fallback")
            # Fallback to basic ask mode
            return BrainResponse(
                success=True,
                response=f"🧠 **Ask Mode - Basic Handler**\n\nI understand you're asking: \"{request.query}\"\n\nThe enhanced memory integration system is currently not available. Please try again or contact support if this issue persists.",
                mode_used=request.mode,
                processing_time=0.3,
                resources_used=["basic_memory"],
                confidence=0.6,
                metadata={"fallback_mode": True, "error": str(e)}
            )
        except Exception as e:
            logger.error(f"Error in ask mode handler: {e}")
            return BrainResponse(
                success=False,
                response=f"🚨 **Ask Mode Error**\n\nI encountered an error while processing your question: \"{request.query}\"\n\nError: {str(e)}\n\nPlease try rephrasing your question or contact support.",
                mode_used=request.mode,
                processing_time=0.1,
                resources_used=[],
                confidence=0.0,
                metadata={"error": str(e)}
            )
    
    async def _handle_suggest_mode(self, request: ChatRequest) -> BrainResponse:
        """Handle Suggest mode - Memory-Integrated Proactive Suggestions"""
        try:
            # Import the suggest mode handler
            from brain.handlers.suggest_mode_handler import handle_suggest_mode
            
            # Use the enhanced suggestion system with memory integration
            response = await handle_suggest_mode(request)
            return response
            
        except ImportError as e:
            logger.warning(f"Suggest handler not available: {e}, using fallback")
            # Fallback to basic suggest mode
            return BrainResponse(
                success=True,
                response=f"💡 **Suggest Mode - Basic Handler**\n\nRegarding: \"{request.query}\"\n\nI'd suggest taking a moment to review your current priorities and plan your next steps. The enhanced suggestion system is currently not available.",
                mode_used=request.mode,
                processing_time=0.4,
                resources_used=["basic_analysis"],
                confidence=0.5,
                metadata={"fallback_mode": True, "error": str(e)}
            )
        except Exception as e:
            logger.error(f"Error in suggest mode handler: {e}")
            return BrainResponse(
                success=False,
                response=f"🚨 **Suggest Mode Error**\n\nI encountered an error while generating suggestions for: \"{request.query}\"\n\nError: {str(e)}\n\nPlease try rephrasing your request or contact support.",
                mode_used=request.mode,
                processing_time=0.1,
                resources_used=[],
                confidence=0.0,
                metadata={"error": str(e)}
            )
    
    async def _handle_general_mode(self, request: ChatRequest) -> BrainResponse:
        """Handle General mode - Simple responses"""
        return BrainResponse(
            success=True,
            response=f"General mode processing: {request.query}. This will be replaced by specialized handler.",
            mode_used=request.mode,
            processing_time=0.2,
            resources_used=["llm"],
            confidence=0.6
        )
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            "resource_status": self.resource_manager.get_resource_status(),
            "performance_metrics": self.performance_metrics,
            "active_sessions": len(self.active_sessions),
            "handlers_registered": [mode.value for mode in self.mode_handlers.keys()],
            "system_health": "optimal" if self.performance_metrics["successful_requests"] / max(self.performance_metrics["total_requests"], 1) > 0.9 else "degraded"
        }

# Singleton instance
brain_router = BrainRouter()

async def process_chat_request(mode: str, query: str, user_id: str = "default", 
                             session_id: str = "default", context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Main API function for processing chat requests"""
    try:
        # FIX: Handle case sensitivity in mode values (e.g., "agent" vs "Agent")
        mode_upper = mode.upper() if mode else ""
        
        # Match the mode string with the appropriate ChatMode enum (case-insensitive)
        if mode_upper == "AGENT":
            chat_mode = ChatMode.AGENT
        elif mode_upper == "ASK":
            chat_mode = ChatMode.ASK
        elif mode_upper == "SUGGEST":
            chat_mode = ChatMode.SUGGEST
        else:
            # Default to General if no match
            chat_mode = ChatMode.GENERAL
            logger.warning(f"⚠️ Unknown mode '{mode}' converted to General mode")
        
        logger.info(f"🔍 Mode request: '{mode}' -> Using {chat_mode.value} mode")
            
        request = ChatRequest(
            mode=chat_mode,
            query=query,
            user_id=user_id,
            session_id=session_id,
            timestamp=time.time(),
            context=context or {}
        )
        
        response = await brain_router.process_request(request)
        
        return {
            "success": response.success,
            "response": response.response,
            "mode": response.mode_used.value,
            "processing_time": response.processing_time,
            "confidence": response.confidence,
            "verification_status": response.verification_status,
            "resources_used": response.resources_used,
            "metadata": response.metadata
        }
        
    except Exception as e:
        logger.error(f"Error in process_chat_request: {e}")
        return {
            "success": False,
            "response": f"Failed to process request: {str(e)}",
            "mode": mode,
            "processing_time": 0.0,
            "confidence": 0.0,
            "verification_status": "error",
            "resources_used": [],
            "metadata": {"error": str(e)}
        }

if __name__ == "__main__":
    # Test the brain router
    async def test_brain_router():
        print("Testing Brain Router...")
        
        # Test different modes
        modes = ["Agent", "Ask", "Suggest", "General"]
        
        for mode in modes:
            result = await process_chat_request(
                mode=mode,
                query=f"Test query for {mode} mode",
                user_id="test_user",
                session_id="test_session"
            )
            print(f"\n{mode} Mode Result:")
            print(json.dumps(result, indent=2))
        
        # Get system status
        print("\nSystem Status:")
        print(json.dumps(brain_router.get_system_status(), indent=2))
    
    asyncio.run(test_brain_router())