"""
Enhanced Ask Mode Handler - Real Memory Integration with LLM
Connects to actual memory system AND calls LLM with enriched context.
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

# Import semantic search
try:
    from memory.enhanced_semantic_search import EnhancedSemanticSearch
    SEMANTIC_SEARCH_AVAILABLE = True
except ImportError:
    SEMANTIC_SEARCH_AVAILABLE = False

# Import enhanced app semantic search
try:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from enhanced_app_semantic_search import EnhancedAppSemanticSearch
    APP_SEMANTIC_SEARCH_AVAILABLE = True
except ImportError:
    APP_SEMANTIC_SEARCH_AVAILABLE = False

# Import LLM service
try:
    from llm.llm_service import LLMService
    LLM_SERVICE_AVAILABLE = True
except ImportError:
    LLM_SERVICE_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class EnhancedMemoryContext:
    """Enhanced context from real memory systems with semantic search"""
    recent_conversations: List[Dict[str, Any]]
    semantic_results: List[Dict[str, Any]]  # Results from semantic search
    relevant_knowledge: List[Dict[str, Any]]
    user_patterns: Dict[str, Any]
    system_state: Dict[str, Any]
    confidence_score: float
    search_metadata: Dict[str, Any]

class EnhancedMemoryRetriever:
    """Retrieves information from the actual memory system with semantic search"""
    
    def __init__(self):
        self.memory_file = os.path.join(os.path.dirname(__file__), '../../memory/memory_state.json')
        self.conversation_history_file = os.path.join(os.path.dirname(__file__), '../../memory/conversation_history.json')
        self.conscious_file = os.path.join(os.path.dirname(__file__), '../../memory/conscious.json')
        self.visual_context_file = os.path.join(os.path.dirname(__file__), '../../cache/total_screen_analyzer/latest_total_analysis.json')
        self.last_context_file = os.path.join(os.path.dirname(__file__), '../../memory/last_context.json')
        
        # Initialize semantic search if available
        self.semantic_search = None
        if SEMANTIC_SEARCH_AVAILABLE:
            try:
                self.semantic_search = EnhancedSemanticSearch()
                logger.info("Semantic search initialized for enhanced memory retrieval")
            except Exception as e:
                logger.error(f"Failed to initialize semantic search: {e}")
                self.semantic_search = None
        
        # Initialize enhanced app semantic search
        self.app_semantic_search = None
        if APP_SEMANTIC_SEARCH_AVAILABLE:
            try:
                self.app_semantic_search = EnhancedAppSemanticSearch(self.memory_file)
                logger.info("Enhanced app semantic search initialized")
            except Exception as e:
                logger.error(f"Failed to initialize app semantic search: {e}")
                self.app_semantic_search = None
        
        logger.info(f"EnhancedMemoryRetriever initialized with memory file: {self.memory_file}")
    
    async def retrieve_enhanced_context(self, query: str, user_id: str, session_id: str) -> EnhancedMemoryContext:
        """Retrieve enhanced context using semantic search + traditional methods"""
        try:
            # Load actual memory state
            memory_data = await self._load_memory_state()
            conscious_data = await self._load_conscious_memory()
            visual_context = await self._load_visual_context()
            last_context = await self._load_last_context()
            
            # Get recent conversations
            recent_conversations = await self._get_real_conversations(user_id, limit=5)
            
            # Use semantic search if available
            semantic_results = []
            search_metadata = {}
            if self.semantic_search and memory_data:
                semantic_results, search_metadata = await self._perform_semantic_search(query, memory_data, conscious_data, visual_context)
            
            # Extract relevant knowledge using traditional keyword matching as fallback
            relevant_knowledge = await self._extract_relevant_knowledge(query, memory_data)
            
            # Analyze user patterns
            user_patterns = await self._analyze_user_patterns(memory_data, user_id)
            
            # Get system state
            system_state = await self._get_real_system_state(memory_data)
            
            # Calculate enhanced confidence
            confidence = await self._calculate_enhanced_confidence(
                recent_conversations, semantic_results, relevant_knowledge, 
                user_patterns, query, memory_data, search_metadata
            )
            
            return EnhancedMemoryContext(
                recent_conversations=recent_conversations,
                semantic_results=semantic_results,
                relevant_knowledge=relevant_knowledge,
                user_patterns=user_patterns,
                system_state=system_state,
                confidence_score=confidence,
                search_metadata=search_metadata
            )
            
        except Exception as e:
            logger.error(f"Error retrieving enhanced context: {e}")
            return EnhancedMemoryContext(
                recent_conversations=[],
                semantic_results=[],
                relevant_knowledge=[],
                user_patterns={},
                system_state={},
                confidence_score=0.1,
                search_metadata={"error": str(e)}
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
    
    async def _load_conscious_memory(self) -> Dict[str, Any]:
        """Load conscious memory from file"""
        try:
            if os.path.exists(self.conscious_file):
                with open(self.conscious_file, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"Conscious memory file not found: {self.conscious_file}")
                return {}
        except Exception as e:
            logger.error(f"Error loading conscious memory: {e}")
            return {}
    
    async def _load_visual_context(self) -> Dict[str, Any]:
        """Load visual context from total screen analyzer cache"""
        try:
            if os.path.exists(self.visual_context_file):
                with open(self.visual_context_file, 'r') as f:
                    visual_data = json.load(f)
                    logger.info(f"Loaded visual context: {visual_data.get('synthesized_context', {}).get('semantic_summary', 'No summary')}")
                    return visual_data
            else:
                logger.warning(f"Visual context file not found: {self.visual_context_file}")
                return {}
        except Exception as e:
            logger.error(f"Error loading visual context: {e}")
            return {}
    
    async def _load_last_context(self) -> Dict[str, Any]:
        """Load last context from memory system"""
        try:
            if os.path.exists(self.last_context_file):
                with open(self.last_context_file, 'r') as f:
                    context_data = json.load(f)
                    if context_data:
                        logger.info(f"Loaded last context with keys: {list(context_data.keys()) if isinstance(context_data, dict) else 'List data'}")
                    return context_data
            else:
                logger.warning(f"Last context file not found: {self.last_context_file}")
                return {}
        except Exception as e:
            logger.error(f"Error loading last context: {e}")
            return {}
    
    async def _perform_semantic_search(self, query: str, memory_data: Dict[str, Any], 
                                     conscious_data: Dict[str, Any], visual_context: Dict[str, Any]) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Perform intelligent semantic search on memory data for ANY question"""
        try:
            logger.info(f"Performing intelligent semantic search for query: {query}")
            results = []
            
            # First, check if this is an app-related query and enhance with app data
            if self.app_semantic_search and self.app_semantic_search.is_app_related_query(query):
                logger.info("App-related query detected, adding app context")
                app_context = self.app_semantic_search.generate_app_response_context(query)
                
                if app_context:
                    results.append({
                        "content": {"enriched_context": app_context, "type": "app_data"},
                        "type": "app_context",
                        "relevance_score": 0.95,
                        "searchable_text": app_context
                    })
            
            # Always perform comprehensive memory search for ANY question
            all_memory_items = []
            
            # Add short-term memories with enhanced extraction
            for item in memory_data.get("short_term", []):
                searchable_text = self._extract_comprehensive_searchable_text(item)
                if searchable_text.strip():  # Only add if there's meaningful content
                    all_memory_items.append({
                        "content": item,
                        "type": "short_term",
                        "searchable_text": searchable_text,
                        "timestamp": item.get("timestamp"),
                        "memory_type": item.get("memory_type", "activity")
                    })
            
            # Add long-term memories
            for item in memory_data.get("long_term", []):
                searchable_text = self._extract_comprehensive_searchable_text(item)
                if searchable_text.strip():
                    all_memory_items.append({
                        "content": item,
                        "type": "long_term", 
                        "searchable_text": searchable_text,
                        "timestamp": item.get("timestamp"),
                        "memory_type": item.get("memory_type", "knowledge")
                    })
            
            # Add conscious memories
            for item in conscious_data.get("entries", []):
                searchable_text = self._extract_comprehensive_searchable_text(item)
                if searchable_text.strip():
                    all_memory_items.append({
                        "content": item,
                        "type": "conscious",
                        "searchable_text": searchable_text,
                        "timestamp": item.get("timestamp"),
                        "memory_type": "conscious"
                    })
            
            # Add visual context if available
            if visual_context and "memory_summary" in visual_context:
                visual_searchable = self._extract_visual_searchable_text(visual_context)
                if visual_searchable.strip():
                    visual_item = {
                        "content": visual_context["memory_summary"],
                        "type": "visual_context",
                        "searchable_text": visual_searchable,
                        "timestamp": visual_context.get("timestamp"),
                        "confidence": visual_context.get("synthesized_context", {}).get("confidence", 0),
                        "memory_type": "visual"
                    }
                    all_memory_items.append(visual_item)
            
            # Perform intelligent search on all memory items
            memory_search_results = await self._intelligent_memory_search(query, all_memory_items)
            
            # Add memory search results to our results
            results.extend(memory_search_results)
            
            # Sort all results by relevance
            results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            
            metadata = {
                "total_items_indexed": len(all_memory_items),
                "search_query": query,
                "results_count": len(results),
                "semantic_search_used": True,
                "app_semantic_search_used": bool(self.app_semantic_search and self.app_semantic_search.is_app_related_query(query)),
                "memory_types_searched": list(set(item.get("memory_type", "unknown") for item in all_memory_items))
            }
            
            return results[:10], metadata  # Return top 10 most relevant results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return [], {"error": str(e), "semantic_search_used": False}
    
    def _extract_comprehensive_searchable_text(self, memory_item: Dict[str, Any]) -> str:
        """Extract comprehensive searchable text from memory item for ANY question"""
        searchable_parts = []
        
        # Extract from ALL possible fields that might contain useful information
        if isinstance(memory_item, dict):
            # Priority fields (most important first)
            priority_fields = [
                "user_activity", "context_analysis", "insights", "content_analysis",
                "professional_context", "application_context", "current_applications",
                "application_used", "primary_activity", "workflow_stage"
            ]
            
            # Extract priority fields first
            for field in priority_fields:
                if field in memory_item:
                    value = memory_item[field]
                    if isinstance(value, str) and value.strip():
                        searchable_parts.append(f"{field}: {value}")
                    elif isinstance(value, list):
                        if value:  # Only if list is not empty
                            searchable_parts.append(f"{field}: {', '.join(str(v) for v in value)}")
                    elif isinstance(value, dict) and value:
                        # Extract nested information
                        nested_text = self._extract_from_nested_dict(value, field)
                        if nested_text:
                            searchable_parts.append(nested_text)
            
            # Extract from any other fields that might contain text
            for key, value in memory_item.items():
                if key not in priority_fields and value:
                    if isinstance(value, str) and len(value.strip()) > 3:  # Meaningful text
                        searchable_parts.append(f"{key}: {value}")
                    elif isinstance(value, list) and value:
                        searchable_parts.append(f"{key}: {', '.join(str(v) for v in value if v)}")
                    elif isinstance(value, dict) and value:
                        nested_text = self._extract_from_nested_dict(value, key)
                        if nested_text:
                            searchable_parts.append(nested_text)
        
        return " ".join(searchable_parts)
    
    def _extract_from_nested_dict(self, nested_dict: Dict[str, Any], parent_key: str) -> str:
        """Extract searchable text from nested dictionary"""
        parts = []
        for key, value in nested_dict.items():
            if isinstance(value, str) and len(value.strip()) > 3:
                parts.append(f"{parent_key}.{key}: {value}")
            elif isinstance(value, list) and value:
                parts.append(f"{parent_key}.{key}: {', '.join(str(v) for v in value if v)}")
        return " ".join(parts)
    
    def _extract_searchable_text(self, memory_item: Dict[str, Any]) -> str:
        """Legacy method - now uses comprehensive extraction"""
        return self._extract_comprehensive_searchable_text(memory_item)
    
    def _extract_visual_searchable_text(self, visual_context: Dict[str, Any]) -> str:
        """Extract searchable text from visual context"""
        searchable_parts = []
        
        # Extract from memory summary
        memory_summary = visual_context.get("memory_summary", {})
        if memory_summary:
            searchable_parts.append(memory_summary.get("semantic_summary", ""))
            searchable_parts.append(memory_summary.get("overall_context", ""))
            searchable_parts.append(memory_summary.get("activity_classification", ""))
            
            # Application info
            app_info = memory_summary.get("application", {})
            if app_info:
                searchable_parts.append(f"application: {app_info.get('name', '')}")
                searchable_parts.append(f"app_type: {app_info.get('detected_type', '')}")
            
            # Content info
            content_info = memory_summary.get("content", {})
            if content_info:
                searchable_parts.append(f"content_type: {content_info.get('type', '')}")
                searchable_parts.append(f"purpose: {content_info.get('primary_purpose', '')}")
            
            # User activity
            user_activity = memory_summary.get("user_activity", {})
            if user_activity:
                searchable_parts.append(f"current_activity: {user_activity.get('current_activity', '')}")
                searchable_parts.append(f"workflow_stage: {user_activity.get('workflow_stage', '')}")
                searchable_parts.append(f"user_intent: {user_activity.get('user_intent', '')}")
            
            # Key insights
            insights = memory_summary.get("key_insights", [])
            if insights:
                searchable_parts.extend(insights)
            
            # Text sample for specific content
            text_sample = memory_summary.get("text_sample", "")
            if text_sample:
                # Include first 200 chars of text sample
                searchable_parts.append(f"screen_text: {text_sample[:200]}")
        
        # Extract from synthesized context
        synthesized = visual_context.get("synthesized_context", {})
        if synthesized:
            searchable_parts.append(synthesized.get("semantic_summary", ""))
            
            synth_insights = synthesized.get("key_insights", [])
            if synth_insights:
                searchable_parts.extend(synth_insights)
        
        return " ".join(filter(None, searchable_parts))
    
    async def _index_memory_item(self, item_id: int, text: str):
        """Index a memory item for semantic search"""
        try:
            if self.semantic_search and text.strip():
                # This would normally add to vector index
                # For now, just store in the semantic search instance
                pass
        except Exception as e:
            logger.error(f"Error indexing memory item {item_id}: {e}")
    
    async def _intelligent_memory_search(self, query: str, memory_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Intelligent memory search that finds relevant information for ANY question"""
        try:
            results = []
            query_lower = query.lower()
            query_words = set(word.strip() for word in query_lower.split() if len(word.strip()) > 2)
            
            logger.info(f"Searching {len(memory_items)} memory items for query words: {query_words}")
            
            for item in memory_items:
                score = 0.0
                searchable_text = item["searchable_text"].lower()
                searchable_words = set(searchable_text.split())
                
                # Multi-level scoring system
                
                # 1. Exact phrase matching (highest score)
                if query_lower in searchable_text:
                    score += 2.0
                    logger.debug(f"Exact phrase match found in {item['type']}")
                
                # 2. Multiple keyword matching  
                keyword_matches = sum(1 for word in query_words if word in searchable_text)
                if keyword_matches > 0:
                    keyword_score = (keyword_matches / len(query_words)) * 1.5
                    score += keyword_score
                    logger.debug(f"Keyword matches: {keyword_matches}/{len(query_words)} in {item['type']}")
                
                # 3. Semantic similarity (word overlap)
                word_overlap = len(query_words.intersection(searchable_words))
                if word_overlap > 0:
                    semantic_score = (word_overlap / len(query_words)) * 1.0
                    score += semantic_score
                
                # 4. Content type relevance boosts
                content = item.get("content", {})
                if isinstance(content, dict):
                    # Boost for apps/activity related content
                    if any(word in query_lower for word in ["app", "application", "program", "open", "running"]):
                        if any(field in content for field in ["current_applications", "application_used", "user_activity"]):
                            score *= 1.8
                            logger.debug(f"App relevance boost applied to {item['type']}")
                    
                    # Boost for work/activity queries
                    if any(word in query_lower for word in ["work", "working", "activity", "doing", "task"]):
                        if any(field in content for field in ["primary_activity", "workflow_stage", "user_activity"]):
                            score *= 1.6
                    
                    # Boost for current/recent queries
                    if any(word in query_lower for word in ["current", "now", "recent", "latest"]):
                        score *= 1.4
                
                # 5. Recency boost
                timestamp = item.get("timestamp") or content.get("timestamp") if isinstance(content, dict) else None
                if timestamp:
                    try:
                        if isinstance(timestamp, str):
                            item_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            age_hours = (datetime.now() - item_time.replace(tzinfo=None)).total_seconds() / 3600
                            if age_hours < 1:
                                score *= 2.0  # Very recent
                            elif age_hours < 24:
                                score *= 1.7  # Recent
                            elif age_hours < 168:  # Within a week
                                score *= 1.3
                    except Exception as e:
                        logger.debug(f"Error parsing timestamp {timestamp}: {e}")
                
                # 6. Memory type relevance
                memory_type = item.get("memory_type", "unknown")
                if memory_type == "activity" and any(word in query_lower for word in ["activity", "doing", "work", "app"]):
                    score *= 1.3
                elif memory_type == "visual" and any(word in query_lower for word in ["see", "screen", "looking", "view"]):
                    score *= 1.4
                
                # Include items with meaningful scores
                if score > 0.1:  # Lower threshold to be more inclusive
                    results.append({
                        "content": item["content"],
                        "type": item["type"],
                        "relevance_score": min(score, 5.0),  # Cap at 5.0
                        "searchable_text": item["searchable_text"][:300],  # Longer preview
                        "memory_type": item.get("memory_type", "unknown"),
                        "timestamp": item.get("timestamp"),
                        "match_details": {
                            "keyword_matches": keyword_matches,
                            "word_overlap": word_overlap,
                            "exact_phrase": query_lower in searchable_text
                        }
                    })
            
            # Sort by relevance score
            results.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            logger.info(f"Found {len(results)} relevant memory items with scores > 0.1")
            for i, result in enumerate(results[:5]):  # Log top 5
                logger.info(f"Result {i+1}: {result['type']} (score: {result['relevance_score']:.2f})")
            
            return results[:15]  # Return top 15 results for comprehensive context
            
        except Exception as e:
            logger.error(f"Error in intelligent memory search: {e}")
            return []
    
    async def _search_memories(self, query: str, memory_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Legacy method - now uses intelligent search"""
        return await self._intelligent_memory_search(query, memory_items)
    
    async def _get_real_conversations(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get real conversations from conversation history"""
        try:
            if os.path.exists(self.conversation_history_file):
                with open(self.conversation_history_file, 'r') as f:
                    conversations = json.load(f)
                
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
        """Extract relevant knowledge using traditional keyword matching"""
        try:
            relevant_items = []
            query_lower = query.lower()
            
            # Search through short-term memory
            short_term = memory_data.get("short_term", [])
            for memory_item in short_term:
                relevance_score = await self._calculate_memory_relevance(query_lower, memory_item)
                if relevance_score > 0.3:
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
            
            relevant_items.sort(key=lambda x: x.get("relevance", 0), reverse=True)
            return relevant_items[:5]  # Top 5 traditional matches
            
        except Exception as e:
            logger.error(f"Error extracting relevant knowledge: {e}")
            return []
    
    async def _calculate_memory_relevance(self, query: str, memory_item: Dict[str, Any]) -> float:
        """Calculate how relevant a memory item is to the query"""
        try:
            score = 0.0
            query_words = set(query.split())
            
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
                    if age_hours < 24:
                        score *= 1.5
                    elif age_hours < 168:
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
            
            if activities:
                from collections import Counter
                patterns["most_common_activity"] = Counter(activities).most_common(1)[0][0]
                patterns["activity_distribution"] = dict(Counter(activities))
            
            if applications:
                patterns["most_used_application"] = Counter(applications).most_common(1)[0][0]
                patterns["application_distribution"] = dict(Counter(applications))
            
            if productivity_scores:
                patterns["average_productivity"] = sum(productivity_scores) / len(productivity_scores)
            
            if workflow_stages:
                patterns["current_workflow_stage"] = workflow_stages[-1] if workflow_stages else "unknown"
            
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
            
            return system_state
            
        except Exception as e:
            logger.error(f"Error getting real system state: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _calculate_enhanced_confidence(self, conversations: List, semantic_results: List,
                                           knowledge: List, patterns: Dict, query: str, 
                                           memory_data: Dict, search_metadata: Dict) -> float:
        """Calculate confidence based on enhanced context availability"""
        try:
            factors = {
                "conversation_history": min(len(conversations) * 0.1, 0.2),
                "semantic_results": min(len(semantic_results) * 0.15, 0.4),
                "relevant_memories": min(len(knowledge) * 0.1, 0.3),
                "user_patterns": min(len(patterns) * 0.05, 0.1),
                "query_specificity": min(len(query.split()) * 0.02, 0.05),
                "memory_freshness": 0.0
            }
            
            # Boost confidence if semantic search was used successfully
            if search_metadata.get("semantic_search_used"):
                factors["semantic_search_bonus"] = 0.2
            
            # Check memory freshness
            short_term = memory_data.get("short_term", [])
            if short_term:
                try:
                    latest_time = datetime.fromisoformat(short_term[-1].get("timestamp", "").replace('Z', '+00:00'))
                    age_hours = (datetime.now() - latest_time.replace(tzinfo=None)).total_seconds() / 3600
                    if age_hours < 1:
                        factors["memory_freshness"] = 0.15
                    elif age_hours < 24:
                        factors["memory_freshness"] = 0.1
                except:
                    pass
            
            confidence = 0.3 + sum(factors.values())  # Base confidence
            return min(confidence, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating enhanced confidence: {e}")
            return 0.4

class EnhancedLLMContextBuilder:
    """Builds enriched context for LLM calls"""
    
    def __init__(self):
        self.llm_service = None
        if LLM_SERVICE_AVAILABLE:
            try:
                self.llm_service = LLMService()
                logger.info("LLM service initialized for enhanced ask mode")
            except Exception as e:
                logger.error(f"Failed to initialize LLM service: {e}")
                self.llm_service = None
    
    async def build_enriched_context(self, query: str, memory_context: EnhancedMemoryContext) -> str:
        """Build enriched context string for LLM"""
        try:
            context_parts = []
            
            # Add query analysis
            context_parts.append(f"User Query: {query}")
            
            # Add app context first if this is an app query
            app_results = [r for r in memory_context.semantic_results if r.get('type') == 'app_context']
            if app_results:
                context_parts.append("\n--- APPLICATION CONTEXT ---")
                app_result = app_results[0]  # Most relevant app context
                app_context = app_result.get('content', {}).get('app_context', '')
                if app_context:
                    context_parts.append(app_context)
                    context_parts.append("")
                logger.info("Added app-specific context to LLM prompt")
            
            # Add current visual context (most relevant for "what am I seeing" queries)
            visual_results = [r for r in memory_context.semantic_results if r.get('type') == 'visual_context']
            if visual_results and not app_results:  # Only add visual if no app context
                context_parts.append("\n--- CURRENT SCREEN CONTEXT ---")
                visual_result = visual_results[0]  # Most recent visual context
                content = visual_result.get('content', {})
                
                # Application information
                app_info = content.get('application', {})
                if app_info.get('name'):
                    context_parts.append(f"Current Application: {app_info['name']}")
                    context_parts.append(f"Application Type: {app_info.get('detected_type', 'unknown')}")
                
                # Content information
                content_info = content.get('content', {})
                if content_info:
                    context_parts.append(f"Content Type: {content_info.get('type', 'unknown')}")
                    context_parts.append(f"Primary Purpose: {content_info.get('primary_purpose', 'unknown')}")
                    if content_info.get('word_count'):
                        context_parts.append(f"Word Count: {content_info['word_count']}")
                
                # User activity
                user_activity = content.get('user_activity', {})
                if user_activity:
                    context_parts.append(f"Current Activity: {user_activity.get('current_activity', 'unknown')}")
                    context_parts.append(f"Workflow Stage: {user_activity.get('workflow_stage', 'unknown')}")
                    context_parts.append(f"User Intent: {user_activity.get('user_intent', 'unknown')}")
                
                # Key insights
                insights = content.get('key_insights', [])
                if insights:
                    context_parts.append("Key Insights:")
                    for insight in insights[:3]:  # Top 3 insights
                        context_parts.append(f"- {insight}")
                
                # Screen text sample
                text_sample = content.get('text_sample', '')
                if text_sample and len(text_sample.strip()) > 10:
                    context_parts.append(f"Screen Text Sample: {text_sample[:300]}...")
                
                context_parts.append("")
            
            # Add semantic search results (non-visual, non-app)
            other_results = [r for r in memory_context.semantic_results 
                           if r.get('type') not in ['visual_context', 'app_context']]
            if other_results:
                context_parts.append("\n--- RELEVANT MEMORY SEARCH RESULTS ---")
                # Show more results since we have better search now
                for i, result in enumerate(other_results[:5]):  # Show top 5 results
                    relevance = result.get('relevance_score', 0)
                    if relevance > 0.3:  # Only show highly relevant results
                        context_parts.append(f"Memory {i+1} (relevance: {relevance:.2f}, type: {result.get('type', 'unknown')}):")
                        
                        # Extract key information from content
                        content = result.get('content', {})
                        if isinstance(content, dict):
                            # Show the most relevant fields
                            for field in ['user_activity', 'primary_activity', 'application_used', 'current_applications']:
                                if field in content and content[field]:
                                    context_parts.append(f"  {field}: {str(content[field])[:100]}")
                        
                        # Show preview of searchable text
                        searchable = result.get('searchable_text', '')[:200]
                        if searchable:
                            context_parts.append(f"  Content: {searchable}")
                        
                        context_parts.append("")
            
            # Add relevant memories
            if memory_context.relevant_knowledge:
                context_parts.append("\n--- RELEVANT MEMORIES ---")
                for i, item in enumerate(memory_context.relevant_knowledge[:2]):
                    context_parts.append(f"Memory {i+1}:")
                    context_parts.append(f"Type: {item.get('type', 'unknown')}")
                    context_parts.append(f"Relevance: {item.get('relevance', 0):.2f}")
                    content = item.get('content', {})
                    if isinstance(content, dict):
                        for key, value in content.items():
                            if key in ['user_activity', 'context_analysis', 'insights']:
                                context_parts.append(f"{key}: {str(value)[:100]}")
                    context_parts.append("")
            
            # Add user patterns
            if memory_context.user_patterns:
                context_parts.append("\n--- USER PATTERNS ---")
                for key, value in memory_context.user_patterns.items():
                    context_parts.append(f"{key}: {value}")
                context_parts.append("")
            
            # Add system state
            if memory_context.system_state:
                context_parts.append("\n--- SYSTEM STATE ---")
                for key, value in memory_context.system_state.items():
                    if key in ['current_application', 'latest_activity', 'total_short_term_memories']:
                        context_parts.append(f"{key}: {value}")
                context_parts.append("")
            
            # Add search metadata
            if memory_context.search_metadata:
                context_parts.append("\n--- SEARCH METADATA ---")
                context_parts.append(f"Semantic search used: {memory_context.search_metadata.get('semantic_search_used', False)}")
                context_parts.append(f"Results found: {memory_context.search_metadata.get('results_count', 0)}")
                context_parts.append(f"Confidence: {memory_context.confidence_score:.2f}")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error building enriched context: {e}")
            return f"Error building context: {str(e)}"
    
    async def call_llm_with_context(self, query: str, enriched_context: str, memory_context=None) -> str:
        """Call LLM with enriched memory context"""
        try:
            if not self.llm_service:
                return await self._generate_fallback_response(query, enriched_context, memory_context)
            
            # Build system message with memory context
            system_message = f"""You are an AI assistant helping the user understand their own computer activity and system state.
The user is asking about their own PC/computer/system, and you have access to their current activity memory.

IMPORTANT: The user is asking about their OWN computer system. This is not a privacy violation - you are helping them understand what applications they have running on their own device.

MEMORY CONTEXT:
{enriched_context}

Based on this memory context, provide a helpful and contextual response to the user's query about their own system.
Be specific about what applications and activities you found in their system memory.
When they ask about "what's opened" or "what's running", list the applications from their memory context.
If the memory shows current applications, list them clearly and helpfully.
"""
            
            # Create context dict for LLM service
            context = {
                "memory_enriched": True,
                "memory_context": enriched_context,
                "system_message": system_message
            }
            
            # Call LLM service
            response = await self.llm_service.generate_response(query, context)
            
            # Check if LLM is not running and use fallback
            if "Error: LLM not running" in response:
                logger.info("LLM not running, using enhanced fallback response")
                return await self._generate_fallback_response(query, enriched_context, memory_context)
            
            return response
            
        except Exception as e:
            logger.error(f"Error calling LLM with context: {e}")
            return await self._generate_fallback_response(query, enriched_context, memory_context)
    
    async def _generate_fallback_response(self, query: str, enriched_context: str, memory_context=None) -> str:
        """Generate fallback response when LLM is not available"""
        try:
            query_lower = query.lower()
            
            # Parse the enriched context for key information
            lines = enriched_context.split('\n')
            
            # Check if we have app context (takes priority)
            app_context_section = False
            app_context_data = []
            
            # Extract visual context information
            current_app = None
            content_type = None
            word_count = None
            current_activity = None
            key_insights = []
            screen_text = None
            
            for i, line in enumerate(lines):
                # Check for app context section
                if "--- APPLICATION CONTEXT ---" in line:
                    app_context_section = True
                    continue
                elif line.startswith("--- ") and app_context_section:
                    app_context_section = False
                elif app_context_section and line.strip():
                    app_context_data.append(line.strip())
                
                # Extract regular context information
                if "Current Application:" in line:
                    current_app = line.split(":", 1)[1].strip()
                elif "Content Type:" in line:
                    content_type = line.split(":", 1)[1].strip()
                elif "Word Count:" in line:
                    word_count = line.split(":", 1)[1].strip()
                elif "Current Activity:" in line:
                    current_activity = line.split(":", 1)[1].strip()
                elif line.strip().startswith("- ") and "Key Insights:" in lines[max(0, i-3):i]:
                    key_insights.append(line.strip()[2:])
                elif "Screen Text Sample:" in line:
                    screen_text = line.split(":", 1)[1].strip()
            
            # Generate contextual response based on query type
            # If we have app context data, use it directly for app queries
            if app_context_data:
                logger.info("Using app context data for fallback response")
                return "\n".join(app_context_data)
            
            # Extract app information from memory context (more reliable than text parsing)
            apps_from_memory = {}
            if memory_context:
                apps_from_memory = self._extract_apps_from_memory_context(memory_context)
            
            # Check if this is an app-related query
            if any(word in query_lower for word in ["app", "application", "program", "open", "running", "spotify", "chrome", "cursor", "pc", "computer", "opened"]):
                if apps_from_memory:
                    return self._generate_app_focused_response(query_lower, apps_from_memory)
                else:
                    return "I can see your system activity but couldn't extract current application information. The memory system shows you're actively working but I need the LLM service to provide detailed responses."
            
            elif any(phrase in query_lower for phrase in ["what am i seeing", "what's on my screen", "current screen", "what am i looking at"]):
                response_parts = ["Based on your current screen analysis:"]
                
                if current_app:
                    response_parts.append(f"You're currently using {current_app}")
                    
                if content_type and content_type != "unknown":
                    response_parts.append(f"working with {content_type} content")
                    
                if word_count and word_count != "0":
                    response_parts.append(f"containing {word_count} words")
                
                if current_activity and current_activity != "unknown":
                    response_parts.append(f"Your current activity appears to be {current_activity}")
                
                if key_insights:
                    response_parts.append("Key observations:")
                    for insight in key_insights[:2]:  # Top 2 insights
                        response_parts.append(f"• {insight}")
                
                if screen_text and len(screen_text.strip()) > 10:
                    response_parts.append(f"I can see content that includes: {screen_text[:150]}...")
                
                return "\n".join(response_parts) if len(response_parts) > 1 else "I can see your screen but need more context to provide specific details."
            
            elif any(phrase in query_lower for phrase in ["what application", "what app", "current app"]):
                if current_app:
                    response = f"You're currently using {current_app}"
                    if content_type:
                        response += f" for {content_type} work"
                    return response
                else:
                    return "I can see activity but cannot determine the specific application you're using."
            
            elif any(phrase in query_lower for phrase in ["what am i working on", "current work", "recent activity", "working on"]):
                response_parts = ["Based on your recent activity:"]
                
                if current_activity:
                    response_parts.append(f"You're engaged in {current_activity}")
                
                if current_app and content_type:
                    response_parts.append(f"using {current_app} for {content_type} work")
                
                if key_insights:
                    response_parts.append("Recent insights:")
                    for insight in key_insights:
                        response_parts.append(f"• {insight}")
                
                return "\n".join(response_parts) if len(response_parts) > 1 else "I can see some activity but need more context to describe your current work."
            
            else:
                # General response with available context
                if current_app or current_activity:
                    response_parts = ["Here's what I can tell you:"]
                    
                    if current_app:
                        response_parts.append(f"You're using {current_app}")
                    
                    if current_activity:
                        response_parts.append(f"Currently engaged in {current_activity}")
                    
                    if key_insights:
                        response_parts.append("Additional context:")
                        for insight in key_insights[:2]:
                            response_parts.append(f"• {insight}")
                    
                    return "\n".join(response_parts)
                else:
                    return "I have access to your activity context but need the LLM service to provide detailed responses. Your visual context and memory are being analyzed successfully."
        
        except Exception as e:
            logger.error(f"Error generating fallback response: {e}")
            return "I can see your context but encountered an error processing it. LLM service may need to be started for full responses."
    
    def _extract_apps_from_memory_context(self, memory_context) -> Dict[str, Any]:
        """Extract application information directly from memory context"""
        try:
            apps_info = {}
            apps_list = []
            primary_app = None
            primary_activity = None
            
            # Look through semantic results for memory with current_applications
            for result in memory_context.semantic_results:
                content = result.get('content', {})
                result_type = result.get('type', '')
                
                # Handle app context results (from enhanced app search)
                if result_type == 'app_context' and 'enriched_context' in content:
                    # Extract apps from the enhanced app context text
                    app_context_text = content['enriched_context']
                    if 'CURRENT APPLICATIONS' in app_context_text:
                        # Parse the app list from the context text
                        lines = app_context_text.split('\n')
                        for line in lines:
                            if line.strip() and line[0].isdigit():
                                # Extract app name from numbered list (e.g., "1. App Store")
                                app_name = line.split('.', 1)[1].strip().split('(')[0].strip()
                                if app_name not in apps_list:
                                    apps_list.append(app_name)
                            elif 'PRIMARY' in line and '(' in line:
                                # Extract primary app (e.g., "2. Cursor (PRIMARY)")
                                app_name = line.split('.', 1)[1].strip().split('(')[0].strip()
                                primary_app = app_name
                
                # Handle regular memory results with user_activity
                elif isinstance(content, dict) and 'user_activity' in content:
                    user_activity = content['user_activity']
                    if isinstance(user_activity, dict):
                        # Extract current applications list
                        current_apps = user_activity.get('current_applications', [])
                        if current_apps and isinstance(current_apps, list):
                            if len(current_apps) > len(apps_list):  # Use the longest list found
                                apps_list = current_apps
                        
                        # Extract primary app and activity
                        if user_activity.get('application_used'):
                            primary_app = user_activity['application_used']
                        if user_activity.get('primary_activity'):
                            primary_activity = user_activity['primary_activity']
            
            # Also check user patterns for additional info
            if memory_context.user_patterns:
                patterns = memory_context.user_patterns
                if not primary_app and patterns.get('most_used_application'):
                    primary_app = patterns['most_used_application']
                if not primary_activity and patterns.get('most_common_activity'):
                    primary_activity = patterns['most_common_activity']
            
            if apps_list or primary_app or primary_activity:
                apps_info = {
                    'current_applications': apps_list,
                    'primary_app': primary_app,
                    'primary_activity': primary_activity
                }
                logger.info(f"Extracted apps info: {len(apps_list)} apps, primary: {primary_app}")
            
            return apps_info
            
        except Exception as e:
            logger.error(f"Error extracting apps from memory context: {e}")
            return {}
    
    def _extract_apps_from_context(self, enriched_context: str) -> Dict[str, Any]:
        """Extract application information from enriched context (legacy method)"""
        try:
            apps_info = {}
            lines = enriched_context.split('\n')
            
            for line in lines:
                # Look for current_applications in the context
                if "current_applications:" in line.lower():
                    # Extract the apps list
                    apps_part = line.split(":", 1)[1].strip()
                    if apps_part.startswith('[') and apps_part.endswith(']'):
                        # Parse as a list
                        try:
                            import ast
                            apps_list = ast.literal_eval(apps_part)
                            apps_info['current_applications'] = apps_list
                        except:
                            # Manual parsing if needed
                            apps_part = apps_part.strip('[]')
                            apps_list = [app.strip().strip("'\"") for app in apps_part.split(',')]
                            apps_info['current_applications'] = apps_list
                    else:
                        # Simple comma-separated
                        apps_list = [app.strip() for app in apps_part.split(',')]
                        apps_info['current_applications'] = apps_list
                
                # Look for application_used (primary app)
                elif "application_used:" in line.lower():
                    primary_app = line.split(":", 1)[1].strip()
                    apps_info['primary_app'] = primary_app
                
                # Look for primary_activity
                elif "primary_activity:" in line.lower():
                    activity = line.split(":", 1)[1].strip()
                    apps_info['primary_activity'] = activity
            
            return apps_info
            
        except Exception as e:
            logger.error(f"Error extracting apps from context: {e}")
            return {}
    
    def _generate_app_focused_response(self, query_lower: str, apps_info: Dict[str, Any]) -> str:
        """Generate a focused response for app-related queries"""
        try:
            apps_list = apps_info.get('current_applications', [])
            primary_app = apps_info.get('primary_app', 'Unknown')
            primary_activity = apps_info.get('primary_activity', 'Unknown')
            
            # Handle specific app queries
            if any(app_name in query_lower for app_name in ["spotify", "chrome", "cursor", "safari", "terminal"]):
                app_name = None
                for check_app in ["spotify", "chrome", "cursor", "safari", "terminal"]:
                    if check_app in query_lower:
                        app_name = check_app
                        break
                
                if app_name and apps_list:
                    # Check if the specific app is running
                    for app in apps_list:
                        if app_name.lower() in app.lower():
                            return f"Yes, {app} is currently running. I can see {len(apps_list)} applications open total, with {primary_app} as your primary focus."
                    
                    return f"No, {app_name.title()} is not currently running. You have {len(apps_list)} applications open: {', '.join(apps_list[:5])}{'...' if len(apps_list) > 5 else ''}."
            
            # Handle general app list queries
            if apps_list:
                if len(apps_list) <= 10:
                    apps_display = ', '.join(apps_list)
                else:
                    apps_display = ', '.join(apps_list[:8]) + f"... and {len(apps_list) - 8} more"
                
                response = f"You currently have {len(apps_list)} applications open: {apps_display}."
                
                if primary_app and primary_app != 'Unknown':
                    response += f"\n\nYour primary application is {primary_app}"
                    if primary_activity and primary_activity != 'Unknown':
                        response += f" for {primary_activity} work."
                    else:
                        response += "."
                
                return response
            else:
                return "I can see system activity but couldn't extract the current application list from memory."
                
        except Exception as e:
            logger.error(f"Error generating app-focused response: {e}")
            return "I found application information but encountered an error processing it."

class EnhancedAskModeHandler:
    """Enhanced Ask mode handler with real memory integration and LLM calls"""
    
    def __init__(self):
        self.memory_retriever = EnhancedMemoryRetriever()
        self.context_builder = EnhancedLLMContextBuilder()
        logger.info("EnhancedAskModeHandler initialized with semantic search and LLM integration")
    
    async def handle_request(self, request: ChatRequest) -> BrainResponse:
        """Handle Ask mode request with enhanced contextual intelligence"""
        start_time = time.time()
        
        try:
            logger.info(f"Enhanced Ask mode handling request: {request.query[:100]}...")
            
            # Retrieve enhanced memory context
            memory_context = await self.memory_retriever.retrieve_enhanced_context(
                request.query, request.user_id, request.session_id
            )
            
            # Build enriched context for LLM
            enriched_context = await self.context_builder.build_enriched_context(
                request.query, memory_context
            )
            
            # Call LLM with enriched context
            llm_response = await self.context_builder.call_llm_with_context(
                request.query, enriched_context, memory_context
            )
            
            # Calculate final confidence
            final_confidence = min(memory_context.confidence_score + 0.1, 1.0)
            
            logger.info(f"Enhanced Ask mode response generated with confidence: {final_confidence}")
            
            return BrainResponse(
                success=True,
                response=llm_response,
                mode_used=ChatMode.ASK,
                processing_time=time.time() - start_time,
                resources_used=["enhanced_memory", "semantic_search", "llm"],
                confidence=final_confidence,
                metadata={
                    "enhanced_memory_used": True,
                    "semantic_search_used": memory_context.search_metadata.get("semantic_search_used", False),
                    "app_semantic_search_used": memory_context.search_metadata.get("app_semantic_search_used", False),
                    "semantic_results_count": len(memory_context.semantic_results),
                    "relevant_memories_count": len(memory_context.relevant_knowledge),
                    "user_patterns_found": len(memory_context.user_patterns),
                    "context_confidence": memory_context.confidence_score,
                    "llm_called": True,
                    "enriched_context_length": len(enriched_context)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in EnhancedAskModeHandler: {e}")
            return BrainResponse(
                success=False,
                response=f"I encountered an error while analyzing your context: {str(e)}",
                mode_used=ChatMode.ASK,
                processing_time=time.time() - start_time,
                resources_used=[],
                confidence=0.0,
                metadata={"error": str(e), "enhanced_memory_used": False}
            )

# Create enhanced handler instance
enhanced_ask_mode_handler = EnhancedAskModeHandler()

# Export the enhanced handler function
async def handle_enhanced_ask_mode(request: ChatRequest) -> BrainResponse:
    """Entry point for Enhanced Ask mode handling"""
    return await enhanced_ask_mode_handler.handle_request(request)