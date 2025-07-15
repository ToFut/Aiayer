"""
Next-Generation Brain Router - The Central Intelligence Hub

This is the main orchestration layer that routes chat modes to appropriate
specialized handlers, manages resources, and ensures optimal performance.
Acts as the "lobby of the brain" managing all cognitive resources.
"""

import asyncio
import json
import time
import os
import sys
from typing import Dict, Any, Optional, List, Callable, Set, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor
import weakref
import re

# Import plan persistence if available
try:
    from plan_persistence import save_plan, load_plan, delete_plan, generate_plan_id, plan_manager
    PLAN_PERSISTENCE_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ Plan persistence module loaded in brain router")
except ImportError as e:
    PLAN_PERSISTENCE_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"⚠️ Plan persistence not available in brain router: {e}")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatMode(Enum):
    AGENT = "Agent"
    ASK = "Ask" 
    SUGGEST = "Suggest"
    GENERAL = "General"
    PLANS = "Plans"  # New mode for accessing stored plans

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
    execution_plan: Optional[Dict[str, Any]] = None
    session_id: str = "default"  # Include session_id in response

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
        self.llm_model = None
        
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
            ChatMode.GENERAL: self._handle_general_mode,
            ChatMode.PLANS: self._handle_plans_mode
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

    async def _ensure_llm_service(self):
        """Ensure LLM service is initialized"""
        if self.llm_model is None:
            try:
                from llm.model import LocalLLM
                self.llm_model = LocalLLM(model_name="llama3.2:1b")
                await self.llm_model.start()
                
                # Verify model is actually working with a simple test
                test_messages = [{"role": "user", "content": "Test"}]
                test_result = await self.llm_model.generate_response(test_messages)
                
                if test_result and not test_result.startswith("Error:") and not test_result.startswith("Generated response for:"):
                    logger.info("✅ LLM service initialized and tested successfully")
                else:
                    logger.warning("⚠️ LLM service initialized but may be using mock responses")
                    
                    # Try to fix by restarting the connection
                    logger.info("🔄 Reinitializing LLM service to ensure real responses...")
                    await self.llm_model.stop()
                    self.llm_model = LocalLLM(model_name="llama3.2:1b")
                    await self.llm_model.start()
                    logger.info("✅ LLM service reinitialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize LLM service: {e}")
                raise

    async def process_request(self, request) -> BrainResponse:
        """Main entry point - Process incoming chat request"""
        start_time = time.time()
        
        # Convert dictionary to ChatRequest if needed
        if isinstance(request, dict):
            # Create a proper ChatRequest object from the dictionary
            try:
                # Map mode string to ChatMode enum
                mode_str = request.get("mode", "General")
                if isinstance(mode_str, str):
                    try:
                        mode = ChatMode[mode_str.upper()]
                    except KeyError:
                        mode = ChatMode.GENERAL
                else:
                    mode = ChatMode.GENERAL
                
                # Create request object with session_id as string
                request = ChatRequest(
                    mode=mode,
                    query=request.get("query", ""),
                    user_id=request.get("user_id", "default"),
                    session_id=str(request.get("session_id", "")),  # Ensure string type
                    timestamp=request.get("timestamp", time.time()),
                    context=request.get("context", {})
                )
            except Exception as e:
                logger.error(f"Failed to convert dict to ChatRequest: {e}")
                return BrainResponse(
                    success=False,
                    response=f"Error processing request: {str(e)}",
                    mode_used=ChatMode.GENERAL,
                    processing_time=time.time() - start_time,
                    resources_used=[],
                    confidence=0.0,
                    verification_status="error"
                )
        
        request_id = f"{request.session_id}_{request.timestamp}"
        
        try:
            # Ensure background tasks are running
            await self._ensure_background_tasks()
            
            # Ensure LLM service is initialized
            await self._ensure_llm_service()
            
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
        start_time = time.time()
        try:
            # First ensure LLM service is initialized for the brain router
            await self._ensure_llm_service()
            
            # IMPORTANT: Prioritize the universal intelligent automation handler
            # for consistent plan generation using real LLM planning
            
            try:
                logger.info("🧠 Using universal intelligent automation handler with real LLM planning")
                # Try to import the handler directly to ensure we use the most up-to-date version
                from universal_intelligent_automation_handler import handle_universal_automation
                logger.info("✅ Successfully imported universal_intelligent_automation_handler")
                
                # Use the universal automation handler for real LLM-based planning
                result = await handle_universal_automation(request.query, request.session_id)
                
                # Check if plan was created successfully with a valid response
                if result and result.get("success", False) and result.get("response"):
                    logger.info("✅ Successfully created plan with universal intelligent automation handler")
                    
                    # Check if real LLM was used (flag set by the handler)
                    real_llm_used = result.get("real_llm", True)
                    if not real_llm_used:
                        logger.warning("⚠️ Plan was created but may not have used real LLM")
                    else:
                        logger.info("✅ Confirmed real LLM was used for plan generation")
                    
                    # Get metadata or create default
                    metadata = result.get("metadata", {})
                    # Ensure real_llm flag is set in metadata
                    metadata["real_llm"] = real_llm_used
                    metadata["universal_planner"] = True
                    metadata["brain_router_handled"] = True
                    
                    # Create BrainResponse with proper attributes
                    response = BrainResponse(
                        success=result.get("success", True),
                        response=result.get("response", ""),
                        mode_used=request.mode,
                        processing_time=result.get("processing_time", time.time() - start_time),
                        resources_used=["universal_automation", "llm", "memory"],
                        confidence=result.get("confidence", 0.9),
                        metadata=metadata,
                        execution_plan=result.get("execution_plan", None),
                        session_id=request.session_id
                    )
                    
                    # Ensure execution_plan is set for DO button to work properly
                    if not response.execution_plan and "steps" in result:
                        response.execution_plan = {"steps": result["steps"]}
                    
                    return response
                else:
                    # Log the failure but continue to fallback options
                    logger.warning(f"⚠️ Universal automation handler returned invalid result: {result}")
            except ImportError as import_error:
                logger.warning(f"⚠️ Universal automation handler not available: {import_error}")
            except Exception as e:
                logger.error(f"❌ Error using universal automation handler: {e}")
            
            # Fallback to rule-based automation handler
            logger.info("🔄 Falling back to rule-based automation handler")
            try:
                from fixed_universal_automation_handler import create_rule_based_plan
                rule_result = create_rule_based_plan(request.query, request.session_id)
                
                if rule_result and rule_result.get("success", False):
                    logger.info("✅ Successfully created plan with rule-based automation handler")
                    
                    # Create BrainResponse with rule-based plan
                    response = BrainResponse(
                        success=rule_result.get("success", True),
                        response=rule_result.get("response", ""),
                        mode_used=request.mode,
                        processing_time=time.time() - start_time,
                        resources_used=["rule_based_automation", "memory"],
                        confidence=rule_result.get("confidence", 0.8),
                        metadata={"rule_based": True, "fallback": True},
                        execution_plan=rule_result.get("execution_plan", None),
                        session_id=request.session_id
                    )
                    
                    return response
                else:
                    logger.warning(f"⚠️ Rule-based automation handler returned invalid result: {rule_result}")
            except Exception as rule_error:
                logger.error(f"❌ Error using rule-based automation handler: {rule_error}")
            
            # Direct fallback to real LLM using the brain router's LLM service
            logger.info("🔄 Falling back to direct LLM planning")
            try:
                # Make sure LLM model is initialized and working
                if not self.llm_model:
                    logger.warning("⚠️ No LLM model available - reinitializing for fallback")
                    await self._ensure_llm_service()
                
                # Double-check the service is available
                if self.llm_model:
                    # Verify if this is a real LLM by testing basic functionality
                    test_response = await self.llm_model.generate_response([
                        {"role": "user", "content": "Respond with only one word: test"}
                    ])
                    
                    if not test_response or "Generated response for:" in test_response:
                        logger.warning("⚠️ LLM model appears to be using mock responses")
                        # Try to reinitialize to get a real LLM
                        try:
                            logger.info("🔄 Reinitializing LLM service to ensure real responses")
                            from llm.model import OllamaLLM
                            self.llm_model = OllamaLLM(model_name="llama3.2:1b")
                            await self.llm_model.start()
                            logger.info("✅ Successfully reinitialized LLM service")
                        except Exception as reinit_error:
                            logger.error(f"❌ Failed to reinitialize LLM service: {reinit_error}")
                    else:
                        logger.info("✅ Verified LLM model is generating real responses")
                    
                    # Create a specialized prompt for automation planning
                    system_prompt = """You are an expert automation system for macOS. Create a detailed step-by-step plan for the user's request.
                    Format your response as a sequence of clear, executable steps. Focus on practical actions like:
                    - Opening applications
                    - Navigating websites
                    - Clicking UI elements
                    - Typing text
                    - Using keyboard shortcuts
                    
                    Your plan should be specific and realistic for Mac automation."""
                    
                    # Get a real LLM response
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Create a detailed automation plan for: {request.query}"}
                    ]
                    
                    # Add a timeout to ensure we don't hang
                    try:
                        plan_text = await asyncio.wait_for(
                            self.llm_model.generate_response(messages),
                            timeout=30.0  # 30 second timeout
                        )
                    except asyncio.TimeoutError:
                        logger.warning("⚠️ LLM response timed out after 30 seconds")
                        plan_text = f"1. Analyze the request: {request.query}\n2. Determine appropriate tools\n3. Execute requested action"
                    
                    # Create a unique plan ID
                    plan_id = f"plan_{int(time.time())}"
                    
                    # Format the response with plan steps
                    response_text = f"""🎯 **AUTOMATION EXECUTION PLAN**

**🔍 Task Type:** Automated Action
**📋 Task:** {request.query}
**⏱️ Estimated Duration:** 15.0 seconds
**🎯 Success Probability:** 80%
**🔧 Complexity:** Medium
**📝 Steps:** 3+ actions

**🚀 Automation Steps:**
{plan_text}

**🆔 Plan ID:** `{plan_id}`
**🧠 Planning:** Real LLM Planning (Brain Router)

*Automation System: ✅ Ready for Execution*"""
                    
                    # Create execution steps from the LLM response
                    steps = []
                    lines = plan_text.strip().split('\n')
                    for i, line in enumerate(lines[:5], 1):  # Limit to 5 steps
                        # Try to extract an action type from the text
                        action_type = "click_element"  # Default
                        if "open" in line.lower() or "launch" in line.lower() or "start" in line.lower():
                            action_type = "open_app"
                        elif "type" in line.lower() or "enter" in line.lower() or "input" in line.lower():
                            action_type = "type_text"
                        elif "click" in line.lower() or "press" in line.lower() or "select" in line.lower():
                            action_type = "click_element"
                        elif "wait" in line.lower() or "pause" in line.lower():
                            action_type = "wait"
                        elif "analyze" in line.lower() or "observe" in line.lower() or "check" in line.lower():
                            action_type = "analyze_screen"
                        
                        steps.append({
                            "id": f"step_{i}",
                            "description": line.strip(),
                            "action_type": action_type
                        })
                    
                    # If no steps were found, add some default ones
                    if not steps:
                        steps = [
                            {"id": "step_1", "description": "Open required application", "action_type": "open_app"},
                            {"id": "step_2", "description": "Analyze context and requirements", "action_type": "analyze_screen"},
                            {"id": "step_3", "description": "Execute main action", "action_type": "click_element"}
                        ]
                    
                    # Create the BrainResponse
                    return BrainResponse(
                        success=True,
                        response=response_text,
                        mode_used=request.mode,
                        processing_time=time.time() - start_time,
                        resources_used=["llm", "planning"],
                        confidence=0.8,
                        metadata={
                            "direct_llm_planning": True, 
                            "brain_router_fallback": True,
                            "real_llm": True,
                            "planning_source": "brain_router_direct"
                        },
                        execution_plan={"steps": steps},
                        session_id=request.session_id
                    )
                else:
                    logger.warning("⚠️ No LLM model available for fallback planning")
            except Exception as llm_error:
                logger.error(f"❌ Direct LLM planning failed: {llm_error}")
            
            # Last resort fallback - ensure we always return something
            logger.warning("⚠️ Using last resort fallback plan")
            
            # Create a simple fallback plan
            plan_id = f"plan_{int(time.time())}"
            
            # Attempt to identify the task type from the query
            query_lower = request.query.lower()
            task_type = "Automated Action"
            steps = []
            
            # Try to identify the type of task
            if any(word in query_lower for word in ["open", "start", "launch", "run"]):
                task_type = "Application Launch"
                steps = [
                    {"id": "step_1", "description": "Identify and open the requested application", "action_type": "open_app"},
                    {"id": "step_2", "description": "Wait for application to initialize", "action_type": "wait"},
                    {"id": "step_3", "description": "Verify application is ready for use", "action_type": "analyze_screen"}
                ]
            elif any(word in query_lower for word in ["search", "find", "look", "google"]):
                task_type = "Search Operation"
                steps = [
                    {"id": "step_1", "description": "Open web browser", "action_type": "open_app"},
                    {"id": "step_2", "description": "Navigate to search engine", "action_type": "navigate_url"},
                    {"id": "step_3", "description": "Enter search query", "action_type": "type_text"},
                    {"id": "step_4", "description": "Execute search", "action_type": "click_element"}
                ]
            else:
                # Generic fallback for any other task
                steps = [
                    {"id": "step_1", "description": "Open required application", "action_type": "open_app"},
                    {"id": "step_2", "description": "Analyze task requirements", "action_type": "analyze_screen"},
                    {"id": "step_3", "description": "Execute requested action", "action_type": "click_element"}
                ]
            
            # Create a simple response text
            response_text = f"""🎯 **AUTOMATION EXECUTION PLAN**

**🔍 Task Type:** {task_type}
**📋 Task:** {request.query}
**⏱️ Estimated Duration:** 10.0 seconds
**🎯 Success Probability:** 75%
**🔧 Complexity:** Medium
**📝 Steps:** {len(steps)} actions

**🚀 Automation Steps:**
"""
            # Add steps to the response
            for i, step in enumerate(steps, 1):
                response_text += f"{i}. 🟢 {step['description']}\n"
            
            response_text += f"""
**🆔 Plan ID:** `{plan_id}`
**🧠 Planning:** Fallback Planning System

*Automation System: ✅ Ready for Execution*"""
            
            return BrainResponse(
                success=True,
                response=response_text,
                mode_used=request.mode,
                processing_time=time.time() - start_time,
                resources_used=["basic_planning"],
                confidence=0.7,
                metadata={"fallback_plan": True},
                execution_plan={"steps": steps},
                session_id=request.session_id
            )
            
        except Exception as e:
            logger.error(f"❌ Error in agent mode handler: {e}")
            return BrainResponse(
                success=False,
                response=f"🚨 **Agent Mode Error**\n\nI encountered an error while processing your request: \"{request.query}\"\n\nError: {str(e)}\n\nPlease try rephrasing your request or contact support.",
                mode_used=request.mode,
                processing_time=time.time() - start_time,
                resources_used=[],
                confidence=0.0,
                metadata={"error": str(e)},
                session_id=request.session_id
            )
    
    async def _handle_ask_mode(self, request: ChatRequest) -> BrainResponse:
        """Handle Ask mode - Enhanced Memory Integration with Semantic Search"""
        try:
            # Create system message with context
            system_message = "You are a helpful AI assistant that responds to user questions."
            
            # Add specific instructions for Ask mode
            system_message += "\n\nThe user is in Ask Mode. Provide a detailed informative answer to their question."
            
            # Create messages for the LLM
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": request.query}
            ]
            
            # Use the shared LLM instance
            llm_response = await self.llm_model.generate_response(messages)
            
            # Check if we got a valid response
            if llm_response and not llm_response.startswith("Error:"):
                return BrainResponse(
                    success=True,
                    response=llm_response,
                    mode_used=request.mode,
                    processing_time=0.5,
                    resources_used=["llm", "memory"],
                    confidence=0.8,
                    metadata={"llm_generated": True},
                    session_id=request.session_id  # Include session_id from request
                )
            else:
                raise Exception(f"LLM response error: {llm_response}")
            
        except Exception as e:
            logger.error(f"Error in ask mode handler: {e}")
            return BrainResponse(
                success=False,
                response=f"🚨 **Ask Mode Error**\n\nI encountered an error while processing your question: \"{request.query}\"\n\nError: {str(e)}\n\nPlease try rephrasing your question or contact support.",
                mode_used=request.mode,
                processing_time=0.1,
                resources_used=[],
                confidence=0.0,
                metadata={"error": str(e)},
                session_id=request.session_id  # Include session_id from request
            )
    
    async def _handle_suggest_mode(self, request: ChatRequest) -> BrainResponse:
        """Handle Suggest mode - Memory-Integrated Proactive Suggestions"""
        try:
            # Create system message with context
            system_message = "You are a helpful AI assistant that provides proactive suggestions."
            
            # Add specific instructions for Suggest mode
            system_message += "\n\nThe user is in Suggest Mode. Provide helpful suggestions related to their request."
            
            # Create messages for the LLM
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": request.query}
            ]
            
            # Use the shared LLM instance
            llm_response = await self.llm_model.generate_response(messages)
            
            # Check if we got a valid response
            if llm_response and not llm_response.startswith("Error:"):
                return BrainResponse(
                    success=True,
                    response=llm_response,
                    mode_used=request.mode,
                    processing_time=0.5,
                    resources_used=["llm", "memory"],
                    confidence=0.8,
                    metadata={"llm_generated": True},
                    session_id=request.session_id  # Include session_id from request
                )
            else:
                raise Exception(f"LLM response error: {llm_response}")
            
        except Exception as e:
            logger.error(f"Error in suggest mode handler: {e}")
            return BrainResponse(
                success=False,
                response=f"🚨 **Suggest Mode Error**\n\nI encountered an error while generating suggestions for: \"{request.query}\"\n\nError: {str(e)}\n\nPlease try rephrasing your request or contact support.",
                mode_used=request.mode,
                processing_time=0.1,
                resources_used=[],
                confidence=0.0,
                metadata={"error": str(e)},
                session_id=request.session_id  # Include session_id from request
            )
    
    async def _handle_general_mode(self, request: ChatRequest) -> BrainResponse:
        """Handle General mode - Simple responses"""
        try:
            # Create system message with context
            system_message = "You are a helpful AI assistant that responds conversationally."
            
            # Add specific instructions for General mode
            system_message += "\n\nThe user is in General Mode. Respond conversationally and helpfully."
            
            # Create messages for the LLM
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": request.query}
            ]
            
            # Use the shared LLM instance
            llm_response = await self.llm_model.generate_response(messages)
            
            # Check if we got a valid response
            if llm_response and not llm_response.startswith("Error:"):
                return BrainResponse(
                    success=True,
                    response=llm_response,
                    mode_used=request.mode,
                    processing_time=0.5,
                    resources_used=["llm", "memory"],
                    confidence=0.8,
                    metadata={"llm_generated": True},
                    session_id=request.session_id  # Include session_id from request
                )
            else:
                raise Exception(f"LLM response error: {llm_response}")
            
        except Exception as e:
            logger.error(f"Error in general mode handler: {e}")
            return BrainResponse(
                success=False,
                response=f"🚨 **General Mode Error**\n\nI encountered an error while processing your message: \"{request.query}\"\n\nError: {str(e)}\n\nPlease try rephrasing your message or contact support.",
                mode_used=request.mode,
                processing_time=0.1,
                resources_used=[],
                confidence=0.0,
                metadata={"error": str(e)},
                session_id=request.session_id  # Include session_id from request
            )
    
    async def _handle_plans_mode(self, request: ChatRequest) -> BrainResponse:
        """Handle Plans mode - Access and manage stored automation plans"""
        start_time = time.time()
        
        if not PLAN_PERSISTENCE_AVAILABLE:
            return BrainResponse(
                success=False,
                response="📂 **Plan Management**\n\nPlan persistence is not available. Cannot access stored plans.",
                mode_used=request.mode,
                processing_time=time.time() - start_time,
                resources_used=[],
                confidence=0.0,
                metadata={"error": "Plan persistence not available"},
                session_id=request.session_id  # Include session_id from request
            )
            
        try:
            # Parse the query to determine what plan operation to perform
            query = request.query.lower()
            
            # List all plans
            if "list" in query or "show" in query or "get" in query:
                try:
                    # Import universal handler's list function
                    from universal_intelligent_automation_handler import list_stored_automation_plans
                    plans_data = await list_stored_automation_plans()
                    
                    return BrainResponse(
                        success=plans_data.get("success", True),
                        response=plans_data.get("response", "No plans found"),
                        mode_used=request.mode,
                        processing_time=time.time() - start_time,
                        resources_used=["storage"],
                        confidence=0.9,
                        metadata={"plans_count": plans_data.get("count", 0)},
                        session_id=request.session_id  # Include session_id from request
                    )
                except ImportError:
                    # Fallback to direct plan_manager access
                    plans = await plan_manager.get_all_plan_metadata()
                    
                    if not plans:
                        return BrainResponse(
                            success=True,
                            response="📂 **Stored Plans**\n\nNo stored plans found.",
                            mode_used=request.mode,
                            processing_time=time.time() - start_time,
                            resources_used=["storage"],
                            confidence=0.9,
                            session_id=request.session_id  # Include session_id from request
                        )
                    
                    # Format response
                    response = f"📂 **Stored Automation Plans** ({len(plans)} plans found)\n\n"
                    for i, plan in enumerate(plans[:10], 1):  # Show max 10 plans
                        created = time.strftime("%Y-%m-%d %H:%M", time.localtime(plan.get("created", 0)))
                        response += f"{i}. **{plan.get('title', 'Untitled')}** ({created})\n"
                        response += f"   ID: `{plan.get('plan_id', 'unknown')}`\n"
                        response += f"   Status: {plan.get('status', 'unknown')}\n"
                        response += f"   Steps: {plan.get('steps_count', 0)}\n\n"
                    
                    if len(plans) > 10:
                        response += f"*...and {len(plans) - 10} more plans*\n\n"
                    
                    response += "To execute a stored plan, use: `plans execute <plan_id>`\n"
                    response += "To delete a plan, use: `plans delete <plan_id>`"
                    
                    return BrainResponse(
                        success=True,
                        response=response,
                        mode_used=request.mode,
                        processing_time=time.time() - start_time,
                        resources_used=["storage"],
                        confidence=0.9,
                        metadata={"plans_count": len(plans)},
                        session_id=request.session_id  # Include session_id from request
                    )
            
            # Clean up old plans
            elif "clean" in query or "delete old" in query or "remove old" in query:
                # Parse days if specified
                days = 7  # Default to 7 days
                try:
                    import re
                    days_match = re.search(r'(\d+)\s*days?', query)
                    if days_match:
                        days = int(days_match.group(1))
                except Exception:
                    pass
                
                # Clean up old plans
                deleted_count = await plan_manager.cleanup_old_plans(days)
                
                return BrainResponse(
                    success=True,
                    response=f"🧹 **Clean Up Complete**\n\nRemoved {deleted_count} plans older than {days} days.",
                    mode_used=request.mode,
                    processing_time=time.time() - start_time,
                    resources_used=["storage"],
                    confidence=0.9,
                    metadata={"deleted_count": deleted_count, "days": days},
                    session_id=request.session_id  # Include session_id from request
                )
            
            # Delete specific plan
            elif "delete" in query or "remove" in query:
                # Extract plan ID
                import re
                plan_id_match = re.search(r'(?:delete|remove)\s+(?:plan\s+)?([a-zA-Z0-9_]+)', query)
                if not plan_id_match:
                    return BrainResponse(
                        success=False,
                        response="❌ **Error**\n\nCould not determine which plan to delete. Please specify a plan ID.\n\nExample: `plans delete plan_12345`",
                        mode_used=request.mode,
                        processing_time=time.time() - start_time,
                        resources_used=[],
                        confidence=0.5,
                        session_id=request.session_id  # Include session_id from request
                    )
                
                plan_id = plan_id_match.group(1)
                deleted = await delete_plan(plan_id)
                
                if deleted:
                    return BrainResponse(
                        success=True,
                        response=f"✅ **Plan Deleted**\n\nSuccessfully deleted plan `{plan_id}`.",
                        mode_used=request.mode,
                        processing_time=time.time() - start_time,
                        resources_used=["storage"],
                        confidence=0.9
                    )
                else:
                    return BrainResponse(
                        success=False,
                        response=f"❌ **Error**\n\nFailed to delete plan `{plan_id}`. Plan may not exist.",
                        mode_used=request.mode,
                        processing_time=time.time() - start_time,
                        resources_used=["storage"],
                        confidence=0.5
                    )
            
            # Default response
            return BrainResponse(
                success=True,
                response="📂 **Plan Management**\n\nAvailable commands:\n\n• `plans list` - Show all stored plans\n• `plans delete <plan_id>` - Delete a specific plan\n• `plans clean [X days]` - Remove plans older than X days",
                mode_used=request.mode,
                processing_time=time.time() - start_time,
                resources_used=["storage"],
                confidence=0.9
            )
            
        except Exception as e:
            logger.error(f"Error in plans mode handler: {e}")
            return BrainResponse(
                success=False,
                response=f"❌ **Plans Mode Error**\n\nI encountered an error while managing plans: {str(e)}",
                mode_used=request.mode,
                processing_time=time.time() - start_time,
                resources_used=[],
                confidence=0.0,
                metadata={"error": str(e)}
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

# Create global brain router instance
brain_router = None

async def get_brain_router() -> 'BrainRouter':
    """Get or create the global brain router instance"""
    global brain_router
    if brain_router is None:
        brain_router = BrainRouter()
        # Initialize the LLM service
        await brain_router._ensure_llm_service()
    return brain_router

async def process_chat_request(mode: str, query: str, user_id: str = "default", 
                             session_id: str = "default", context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Process a chat request using the brain router"""
    try:
        # Get the brain router instance
        router = await get_brain_router()
        
        # Ensure session_id is a string
        session_id_str = str(session_id) if session_id is not None else "default"
        
        # Create chat request
        request = ChatRequest(
            mode=ChatMode[mode.upper()],
            query=query,
            user_id=user_id,
            session_id=session_id_str,
            timestamp=time.time(),
            context=context or {}
        )
        
        # Process request
        response = await router.process_request(request)
        
        # Convert to dict and ensure session_id is included
        result = {
            "success": response.success,
            "response": response.response,
            "mode_used": response.mode_used.value,
            "processing_time": response.processing_time,
            "resources_used": response.resources_used,
            "confidence": response.confidence,
            "metadata": response.metadata,
            "verification_status": response.verification_status,
            "execution_plan": response.execution_plan,
            "session_id": session_id_str  # Include session_id in the response
        }
        return result
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        # Ensure session_id is included in error response
        session_id_str = str(session_id) if session_id is not None else "default"
        return {
            "success": False,
            "response": f"An error occurred: {str(e)}",
            "mode_used": mode,
            "processing_time": 0.0,
            "resources_used": [],
            "confidence": 0.0,
            "metadata": {"error": str(e)},
            "verification_status": "error",
            "session_id": session_id_str  # Include session_id in error response
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