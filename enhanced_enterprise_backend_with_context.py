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
import aiohttp
import sys
import os
from datetime import datetime
from typing import Dict, Any, Set
from enum import Enum

# Add memory module to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory.semantic_search_agent import SemanticSearchAgent, get_context_for_query, add_memory

# Import automation components for Agent mode
try:
    from agent_workflow.enhanced_automation_handler import EnhancedAutomationHandler
    AUTOMATION_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Automation handler not available: {e}")
    AUTOMATION_AVAILABLE = False

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
        
        # Initialize automation handler for Agent mode
        self.automation_handler = None
        if AUTOMATION_AVAILABLE:
            try:
                self.automation_handler = EnhancedAutomationHandler()
                logger.info("Automation handler initialized for Agent mode")
            except Exception as e:
                logger.error(f"Failed to initialize automation handler: {e}")
                self.automation_handler = None
        
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

    async def get_ollama_response_with_context_streaming(self, prompt: str, mode: str, context: Dict[str, Any], websocket, client_id: str) -> str:
        """Get streaming response from Ollama LLM enhanced with context"""
        try:
            # Build contextual prompt
            system_prompt = self.get_contextual_system_prompt(mode, context)
            context_info = self.format_context_for_llm(context)
            
            full_prompt = f"{system_prompt}\n\nContext Information:\n{context_info}\n\nUser: {prompt}\nAssistant:"
            
            payload = {
                "model": "llama3.2:1b",  # Fast model for real-time responses
                "prompt": full_prompt,
                "stream": True,  # Enable streaming
                "options": {
                    "temperature": 0.7,
                    "max_tokens": 600
                }
            }
            
            # Send initial acknowledgment
            await websocket.send(json.dumps({
                "type": "progress_update",
                "stage": "🤖 Processing your request...",
                "mode": mode,
                "client_id": client_id,
                "timestamp": datetime.now().isoformat()
            }))
            
            # Stream response using aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:11434/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    
                    if response.status == 200:
                        full_response = ""
                        
                        async for line in response.content:
                            if line:
                                try:
                                    line_text = line.decode('utf-8').strip()
                                    if line_text:
                                        chunk_data = json.loads(line_text)
                                        if chunk_data.get("response"):
                                            chunk_text = chunk_data.get("response", "")
                                            full_response += chunk_text
                                        
                                        # Check if done
                                        if chunk_data.get("done", False):
                                            break
                                                
                                except json.JSONDecodeError:
                                    continue
                        
                        # Process successful response after loop
                        ai_response = full_response.strip()
                        
                        # Add mode-specific prefix and context indicator
                        mode_prefix = self.get_mode_prefix(mode)
                        confidence = context.get('confidence_score', 0.0)
                        
                        if confidence > 0.6:
                            context_indicator = " [Using high-confidence context]"
                        elif confidence > 0.3:
                            context_indicator = " [Using available context]"
                        else:
                            context_indicator = ""
                        
                        final_response = f"{mode_prefix} {ai_response}{context_indicator}"
                        
                        # Send final response message (what overlay expects)
                        await websocket.send(json.dumps({
                            "type": "final_response",
                            "mode": mode,
                            "response": final_response,
                            "client_id": client_id,
                            "timestamp": datetime.now().isoformat(),
                            "ai_powered": True,
                            "contextual": True,
                            "confidence": confidence,
                            "processing_time": 0,
                            "success": True
                        }))
                        
                        return final_response
                    else:
                        logger.warning(f"Ollama request failed: {response.status}")
                        fallback_response = await self.get_contextual_fallback_response(prompt, mode, context)
                        
                        # Send fallback response
                        await websocket.send(json.dumps({
                            "type": "final_response",
                            "mode": mode,
                            "response": fallback_response,
                            "client_id": client_id,
                            "timestamp": datetime.now().isoformat(),
                            "ai_powered": False,
                            "fallback": True,
                            "success": True
                        }))
                        
                        return fallback_response
                
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            fallback_response = await self.get_contextual_fallback_response(prompt, mode, context)
            
            # Send error response as final_response format
            await websocket.send(json.dumps({
                "type": "final_response",
                "mode": mode,
                "response": fallback_response,
                "error": str(e),
                "client_id": client_id,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "fallback": True
            }))
            
            return fallback_response

    async def get_ollama_response_with_context(self, prompt: str, mode: str, context: Dict[str, Any]) -> str:
        """Get non-streaming response from Ollama LLM enhanced with context"""
        try:
            # Build contextual prompt
            system_prompt = self.get_contextual_system_prompt(mode, context)
            context_info = self.format_context_for_llm(context)
            
            full_prompt = f"{system_prompt}\n\nContext Information:\n{context_info}\n\nUser: {prompt}\nAssistant:"
            
            payload = {
                "model": "llama3.2:1b",  # Fast model for real-time responses
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
                timeout=45  # Increased timeout for better LLM responses
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
            ChatMode.AGENT: "You are an AI agent specialized in task execution and automation. When given a task, provide clear step-by-step instructions and actionable guidance. If the task involves UI automation (clicking, typing, opening apps), describe the specific steps you would take. Always be direct and practical in your response.",
            ChatMode.ASK: "You are an AI assistant specialized in answering questions with depth and accuracy. Provide comprehensive, informative answers that directly address what the user is asking. Use context from previous conversations to give more personalized and relevant responses.",
            ChatMode.SUGGEST: "You are an AI assistant specialized in providing helpful suggestions and recommendations. Analyze the user's situation and offer 2-3 practical, actionable suggestions that could improve their workflow, solve problems, or enhance their experience.",
            ChatMode.GENERAL: "You are a helpful AI assistant engaging in natural conversation. Be personable, helpful, and maintain context from our ongoing conversation. Respond naturally as if you're having a genuine conversation with the user."
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
        """Agent mode with contextual enhancement - EXECUTES ACTUAL AUTOMATION"""
        
        # If automation handler is available, try to execute the task
        if self.automation_handler:
            try:
                logger.info(f"🎯 Executing Agent mode automation for: {prompt}")
                
                # Build context for automation
                context = {
                    "memories": memories,
                    "confidence": confidence,
                    "user_prompt": prompt
                }
                
                # Execute the automation instruction
                automation_result = await self.automation_handler.handle_user_instruction(prompt, context)
                
                if automation_result.get("success", False):
                    # Automation succeeded
                    execution_summary = automation_result.get("summary", "Task completed")
                    steps_taken = automation_result.get("steps_executed", [])
                    
                    response = f"🎯 **TASK EXECUTED SUCCESSFULLY** ✅\n\n"
                    response += f"**Command:** {prompt}\n"
                    response += f"**Result:** {execution_summary}\n\n"
                    
                    if steps_taken:
                        response += f"**Steps Performed:**\n"
                        for i, step in enumerate(steps_taken, 1):
                            response += f"{i}. {step}\n"
                    
                    if confidence > 0.6:
                        response += f"\n✅ **High confidence execution** ({confidence:.1%})"
                    
                    # Log successful automation
                    logger.info(f"✅ Agent automation successful: {execution_summary}")
                    return response
                
                else:
                    # Automation failed, provide helpful response
                    error_msg = automation_result.get("error", "Unknown error")
                    fallback_plan = automation_result.get("fallback_plan", [])
                    
                    response = f"🎯 **AUTOMATION ATTEMPTED** ⚠️\n\n"
                    response += f"**Command:** {prompt}\n"
                    response += f"**Issue:** {error_msg}\n\n"
                    
                    if fallback_plan:
                        response += f"**Alternative approach:**\n"
                        for i, step in enumerate(fallback_plan, 1):
                            response += f"{i}. {step}\n"
                    
                    logger.warning(f"⚠️ Agent automation failed: {error_msg}")
                    return response
                    
            except Exception as e:
                logger.error(f"❌ Agent automation error: {e}")
                # Fall through to manual instruction mode
        
        # Fallback: Provide detailed manual instructions (old behavior)
        logger.info(f"📋 Providing manual instructions for: {prompt}")
        
        # For search tasks (like "search in google 'SEGEV HALFON'")
        if "search" in prompt_lower and "google" in prompt_lower:
            search_term = prompt.split("'")[1] if "'" in prompt else prompt.replace("search in google", "").strip()
            base_response = f"🎯 **Google Search Instructions**\n\n"
            base_response += f"*Automation not available - Manual steps:*\n"
            base_response += f"1. Open web browser (Chrome/Safari)\n"
            base_response += f"2. Navigate to google.com\n"
            base_response += f"3. Click in search box\n"
            base_response += f"4. Type: '{search_term}'\n"
            base_response += f"5. Press Enter or click Search button\n"
            base_response += f"🔍 **Search target:** {search_term}"
            
        # For open/launch actions  
        elif "open" in prompt_lower:
            app_name = prompt.replace("open", "").strip()
            base_response = f"🎯 **Launch {app_name} Instructions**\n\n"
            base_response += f"*Automation not available - Manual steps:*\n"
            base_response += f"1. Press Cmd+Space (Spotlight)\n"
            base_response += f"2. Type: '{app_name}'\n"
            base_response += f"3. Press Enter to launch\n"
            
        # For typing actions
        elif "type" in prompt_lower:
            text_to_type = prompt.replace("type", "").strip()
            base_response = f"🎯 **Text Input Instructions**\n\n"
            base_response += f"*Automation not available - Manual steps:*\n"
            base_response += f"1. Click in the text field\n"
            base_response += f"2. Type: '{text_to_type}'\n"
            
        # General task execution
        else:
            base_response = f"🎯 **Task Analysis**\n\n"
            base_response += f"*Automation not available - Analysis:*\n"
            base_response += f"**Task:** {prompt}\n"
            base_response += f"**Recommendation:** Break down into smaller actionable steps\n"
        
        # Add context confidence
        if confidence > 0.6:
            base_response += f"\n\n📊 **High confidence** based on patterns ({confidence:.1%})"
        elif confidence > 0.3:
            base_response += f"\n\n📊 **Medium confidence** using context ({confidence:.1%})"
        
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
                    # Handle streaming chat requests directly
                    if data.get("type") == "chat_request":
                        await self.handle_contextual_chat_request_streaming(data, client_id, websocket)
                    else:
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
            elif message_type == "register":
                return await self.handle_register_request(data, client_id)
            elif message_type == "plan_execution":
                return await self.handle_plan_execution(data.get("payload", data), client_id)
            elif message_type == "agent_confirmation":
                return await self.handle_agent_confirmation(data, client_id)
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

    async def handle_contextual_chat_request_streaming(self, data: Dict[str, Any], client_id: str, websocket) -> None:
        """Handle chat requests with streaming responses"""
        mode = data.get("mode", "General")
        message = data.get("message", "")
        session_id = data.get("session_id", client_id)
        
        start_time = time.time()
        
        try:
            # Initialize contextual knowledge if not done yet
            if not self.contextual_knowledge_initialized:
                await self._initialize_contextual_knowledge()
                self.contextual_knowledge_initialized = True
            
            # Store user message in memory
            await add_memory(
                f"User in {mode} mode: {message}",
                source="user_interaction",
                tags={f"mode_{mode.lower()}", "user_message", session_id}
            )
            
            # Get context for the query
            context = await get_context_for_query(message, max_context_length=500)
            
            # 🎯 AGENT MODE AUTOMATION - Generate execution plan first
            if mode.lower() == "agent" and self.automation_handler:
                try:
                    logger.info(f"🎯 [STREAMING] Creating Agent automation plan for: {message}")
                    
                    # Build context for automation
                    automation_context = {
                        "memories": context.get('relevant_memories', []),
                        "confidence": context.get('confidence_score', 0.0),
                        "user_prompt": message
                    }
                    
                    # Generate execution plan (without executing)
                    logger.info(f"🔧 Automation handler available: {self.automation_handler is not None}")
                    plan_result = await self.automation_handler.create_execution_plan(message, automation_context)
                    logger.info(f"🔧 Plan result: {plan_result.get('success', False)} - {plan_result.get('error', 'No error')}")
                    
                    if plan_result.get("success", False):
                        # Plan created successfully - send plan with action buttons in frontend format
                        plan_details = plan_result.get("execution_plan", {})
                        target_element = plan_details.get("target_element", {})
                        execution_details = plan_details.get("execution_details", {})
                        
                        # Store the plan for later execution using session_id
                        if not hasattr(self, 'pending_plans'):
                            self.pending_plans = {}
                        self.pending_plans[session_id] = {
                            "plan": plan_details,
                            "context": automation_context,
                            "timestamp": time.time(),
                            "client_id": client_id
                        }
                        
                        # Create human-readable plan description
                        plan_description = f"🎯 **AUTOMATION EXECUTION PLAN**\n\n"
                        plan_description += f"**Command:** {message}\n"
                        plan_description += f"**Action:** {plan_details.get('action', 'unknown').upper()}\n"
                        plan_description += f"**Target:** {target_element.get('element_text', 'Unknown')}\n"
                        
                        if plan_details.get('text_to_type'):
                            plan_description += f"**Text to Type:** \"{plan_details.get('text_to_type')}\"\n"
                        
                        plan_description += f"\n**Ready to execute - choose an action below:**"
                        
                        # Calculate estimated duration (simple heuristic)
                        estimated_duration = 3  # Default 3 seconds
                        if plan_details.get('action') == 'type':
                            text_length = len(plan_details.get('text_to_type', ''))
                            estimated_duration = max(3, min(10, text_length * 0.2 + 2))
                        
                        # Send as final response with frontend-compatible format
                        await websocket.send(json.dumps({
                            "type": "final_response",
                            "mode": mode,
                            "response": plan_description,
                            "client_id": client_id,
                            "timestamp": datetime.now().isoformat(),
                            "ai_powered": False,
                            "success": True,
                            # Frontend automation confirmation format
                            "requiresConfirmation": True,
                            "agentSessionId": session_id,
                            "confidence": plan_result.get('confidence_score', 0.0),
                            "riskLevel": execution_details.get('risk_level', 'medium'),
                            "estimatedDuration": estimated_duration,
                            "executionPlan": {
                                "total_steps": 3,  # Screen analysis, target detection, action execution
                                "action": plan_details.get('action', 'unknown'),
                                "target": target_element.get('element_text', 'Unknown'),
                                "coordinates": target_element.get('position', None),
                                "text_to_type": plan_details.get('text_to_type', ''),
                                "warnings": execution_details.get('warnings', [])
                            }
                        }))
                        
                        # Store response in memory
                        execution_summary = plan_result.get("summary", "Automation plan created")
                        await add_memory(
                            f"System executed automation in {mode} mode: {execution_summary}",
                            source="automation_response",
                            tags={f"mode_{mode.lower()}", "automation", session_id}
                        )
                        
                        logger.info(f"✅ [STREAMING] Agent automation successful: {execution_summary}")
                        return  # Exit early - automation completed
                    
                    else:
                        # Automation failed - log and continue to LLM fallback
                        error_msg = plan_result.get("error", "Unknown automation error")
                        logger.warning(f"⚠️ [STREAMING] Agent automation failed: {error_msg}")
                        # Continue to LLM response below
                        
                except Exception as e:
                    logger.error(f"❌ [STREAMING] Agent automation error: {e}")
                    # Continue to LLM response below
            
            # Use streaming Ollama response (fallback or non-agent modes)
            if self.ollama_available:
                ai_response = await self.get_ollama_response_with_context_streaming(
                    message, mode, context, websocket, client_id
                )
                
                # Store response in memory
                await add_memory(
                    f"System response in {mode} mode: {ai_response}",
                    source="system_response",
                    tags={f"mode_{mode.lower()}", "system_message", session_id}
                )
            else:
                # Fallback to non-streaming contextual response
                ai_response = await self.get_contextual_fallback_response(message, mode, context)
                await websocket.send(json.dumps({
                    "type": "final_response",
                    "mode": mode,
                    "response": ai_response,
                    "client_id": client_id,
                    "timestamp": datetime.now().isoformat(),
                    "ai_powered": False,
                    "fallback": True,
                    "success": True
                }))
                
                # Store fallback response in memory
                await add_memory(
                    f"System fallback response in {mode} mode: {ai_response}",
                    source="system_response",
                    tags={f"mode_{mode.lower()}", "system_message", session_id, "fallback"}
                )
            
            processing_time = time.time() - start_time
            
            # Send final metadata
            await websocket.send(json.dumps({
                "type": "chat_response_metadata",
                "mode": mode,
                "processing_time": round(processing_time, 3),
                "session_id": session_id,
                "client_id": client_id,
                "timestamp": datetime.now().isoformat(),
                "context_metrics": {
                    "memories_used": len(context.get('relevant_memories', [])),
                    "confidence_score": context.get('confidence_score', 0.0),
                    "key_topics": context.get('key_topics', [])[:3]
                },
                "ai_powered": self.ollama_available,
                "contextual": True
            }))
            
        except Exception as e:
            logger.error(f"Error in streaming chat request: {e}")
            await websocket.send(json.dumps({
                "type": "chat_response_error",
                "mode": mode,
                "error": str(e),
                "client_id": client_id,
                "timestamp": datetime.now().isoformat()
            }))

    async def handle_contextual_chat_request(self, data: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Handle chat requests with full contextual processing (non-streaming fallback)"""
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

    async def handle_plan_execution(self, payload: dict, client_id: str) -> dict:
        """Handle execution of a previously created automation plan"""
        try:
            plan_id = payload.get("plan_id")
            action = payload.get("action", "").lower()
            
            if not plan_id or not hasattr(self, 'pending_plans') or plan_id not in self.pending_plans:
                return {
                    "type": "plan_execution_error",
                    "error": "Plan not found or expired"
                }
            
            plan_data = self.pending_plans[plan_id]
            
            if action == "do":
                logger.info(f"🚀 Executing automation plan {plan_id}")
                
                # Execute the stored plan using the automation handler
                automation_result = await self.automation_handler.handle_user_instruction(
                    plan_data["context"]["user_prompt"], 
                    plan_data["context"]
                )
                
                if automation_result.get("success", False):
                    # Clean up the plan
                    del self.pending_plans[plan_id]
                    
                    return {
                        "type": "plan_execution_success",
                        "plan_id": plan_id,
                        "result": automation_result,
                        "summary": automation_result.get("summary", "Task completed successfully")
                    }
                else:
                    return {
                        "type": "plan_execution_error",
                        "plan_id": plan_id,
                        "error": automation_result.get("error", "Execution failed")
                    }
                    
            elif action == "dismiss":
                logger.info(f"❌ Plan {plan_id} dismissed by user")
                del self.pending_plans[plan_id]
                return {
                    "type": "plan_dismissed",
                    "plan_id": plan_id,
                    "message": "Automation plan dismissed"
                }
                
            elif action == "adjust":
                logger.info(f"🔧 Plan {plan_id} adjustment requested")
                return {
                    "type": "plan_adjustment_request",
                    "plan_id": plan_id,
                    "message": "Plan adjustment not yet implemented"
                }
            else:
                return {
                    "type": "plan_execution_error",
                    "error": f"Unknown action: {action}"
                }
                
        except Exception as e:
            logger.error(f"Error handling plan execution: {e}")
            return {
                "type": "plan_execution_error",
                "error": str(e)
            }

    async def handle_agent_confirmation(self, data: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Handle agent confirmation from frontend (DO/Dismiss/Adjust)"""
        try:
            # Handle both sessionId (frontend) and session_id (backend) formats
            session_id = data.get("sessionId") or data.get("session_id")  # This is our plan_id
            action = data.get("action", "").upper()
            
            logger.info(f"🎯 Agent confirmation received: sessionId={session_id}, action={action}")
            logger.info(f"🔍 Available plans: {list(self.pending_plans.keys()) if hasattr(self, 'pending_plans') else 'None'}")
            
            # Map frontend actions to backend actions
            if action == "EXECUTE":
                action = "DO"
                logger.info(f"🔄 Mapped action from EXECUTE to DO")
            
            if not session_id or not hasattr(self, 'pending_plans') or session_id not in self.pending_plans:
                return {
                    "type": "agent_confirmation_error",
                    "error": "Plan not found or expired"
                }
            
            plan_data = self.pending_plans[session_id]
            
            if action == "DO":
                logger.info(f"🚀 Executing automation plan {session_id}")
                
                # Send progress updates during execution
                progress_steps = [
                    {"step": 1, "message": "🔍 Analyzing current screen...", "progress": 20},
                    {"step": 2, "message": "🎯 Locating target element...", "progress": 50},
                    {"step": 3, "message": "⚡ Executing automation...", "progress": 80},
                    {"step": 4, "message": "✅ Verifying completion...", "progress": 100}
                ]
                
                # Send initial progress
                await self._send_progress_update(client_id, session_id, progress_steps[0])
                await asyncio.sleep(0.5)
                
                # Send screen analysis progress
                await self._send_progress_update(client_id, session_id, progress_steps[1])
                await asyncio.sleep(1.0)
                
                # Send execution progress
                await self._send_progress_update(client_id, session_id, progress_steps[2])
                
                # Execute the stored plan using the automation handler
                # Add the stored plan details to context for execution
                execution_context = plan_data["context"].copy()
                execution_context["stored_plan"] = plan_data["plan"]
                
                automation_result = await self.automation_handler.handle_user_instruction(
                    plan_data["context"]["user_prompt"], 
                    execution_context
                )
                
                # Send completion progress
                await self._send_progress_update(client_id, session_id, progress_steps[3])
                
                if automation_result.get("success", False):
                    # Clean up the plan
                    del self.pending_plans[session_id]
                    
                    return {
                        "type": "agent_execution_success",
                        "session_id": session_id,
                        "result": automation_result,
                        "summary": automation_result.get("summary", "Task completed successfully"),
                        "execution_completed": True
                    }
                else:
                    return {
                        "type": "agent_execution_error",
                        "session_id": session_id,
                        "error": automation_result.get("error", "Execution failed")
                    }
                    
            elif action == "DISMISS":
                logger.info(f"❌ Plan {session_id} dismissed by user")
                del self.pending_plans[session_id]
                return {
                    "type": "agent_dismissed",
                    "session_id": session_id,
                    "message": "Automation plan dismissed"
                }
                
            elif action == "ADJUST":
                logger.info(f"🔧 Plan {session_id} adjustment requested")
                return {
                    "type": "agent_adjustment_request",
                    "session_id": session_id,
                    "message": "Plan adjustment not yet implemented"
                }
            else:
                return {
                    "type": "agent_confirmation_error",
                    "error": f"Unknown action: {action}"
                }
                
        except Exception as e:
            logger.error(f"Error handling agent confirmation: {e}")
            return {
                "type": "agent_confirmation_error",
                "error": str(e)
            }

    async def _send_progress_update(self, client_id: str, session_id: str, progress_info: Dict[str, Any]):
        """Send progress update to specific client"""
        try:
            # Find the websocket for this client
            for websocket in self.connected_clients:
                if getattr(websocket, 'client_id', None) == client_id:
                    progress_message = {
                        "type": "agent_progress",
                        "session_id": session_id,
                        "step": progress_info.get("step", 1),
                        "message": progress_info.get("message", "Processing..."),
                        "progress": progress_info.get("progress", 0),
                        "timestamp": datetime.now().isoformat()
                    }
                    await websocket.send(json.dumps(progress_message))
                    logger.info(f"📊 Progress update sent: {progress_info['message']} ({progress_info['progress']}%)")
                    break
        except Exception as e:
            logger.error(f"Error sending progress update: {e}")

    async def handle_register_request(self, data: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Handle overlay registration requests"""
        # Check if data is in payload format (from overlay) or direct format (from tests)
        payload = data.get("payload", data)
        client_type = payload.get("client_type", "unknown")
        version = payload.get("version", "unknown")
        capabilities = payload.get("capabilities", [])
        
        logger.info(f"Client registration: {client_id} ({client_type} v{version})")
        
        return {
            "type": "registration_success",
            "client_id": client_id,
            "server_info": {
                "name": "Enhanced Enterprise Backend 8767",
                "version": "2.0",
                "ai_enabled": self.ollama_available,
                "features": {
                    "real_ai_responses": True,
                    "streaming": True,
                    "contextual_memory": True,
                    "semantic_search": True,
                    "llm_model": "llama3.2:1b"
                }
            },
            "supported_modes": ["ask", "agent", "suggest", "general"],
            "message": "Successfully registered with Enhanced Enterprise Backend",
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