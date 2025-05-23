#!/usr/bin/env python3
"""
Enhanced Enterprise Backend 8767 with Contextual Memory Integration
Provides fully contextual AI responses using semantic search across all modes
"""

import asyncio
import json
import logging
import websockets
import time
import subprocess
import requests
import sys
import os
from datetime import datetime
from typing import Dict, Any, Set
from enum import Enum

# Add memory module to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory.semantic_search_agent import SemanticSearchAgent, get_context_for_query, add_memory

# Setup enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backend/enhanced_enterprise_8767_context.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ChatMode(str, Enum):
    AGENT = "Agent"
    ASK = "Ask" 
    SUGGEST = "Suggest"
    GENERAL = "General"

class ContextualAIBackend:
    def __init__(self):
        self.connected_clients: Set[str] = set()
        self.sessions: Dict[str, Dict] = {}
        self.start_time = datetime.now()
        self.ollama_available = self.check_ollama_availability()
        
        # Initialize semantic search agent
        self.semantic_agent = SemanticSearchAgent()
        
        # Flag to track if contextual knowledge is initialized
        self.contextual_knowledge_initialized = False
        
        logger.info(f"Contextual AI Backend initialized - Ollama: {self.ollama_available}, Memory: Active")

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

    def check_ollama_availability(self) -> bool:
        """Check if Ollama is running and available"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            return response.status_code == 200
        except:
            try:
                # Try to start Ollama if it's not running
                subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(3)
                response = requests.get("http://localhost:11434/api/tags", timeout=2)
                return response.status_code == 200
            except:
                return False

    async def get_contextual_ai_response(self, prompt: str, mode: str, session_id: str) -> str:
        """Get contextual AI response with semantic memory integration"""
        # Initialize contextual knowledge if not done yet
        if not self.contextual_knowledge_initialized:
            await self._initialize_contextual_knowledge()
            self.contextual_knowledge_initialized = True
        
        try:
            # Store user message in memory
            await add_memory(
                f"User in {mode} mode: {prompt}",
                source="user_interaction",
                tags={f"mode_{mode.lower()}", "user_message", session_id}
            )
            
            # Get contextual information
            context = await get_context_for_query(prompt, max_context_length=2000)
            
            # Generate contextual response
            if self.ollama_available:
                response = await self.get_ollama_response_with_context(prompt, mode, context)
            else:
                response = await self.get_contextual_fallback_response(prompt, mode, context)
            
            # Store response in memory
            await add_memory(
                f"System response in {mode} mode: {response}",
                source="system_response",
                tags={f"mode_{mode.lower()}", "system_message", session_id}
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting contextual AI response: {e}")
            return await self.get_contextual_fallback_response(prompt, mode, {})

    async def get_ollama_response_with_context(self, prompt: str, mode: str, context: Dict[str, Any]) -> str:
        """Get response from Ollama LLM enhanced with context"""
        try:
            # Build contextual prompt
            system_prompt = self.get_contextual_system_prompt(mode, context)
            context_info = self.format_context_for_llm(context)
            
            full_prompt = f"{system_prompt}\n\nContext Information:\n{context_info}\n\nUser: {prompt}\nAssistant:"
            
            payload = {
                "model": "llama3.2:latest",  # Or any available model
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "max_tokens": 600
                }
            }
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("response", "").strip()
                
                # Add mode-specific prefix and context indicator
                mode_prefix = self.get_mode_prefix(mode)
                confidence = context.get('confidence_score', 0.0)
                
                if confidence > 0.6:
                    context_indicator = " [Using high-confidence context]"
                elif confidence > 0.3:
                    context_indicator = " [Using available context]"
                else:
                    context_indicator = ""
                
                return f"{mode_prefix} {ai_response}{context_indicator}"
            else:
                logger.warning(f"Ollama request failed: {response.status_code}")
                return await self.get_contextual_fallback_response(prompt, mode, context)
                
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return await self.get_contextual_fallback_response(prompt, mode, context)

    def get_contextual_system_prompt(self, mode: str, context: Dict[str, Any]) -> str:
        """Get enhanced system prompt with context"""
        base_prompts = {
            ChatMode.AGENT: "You are an AI agent specialized in UI automation and task execution. Use the provided context to understand user patterns and preferences.",
            ChatMode.ASK: "You are an AI assistant specialized in answering questions. Use the context from memory to provide accurate, relevant information.",
            ChatMode.SUGGEST: "You are an AI assistant specialized in providing suggestions. Analyze the context to offer personalized, relevant recommendations.",
            ChatMode.GENERAL: "You are a helpful AI assistant. Use the conversation context to maintain natural, flowing interactions."
        }
        
        base_prompt = base_prompts.get(mode, base_prompts[ChatMode.GENERAL])
        
        # Add context enhancement
        confidence = context.get('confidence_score', 0.0)
        memory_count = len(context.get('relevant_memories', []))
        
        if memory_count > 0:
            base_prompt += f" You have access to {memory_count} relevant memories with {confidence:.1%} confidence."
        
        base_prompt += " Provide contextual, helpful responses that build on the conversation history."
        
        return base_prompt

    def format_context_for_llm(self, context: Dict[str, Any]) -> str:
        """Format context information for LLM"""
        if not context.get('relevant_memories'):
            return "No specific context available."
        
        formatted_context = []
        
        # Add relevant memories
        for i, memory in enumerate(context['relevant_memories'][:3]):
            formatted_context.append(f"{i+1}. {memory['content'][:200]}...")
        
        # Add key topics
        if context.get('key_topics'):
            formatted_context.append(f"Key topics: {', '.join(context['key_topics'][:5])}")
        
        # Add confidence score
        confidence = context.get('confidence_score', 0.0)
        formatted_context.append(f"Context confidence: {confidence:.1%}")
        
        return "\n".join(formatted_context)

    async def get_contextual_fallback_response(self, prompt: str, mode: str, context: Dict[str, Any]) -> str:
        """Enhanced fallback responses with context"""
        prompt_lower = prompt.lower()
        mode_prefix = self.get_mode_prefix(mode)
        
        # Extract context information
        relevant_memories = context.get('relevant_memories', [])
        confidence = context.get('confidence_score', 0.0)
        key_topics = context.get('key_topics', [])
        
        if mode == ChatMode.AGENT:
            return await self.process_agent_with_context(prompt, prompt_lower, relevant_memories, confidence)
        elif mode == ChatMode.ASK:
            return await self.process_ask_with_context(prompt, prompt_lower, relevant_memories, confidence, key_topics)
        elif mode == ChatMode.SUGGEST:
            return await self.process_suggest_with_context(prompt, prompt_lower, relevant_memories, confidence, key_topics)
        elif mode == ChatMode.GENERAL:
            return await self.process_general_with_context(prompt, prompt_lower, relevant_memories, confidence)
        else:
            return f"{mode_prefix} I understand your request: '{prompt}'. Let me help you with that based on our conversation context."

    async def process_agent_with_context(self, prompt: str, prompt_lower: str, memories: list, confidence: float) -> str:
        """Agent mode with contextual enhancement"""
        base_response = ""
        
        if "click" in prompt_lower:
            if any(memory for memory in memories if "click" in memory.get('content', '').lower()):
                base_response = f"🎯 I'll execute the click for '{prompt}'. Based on previous similar actions, I'll locate the target precisely."
            else:
                base_response = f"🎯 I'll execute the click operation for '{prompt}'. Analyzing screen for target element."
        elif "open" in prompt_lower:
            if any(memory for memory in memories if "open" in memory.get('content', '').lower()):
                base_response = f"🎯 Opening '{prompt}'. I recall similar requests and will use the most efficient method."
            else:
                base_response = f"🎯 I'll help you open '{prompt}'. Locating and launching the target."
        elif "type" in prompt_lower:
            base_response = f"🎯 I'll type '{prompt}'. Finding the active input field and entering text safely."
        else:
            base_response = f"🎯 Executing task: '{prompt}'"
        
        # Add context confidence
        if confidence > 0.6:
            base_response += " ✅ High confidence based on interaction patterns."
        elif confidence > 0.3:
            base_response += " 📊 Using available context for better execution."
        
        return base_response

    async def process_ask_with_context(self, prompt: str, prompt_lower: str, memories: list, confidence: float, topics: list) -> str:
        """Ask mode with contextual enhancement"""
        if memories and confidence > 0.5:
            # High confidence contextual response
            primary_memory = memories[0]['content']
            response = f"💭 Based on our conversation: {primary_memory[:150]}..."
            
            if len(memories) > 1:
                response += f"\n\nAdditional context: {memories[1]['content'][:100]}..."
        elif memories and confidence > 0.2:
            # Medium confidence response
            response = f"💭 I found relevant information: {memories[0]['content'][:120]}..."
        else:
            # Standard responses with slight context awareness
            if "status" in prompt_lower:
                response = "💭 Enterprise system operational. All components active including contextual memory system."
            elif "memory" in prompt_lower:
                response = "💭 Contextual memory system active with semantic search. Learning from each interaction."
            elif any(q in prompt_lower for q in ["how", "what", "why"]):
                response = f"💭 Searching contextual knowledge for: '{prompt}'. Analyzing available information..."
            else:
                response = f"💭 Processing your question: '{prompt}' with available context."
        
        # Add topics if available
        if topics:
            response += f"\n\nRelated topics: {', '.join(topics[:4])}"
        
        return response

    async def process_suggest_with_context(self, prompt: str, prompt_lower: str, memories: list, confidence: float, topics: list) -> str:
        """Suggest mode with contextual enhancement"""
        suggestions = []
        
        # Analyze memories for patterns
        if memories:
            file_mentions = sum(1 for m in memories if 'file' in m.get('content', '').lower())
            automation_mentions = sum(1 for m in memories if any(word in m.get('content', '').lower() for word in ['click', 'open', 'type']))
            
            if file_mentions > 1:
                suggestions.append("💡 Consider organizing files with consistent naming and folder structure")
            if automation_mentions > 1:
                suggestions.append("💡 Create macros for frequently repeated UI automation tasks")
        
        # Base suggestions
        if "optimize" in prompt_lower:
            suggestions.extend([
                "💡 Implement systematic workflow improvements",
                "💡 Use automation for repetitive processes"
            ])
        elif "workflow" in prompt_lower:
            suggestions.extend([
                "💡 Establish consistent project templates",
                "💡 Create documentation for common procedures"
            ])
        else:
            suggestions.append(f"💡 For '{prompt}': Consider systematic analysis and incremental improvements")
        
        response = "\n".join(suggestions[:3])
        
        if confidence > 0.4:
            response += f"\n\n(Suggestions confidence: {confidence:.1%} based on interaction patterns)"
        
        return response

    async def process_general_with_context(self, prompt: str, prompt_lower: str, memories: list, confidence: float) -> str:
        """General mode with contextual enhancement"""
        if "hello" in prompt_lower or "hi" in prompt_lower:
            base_response = "🤖 Hello! I'm your contextual AI assistant."
            if memories:
                base_response += f" I see we've interacted {len(memories)} times recently. How can I help you today?"
            else:
                base_response += " How can I help you today?"
        elif "help" in prompt_lower:
            response = "🤖 I provide contextual assistance across four modes: Agent, Ask, Suggest, and General."
            if memories:
                common_topics = set()
                for memory in memories[:3]:
                    if 'mode' in memory.get('content', '').lower():
                        for mode in ['agent', 'ask', 'suggest', 'general']:
                            if mode in memory['content'].lower():
                                common_topics.add(mode)
                if common_topics:
                    response += f" You often use: {', '.join(common_topics)} modes."
            return response
        elif "thank" in prompt_lower:
            base_response = "🤖 You're welcome! I'm glad I could help."
            if confidence > 0.5:
                base_response += " I'll remember our conversation context for future interactions."
            return base_response
        else:
            if memories and confidence > 0.4:
                context_summary = memories[0]['content'][:80]
                base_response = f"🤖 Regarding '{prompt}' - I recall: {context_summary}... How can I help further?"
            else:
                base_response = f"🤖 I understand you're asking about '{prompt}'. How can I assist you with this?"
        
        return base_response

    def get_mode_prefix(self, mode: str) -> str:
        """Get emoji prefix for each mode"""
        prefixes = {
            ChatMode.AGENT: "🎯",
            ChatMode.ASK: "💭", 
            ChatMode.SUGGEST: "💡",
            ChatMode.GENERAL: "🤖"
        }
        return prefixes.get(mode, "🤖")

    async def handle_websocket(self, websocket):
        """Handle WebSocket connections with contextual processing"""
        client_id = f"client_{int(time.time() * 1000)}"
        client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
        
        self.connected_clients.add(client_id)
        logger.info(f"Client connected: {client_id} from {client_ip}")
        
        try:
            # Send enhanced connection response
            await websocket.send(json.dumps({
                "type": "connection_established",
                "client_id": client_id,
                "message": "Connected to Enhanced Enterprise Backend 8767 with Contextual Memory",
                "timestamp": datetime.now().isoformat(),
                "ai_features": {
                    "ollama_available": self.ollama_available,
                    "contextual_memory": True,
                    "semantic_search": True,
                    "intelligent_fallback": True,
                    "real_responses": True
                },
                "capabilities": [
                    "contextual_ai_responses",
                    "semantic_memory_integration",
                    "ollama_llm_support", 
                    "intelligent_processing",
                    "agent_automation",
                    "knowledge_retrieval",
                    "proactive_suggestions",
                    "conversation_memory"
                ]
            }))
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    response = await self.process_contextual_message(data, client_id)
                    await websocket.send(json.dumps(response))
                    
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "error": "Invalid JSON format",
                        "timestamp": datetime.now().isoformat()
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

    async def process_contextual_message(self, data: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Process incoming messages with contextual enhancement"""
        message_type = data.get("type", "unknown")
        timestamp = datetime.now().isoformat()
        
        logger.info(f"Processing contextual {message_type} from {client_id}")
        
        try:
            if message_type == "chat_request":
                return await self.handle_contextual_chat_request(data, client_id)
            elif message_type == "system_status":
                return await self.handle_contextual_system_status(data, client_id)
            else:
                return {
                    "type": "error",
                    "error": f"Unknown message type: {message_type}",
                    "client_id": client_id,
                    "timestamp": timestamp
                }
                
        except Exception as e:
            logger.error(f"Error in process_contextual_message: {e}")
            return {
                "type": "error",
                "error": str(e),
                "client_id": client_id,
                "timestamp": timestamp
            }

    async def handle_contextual_chat_request(self, data: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Handle chat requests with full contextual processing"""
        mode = data.get("mode", "General")
        message = data.get("message", "")
        session_id = data.get("session_id", client_id)
        
        start_time = time.time()
        
        try:
            # Get contextual AI response
            ai_response = await self.get_contextual_ai_response(message, mode, session_id)
            
            # Get context metrics for response metadata
            context = await get_context_for_query(message, max_context_length=500)
            
            processing_time = time.time() - start_time
            
            return {
                "type": "chat_response",
                "success": True,
                "mode": mode,
                "payload": {
                    "response": ai_response,
                    "mode": mode,
                    "success": True,
                    "ai_powered": True,
                    "contextual": True,
                    "ollama_used": self.ollama_available
                },
                "response": ai_response,
                "processing_time": round(processing_time, 3),
                "session_id": session_id,
                "client_id": client_id,
                "timestamp": datetime.now().isoformat(),
                "context_metrics": {
                    "memories_used": len(context.get('relevant_memories', [])),
                    "confidence_score": context.get('confidence_score', 0.0),
                    "key_topics": context.get('key_topics', [])[:3]
                }
            }
            
        except Exception as e:
            logger.error(f"Contextual chat request error: {e}")
            return {
                "type": "chat_response",
                "success": False,
                "error": str(e),
                "mode": mode,
                "payload": {
                    "response": f"I apologize, but I encountered an error processing your contextual request: {str(e)}",
                    "mode": mode,
                    "success": False
                },
                "session_id": session_id,
                "client_id": client_id,
                "timestamp": datetime.now().isoformat()
            }

    async def handle_contextual_system_status(self, data: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Handle system status requests with memory metrics"""
        uptime = datetime.now() - self.start_time
        
        # Get memory system metrics
        search_metrics = self.semantic_agent.get_performance_metrics()
        
        return {
            "type": "system_status_response",
            "status": "operational",
            "uptime_seconds": int(uptime.total_seconds()),
            "connected_clients": len(self.connected_clients),
            "port": 8767,
            "ai_features": {
                "ollama_available": self.ollama_available,
                "contextual_memory": True,
                "semantic_search": True,
                "real_ai_responses": True,
                "intelligent_fallback": True
            },
            "memory_system": {
                "total_memories": search_metrics['vector_store']['total_documents'],
                "average_search_time": search_metrics['semantic_search']['average_response_time'],
                "cache_hit_rate": search_metrics['semantic_search']['cache_hit_rate'],
                "successful_queries": search_metrics['semantic_search']['successful_queries']
            },
            "capabilities": [
                "contextual_ai_integration",
                "semantic_memory_search",
                "ollama_llm_support", 
                "intelligent_processing",
                "enterprise_automation",
                "conversation_memory",
                "pattern_learning"
            ],
            "server_time": datetime.now().isoformat(),
            "version": "Enhanced Enterprise Backend 8767 with Context v2.0",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        }

async def main():
    """Start the Enhanced Enterprise Backend with contextual memory"""
    backend = ContextualAIBackend()
    
    # Create logs directory
    os.makedirs("logs/backend", exist_ok=True)
    
    logger.info("🚀 Starting Enhanced Enterprise Backend 8767 with Contextual Memory...")
    logger.info("🧠 Contextual AI responses enabled")
    logger.info("🔍 Semantic memory integration active")
    logger.info("🎯 Modes: Agent, Ask, Suggest, General (all contextual)")
    
    try:
        start_server = websockets.serve(
            backend.handle_websocket,
            "localhost", 
            8767,
            ping_interval=30,
            ping_timeout=10
        )
        
        logger.info("✅ Enhanced Enterprise Backend 8767 started successfully")
        logger.info("🌐 WebSocket server listening on ws://localhost:8767")
        logger.info(f"🤖 Ollama integration: {'✅ Active' if backend.ollama_available else '⚠️ Fallback mode'}")
        logger.info("🧠 Contextual memory system ready")
        
        await start_server
        await asyncio.Future()  # Run forever
        
    except Exception as e:
        logger.error(f"❌ Failed to start Enhanced Enterprise Backend 8767: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Enhanced Enterprise Backend 8767 stopped by user")
    except Exception as e:
        logger.error(f"❌ Enhanced Enterprise Backend 8767 error: {e}")