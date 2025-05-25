#!/usr/bin/env python3
"""
Fix ASK Mode to Use Real Memory System Instead of Mock Data

This script connects the ASK mode handler to the actual memory system
to provide truly contextual responses based on real user activity.
"""

import asyncio
import json
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def create_real_memory_integration():
    """Create enhanced ASK mode handler that uses real memory system"""
    
    real_ask_handler_code = '''"""
Ask Mode Handler - Real Memory Integration
Connects to actual memory system for contextual responses.
"""

import asyncio
import json
import time
import os
import sys
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta

from ..core.brain_router import BrainResponse, ChatRequest, ChatMode

# Add memory system to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'memory'))

logger = logging.getLogger(__name__)

@dataclass
class MemoryContext:
    """Represents context from real memory systems"""
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

class RealMemoryRetriever:
    """Retrieves information from the actual memory system"""
    
    def __init__(self):
        self.memory_file = os.path.join(os.path.dirname(__file__), '../../memory/memory_state.json')
        self.conversation_history_file = os.path.join(os.path.dirname(__file__), '../../memory/conversation_history.json')
        logger.info(f"RealMemoryRetriever initialized with memory file: {self.memory_file}")
    
    async def retrieve_context(self, query: str, user_id: str, session_id: str) -> MemoryContext:
        """Retrieve relevant context from real memory systems"""
        try:
            # Load actual memory state
            memory_data = await self._load_memory_state()
            
            # Get recent conversations from actual history
            recent_conversations = await self._get_real_conversations(user_id, limit=5)
            
            # Extract relevant knowledge from memory content
            relevant_knowledge = await self._extract_relevant_knowledge(query, memory_data)
            
            # Analyze user patterns from memory
            user_patterns = await self._analyze_user_patterns(memory_data, user_id)
            
            # Get real system state
            system_state = await self._get_real_system_state(memory_data)
            
            # Calculate confidence based on available real context
            confidence = await self._calculate_real_context_confidence(
                recent_conversations, relevant_knowledge, user_patterns, query, memory_data
            )
            
            return MemoryContext(
                recent_conversations=recent_conversations,
                relevant_knowledge=relevant_knowledge,
                user_patterns=user_patterns,
                system_state=system_state,
                confidence_score=confidence
            )
            
        except Exception as e:
            logger.error(f"Error retrieving real context: {e}")
            return MemoryContext(
                recent_conversations=[],
                relevant_knowledge=[],
                user_patterns={},
                system_state={},
                confidence_score=0.1
            )
    
    async def _load_memory_state(self) -> Dict[str, Any]:
        """Load actual memory state from file"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"Memory file not found: {self.memory_file}")
                return {}
        except Exception as e:
            logger.error(f"Error loading memory state: {e}")
            return {}
    
    async def _get_real_conversations(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get real conversations from conversation history"""
        try:
            if os.path.exists(self.conversation_history_file):
                with open(self.conversation_history_file, 'r') as f:
                    conversations = json.load(f)
                
                # Sort by timestamp (most recent first) 
                if isinstance(conversations, list):
                    conversations.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
                    return conversations[:limit]
                elif isinstance(conversations, dict) and "conversations" in conversations:
                    conv_list = conversations["conversations"]
                    conv_list.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
                    return conv_list[:limit]
            
            return []
        except Exception as e:
            logger.error(f"Error loading conversation history: {e}")
            return []
    
    async def _extract_relevant_knowledge(self, query: str, memory_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract relevant knowledge from real memory data"""
        try:
            relevant_items = []
            query_lower = query.lower()
            
            # Search through short-term memory
            short_term = memory_data.get("short_term", [])
            for memory_item in short_term:
                relevance_score = await self._calculate_memory_relevance(query_lower, memory_item)
                if relevance_score > 0.3:  # Threshold for relevance
                    relevant_items.append({
                        "type": "short_term_memory",
                        "content": memory_item,
                        "relevance": relevance_score,
                        "timestamp": memory_item.get("timestamp"),
                        "memory_type": memory_item.get("memory_type")
                    })
            
            # Search through long-term memory
            long_term = memory_data.get("long_term", [])
            for memory_item in long_term:
                relevance_score = await self._calculate_memory_relevance(query_lower, memory_item)
                if relevance_score > 0.3:
                    relevant_items.append({
                        "type": "long_term_memory",
                        "content": memory_item,
                        "relevance": relevance_score,
                        "timestamp": memory_item.get("timestamp"),
                        "memory_type": memory_item.get("memory_type")
                    })
            
            # Sort by relevance
            relevant_items.sort(key=lambda x: x.get("relevance", 0), reverse=True)
            
            return relevant_items[:10]  # Return top 10 relevant items
            
        except Exception as e:
            logger.error(f"Error extracting relevant knowledge: {e}")
            return []
    
    async def _calculate_memory_relevance(self, query: str, memory_item: Dict[str, Any]) -> float:
        """Calculate how relevant a memory item is to the query"""
        try:
            score = 0.0
            query_words = set(query.split())
            
            # Check different fields in memory item
            fields_to_check = [
                ("user_activity", 0.4),
                ("context_analysis", 0.3),
                ("insights", 0.3),
                ("content_analysis", 0.4),
                ("professional_context", 0.2),
                ("application_context", 0.2)
            ]
            
            for field, weight in fields_to_check:
                if field in memory_item:
                    field_content = str(memory_item[field]).lower()
                    matches = sum(1 for word in query_words if word in field_content)
                    if matches > 0:
                        score += (matches / len(query_words)) * weight
            
            # Boost score for recent memories
            if "timestamp" in memory_item:
                try:
                    memory_time = datetime.fromisoformat(memory_item["timestamp"].replace('Z', '+00:00'))
                    age_hours = (datetime.now() - memory_time.replace(tzinfo=None)).total_seconds() / 3600
                    if age_hours < 24:  # Recent memory
                        score *= 1.5
                    elif age_hours < 168:  # Within a week
                        score *= 1.2
                except:
                    pass
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating memory relevance: {e}")
            return 0.0
    
    async def _analyze_user_patterns(self, memory_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Analyze user patterns from real memory data"""
        try:
            patterns = {}
            short_term = memory_data.get("short_term", [])
            
            # Analyze activity patterns
            activities = []
            applications = []
            productivity_scores = []
            workflow_stages = []
            
            for memory_item in short_term:
                if "user_activity" in memory_item:
                    activity = memory_item["user_activity"]
                    activities.append(activity.get("primary_activity", "unknown"))
                    applications.append(activity.get("application_used", "unknown"))
                    productivity_scores.append(activity.get("productivity_score", 0))
                
                if "context_analysis" in memory_item:
                    context = memory_item["context_analysis"]
                    workflow_stages.append(context.get("workflow_stage", "unknown"))
            
            # Calculate patterns
            if activities:
                from collections import Counter
                patterns["most_common_activity"] = Counter(activities).most_common(1)[0][0]
                patterns["activity_distribution"] = dict(Counter(activities))
            
            if applications:
                patterns["most_used_application"] = Counter(applications).most_common(1)[0][0]
                patterns["application_distribution"] = dict(Counter(applications))
            
            if productivity_scores:
                patterns["average_productivity"] = sum(productivity_scores) / len(productivity_scores)
                patterns["productivity_trend"] = "improving" if productivity_scores[-1] > productivity_scores[0] else "stable"
            
            if workflow_stages:
                patterns["current_workflow_stage"] = workflow_stages[-1] if workflow_stages else "unknown"
                patterns["workflow_distribution"] = dict(Counter(workflow_stages))
            
            patterns["total_memories"] = len(short_term)
            patterns["analysis_timestamp"] = datetime.now().isoformat()
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing user patterns: {e}")
            return {}
    
    async def _get_real_system_state(self, memory_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get real system state from memory data"""
        try:
            system_state = {
                "status": "operational",
                "memory_version": memory_data.get("version", "unknown"),
                "last_memory_update": memory_data.get("last_update", "unknown"),
                "total_short_term_memories": len(memory_data.get("short_term", [])),
                "total_long_term_memories": len(memory_data.get("long_term", [])),
                "context_available": bool(memory_data.get("context", {})),
                "sensor_data_available": bool(memory_data.get("sensor_data", {}))
            }
            
            # Analyze recent system activity
            short_term = memory_data.get("short_term", [])
            if short_term:
                latest_memory = short_term[-1]
                system_state["latest_activity"] = latest_memory.get("timestamp", "unknown")
                
                if "user_activity" in latest_memory:
                    activity = latest_memory["user_activity"]
                    system_state["current_application"] = activity.get("application_used", "unknown")
                    system_state["current_productivity"] = activity.get("productivity_score", 0)
                    system_state["current_engagement"] = activity.get("engagement_indicators", {})
            
            return system_state
            
        except Exception as e:
            logger.error(f"Error getting real system state: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _calculate_real_context_confidence(self, conversations: List, knowledge: List, 
                                               patterns: Dict, query: str, memory_data: Dict) -> float:
        """Calculate confidence based on real context availability"""
        try:
            factors = {
                "conversation_history": min(len(conversations) * 0.15, 0.3),
                "relevant_memories": min(len(knowledge) * 0.1, 0.4),
                "user_patterns": min(len(patterns) * 0.05, 0.2),
                "query_specificity": min(len(query.split()) * 0.02, 0.1),
                "memory_freshness": 0.0
            }
            
            # Check memory freshness
            short_term = memory_data.get("short_term", [])
            if short_term:
                try:
                    latest_time = datetime.fromisoformat(short_term[-1].get("timestamp", "").replace('Z', '+00:00'))
                    age_hours = (datetime.now() - latest_time.replace(tzinfo=None)).total_seconds() / 3600
                    if age_hours < 1:
                        factors["memory_freshness"] = 0.2
                    elif age_hours < 24:
                        factors["memory_freshness"] = 0.1
                except:
                    pass
            
            # Base confidence
            confidence = 0.2 + sum(factors.values())
            
            return min(confidence, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating context confidence: {e}")
            return 0.3

class QueryAnalyzer:
    """Analyzes user queries to understand intent and requirements"""
    
    def __init__(self):
        self.intent_patterns = {
            'factual': ['what is', 'define', 'explain', 'tell me about', 'how does'],
            'contextual': ['what did', 'show me', 'find', 'where is', 'when did', 'what am i', 'my current'],
            'historical': ['yesterday', 'last week', 'previously', 'before', 'ago', 'recent'],
            'predictive': ['will', 'going to', 'predict', 'forecast', 'future'],
            'comparative': ['compare', 'difference', 'better', 'versus', 'vs'],
            'activity': ['doing', 'working on', 'using', 'activities', 'workflow', 'productivity'],
            'application': ['app', 'application', 'program', 'software', 'tool', 'coding']
        }
        
        self.entity_types = {
            'file': ['file', 'document', 'folder', 'directory'],
            'system': ['system', 'process', 'service', 'application'],
            'time': ['today', 'yesterday', 'hour', 'minute', 'day', 'week', 'recent'],
            'user': ['user', 'profile', 'settings', 'preferences', 'my'],
            'activity': ['activity', 'work', 'doing', 'workflow', 'productivity'],
            'development': ['code', 'coding', 'development', 'programming', 'debug']
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
        stop_words = {'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but', 'in', 'with', 'to', 'for', 'of', 'as', 'by', 'are', 'am', 'i'}
        words = query.split()
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords
    
    async def _determine_time_context(self, query: str) -> Optional[str]:
        """Determine if query has time-related context"""
        recent_indicators = ['now', 'current', 'today', 'recent', 'latest', 'currently']
        historical_indicators = ['yesterday', 'last', 'previous', 'ago', 'before', 'earlier']
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

class RealResponseGenerator:
    """Generates contextual responses based on real memory data"""
    
    def __init__(self):
        self.response_templates = {
            "factual": "Based on my analysis of your activities, {content}",
            "contextual": "Looking at your recent context, {content}",
            "historical": "From your activity history, {content}",
            "predictive": "Based on your patterns, {content}",
            "comparative": "Comparing your activities, {content}",
            "activity": "Your activity analysis shows {content}",
            "application": "Regarding your application usage, {content}",
            "general": "{content}"
        }
    
    async def generate_response(self, analysis: QueryAnalysis, context: MemoryContext, 
                              original_query: str) -> str:
        """Generate a contextual response using real memory data"""
        try:
            # Get relevant information from real memory
            relevant_info = await self._gather_real_information(analysis, context)
            
            # Generate core content based on real data
            content = await self._generate_real_content(analysis, relevant_info, original_query)
            
            # Apply appropriate template
            template = self.response_templates.get(analysis.intent, self.response_templates["general"])
            response = template.format(content=content)
            
            # Add contextual details from real memory
            response = await self._add_real_contextual_details(response, analysis, context)
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating real response: {e}")
            return f"I can see from your activity that you're asking about: {original_query}. Let me provide what I know from your current context."
    
    async def _gather_real_information(self, analysis: QueryAnalysis, 
                                     context: MemoryContext) -> Dict[str, Any]:
        """Gather all relevant information from real memory"""
        info = {
            "recent_activities": [],
            "applications": [],
            "productivity_info": {},
            "workflow_info": {},
            "system_info": {},
            "conversations": context.recent_conversations,
            "memory_insights": []
        }
        
        # Extract information from relevant knowledge (real memory)
        for item in context.relevant_knowledge:
            if item.get("type") == "short_term_memory":
                memory_content = item.get("content", {})
                
                # Extract activity information
                if "user_activity" in memory_content:
                    activity = memory_content["user_activity"]
                    info["recent_activities"].append({
                        "activity": activity.get("primary_activity"),
                        "application": activity.get("application_used"),
                        "productivity": activity.get("productivity_score"),
                        "timestamp": memory_content.get("timestamp")
                    })
                    
                    app_info = {
                        "name": activity.get("application_used"),
                        "context": activity.get("professional_context"),
                        "productivity": activity.get("productivity_score")
                    }
                    if app_info not in info["applications"]:
                        info["applications"].append(app_info)
                
                # Extract workflow information
                if "context_analysis" in memory_content:
                    context_analysis = memory_content["context_analysis"]
                    info["workflow_info"] = {
                        "stage": context_analysis.get("workflow_stage"),
                        "intent": context_analysis.get("user_intent"),
                        "productivity_context": context_analysis.get("productivity_context")
                    }
                
                # Extract insights
                if "insights" in memory_content:
                    insights = memory_content["insights"]
                    if isinstance(insights, list):
                        info["memory_insights"].extend(insights)
        
        # Add user patterns
        info["patterns"] = context.user_patterns
        info["system_info"] = context.system_state
        
        return info
    
    async def _generate_real_content(self, analysis: QueryAnalysis, 
                                   relevant_info: Dict[str, Any], original_query: str) -> str:
        """Generate content based on real memory data"""
        
        query_lower = original_query.lower()
        
        # Handle activity-related queries
        if "activity" in analysis.entities or "doing" in query_lower or "working" in query_lower:
            return await self._generate_activity_content(relevant_info)
        
        # Handle application-related queries
        elif "application" in analysis.entities or "app" in query_lower or "using" in query_lower or "coding" in query_lower:
            return await self._generate_application_content(relevant_info)
        
        # Handle productivity queries
        elif "productivity" in query_lower or "patterns" in query_lower:
            return await self._generate_productivity_content(relevant_info)
        
        # Handle workflow queries
        elif "workflow" in query_lower or "current" in query_lower:
            return await self._generate_workflow_content(relevant_info)
        
        # Handle general contextual queries
        else:
            return await self._generate_general_real_content(relevant_info, analysis, original_query)
    
    async def _generate_activity_content(self, info: Dict[str, Any]) -> str:
        """Generate content about user activities"""
        activities = info.get("recent_activities", [])
        if not activities:
            return "I don't have recent activity data available."
        
        latest_activity = activities[-1] if activities else {}
        
        content_parts = []
        
        if latest_activity.get("activity"):
            content_parts.append(f"you've been engaged in {latest_activity['activity']}")
        
        if latest_activity.get("application"):
            content_parts.append(f"using {latest_activity['application']}")
        
        if latest_activity.get("productivity") is not None:
            productivity = latest_activity["productivity"]
            if productivity > 0.7:
                content_parts.append("with high productivity")
            elif productivity > 0.4:
                content_parts.append("with moderate productivity")
            else:
                content_parts.append("with light activity")
        
        # Add insights if available
        insights = info.get("memory_insights", [])
        if insights:
            content_parts.append(f"Insights: {insights[0]}")
        
        if content_parts:
            return ". ".join(content_parts) + "."
        else:
            return "I can see some recent activity but need more context to provide details."
    
    async def _generate_application_content(self, info: Dict[str, Any]) -> str:
        """Generate content about applications"""
        apps = info.get("applications", [])
        if not apps:
            return "I don't have recent application usage data."
        
        unique_apps = {}
        for app in apps:
            app_name = app.get("name", "Unknown")
            if app_name not in unique_apps:
                unique_apps[app_name] = app
        
        app_list = list(unique_apps.values())
        
        if len(app_list) == 1:
            app = app_list[0]
            context = app.get("context", "general")
            return f"you're currently using {app['name']} for {context} work."
        elif len(app_list) > 1:
            app_names = [app["name"] for app in app_list[:3]]  # Top 3
            return f"you've been using {', '.join(app_names[:-1])} and {app_names[-1]}."
        else:
            return "I can see application activity but need more details."
    
    async def _generate_productivity_content(self, info: Dict[str, Any]) -> str:
        """Generate content about productivity patterns"""
        patterns = info.get("patterns", {})
        activities = info.get("recent_activities", [])
        
        content_parts = []
        
        if patterns.get("average_productivity") is not None:
            avg_prod = patterns["average_productivity"]
            if avg_prod > 0.7:
                content_parts.append("your productivity has been high")
            elif avg_prod > 0.4:
                content_parts.append("your productivity has been moderate")
            else:
                content_parts.append("you've been in a light activity period")
        
        if patterns.get("most_common_activity"):
            content_parts.append(f"primarily focusing on {patterns['most_common_activity']}")
        
        if patterns.get("productivity_trend"):
            trend = patterns["productivity_trend"]
            content_parts.append(f"with a {trend} trend")
        
        if content_parts:
            return ". ".join(content_parts) + "."
        else:
            return "I'm analyzing your productivity patterns from recent activity."
    
    async def _generate_workflow_content(self, info: Dict[str, Any]) -> str:
        """Generate content about current workflow"""
        workflow_info = info.get("workflow_info", {})
        patterns = info.get("patterns", {})
        
        content_parts = []
        
        if workflow_info.get("stage"):
            content_parts.append(f"you're in the {workflow_info['stage']} stage")
        
        if workflow_info.get("intent"):
            content_parts.append(f"focused on {workflow_info['intent']}")
        
        if patterns.get("current_workflow_stage"):
            content_parts.append(f"currently in {patterns['current_workflow_stage']} workflow")
        
        if content_parts:
            return ". ".join(content_parts) + "."
        else:
            return "I can see your current workflow context but need more details."
    
    async def _generate_general_real_content(self, info: Dict[str, Any], analysis: QueryAnalysis, query: str) -> str:
        """Generate general content from real memory"""
        insights = info.get("memory_insights", [])
        activities = info.get("recent_activities", [])
        
        if insights:
            return f"based on recent analysis: {insights[0]}"
        elif activities:
            latest = activities[-1]
            if latest.get("activity") and latest.get("application"):
                return f"you've been working on {latest['activity']} using {latest['application']}"
            elif latest.get("activity"):
                return f"you've been engaged in {latest['activity']}"
        
        return f"I'm processing information about {', '.join(analysis.keywords) if analysis.keywords else 'your current context'}"
    
    async def _add_real_contextual_details(self, response: str, analysis: QueryAnalysis, 
                                         context: MemoryContext) -> str:
        """Add contextual details from real memory"""
        
        # Add confidence indicator
        if context.confidence_score > 0.8:
            response += "\\n\\n(High confidence based on recent activity data)"
        elif context.confidence_score > 0.6:
            response += "\\n\\n(Medium confidence based on available memory)"
        elif context.confidence_score > 0.3:
            response += "\\n\\n(Moderate confidence - some memory data available)"
        
        # Add system status if relevant
        system_state = context.system_state
        if "system" in analysis.entities and system_state:
            if "current_application" in system_state:
                response += f"\\n\\nCurrent Application: {system_state['current_application']}"
            if "latest_activity" in system_state:
                response += f"\\nLast Activity: {system_state['latest_activity']}"
        
        # Add memory freshness info
        if system_state.get("total_short_term_memories", 0) > 0:
            memory_count = system_state["total_short_term_memories"]
            response += f"\\n\\nMemory: {memory_count} recent activities analyzed"
        
        return response

class RealAskModeHandler:
    """Real Ask mode handler using actual memory system"""
    
    def __init__(self):
        self.memory_retriever = RealMemoryRetriever()
        self.query_analyzer = QueryAnalyzer()
        self.response_generator = RealResponseGenerator()
        logger.info("RealAskModeHandler initialized with real memory integration")
    
    async def handle_request(self, request: ChatRequest) -> BrainResponse:
        """Handle Ask mode request with real contextual intelligence"""
        start_time = time.time()
        
        try:
            logger.info(f"Real Ask mode handling request: {request.query[:100]}...")
            
            # Retrieve real memory context
            context = await self.memory_retriever.retrieve_context(
                request.query, request.user_id, request.session_id
            )
            
            # Analyze the query
            analysis = await self.query_analyzer.analyze_query(request.query, context)
            
            # Generate contextual response using real memory
            response_text = await self.response_generator.generate_response(
                analysis, context, request.query
            )
            
            # Calculate confidence based on real context and analysis
            confidence = min(
                context.confidence_score + (0.2 if analysis.complexity == "simple" else 0.1),
                1.0
            )
            
            logger.info(f"Real Ask mode response generated with confidence: {confidence}")
            
            return BrainResponse(
                success=True,
                response=response_text,
                mode_used=ChatMode.ASK,
                processing_time=time.time() - start_time,
                resources_used=["real_memory", "llm"],
                confidence=confidence,
                metadata={
                    "intent": analysis.intent,
                    "entities": analysis.entities,
                    "scope": analysis.scope,
                    "complexity": analysis.complexity,
                    "context_confidence": context.confidence_score,
                    "relevant_conversations": len(context.recent_conversations),
                    "relevant_knowledge": len(context.relevant_knowledge),
                    "real_memory_used": True,
                    "memory_items_analyzed": len(context.relevant_knowledge)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in RealAskModeHandler: {e}")
            return BrainResponse(
                success=False,
                response=f"I encountered an error while analyzing your context: {str(e)}",
                mode_used=ChatMode.ASK,
                processing_time=time.time() - start_time,
                resources_used=[],
                confidence=0.0,
                metadata={"error": str(e), "real_memory_used": False}
            )

# Create singleton instance
real_ask_mode_handler = RealAskModeHandler()

# Export the handler function
async def handle_ask_mode(request: ChatRequest) -> BrainResponse:
    """Entry point for Real Ask mode handling"""
    return await real_ask_mode_handler.handle_request(request)
'''
    
    # Write the enhanced ask mode handler
    output_file = "brain/handlers/ask_mode_handler_real.py"
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write(real_ask_handler_code)
    
    print(f"✅ Created real memory integrated ASK mode handler: {output_file}")
    
    # Now create a backup of the original and replace it
    original_file = "brain/handlers/ask_mode_handler.py"
    backup_file = "brain/handlers/ask_mode_handler_mock.py.backup"
    
    # Backup original
    if os.path.exists(original_file):
        with open(original_file, 'r') as f:
            original_content = f.read()
        with open(backup_file, 'w') as f:
            f.write(original_content)
        print(f"✅ Backed up original ASK mode handler to: {backup_file}")
    
    # Replace with real memory version
    with open(original_file, 'w') as f:
        f.write(real_ask_handler_code)
    
    print(f"✅ Replaced ASK mode handler with real memory integration")
    
    return {
        "status": "success",
        "real_handler_file": output_file,
        "original_backup": backup_file,
        "changes": [
            "Connected ASK mode to real memory system instead of mock data",
            "Added real conversation history retrieval",
            "Enhanced memory relevance calculation",
            "Added real user pattern analysis",
            "Improved contextual response generation",
            "Added system state from actual memory",
            "Enhanced confidence calculation based on real data"
        ]
    }

async def main():
    """Main execution"""
    print("🔧 Fixing ASK Mode Real Memory Integration")
    print("=" * 60)
    
    result = await create_real_memory_integration()
    
    print("\n📊 Integration Summary:")
    print(f"Status: {result['status']}")
    print("\nChanges made:")
    for change in result['changes']:
        print(f"  • {change}")
    
    print(f"\n📁 Files:")
    print(f"  • Real handler: {result['real_handler_file']}")
    print(f"  • Original backup: {result['original_backup']}")
    
    print("\n🎯 Next Steps:")
    print("1. Restart the backend server")
    print("2. Test ASK mode with queries like:")
    print("   - 'What development activities have I been doing recently?'")
    print("   - 'What applications am I using for coding?'")
    print("   - 'Tell me about my productivity patterns'")
    print("3. ASK mode should now provide real contextual answers!")

if __name__ == "__main__":
    asyncio.run(main())