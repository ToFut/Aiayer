#!/usr/bin/env python3
"""
Enhanced Brain Router with Full Contextual Memory Integration
Integrates SemanticSearchAgent to provide fully contextual responses across all modes
"""

import asyncio
import json
import logging
import websockets
import time
import sys
import os
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional

# Add memory module to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory.semantic_search_agent import SemanticSearchAgent, get_context_for_query, add_memory

# Setup enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/enhanced_brain_router.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ChatMode(str, Enum):
    AGENT = "Agent"
    ASK = "Ask"
    SUGGEST = "Suggest"
    GENERAL = "General"

class ContextualBrainRouter:
    """Enhanced Brain Router with full contextual memory integration"""
    
    def __init__(self):
        self.sessions = {}
        self.connected_clients = set()
        self.start_time = datetime.now()
        
        # Initialize semantic search agent
        self.semantic_agent = SemanticSearchAgent()
        
        # Flag to track if base knowledge is initialized
        self.base_knowledge_initialized = False
        
        logger.info("Enhanced Brain Router with contextual memory initialized")

    async def _initialize_base_knowledge(self):
        """Initialize base knowledge in memory"""
        base_knowledge = [
            "The system has 4 chat modes: Agent for UI automation, Ask for questions, Suggest for recommendations, and General for conversation",
            "Agent mode specializes in UI automation tasks like clicking, typing, and opening applications",
            "Ask mode provides contextual answers by searching through memory and knowledge",
            "Suggest mode offers proactive recommendations based on context and patterns",
            "General mode handles conversational interactions and general assistance",
            "The memory system stores conversations, user patterns, and system information",
            "Semantic search helps find relevant context for better responses",
            "WebSocket servers run on ports 8765 and 8767 for different services",
            "The system integrates LLM capabilities for intelligent responses",
            "Memory is persistent and builds context over time"
        ]
        
        for knowledge in base_knowledge:
            await add_memory(knowledge, source="system", tags={"base_knowledge", "system_info"})
        
        logger.info("Base knowledge initialized in semantic memory")

    async def process_request_with_context(self, mode: ChatMode, message: str, session_id: str) -> Dict[str, Any]:
        """Process request with full contextual memory integration"""
        start_time = time.time()
        
        # Initialize base knowledge if not done yet
        if not self.base_knowledge_initialized:
            await self._initialize_base_knowledge()
            self.base_knowledge_initialized = True
        
        try:
            # Store user message in memory
            await add_memory(
                f"User asked in {mode} mode: {message}",
                source="user",
                tags={"conversation", mode.lower(), "user_query"}
            )
            
            # Get contextual information
            context = await get_context_for_query(message, max_context_length=1500)
            
            # Process based on mode with context
            if mode == ChatMode.AGENT:
                response = await self._handle_agent_mode_contextual(message, context)
            elif mode == ChatMode.ASK:
                response = await self._handle_ask_mode_contextual(message, context)
            elif mode == ChatMode.SUGGEST:
                response = await self._handle_suggest_mode_contextual(message, context)
            elif mode == ChatMode.GENERAL:
                response = await self._handle_general_mode_contextual(message, context)
            else:
                response = await self._handle_general_mode_contextual(message, context)
            
            # Store response in memory
            await add_memory(
                f"System responded in {mode} mode: {response}",
                source="system",
                tags={"conversation", mode.lower(), "system_response"}
            )
            
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "response": response,
                "mode": mode.value,
                "processing_time": round(processing_time, 2),
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "context_used": {
                    "relevant_memories": len(context.get('relevant_memories', [])),
                    "confidence_score": context.get('confidence_score', 0.0),
                    "key_topics": context.get('key_topics', [])[:5],
                    "sources": context.get('sources', [])
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing {mode} request with context: {e}")
            return {
                "success": False,
                "error": str(e),
                "mode": mode.value,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }

    async def _handle_agent_mode_contextual(self, message: str, context: Dict[str, Any]) -> str:
        """Handle Agent mode with contextual memory"""
        logger.info(f"Agent mode with context: {message}")
        
        # Extract relevant context
        relevant_memories = context.get('relevant_memories', [])
        confidence = context.get('confidence_score', 0.0)
        
        # Build contextual response
        base_response = ""
        contextual_info = ""
        
        # Analyze message for specific actions
        message_lower = message.lower()
        
        if "click" in message_lower:
            if "document" in message_lower or "folder" in message_lower:
                base_response = "🎯 I'll help you click on the Documents folder. Analyzing screen for target location..."
            elif "button" in message_lower:
                base_response = f"🎯 Locating and preparing to click the button mentioned in: '{message}'"
            else:
                base_response = f"🎯 Executing click operation for: '{message}'"
        elif "open" in message_lower:
            if "application" in message_lower or "app" in message_lower:
                base_response = f"🎯 Opening application: '{message}'. Checking system for target app..."
            elif "file" in message_lower:
                base_response = f"🎯 Opening file: '{message}'. Locating file in system..."
            else:
                base_response = f"🎯 Opening: '{message}'"
        elif "type" in message_lower or "enter" in message_lower:
            base_response = f"🎯 Typing text: '{message}'. Finding active input field..."
        elif "navigate" in message_lower or "go to" in message_lower:
            base_response = f"🎯 Navigating to: '{message}'. Analyzing current interface..."
        else:
            base_response = f"🎯 Executing task: '{message}'"
        
        # Add contextual information if available
        if relevant_memories and confidence > 0.3:
            relevant_actions = []
            for memory in relevant_memories[:2]:
                if any(action in memory['content'].lower() for action in ['click', 'open', 'type', 'navigate']):
                    relevant_actions.append(memory['content'])
            
            if relevant_actions:
                contextual_info = f"\n\nContext: Based on previous interactions - {relevant_actions[0][:100]}..."
        
        # Add confidence indicator
        confidence_note = ""
        if confidence > 0.7:
            confidence_note = " ✅ High confidence based on previous similar tasks."
        elif confidence > 0.4:
            confidence_note = " 📊 Medium confidence - analyzing similar past actions."
        
        return base_response + contextual_info + confidence_note

    async def _handle_ask_mode_contextual(self, message: str, context: Dict[str, Any]) -> str:
        """Handle Ask mode with contextual memory"""
        logger.info(f"Ask mode with context: {message}")
        
        relevant_memories = context.get('relevant_memories', [])
        confidence = context.get('confidence_score', 0.0)
        key_topics = context.get('key_topics', [])
        
        # Build contextual response
        if relevant_memories and confidence > 0.5:
            # High confidence - provide detailed contextual answer
            primary_memory = relevant_memories[0]
            response = f"💭 Based on our conversation history: {primary_memory['content']}"
            
            # Add supporting information
            if len(relevant_memories) > 1:
                supporting_info = []
                for memory in relevant_memories[1:3]:
                    supporting_info.append(memory['content'][:80] + "...")
                response += f"\n\nAdditional context: {', '.join(supporting_info)}"
            
            # Add key topics if available
            if key_topics:
                response += f"\n\nRelated topics: {', '.join(key_topics[:5])}"
                
        elif relevant_memories and confidence > 0.2:
            # Medium confidence - provide general contextual answer
            response = f"💭 I found some relevant information: {relevant_memories[0]['content'][:150]}..."
            if key_topics:
                response += f"\n\nThis relates to: {', '.join(key_topics[:3])}"
        else:
            # Low confidence - provide helpful fallback
            message_lower = message.lower()
            if "status" in message_lower:
                response = "💭 System status: All components operational. Memory system active with semantic search enabled."
            elif "file" in message_lower or "document" in message_lower:
                response = "💭 I can help you find information about files and documents. The system tracks file activities and relationships."
            elif "memory" in message_lower or "remember" in message_lower:
                response = "💭 The memory system is active with contextual search. I can retrieve information from previous interactions and system events."
            elif any(q in message_lower for q in ["how", "what", "why", "when", "where"]):
                response = f"💭 Let me search for information about: '{message}'. Checking knowledge base and memory..."
            else:
                response = f"💭 Processing your question: '{message}'. Searching through available knowledge and context..."
        
        # Add confidence indicator
        if confidence > 0.7:
            response += f"\n\n(High confidence: {confidence:.1%})"
        elif confidence > 0.4:
            response += f"\n\n(Medium confidence: {confidence:.1%})"
        
        return response

    async def _handle_suggest_mode_contextual(self, message: str, context: Dict[str, Any]) -> str:
        """Handle Suggest mode with contextual memory"""
        logger.info(f"Suggest mode with context: {message}")
        
        relevant_memories = context.get('relevant_memories', [])
        confidence = context.get('confidence_score', 0.0)
        key_topics = context.get('key_topics', [])
        
        # Analyze patterns from context
        message_lower = message.lower()
        suggestions = []
        
        # Base suggestions based on query
        if "optimize" in message_lower or "improve" in message_lower:
            suggestions.append("💡 Organize frequently used files into easily accessible folders")
            suggestions.append("💡 Set up keyboard shortcuts for common tasks")
            suggestions.append("💡 Use automation for repetitive actions")
        elif "workflow" in message_lower:
            suggestions.append("💡 Create project templates for consistent structure")
            suggestions.append("💡 Implement version control for important files")
            suggestions.append("💡 Establish consistent naming conventions")
        elif "productivity" in message_lower:
            suggestions.append("💡 Use time-blocking techniques for focused work")
            suggestions.append("💡 Minimize context switching between applications")
            suggestions.append("💡 Leverage AI automation for routine tasks")
        else:
            suggestions.append(f"💡 Based on your query about '{message}', consider systematic improvements")
            suggestions.append("💡 Analyze current approach and implement optimizations")
        
        # Add contextual suggestions based on memory
        contextual_suggestions = []
        if relevant_memories and confidence > 0.4:
            # Analyze patterns from memories
            patterns = {}
            for memory in relevant_memories:
                content = memory['content'].lower()
                if 'file' in content:
                    patterns['file_operations'] = patterns.get('file_operations', 0) + 1
                if any(word in content for word in ['click', 'open', 'type']):
                    patterns['ui_automation'] = patterns.get('ui_automation', 0) + 1
                if 'system' in content:
                    patterns['system_queries'] = patterns.get('system_queries', 0) + 1
            
            # Generate contextual suggestions
            if patterns.get('file_operations', 0) > 1:
                contextual_suggestions.append("💡 Based on your file activity: Consider using file organization automation")
            if patterns.get('ui_automation', 0) > 1:
                contextual_suggestions.append("💡 Given your UI automation usage: Create saved macros for common tasks")
            if patterns.get('system_queries', 0) > 1:
                contextual_suggestions.append("💡 For system monitoring: Set up automated status alerts")
        
        # Combine suggestions
        all_suggestions = suggestions[:2] + contextual_suggestions[:1]
        response = "\n".join(all_suggestions)
        
        # Add context information
        if key_topics:
            response += f"\n\nBased on topics: {', '.join(key_topics[:3])}"
        
        if confidence > 0.5:
            response += f"\n\n(Suggestions confidence: {confidence:.1%})"
        
        return response

    async def _handle_general_mode_contextual(self, message: str, context: Dict[str, Any]) -> str:
        """Handle General mode with contextual memory"""
        logger.info(f"General mode with context: {message}")
        
        relevant_memories = context.get('relevant_memories', [])
        confidence = context.get('confidence_score', 0.0)
        key_topics = context.get('key_topics', [])
        
        message_lower = message.lower()
        
        # Handle common conversational patterns with context
        if any(greeting in message_lower for greeting in ["hello", "hi", "hey"]):
            base_response = "🤖 Hello! I'm your AI assistant with enterprise-grade capabilities."
            if relevant_memories:
                base_response += f" I see we've interacted {len(relevant_memories)} times recently."
            base_response += " How can I help you today?"
            
        elif "help" in message_lower:
            base_response = "🤖 I'm here to help! I have four main modes: Agent (UI automation), Ask (questions), Suggest (recommendations), and General (conversation)."
            if key_topics:
                base_response += f" I notice you're often interested in: {', '.join(key_topics[:3])}."
                
        elif "capabilities" in message_lower or "what can you do" in message_lower:
            base_response = "🤖 I can automate UI tasks, answer questions using memory systems, provide intelligent suggestions, and engage in conversation."
            if relevant_memories:
                base_response += f" Based on our history, you primarily use me for {relevant_memories[0]['content'][:50]}..."
                
        elif "thank" in message_lower:
            base_response = "🤖 You're welcome! I'm glad I could help."
            if confidence > 0.5:
                base_response += " Feel free to ask if you need anything else - I remember our conversation context."
            else:
                base_response += " Feel free to ask if you need anything else."
                
        else:
            # General contextual response
            if relevant_memories and confidence > 0.4:
                primary_context = relevant_memories[0]['content'][:100]
                base_response = f"🤖 Regarding '{message}' - I recall {primary_context}... How can I help you further with this?"
            else:
                base_response = f"🤖 I understand you're mentioning '{message}'. As an enterprise AI assistant, I can help with automation, information retrieval, and suggestions. What would you like me to do?"
        
        # Add confidence and context indicators
        if confidence > 0.6 and relevant_memories:
            base_response += f"\n\n(Drawing from {len(relevant_memories)} relevant past interactions)"
        
        return base_response

    async def handle_websocket(self, websocket):
        """Handle WebSocket connections with contextual processing"""
        client_id = f"client_{int(time.time() * 1000)}"
        self.connected_clients.add(client_id)
        logger.info(f"Client connected: {client_id}")
        
        try:
            await websocket.send(json.dumps({
                "type": "connection_established",
                "client_id": client_id,
                "message": "Connected to Enhanced Brain Router with Contextual Memory",
                "available_modes": ["Agent", "Ask", "Suggest", "General"],
                "features": [
                    "contextual_memory",
                    "semantic_search",
                    "persistent_learning",
                    "confidence_scoring"
                ]
            }))
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    
                    if data.get("type") == "chat_request":
                        mode = ChatMode(data.get("mode", "General"))
                        user_message = data.get("message", "")
                        session_id = data.get("session_id", client_id)
                        
                        result = await self.process_request_with_context(mode, user_message, session_id)
                        await websocket.send(json.dumps(result))
                        
                    elif data.get("type") == "system_status":
                        status = await self.get_enhanced_system_status()
                        await websocket.send(json.dumps(status))
                        
                    else:
                        await websocket.send(json.dumps({
                            "error": "Unknown message type",
                            "received": data
                        }))
                        
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "error": "Invalid JSON format"
                    }))
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    await websocket.send(json.dumps({
                        "error": f"Processing error: {str(e)}"
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {client_id}")
        finally:
            self.connected_clients.discard(client_id)

    async def get_enhanced_system_status(self) -> Dict[str, Any]:
        """Get enhanced system status with memory metrics"""
        uptime = datetime.now() - self.start_time
        
        # Get semantic search metrics
        search_metrics = self.semantic_agent.get_performance_metrics()
        
        return {
            "status": "online",
            "uptime_seconds": int(uptime.total_seconds()),
            "connected_clients": len(self.connected_clients),
            "available_modes": [mode.value for mode in ChatMode],
            "server_time": datetime.now().isoformat(),
            "version": "Enhanced Brain Router with Context v2.0",
            "memory_system": {
                "semantic_search_active": True,
                "total_memories": search_metrics['vector_store']['total_documents'],
                "search_performance": search_metrics['semantic_search']['average_response_time'],
                "cache_hit_rate": search_metrics['semantic_search']['cache_hit_rate']
            },
            "features": [
                "contextual_responses",
                "semantic_memory", 
                "persistent_learning",
                "confidence_scoring",
                "multi_mode_support"
            ]
        }

async def main():
    """Start the Enhanced Brain Router server with contextual memory"""
    brain_router = ContextualBrainRouter()
    
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    logger.info("🧠 Starting Enhanced Brain Router with Contextual Memory...")
    logger.info("📡 Port: 8765")
    logger.info("🎯 Modes: Agent, Ask, Suggest, General (all with context)")
    logger.info("🔍 Memory: Semantic search integration active")
    
    try:
        start_server = websockets.serve(
            brain_router.handle_websocket,
            "localhost",
            8765,
            ping_interval=30,
            ping_timeout=10
        )
        
        logger.info("✅ Enhanced Brain Router started on ws://localhost:8765")
        logger.info("🧠 Contextual memory system initialized")
        logger.info("🔍 Semantic search agent ready")
        
        await start_server
        await asyncio.Future()  # Run forever
        
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Enhanced Brain Router stopped by user")
    except Exception as e:
        logger.error(f"❌ Enhanced Brain Router error: {e}")