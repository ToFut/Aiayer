"""
Ask Mode Handler - Contextual Memory and Knowledge Queries

Handles Ask mode requests by accessing memory systems, contextual data,
and providing intelligent responses based on accumulated knowledge.
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta

from ..core.brain_router import BrainResponse, ChatRequest, ChatMode

logger = logging.getLogger(__name__)

@dataclass
class MemoryContext:
    """Represents context from memory systems"""
    recent_conversations: List[Dict[str, Any]]
    relevant_knowledge: List[Dict[str, Any]]
    user_patterns: Dict[str, Any]
    system_state: Dict[str, Any]
    confidence_score: float

@dataclass
class QueryAnalysis:
    """Analysis of the user's query intent and requirements"""
    intent: str  # 'factual', 'contextual', 'historical', 'predictive', 'comparative'
    entities: List[str]
    keywords: List[str]
    time_context: Optional[str]  # 'recent', 'historical', 'future'
    scope: str  # 'personal', 'system', 'general'
    complexity: str  # 'simple', 'medium', 'complex'

class MemoryRetriever:
    """Retrieves relevant information from various memory systems"""
    
    def __init__(self):
        # Simulated memory systems - in real implementation these would connect to actual memory stores
        self.conversation_memory = []
        self.knowledge_base = {}
        self.user_profiles = {}
        self.system_logs = []
        
        # Initialize with some sample data
        self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """Initialize with sample memory data for demonstration"""
        current_time = time.time()
        
        # Sample conversation history
        self.conversation_memory = [
            {
                "timestamp": current_time - 3600,  # 1 hour ago
                "user_id": "default",
                "mode": "Ask",
                "query": "What files did I work on yesterday?",
                "response": "You worked on project files including main.py and config.json",
                "context": {"files_accessed": ["main.py", "config.json"]}
            },
            {
                "timestamp": current_time - 7200,  # 2 hours ago
                "user_id": "default", 
                "mode": "Agent",
                "query": "Help me optimize my workflow",
                "response": "I've analyzed your workflow and suggested improvements",
                "context": {"workflow_analysis": True}
            }
        ]
        
        # Sample knowledge base
        self.knowledge_base = {
            "system_capabilities": {
                "chat_modes": ["Agent", "Ask", "Suggest", "General"],
                "automation_features": ["file_operations", "system_monitoring", "task_scheduling"],
                "memory_systems": ["conversation_history", "knowledge_base", "user_patterns"]
            },
            "user_preferences": {
                "default": {
                    "preferred_mode": "Ask",
                    "automation_level": "medium",
                    "notification_preferences": "minimal"
                }
            },
            "frequently_asked": {
                "how_to_use": "The system has 4 chat modes: Agent for task execution, Ask for questions, Suggest for proactive help, and General for basic chat.",
                "system_status": "All systems operational, memory systems active, automation ready"
            }
        }
        
        # Sample user patterns
        self.user_profiles = {
            "default": {
                "most_used_mode": "Ask",
                "typical_query_types": ["system_status", "file_operations", "workflow_help"],
                "active_hours": "9-17",
                "response_preference": "detailed"
            }
        }
    
    async def retrieve_context(self, query: str, user_id: str, session_id: str) -> MemoryContext:
        """Retrieve relevant context from all memory systems"""
        try:
            # Get recent conversations
            recent_conversations = await self._get_recent_conversations(user_id, limit=5)
            
            # Get relevant knowledge
            relevant_knowledge = await self._search_knowledge_base(query)
            
            # Get user patterns
            user_patterns = self.user_profiles.get(user_id, {})
            
            # Get system state
            system_state = await self._get_system_state()
            
            # Calculate confidence based on available context
            confidence = await self._calculate_context_confidence(
                recent_conversations, relevant_knowledge, user_patterns, query
            )
            
            return MemoryContext(
                recent_conversations=recent_conversations,
                relevant_knowledge=relevant_knowledge,
                user_patterns=user_patterns,
                system_state=system_state,
                confidence_score=confidence
            )
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return MemoryContext(
                recent_conversations=[],
                relevant_knowledge=[],
                user_patterns={},
                system_state={},
                confidence_score=0.1
            )
    
    async def _get_recent_conversations(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent conversations for context"""
        user_conversations = [
            conv for conv in self.conversation_memory 
            if conv.get("user_id") == user_id
        ]
        
        # Sort by timestamp (most recent first)
        user_conversations.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        
        return user_conversations[:limit]
    
    async def _search_knowledge_base(self, query: str) -> List[Dict[str, Any]]:
        """Search knowledge base for relevant information"""
        query_lower = query.lower()
        relevant_items = []
        
        # Search through knowledge base
        for category, content in self.knowledge_base.items():
            if isinstance(content, dict):
                for key, value in content.items():
                    # Simple keyword matching
                    if any(word in key.lower() or (isinstance(value, str) and word in value.lower()) 
                           for word in query_lower.split()):
                        relevant_items.append({
                            "category": category,
                            "key": key,
                            "content": value,
                            "relevance": 0.8  # Simplified relevance score
                        })
        
        # Sort by relevance
        relevant_items.sort(key=lambda x: x.get("relevance", 0), reverse=True)
        
        return relevant_items[:10]  # Return top 10 relevant items
    
    async def _get_system_state(self) -> Dict[str, Any]:
        """Get current system state"""
        return {
            "status": "operational",
            "uptime": "24h 30m",
            "memory_usage": "moderate",
            "active_sessions": 1,
            "last_update": datetime.now().isoformat(),
            "services": {
                "memory_system": "active",
                "llm_service": "active", 
                "automation": "ready",
                "sensors": "monitoring"
            }
        }
    
    async def _calculate_context_confidence(self, conversations: List, knowledge: List, 
                                          patterns: Dict, query: str) -> float:
        """Calculate confidence score based on available context"""
        factors = {
            "conversation_history": len(conversations) * 0.1,
            "relevant_knowledge": len(knowledge) * 0.15,
            "user_patterns": len(patterns) * 0.05,
            "query_clarity": len(query.split()) * 0.02
        }
        
        # Cap individual factors
        for key in factors:
            factors[key] = min(factors[key], 0.3)
        
        # Base confidence
        confidence = 0.3 + sum(factors.values())
        
        return min(confidence, 1.0)

class QueryAnalyzer:
    """Analyzes user queries to understand intent and requirements"""
    
    def __init__(self):
        self.intent_patterns = {
            'factual': ['what is', 'define', 'explain', 'tell me about', 'how does'],
            'contextual': ['what did', 'show me', 'find', 'where is', 'when did'],
            'historical': ['yesterday', 'last week', 'previously', 'before', 'ago'],
            'predictive': ['will', 'going to', 'predict', 'forecast', 'future'],
            'comparative': ['compare', 'difference', 'better', 'versus', 'vs']
        }
        
        self.entity_types = {
            'file': ['file', 'document', 'folder', 'directory'],
            'system': ['system', 'process', 'service', 'application'],
            'time': ['today', 'yesterday', 'hour', 'minute', 'day', 'week'],
            'user': ['user', 'profile', 'settings', 'preferences']
        }
    
    async def analyze_query(self, query: str, context: MemoryContext) -> QueryAnalysis:
        """Analyze query to understand intent and requirements"""
        try:
            query_lower = query.lower()
            
            # Determine intent
            intent = await self._determine_intent(query_lower)
            
            # Extract entities
            entities = await self._extract_entities(query_lower)
            
            # Extract keywords
            keywords = await self._extract_keywords(query_lower)
            
            # Determine time context
            time_context = await self._determine_time_context(query_lower)
            
            # Determine scope
            scope = await self._determine_scope(query_lower, context)
            
            # Assess complexity
            complexity = await self._assess_complexity(query, entities, keywords)
            
            return QueryAnalysis(
                intent=intent,
                entities=entities,
                keywords=keywords,
                time_context=time_context,
                scope=scope,
                complexity=complexity
            )
            
        except Exception as e:
            logger.error(f"Error analyzing query: {e}")
            return QueryAnalysis(
                intent="general",
                entities=[],
                keywords=query.split(),
                time_context=None,
                scope="general",
                complexity="medium"
            )
    
    async def _determine_intent(self, query: str) -> str:
        """Determine the primary intent of the query"""
        for intent, patterns in self.intent_patterns.items():
            if any(pattern in query for pattern in patterns):
                return intent
        return "general"
    
    async def _extract_entities(self, query: str) -> List[str]:
        """Extract relevant entities from the query"""
        entities = []
        
        for entity_type, keywords in self.entity_types.items():
            if any(keyword in query for keyword in keywords):
                entities.append(entity_type)
        
        return list(set(entities))  # Remove duplicates
    
    async def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords from the query"""
        # Simple keyword extraction - remove common words
        stop_words = {'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but', 'in', 'with', 'to', 'for', 'of', 'as', 'by'}
        words = query.split()
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords
    
    async def _determine_time_context(self, query: str) -> Optional[str]:
        """Determine if query has time-related context"""
        recent_indicators = ['now', 'current', 'today', 'recent', 'latest']
        historical_indicators = ['yesterday', 'last', 'previous', 'ago', 'before']
        future_indicators = ['will', 'future', 'next', 'upcoming', 'plan']
        
        if any(indicator in query for indicator in recent_indicators):
            return "recent"
        elif any(indicator in query for indicator in historical_indicators):
            return "historical"
        elif any(indicator in query for indicator in future_indicators):
            return "future"
        
        return None
    
    async def _determine_scope(self, query: str, context: MemoryContext) -> str:
        """Determine the scope of the query"""
        personal_indicators = ['my', 'me', 'i', 'personal', 'user']
        system_indicators = ['system', 'server', 'application', 'service']
        
        if any(indicator in query for indicator in personal_indicators):
            return "personal"
        elif any(indicator in query for indicator in system_indicators):
            return "system"
        
        return "general"
    
    async def _assess_complexity(self, query: str, entities: List[str], keywords: List[str]) -> str:
        """Assess the complexity of the query"""
        # Simple complexity assessment
        factors = {
            "length": len(query.split()),
            "entities": len(entities),
            "keywords": len(keywords)
        }
        
        complexity_score = (factors["length"] * 0.1 + 
                          factors["entities"] * 0.3 + 
                          factors["keywords"] * 0.2)
        
        if complexity_score < 2:
            return "simple"
        elif complexity_score < 5:
            return "medium"
        else:
            return "complex"

class ResponseGenerator:
    """Generates contextual responses based on query analysis and memory context"""
    
    def __init__(self):
        self.response_templates = {
            "factual": "Based on my knowledge, {content}",
            "contextual": "Looking at your context, {content}",
            "historical": "From what I can see in your history, {content}",
            "predictive": "Based on current patterns, {content}",
            "comparative": "Comparing the options, {content}",
            "general": "{content}"
        }
    
    async def generate_response(self, analysis: QueryAnalysis, context: MemoryContext, 
                              original_query: str) -> str:
        """Generate a contextual response"""
        try:
            # Get relevant information
            relevant_info = await self._gather_relevant_information(analysis, context)
            
            # Generate core content
            content = await self._generate_core_content(analysis, relevant_info, original_query)
            
            # Apply template
            template = self.response_templates.get(analysis.intent, self.response_templates["general"])
            response = template.format(content=content)
            
            # Add context-specific information
            response = await self._add_contextual_details(response, analysis, context)
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"I understand you're asking about: {original_query}. Let me help you with that based on what I know."
    
    async def _gather_relevant_information(self, analysis: QueryAnalysis, 
                                         context: MemoryContext) -> Dict[str, Any]:
        """Gather all relevant information for the response"""
        info = {
            "conversations": [],
            "knowledge": [],
            "patterns": {},
            "system_info": {}
        }
        
        # Filter relevant conversations
        for conv in context.recent_conversations:
            if any(keyword in conv.get("query", "").lower() for keyword in analysis.keywords):
                info["conversations"].append(conv)
        
        # Filter relevant knowledge
        for item in context.relevant_knowledge:
            if any(keyword in str(item.get("content", "")).lower() for keyword in analysis.keywords):
                info["knowledge"].append(item)
        
        # Add relevant patterns
        if analysis.scope == "personal":
            info["patterns"] = context.user_patterns
        
        # Add system information if relevant
        if "system" in analysis.entities:
            info["system_info"] = context.system_state
        
        return info
    
    async def _generate_core_content(self, analysis: QueryAnalysis, 
                                   relevant_info: Dict[str, Any], original_query: str) -> str:
        """Generate the core content of the response"""
        
        # Handle different intent types
        if analysis.intent == "factual":
            return await self._generate_factual_content(relevant_info, analysis)
        elif analysis.intent == "contextual":
            return await self._generate_contextual_content(relevant_info, analysis)
        elif analysis.intent == "historical":
            return await self._generate_historical_content(relevant_info, analysis)
        elif analysis.intent == "predictive":
            return await self._generate_predictive_content(relevant_info, analysis)
        elif analysis.intent == "comparative":
            return await self._generate_comparative_content(relevant_info, analysis)
        else:
            return await self._generate_general_content(relevant_info, analysis, original_query)
    
    async def _generate_factual_content(self, info: Dict[str, Any], analysis: QueryAnalysis) -> str:
        """Generate factual response content"""
        if info["knowledge"]:
            knowledge_items = info["knowledge"][:3]  # Top 3 relevant items
            content = "Here's what I know:\n"
            for item in knowledge_items:
                content += f"• {item.get('content', 'Information available')}\n"
            return content
        
        return "I have information about this topic in my knowledge base."
    
    async def _generate_contextual_content(self, info: Dict[str, Any], analysis: QueryAnalysis) -> str:
        """Generate contextual response content"""
        if info["conversations"]:
            recent_conv = info["conversations"][0]
            return f"I recall from our recent conversation that {recent_conv.get('response', 'we discussed this topic')}."
        
        if info["patterns"]:
            return f"Based on your usage patterns, {self._format_patterns(info['patterns'])}."
        
        return "I'm analyzing your current context to provide the most relevant information."
    
    async def _generate_historical_content(self, info: Dict[str, Any], analysis: QueryAnalysis) -> str:
        """Generate historical response content"""
        if info["conversations"]:
            historical_items = [conv for conv in info["conversations"] 
                              if time.time() - conv.get("timestamp", 0) > 3600]  # Older than 1 hour
            if historical_items:
                return f"Looking at your history, you {historical_items[0].get('query', 'asked about this topic')}."
        
        return "I can see some historical context for your query."
    
    async def _generate_predictive_content(self, info: Dict[str, Any], analysis: QueryAnalysis) -> str:
        """Generate predictive response content"""
        if info["patterns"]:
            return "Based on your patterns, I predict you might be interested in similar topics."
        
        return "I can make some predictions based on available data."
    
    async def _generate_comparative_content(self, info: Dict[str, Any], analysis: QueryAnalysis) -> str:
        """Generate comparative response content"""
        if info["knowledge"]:
            return "I can compare the different options based on the information I have."
        
        return "Let me compare the available options for you."
    
    async def _generate_general_content(self, info: Dict[str, Any], analysis: QueryAnalysis, query: str) -> str:
        """Generate general response content"""
        if info["knowledge"]:
            return f"I found relevant information about {', '.join(analysis.keywords)}."
        
        return f"I'm processing your query about {', '.join(analysis.keywords) if analysis.keywords else 'this topic'}."
    
    async def _add_contextual_details(self, response: str, analysis: QueryAnalysis, 
                                    context: MemoryContext) -> str:
        """Add contextual details to enhance the response"""
        
        # Add confidence indicator
        if context.confidence_score > 0.8:
            response += "\n\n(High confidence based on available context)"
        elif context.confidence_score > 0.6:
            response += "\n\n(Medium confidence based on available context)"
        
        # Add system status if relevant
        if "system" in analysis.entities and context.system_state:
            response += f"\n\nSystem Status: {context.system_state.get('status', 'Unknown')}"
        
        # Add recent activity if relevant
        if analysis.time_context == "recent" and context.recent_conversations:
            response += f"\n\nRecent Activity: {len(context.recent_conversations)} recent interactions"
        
        return response
    
    def _format_patterns(self, patterns: Dict[str, Any]) -> str:
        """Format user patterns for display"""
        if not patterns:
            return "no specific patterns detected"
        
        formatted = []
        if "most_used_mode" in patterns:
            formatted.append(f"you typically use {patterns['most_used_mode']} mode")
        
        if "response_preference" in patterns:
            formatted.append(f"you prefer {patterns['response_preference']} responses")
        
        return ", ".join(formatted) if formatted else "patterns are being analyzed"

class AskModeHandler:
    """Main handler for Ask mode requests"""
    
    def __init__(self):
        self.memory_retriever = MemoryRetriever()
        self.query_analyzer = QueryAnalyzer()
        self.response_generator = ResponseGenerator()
        logger.info("AskModeHandler initialized")
    
    async def handle_request(self, request: ChatRequest) -> BrainResponse:
        """Handle Ask mode request with contextual intelligence"""
        start_time = time.time()
        
        try:
            logger.info(f"Ask mode handling request: {request.query[:100]}...")
            
            # Retrieve memory context
            context = await self.memory_retriever.retrieve_context(
                request.query, request.user_id, request.session_id
            )
            
            # Analyze the query
            analysis = await self.query_analyzer.analyze_query(request.query, context)
            
            # Generate contextual response
            response_text = await self.response_generator.generate_response(
                analysis, context, request.query
            )
            
            # Calculate confidence based on context and analysis
            confidence = min(
                context.confidence_score + (0.2 if analysis.complexity == "simple" else 0.1),
                1.0
            )
            
            return BrainResponse(
                success=True,
                response=response_text,
                mode_used=ChatMode.ASK,
                processing_time=time.time() - start_time,
                resources_used=["memory", "llm"],
                confidence=confidence,
                metadata={
                    "intent": analysis.intent,
                    "entities": analysis.entities,
                    "scope": analysis.scope,
                    "complexity": analysis.complexity,
                    "context_confidence": context.confidence_score,
                    "relevant_conversations": len(context.recent_conversations),
                    "relevant_knowledge": len(context.relevant_knowledge)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in AskModeHandler: {e}")
            return BrainResponse(
                success=False,
                response=f"I encountered an error while processing your question: {str(e)}",
                mode_used=ChatMode.ASK,
                processing_time=time.time() - start_time,
                resources_used=[],
                confidence=0.0,
                metadata={"error": str(e)}
            )

# Create singleton instance
ask_mode_handler = AskModeHandler()

# Export the handler function
async def handle_ask_mode(request: ChatRequest) -> BrainResponse:
    """Entry point for Ask mode handling"""
    return await ask_mode_handler.handle_request(request)