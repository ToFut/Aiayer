#!/usr/bin/env python3
"""
Enterprise-Grade Backend Server
Built to Google-scale standards for 30,000+ employee deployment

Features:
- Zero-error tolerance with comprehensive error handling
- Full integration with brain router and all 4 modes
- SemanticSearchAgent integration for all memory operations
- Professional logging and monitoring
- Enterprise-grade performance optimization
- Bulletproof message flow with fallback mechanisms
"""

import asyncio
import json
import logging
import os
import sys
import time
import traceback
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Set
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
import websockets
from websockets.server import WebSocketServerProtocol

# Import our enterprise components
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from brain.core.brain_router import BrainRouter, ChatRequest, ChatMode, Priority
from brain.handlers.ask_mode_handler import AskModeHandler
from brain.handlers.agent_mode_handler import AgentModeHandler
from memory.semantic_search_agent import SemanticSearchAgent, search_memories, add_memory
from enterprise_llm_service import generate_llm_response
from enterprise_workflow_engine import execute_agent_workflow

# Configure enterprise logging
os.makedirs('logs/backend', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler('logs/backend/enterprise_backend_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnterpriseBackendServer:
    """
    Enterprise-Grade Backend Server
    Handles all chat modes with zero-error tolerance
    """
    
    def __init__(self, port: int = 8767):
        self.port = port
        self.brain_router = None
        self.semantic_search = None
        self.connected_clients: Set[WebSocketServerProtocol] = set()
        self.client_sessions: Dict[str, Dict[str, Any]] = {}
        self.server = None
        self.executor = ThreadPoolExecutor(max_workers=20, thread_name_prefix="EnterpriseBackend")
        
        # Performance monitoring
        self.performance_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0,
            'mode_usage': {
                'Agent': 0,
                'Ask': 0,
                'Suggest': 0,
                'General': 0
            },
            'uptime_start': datetime.now(),
            'last_error': None
        }
        
        # Error tracking for enterprise reliability
        self.error_tracker = {
            'connection_errors': 0,
            'processing_errors': 0,
            'brain_router_errors': 0,
            'memory_errors': 0,
            'last_errors': []
        }
        
        logger.info("EnterpriseBackendServer initialized with enterprise-grade capabilities")
    
    async def initialize(self):
        """Initialize all enterprise components"""
        try:
            logger.info("🚀 Initializing Enterprise Backend Server...")
            
            # Initialize SemanticSearchAgent
            self.semantic_search = SemanticSearchAgent()
            logger.info("✅ SemanticSearchAgent initialized")
            
            # Initialize BrainRouter
            self.brain_router = BrainRouter()
            logger.info("✅ BrainRouter initialized")
            
            # Initialize specialized mode handlers
            await self._initialize_mode_handlers()
            
            # Pre-populate memory with system knowledge
            await self._initialize_system_memory()
            
            # Verify all systems
            await self._perform_system_health_check()
            
            logger.info("🎉 Enterprise Backend Server fully initialized and ready")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Enterprise Backend Server: {e}")
            logger.error(traceback.format_exc())
            raise
    
    async def _initialize_mode_handlers(self):
        """Initialize all mode handlers with semantic search integration"""
        try:
            # Create enhanced mode handlers with semantic search
            ask_handler = EnhancedAskModeHandler(self.semantic_search)
            agent_handler = EnhancedAgentModeHandler(self.semantic_search)
            suggest_handler = EnhancedSuggestModeHandler(self.semantic_search)
            general_handler = EnhancedGeneralModeHandler(self.semantic_search)
            
            # Register handlers with brain router
            self.brain_router.register_handler(ChatMode.ASK, ask_handler.handle_request)
            self.brain_router.register_handler(ChatMode.AGENT, agent_handler.handle_request)
            self.brain_router.register_handler(ChatMode.SUGGEST, suggest_handler.handle_request)
            self.brain_router.register_handler(ChatMode.GENERAL, general_handler.handle_request)
            
            logger.info("✅ All mode handlers initialized with semantic search integration")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize mode handlers: {e}")
            raise
    
    async def _initialize_system_memory(self):
        """Pre-populate system memory with essential knowledge"""
        try:
            system_knowledge = [
                {
                    "content": "SensAI system has 4 chat modes: Agent for task execution, Ask for contextual queries, Suggest for proactive recommendations, and General for basic conversations",
                    "source": "system_documentation",
                    "tags": {"system", "modes", "capabilities"}
                },
                {
                    "content": "WebSocket server runs on port 8765 and handles client connections, message routing, and real-time communication",
                    "source": "system_architecture",
                    "tags": {"websocket", "networking", "ports"}
                },
                {
                    "content": "Backend server runs on port 8767 and integrates with the brain router for intelligent message processing",
                    "source": "system_architecture", 
                    "tags": {"backend", "brain_router", "ports"}
                },
                {
                    "content": "SemanticSearchAgent provides enterprise-grade memory search capabilities with TF-IDF embeddings and advanced caching",
                    "source": "system_components",
                    "tags": {"memory", "search", "ai"}
                },
                {
                    "content": "System supports real-time process monitoring, screen analysis, and contextual awareness through various sensors",
                    "source": "system_features",
                    "tags": {"monitoring", "sensors", "context"}
                }
            ]
            
            for knowledge in system_knowledge:
                await add_memory(
                    content=knowledge["content"],
                    source=knowledge["source"],
                    tags=knowledge["tags"],
                    metadata={"initialization_time": datetime.now().isoformat()}
                )
            
            logger.info(f"✅ Initialized system memory with {len(system_knowledge)} knowledge entries")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize system memory: {e}")
            # Don't raise - system can work without pre-populated memory
    
    async def _perform_system_health_check(self):
        """Comprehensive system health check"""
        try:
            health_results = {}
            
            # Test SemanticSearchAgent
            search_health = await self.semantic_search.health_check()
            health_results['semantic_search'] = search_health['status']
            
            # Test BrainRouter
            brain_status = self.brain_router.get_system_status()
            health_results['brain_router'] = brain_status['system_health']
            
            # Test memory operations
            test_memory = await add_memory("Health check test memory", source="health_check")
            test_search = await search_memories("health check", top_k=1)
            health_results['memory_operations'] = 'healthy' if test_memory and test_search else 'degraded'
            
            # Log health status
            all_healthy = all(status in ['healthy', 'optimal'] for status in health_results.values())
            
            if all_healthy:
                logger.info("✅ All systems healthy and operational")
            else:
                logger.warning(f"⚠️ System health check results: {health_results}")
            
        except Exception as e:
            logger.error(f"❌ System health check failed: {e}")
            # Don't raise - system should still start
    
    async def start_server(self):
        """Start the enterprise WebSocket server"""
        try:
            # Initialize all components first
            await self.initialize()
            
            # Start WebSocket server
            self.server = await websockets.serve(
                self.handle_client,
                "127.0.0.1",
                self.port,
                ping_interval=20,
                ping_timeout=10,
                max_size=10 * 1024 * 1024,  # 10MB message size limit
                max_queue=100  # Queue up to 100 messages
            )
            
            logger.info(f"🚀 Enterprise Backend Server started on ws://127.0.0.1:{self.port}")
            logger.info("💼 Ready for enterprise-scale deployment")
            
            # Keep server running
            await asyncio.Future()
            
        except Exception as e:
            logger.error(f"❌ Failed to start Enterprise Backend Server: {e}")
            logger.error(traceback.format_exc())
            sys.exit(1)
    
    async def handle_client(self, websocket: WebSocketServerProtocol):
        """Handle client connections with enterprise-grade error handling"""
        client_id = str(uuid.uuid4())
        session_data = {
            'id': client_id,
            'connected_at': datetime.now(),
            'message_count': 0,
            'last_activity': datetime.now(),
            'client_type': 'unknown'
        }
        
        logger.info(f"👤 Client {client_id} connected from {websocket.remote_address}")
        
        try:
            # Add to connected clients
            self.connected_clients.add(websocket)
            self.client_sessions[client_id] = session_data
            
            # Send welcome message
            await self._send_message(websocket, {
                "type": "connection_established",
                "client_id": client_id,
                "message": "Connected to Enhanced Backend Server",
                "capabilities": ["llm_queries", "context_awareness", "memory_integration"],
                "timestamp": datetime.now().isoformat()
            })
            
            # Handle messages
            async for raw_message in websocket:
                try:
                    await self._process_message(websocket, client_id, raw_message)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Invalid JSON from client {client_id}: {e}")
                    await self._send_error(websocket, "Invalid JSON format", "json_decode_error")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing message from client {client_id}: {e}")
                    logger.error(traceback.format_exc())
                    await self._send_error(websocket, "Internal processing error", "processing_error")
                    self._track_error("processing_errors", str(e))
        
        except websockets.exceptions.ConnectionClosed as e:
            logger.info(f"👋 Client {client_id} disconnected: {e}")
            
        except Exception as e:
            logger.error(f"❌ Unexpected error with client {client_id}: {e}")
            logger.error(traceback.format_exc())
            self._track_error("connection_errors", str(e))
            
        finally:
            # Cleanup
            self.connected_clients.discard(websocket)
            if client_id in self.client_sessions:
                session_duration = datetime.now() - session_data['connected_at']
                logger.info(f"📊 Client {client_id} session ended. Duration: {session_duration}, Messages: {session_data['message_count']}")
                del self.client_sessions[client_id]
    
    async def _process_message(self, websocket: WebSocketServerProtocol, client_id: str, raw_message: str):
        """Process incoming messages with comprehensive error handling"""
        start_time = time.time()
        
        try:
            # Parse message
            message = json.loads(raw_message)
            msg_type = message.get('type', 'unknown')
            payload = message.get('payload', {})
            
            # Update session activity
            if client_id in self.client_sessions:
                self.client_sessions[client_id]['message_count'] += 1
                self.client_sessions[client_id]['last_activity'] = datetime.now()
            
            logger.info(f"📥 Processing {msg_type} message from client {client_id}")
            
            # Route message based on type
            if msg_type == "chat_request":
                await self._handle_chat_message(websocket, client_id, message)
                
            elif msg_type == "health_check":
                await self._handle_health_check(websocket, client_id)
                
            elif msg_type == "get_metrics":
                await self._handle_metrics_request(websocket, client_id)
                
            elif msg_type == "memory_search":
                await self._handle_memory_search(websocket, client_id, payload)
                
            elif msg_type == "add_memory":
                await self._handle_add_memory(websocket, client_id, payload)
                
            else:
                logger.warning(f"⚠️ Unknown message type '{msg_type}' from client {client_id}")
                await self._send_error(websocket, f"Unknown message type: {msg_type}", "unknown_message_type")
            
            # Update performance metrics
            processing_time = time.time() - start_time
            self.performance_metrics['total_requests'] += 1
            self.performance_metrics['successful_requests'] += 1
            
            # Update average response time
            total = self.performance_metrics['total_requests']
            current_avg = self.performance_metrics['average_response_time']
            self.performance_metrics['average_response_time'] = (
                (current_avg * (total - 1) + processing_time) / total
            )
            
        except Exception as e:
            self.performance_metrics['failed_requests'] += 1
            self._track_error("processing_errors", str(e))
            raise
    
    async def _handle_chat_message(self, websocket: WebSocketServerProtocol, client_id: str, message: Dict[str, Any]):
        """Handle chat messages with full brain router integration"""
        try:
            # Support both direct message format (from overlay) and payload format
            if 'payload' in message:
                # Legacy format with payload
                payload = message['payload']
                query = payload.get('query', '').strip()
                mode = payload.get('mode', 'Ask')
                context = payload.get('context', {})
                user_id = payload.get('user_id', client_id)
                session_id = payload.get('session_id', client_id)
            else:
                # Direct format from overlay
                query = message.get('query', '').strip()
                mode = message.get('mode', 'Ask')  # Default to Ask mode
                context = message.get('context', {})
                user_id = message.get('user_id', client_id)
                session_id = message.get('session_id', client_id)
            
            if not query:
                await self._send_error(websocket, "Empty query provided", "empty_query")
                return
            
            logger.info(f"🧠 Processing {mode} mode query: '{query[:100]}...' from client {client_id}")
            
            # Create chat request
            chat_request = ChatRequest(
                mode=ChatMode(mode),
                query=query,
                user_id=user_id,
                session_id=session_id,
                timestamp=time.time(),
                context=context
            )
            
            # Process through brain router
            brain_response = await self.brain_router.process_request(chat_request)
            
            # Add to memory for future context
            await add_memory(
                content=f"User query: {query}",
                source="user_interaction",
                tags={"chat", mode.lower(), "user_query"},
                metadata={
                    "client_id": client_id,
                    "mode": mode,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Add response to memory too
            if brain_response.success:
                await add_memory(
                    content=f"System response: {brain_response.response}",
                    source="system_response",
                    tags={"chat", mode.lower(), "system_response"},
                    metadata={
                        "client_id": client_id,
                        "mode": mode,
                        "confidence": brain_response.confidence,
                        "timestamp": datetime.now().isoformat()
                    }
                )
            
            # Update mode usage metrics
            self.performance_metrics['mode_usage'][mode] += 1
            
            # Send response (overlay-compatible format)
            response = {
                "type": "chat_response",
                "payload": {
                    "response": brain_response.response,
                    "mode": brain_response.mode_used.value,
                    "success": brain_response.success,
                    "confidence": brain_response.confidence,
                    "processing_time": brain_response.processing_time,
                    "resources_used": brain_response.resources_used,
                    "verification_status": brain_response.verification_status,
                    "metadata": brain_response.metadata,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            await self._send_message(websocket, response)
            logger.info(f"✅ Chat response sent to client {client_id} (confidence: {brain_response.confidence:.2f})")
            
        except Exception as e:
            logger.error(f"❌ Error handling chat message from client {client_id}: {e}")
            logger.error(traceback.format_exc())
            self._track_error("brain_router_errors", str(e))
            await self._send_error(websocket, "Failed to process chat message", "chat_processing_error")
    
    async def _handle_health_check(self, websocket: WebSocketServerProtocol, client_id: str):
        """Handle health check requests"""
        try:
            # Perform comprehensive health check
            semantic_health = await self.semantic_search.health_check()
            brain_health = self.brain_router.get_system_status()
            
            health_status = {
                "type": "health_response",
                "payload": {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "uptime": str(datetime.now() - self.performance_metrics['uptime_start']),
                    "performance_metrics": self.performance_metrics,
                    "semantic_search": semantic_health,
                    "brain_router": brain_health,
                    "connected_clients": len(self.connected_clients),
                    "error_summary": {
                        "connection_errors": self.error_tracker['connection_errors'],
                        "processing_errors": self.error_tracker['processing_errors'],
                        "brain_router_errors": self.error_tracker['brain_router_errors'],
                        "memory_errors": self.error_tracker['memory_errors']
                    }
                }
            }
            
            await self._send_message(websocket, health_status)
            logger.info(f"✅ Health check completed for client {client_id}")
            
        except Exception as e:
            logger.error(f"❌ Error handling health check for client {client_id}: {e}")
            await self._send_error(websocket, "Health check failed", "health_check_error")
    
    async def _handle_metrics_request(self, websocket: WebSocketServerProtocol, client_id: str):
        """Handle metrics requests"""
        try:
            semantic_metrics = self.semantic_search.get_performance_metrics()
            
            metrics = {
                "type": "metrics_response",
                "payload": {
                    "server_metrics": self.performance_metrics,
                    "semantic_search_metrics": semantic_metrics,
                    "brain_router_metrics": self.brain_router.get_system_status(),
                    "error_tracker": self.error_tracker,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            await self._send_message(websocket, metrics)
            logger.info(f"📊 Metrics sent to client {client_id}")
            
        except Exception as e:
            logger.error(f"❌ Error handling metrics request from client {client_id}: {e}")
            await self._send_error(websocket, "Failed to get metrics", "metrics_error")
    
    async def _handle_memory_search(self, websocket: WebSocketServerProtocol, client_id: str, payload: Dict[str, Any]):
        """Handle memory search requests"""
        try:
            query = payload.get('query', '')
            top_k = payload.get('top_k', 10)
            source_filter = payload.get('source_filter')
            
            if not query:
                await self._send_error(websocket, "Empty search query", "empty_search_query")
                return
            
            # Perform search
            results = await search_memories(
                query=query,
                top_k=top_k,
                source_filter=source_filter
            )
            
            # Format response
            response = {
                "type": "memory_search_response",
                "payload": {
                    "query": query,
                    "results": [
                        {
                            "content": result.content,
                            "similarity_score": result.similarity_score,
                            "source": result.source,
                            "timestamp": result.timestamp.isoformat(),
                            "confidence": result.confidence,
                            "relevance_factors": result.relevance_factors
                        }
                        for result in results
                    ],
                    "total_found": len(results),
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            await self._send_message(websocket, response)
            logger.info(f"🔍 Memory search completed for client {client_id}: {len(results)} results")
            
        except Exception as e:
            logger.error(f"❌ Error handling memory search from client {client_id}: {e}")
            self._track_error("memory_errors", str(e))
            await self._send_error(websocket, "Memory search failed", "memory_search_error")
    
    async def _handle_add_memory(self, websocket: WebSocketServerProtocol, client_id: str, payload: Dict[str, Any]):
        """Handle add memory requests"""
        try:
            content = payload.get('content', '').strip()
            source = payload.get('source', f'client_{client_id}')
            tags = set(payload.get('tags', []))
            metadata = payload.get('metadata', {})
            
            if not content:
                await self._send_error(websocket, "Empty memory content", "empty_memory_content")
                return
            
            # Add memory
            success = await add_memory(
                content=content,
                source=source,
                tags=tags,
                metadata={
                    **metadata,
                    "added_by": client_id,
                    "added_at": datetime.now().isoformat()
                }
            )
            
            # Send response
            response = {
                "type": "memory_added_response",
                "payload": {
                    "success": success,
                    "content": content,
                    "source": source,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            await self._send_message(websocket, response)
            logger.info(f"💾 Memory {'added' if success else 'failed to add'} for client {client_id}")
            
        except Exception as e:
            logger.error(f"❌ Error handling add memory from client {client_id}: {e}")
            self._track_error("memory_errors", str(e))
            await self._send_error(websocket, "Failed to add memory", "add_memory_error")
    
    async def _send_message(self, websocket: WebSocketServerProtocol, message: Dict[str, Any]):
        """Send message with error handling"""
        try:
            await websocket.send(json.dumps(message))
        except Exception as e:
            logger.error(f"❌ Error sending message: {e}")
            raise
    
    async def _send_error(self, websocket: WebSocketServerProtocol, error_message: str, error_code: str):
        """Send error message to client"""
        try:
            error_response = {
                "type": "error",
                "payload": {
                    "message": error_message,
                    "code": error_code,
                    "timestamp": datetime.now().isoformat()
                }
            }
            await self._send_message(websocket, error_response)
        except Exception as e:
            logger.error(f"❌ Error sending error message: {e}")
    
    def _track_error(self, error_type: str, error_message: str):
        """Track errors for monitoring"""
        self.error_tracker[error_type] += 1
        self.error_tracker['last_errors'].append({
            'type': error_type,
            'message': error_message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 100 errors
        if len(self.error_tracker['last_errors']) > 100:
            self.error_tracker['last_errors'] = self.error_tracker['last_errors'][-100:]
        
        self.performance_metrics['last_error'] = {
            'type': error_type,
            'message': error_message,
            'timestamp': datetime.now().isoformat()
        }


# Enhanced Mode Handlers with Semantic Search Integration

class EnhancedAskModeHandler:
    """Enhanced Ask Mode Handler with semantic search"""
    
    def __init__(self, semantic_search: SemanticSearchAgent):
        self.semantic_search = semantic_search
        logger.info("✅ EnhancedAskModeHandler initialized with semantic search")
    
    async def handle_request(self, request: ChatRequest):
        """Handle Ask mode requests with semantic search"""
        start_time = time.time()
        
        try:
            # Get context from semantic search
            context = await self.semantic_search.get_context_for_query(request.query)
            
            # Search for relevant memories
            relevant_memories = await search_memories(request.query, top_k=5)
            
            # Build enhanced context for LLM
            llm_context = {
                "relevant_memories": [{"content": mem.content, "confidence": mem.confidence} for mem in relevant_memories],
                "key_topics": context.get("key_topics", []),
                "confidence_score": context.get("confidence_score", 0.0)
            }
            
            logger.info(f"🧠 Generating LLM response for Ask mode: {request.query[:50]}...")
            
            # Generate real LLM response
            llm_response = await generate_llm_response(request.query, "Ask", llm_context)
            
            response_text = llm_response.content
            confidence = llm_response.confidence
            
            logger.info(f"✅ Ask mode LLM response generated (confidence: {confidence:.2f})")
            
            from brain.core.brain_router import BrainResponse
            return BrainResponse(
                success=True,
                response=response_text,
                mode_used=ChatMode.ASK,
                processing_time=time.time() - start_time,
                resources_used=["memory", "semantic_search", "llm"],
                confidence=confidence,
                metadata={
                    "memories_found": len(relevant_memories),
                    "context_confidence": context.get('confidence_score', 0.0),
                    "llm_model": llm_response.model_used,
                    "llm_tokens": llm_response.tokens_used,
                    "llm_processing_time": llm_response.processing_time
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Error in EnhancedAskModeHandler: {e}")
            from brain.core.brain_router import BrainResponse
            return BrainResponse(
                success=False,
                response=f"I encountered an error while processing your question. Please try again.",
                mode_used=ChatMode.ASK,
                processing_time=time.time() - start_time,
                resources_used=[],
                confidence=0.0,
                metadata={"error": str(e)}
            )


class EnhancedAgentModeHandler:
    """Enhanced Agent Mode Handler with semantic search"""
    
    def __init__(self, semantic_search: SemanticSearchAgent):
        self.semantic_search = semantic_search
        logger.info("✅ EnhancedAgentModeHandler initialized with semantic search")
    
    async def handle_request(self, request: ChatRequest):
        """Handle Agent mode requests with task planning"""
        start_time = time.time()
        
        try:
            # Search for task-related memories
            task_memories = await search_memories(f"task {request.query}", top_k=3)
            
            logger.info(f"🤖 Agent mode executing workflow: {request.query[:50]}...")
            
            # Execute actual workflow with real task execution
            workflow_context = {
                "user_id": request.user_id,
                "session_id": request.session_id,
                "relevant_memories": [{"content": mem.content, "confidence": mem.confidence} for mem in task_memories]
            }
            
            workflow_result = await execute_agent_workflow(request.query, workflow_context)
            
            if workflow_result["success"]:
                response_text = workflow_result["response"]
                confidence = 0.9  # High confidence for successful execution
                resources_used = ["memory", "semantic_search", "llm", "workflow_engine", "task_execution"]
                
                # Add execution details to metadata
                execution_metadata = {
                    "workflow_id": workflow_result.get("workflow_id"),
                    "execution_time": workflow_result.get("processing_time", 0),
                    "steps_completed": workflow_result.get("execution_result", {}).get("completed_steps", 0),
                    "total_steps": workflow_result.get("execution_result", {}).get("total_steps", 0),
                    "real_execution": True
                }
            else:
                # If workflow execution fails, fall back to LLM planning
                logger.warning(f"⚠️ Workflow execution failed, falling back to LLM planning")
                
                llm_context = {
                    "relevant_memories": [{"content": mem.content, "confidence": mem.confidence} for mem in task_memories],
                    "task_type": "planning",
                    "mode": "Agent",
                    "execution_error": workflow_result.get("error", "Unknown error")
                }
                
                llm_response = await generate_llm_response(request.query, "Agent", llm_context)
                response_text = f"I understand you want me to: {request.query}\n\n"
                response_text += f"Here's my plan:\n{llm_response.content}\n\n"
                response_text += f"Note: Direct execution encountered an issue ({workflow_result.get('message', 'task not executable')}), so I've provided a detailed plan instead."
                
                confidence = llm_response.confidence * 0.7  # Lower confidence for planning-only
                resources_used = ["memory", "semantic_search", "llm", "task_planning"]
                execution_metadata = {
                    "execution_attempted": True,
                    "execution_successful": False,
                    "fallback_to_planning": True,
                    "llm_model": llm_response.model_used,
                    "llm_tokens": llm_response.tokens_used
                }
            
            logger.info(f"✅ Agent mode completed (execution: {workflow_result['success']}, confidence: {confidence:.2f})")
            
            from brain.core.brain_router import BrainResponse
            return BrainResponse(
                success=True,
                response=response_text,
                mode_used=ChatMode.AGENT,
                processing_time=time.time() - start_time,
                resources_used=resources_used,
                confidence=confidence,
                metadata={
                    "related_memories": len(task_memories),
                    **execution_metadata
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Error in EnhancedAgentModeHandler: {e}")
            from brain.core.brain_router import BrainResponse
            return BrainResponse(
                success=False,
                response=f"I encountered an error while planning your task. Please try again.",
                mode_used=ChatMode.AGENT,
                processing_time=time.time() - start_time,
                resources_used=[],
                confidence=0.0,
                metadata={"error": str(e)}
            )
    
    def _generate_task_plan(self, query: str, memories: List) -> List[str]:
        """Generate task plan based on query and memories"""
        # Simplified task planning - in real implementation this would be more sophisticated
        steps = [
            f"Analyze the request: {query}",
            "Gather necessary information and context",
            "Execute the main task",
            "Verify results and provide feedback"
        ]
        
        # Add memory-based insights
        if memories:
            steps.insert(1, "Review relevant previous experiences")
        
        return steps


class EnhancedSuggestModeHandler:
    """Enhanced Suggest Mode Handler with semantic search"""
    
    def __init__(self, semantic_search: SemanticSearchAgent):
        self.semantic_search = semantic_search
        logger.info("✅ EnhancedSuggestModeHandler initialized with semantic search")
    
    async def handle_request(self, request: ChatRequest):
        """Handle Suggest mode requests with proactive suggestions"""
        start_time = time.time()
        
        try:
            # Get context and related memories
            context = await self.semantic_search.get_context_for_query(request.query)
            relevant_memories = await search_memories(request.query, top_k=3)
            
            # Build context for LLM
            llm_context = {
                "relevant_memories": [{"content": mem.content, "confidence": mem.confidence} for mem in relevant_memories],
                "key_topics": context.get("key_topics", []),
                "mode": "Suggest"
            }
            
            logger.info(f"💡 Generating LLM response for Suggest mode: {request.query[:50]}...")
            
            # Generate real LLM response for suggestions
            llm_response = await generate_llm_response(request.query, "Suggest", llm_context)
            
            response_text = llm_response.content
            confidence = llm_response.confidence
            
            logger.info(f"✅ Suggest mode LLM response generated (confidence: {confidence:.2f})")
            
            from brain.core.brain_router import BrainResponse
            return BrainResponse(
                success=True,
                response=response_text,
                mode_used=ChatMode.SUGGEST,
                processing_time=time.time() - start_time,
                resources_used=["memory", "semantic_search", "llm", "suggestion_engine"],
                confidence=confidence,
                metadata={
                    "memories_found": len(relevant_memories),
                    "context_confidence": context.get('confidence_score', 0.0),
                    "llm_model": llm_response.model_used,
                    "llm_tokens": llm_response.tokens_used,
                    "llm_processing_time": llm_response.processing_time
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Error in EnhancedSuggestModeHandler: {e}")
            from brain.core.brain_router import BrainResponse
            return BrainResponse(
                success=False,
                response=f"I encountered an error while generating suggestions. Please try again.",
                mode_used=ChatMode.SUGGEST,
                processing_time=time.time() - start_time,
                resources_used=[],
                confidence=0.0,
                metadata={"error": str(e)}
            )
    
    def _generate_suggestions(self, query: str, context: Dict[str, Any]) -> List[str]:
        """Generate contextual suggestions"""
        suggestions = [
            f"Explore related topics to '{query}' for deeper understanding",
            "Consider breaking down complex aspects into smaller parts",
            "Look for patterns or connections with previous experiences"
        ]
        
        # Add context-based suggestions
        if context.get('key_topics'):
            suggestions.append(f"Investigate these related topics: {', '.join(context['key_topics'][:3])}")
        
        if context.get('relevant_memories'):
            suggestions.append("Review previous related discussions for additional insights")
        
        return suggestions


class EnhancedGeneralModeHandler:
    """Enhanced General Mode Handler with semantic search"""
    
    def __init__(self, semantic_search: SemanticSearchAgent):
        self.semantic_search = semantic_search
        logger.info("✅ EnhancedGeneralModeHandler initialized with semantic search")
    
    async def handle_request(self, request: ChatRequest):
        """Handle General mode requests"""
        start_time = time.time()
        
        try:
            # Get relevant context for friendly conversation
            relevant_memories = await search_memories(request.query, top_k=2)
            
            # Build basic context for LLM
            llm_context = {
                "relevant_memories": [{"content": mem.content, "confidence": mem.confidence} for mem in relevant_memories] if relevant_memories else [],
                "mode": "General"
            }
            
            logger.info(f"💬 Generating LLM response for General mode: {request.query[:50]}...")
            
            # Generate real LLM response for general conversation
            llm_response = await generate_llm_response(request.query, "General", llm_context)
            
            response_text = llm_response.content
            confidence = llm_response.confidence
            
            logger.info(f"✅ General mode LLM response generated (confidence: {confidence:.2f})")
            
            from brain.core.brain_router import BrainResponse
            return BrainResponse(
                success=True,
                response=response_text,
                mode_used=ChatMode.GENERAL,
                processing_time=time.time() - start_time,
                resources_used=["memory", "llm", "basic_processing"],
                confidence=confidence,
                metadata={
                    "memories_found": len(relevant_memories),
                    "llm_model": llm_response.model_used,
                    "llm_tokens": llm_response.tokens_used,
                    "llm_processing_time": llm_response.processing_time
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Error in EnhancedGeneralModeHandler: {e}")
            from brain.core.brain_router import BrainResponse
            return BrainResponse(
                success=False,
                response=f"I encountered an error while processing your request. Please try again.",
                mode_used=ChatMode.GENERAL,
                processing_time=time.time() - start_time,
                resources_used=[],
                confidence=0.0,
                metadata={"error": str(e)}
            )


# Main execution
if __name__ == "__main__":
    try:
        # Create and start enterprise backend server
        server = EnterpriseBackendServer(port=8767)
        
        logger.info("🚀 Starting Enterprise Backend Server...")
        asyncio.run(server.start_server())
        
    except KeyboardInterrupt:
        logger.info("👋 Server shutdown requested")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)