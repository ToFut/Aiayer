"""
Suggest Mode Handler - Memory-Integrated Proactive Suggestions
Provides contextual suggestions based on user activity and memory analysis.
"""

import asyncio
import json
import time
import os
import sys
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta

from ..core.brain_router import BrainResponse, ChatRequest, ChatMode

# Import the enhanced ask mode components
try:
    from .enhanced_ask_mode_handler import (
        EnhancedMemoryRetriever, 
        EnhancedLLMContextBuilder,
        EnhancedMemoryContext
    )
    ENHANCED_ASK_AVAILABLE = True
except ImportError:
    ENHANCED_ASK_AVAILABLE = False

logger = logging.getLogger(__name__)

class SuggestModeAnalyzer:
    """Analyzes user context to generate proactive suggestions"""
    
    def __init__(self):
        self.suggestion_patterns = {
            'productivity': {
                'triggers': ['coding', 'development', 'programming', 'debugging'],
                'suggestions': [
                    "Take a short break to maintain focus",
                    "Consider reviewing your code for optimization opportunities",
                    "Document your current progress",
                    "Run tests to validate your changes"
                ]
            },
            'workflow': {
                'triggers': ['task', 'project', 'planning', 'organization'],
                'suggestions': [
                    "Break down large tasks into smaller steps",
                    "Set priorities for remaining work",
                    "Schedule time for code review",
                    "Update project documentation"
                ]
            },
            'learning': {
                'triggers': ['research', 'documentation', 'tutorial', 'learning'],
                'suggestions': [
                    "Take notes on key concepts",
                    "Try implementing what you've learned",
                    "Find related resources for deeper understanding",
                    "Share your learning with others"
                ]
            },
            'collaboration': {
                'triggers': ['team', 'meeting', 'review', 'communication'],
                'suggestions': [
                    "Prepare updates for your team",
                    "Schedule code review sessions",
                    "Document decisions and outcomes",
                    "Follow up on action items"
                ]
            }
        }
    
    async def analyze_for_suggestions(self, query: str, memory_context: EnhancedMemoryContext) -> Dict[str, Any]:
        """Analyze context to generate contextual suggestions"""
        try:
            suggestions = []
            analysis = {
                "query_intent": await self._determine_query_intent(query),
                "activity_patterns": await self._analyze_activity_patterns(memory_context),
                "suggestion_categories": [],
                "contextual_triggers": []
            }
            
            # Analyze query for suggestion triggers
            query_lower = query.lower()
            for category, pattern_data in self.suggestion_patterns.items():
                if any(trigger in query_lower for trigger in pattern_data['triggers']):
                    analysis["suggestion_categories"].append(category)
                    analysis["contextual_triggers"].extend(pattern_data['triggers'])
            
            # Analyze memory context for patterns
            if memory_context.user_patterns:
                most_common_activity = memory_context.user_patterns.get("most_common_activity", "")
                if most_common_activity:
                    analysis["primary_activity"] = most_common_activity
                    
                    # Generate activity-specific suggestions
                    for category, pattern_data in self.suggestion_patterns.items():
                        if any(trigger in most_common_activity.lower() for trigger in pattern_data['triggers']):
                            suggestions.extend(pattern_data['suggestions'])
            
            # Analyze recent activities for proactive suggestions
            if memory_context.semantic_results:
                recent_activities = []
                for result in memory_context.semantic_results[:3]:
                    if result.get('type') == 'short_term':
                        recent_activities.append(result.get('searchable_text', ''))
                
                analysis["recent_activities"] = recent_activities
                suggestions.extend(await self._generate_activity_based_suggestions(recent_activities))
            
            # Remove duplicates and limit suggestions
            unique_suggestions = list(dict.fromkeys(suggestions))[:5]
            analysis["suggestions"] = unique_suggestions
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing for suggestions: {e}")
            return {
                "error": str(e),
                "suggestions": ["Focus on your current task", "Take breaks when needed"]
            }
    
    async def _determine_query_intent(self, query: str) -> str:
        """Determine the intent behind the user's query"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['suggest', 'recommend', 'advice', 'help']):
            return "seeking_suggestions"
        elif any(word in query_lower for word in ['what', 'how', 'when', 'where']):
            return "seeking_information"
        elif any(word in query_lower for word in ['improve', 'optimize', 'better']):
            return "seeking_improvement"
        else:
            return "general_inquiry"
    
    async def _analyze_activity_patterns(self, memory_context: EnhancedMemoryContext) -> Dict[str, Any]:
        """Analyze user activity patterns for suggestions"""
        patterns = {}
        
        if memory_context.user_patterns:
            # Analyze productivity trends
            avg_productivity = memory_context.user_patterns.get("average_productivity", 0)
            if avg_productivity < 0.5:
                patterns["productivity_status"] = "low"
                patterns["productivity_suggestion"] = "Consider taking a break or changing your approach"
            elif avg_productivity > 0.8:
                patterns["productivity_status"] = "high"
                patterns["productivity_suggestion"] = "You're doing great! Keep up the momentum"
            else:
                patterns["productivity_status"] = "moderate"
                patterns["productivity_suggestion"] = "Good progress! Consider optimizing your workflow"
            
            # Analyze application usage
            most_used_app = memory_context.user_patterns.get("most_used_application", "")
            if most_used_app:
                patterns["primary_tool"] = most_used_app
                patterns["tool_suggestion"] = f"Consider exploring advanced features of {most_used_app}"
        
        return patterns
    
    async def _generate_activity_based_suggestions(self, activities: List[str]) -> List[str]:
        """Generate suggestions based on recent activities"""
        suggestions = []
        
        combined_activities = " ".join(activities).lower()
        
        # Code-related suggestions
        if any(word in combined_activities for word in ['code', 'programming', 'development']):
            suggestions.append("Consider running tests for your recent code changes")
            suggestions.append("Document any new functions or complex logic")
        
        # Research-related suggestions
        if any(word in combined_activities for word in ['research', 'documentation', 'reading']):
            suggestions.append("Take notes on key findings for future reference")
            suggestions.append("Consider implementing what you've learned")
        
        # Task management suggestions
        if any(word in combined_activities for word in ['task', 'planning', 'organization']):
            suggestions.append("Update your task priorities based on recent progress")
            suggestions.append("Schedule time for the next important task")
        
        return suggestions

class SuggestModeHandler:
    """Suggest mode handler with memory integration and proactive analysis"""
    
    def __init__(self):
        if ENHANCED_ASK_AVAILABLE:
            self.memory_retriever = EnhancedMemoryRetriever()
            self.context_builder = EnhancedLLMContextBuilder()
        else:
            self.memory_retriever = None
            self.context_builder = None
            
        self.suggestion_analyzer = SuggestModeAnalyzer()
        logger.info("SuggestModeHandler initialized with memory integration and proactive analysis")
    
    async def handle_request(self, request: ChatRequest) -> BrainResponse:
        """Handle Suggest mode request with contextual suggestions"""
        start_time = time.time()
        
        try:
            logger.info(f"Suggest mode handling request: {request.query[:100]}...")
            
            if not ENHANCED_ASK_AVAILABLE or not self.memory_retriever:
                return await self._fallback_suggest_response(request, start_time)
            
            # Retrieve enhanced memory context (same as ask mode)
            memory_context = await self.memory_retriever.retrieve_enhanced_context(
                request.query, request.user_id, request.session_id
            )
            
            # Analyze context for suggestions
            suggestion_analysis = await self.suggestion_analyzer.analyze_for_suggestions(
                request.query, memory_context
            )
            
            # Build suggest-specific context for LLM
            suggest_context = await self._build_suggest_context(
                request.query, memory_context, suggestion_analysis
            )
            
            # Call LLM with suggest-specific prompt
            llm_response = await self._call_llm_for_suggestions(
                request.query, suggest_context, suggestion_analysis
            )
            
            # Calculate confidence
            final_confidence = min(memory_context.confidence_score + 0.15, 1.0)  # Slightly higher for suggestions
            
            logger.info(f"Suggest mode response generated with confidence: {final_confidence}")
            
            return BrainResponse(
                success=True,
                response=llm_response,
                mode_used=ChatMode.SUGGEST,
                processing_time=time.time() - start_time,
                resources_used=["enhanced_memory", "semantic_search", "llm", "suggestion_analysis"],
                confidence=final_confidence,
                metadata={
                    "suggest_mode_used": True,
                    "memory_integrated": True,
                    "suggestion_categories": suggestion_analysis.get("suggestion_categories", []),
                    "suggestions_generated": len(suggestion_analysis.get("suggestions", [])),
                    "query_intent": suggestion_analysis.get("query_intent", "unknown"),
                    "semantic_results_count": len(memory_context.semantic_results),
                    "relevant_memories_count": len(memory_context.relevant_knowledge),
                    "context_confidence": memory_context.confidence_score
                }
            )
            
        except Exception as e:
            logger.error(f"Error in SuggestModeHandler: {e}")
            return BrainResponse(
                success=False,
                response=f"I encountered an error while generating suggestions: {str(e)}",
                mode_used=ChatMode.SUGGEST,
                processing_time=time.time() - start_time,
                resources_used=[],
                confidence=0.0,
                metadata={"error": str(e), "suggest_mode_used": False}
            )
    
    async def _build_suggest_context(self, query: str, memory_context: EnhancedMemoryContext, 
                                   suggestion_analysis: Dict[str, Any]) -> str:
        """Build context specifically for suggestion generation"""
        try:
            context_parts = []
            
            context_parts.append(f"User Query: {query}")
            context_parts.append(f"Query Intent: {suggestion_analysis.get('query_intent', 'unknown')}")
            
            # Add suggestion analysis
            if suggestion_analysis.get("suggestions"):
                context_parts.append("\n--- GENERATED SUGGESTIONS ---")
                for i, suggestion in enumerate(suggestion_analysis["suggestions"]):
                    context_parts.append(f"{i+1}. {suggestion}")
                context_parts.append("")
            
            # Add activity patterns for context
            if "activity_patterns" in suggestion_analysis:
                context_parts.append("\n--- ACTIVITY ANALYSIS ---")
                patterns = suggestion_analysis["activity_patterns"]
                for key, value in patterns.items():
                    context_parts.append(f"{key}: {value}")
                context_parts.append("")
            
            # Add recent memory insights
            if memory_context.semantic_results:
                context_parts.append("\n--- RECENT ACTIVITIES ---")
                for i, result in enumerate(memory_context.semantic_results[:2]):
                    context_parts.append(f"Activity {i+1}: {result.get('searchable_text', '')[:100]}")
                context_parts.append("")
            
            # Add user patterns
            if memory_context.user_patterns:
                context_parts.append("\n--- USER PATTERNS ---")
                for key, value in memory_context.user_patterns.items():
                    if key in ['most_common_activity', 'most_used_application', 'average_productivity']:
                        context_parts.append(f"{key}: {value}")
                context_parts.append("")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error building suggest context: {e}")
            return f"Error building context: {str(e)}"
    
    async def _call_llm_for_suggestions(self, query: str, suggest_context: str, 
                                      suggestion_analysis: Dict[str, Any]) -> str:
        """Call LLM with suggestion-specific prompt"""
        try:
            if not self.context_builder or not self.context_builder.llm_service:
                return await self._generate_fallback_suggestions(suggestion_analysis)
            
            # Build suggestion-specific system message
            system_message = f"""You are a proactive AI assistant that provides helpful suggestions based on user activity and context.

CONTEXT FOR SUGGESTIONS:
{suggest_context}

Your role is to:
1. Provide actionable, contextual suggestions based on the user's recent activities
2. Be proactive and helpful, focusing on productivity and workflow improvement
3. Reference specific activities or patterns you see in their memory
4. Offer 2-3 concrete, specific suggestions rather than generic advice
5. Be encouraging and supportive in your tone

Based on the context above, provide thoughtful suggestions that would be helpful for the user's current situation.
"""
            
            # Create context dict for LLM service
            context = {
                "memory_enriched": True,
                "suggestion_mode": True,
                "memory_context": suggest_context,
                "system_message": system_message
            }
            
            # Call LLM service
            response = await self.context_builder.call_llm_with_context(query, context)
            
            # Check if LLM is not running and use enhanced fallback
            if "Error: LLM not running" in response:
                logger.info("LLM not running, using enhanced suggestion fallback")
                return await self._generate_enhanced_fallback_suggestions(suggestion_analysis, suggest_context)
            
            return response
            
        except Exception as e:
            logger.error(f"Error calling LLM for suggestions: {e}")
            return await self._generate_fallback_suggestions(suggestion_analysis)
    
    async def _generate_fallback_suggestions(self, suggestion_analysis: Dict[str, Any]) -> str:
        """Generate fallback suggestions when LLM is not available"""
        try:
            suggestions = suggestion_analysis.get("suggestions", [])
            
            if suggestions:
                response_parts = ["Here are some suggestions based on your recent activity:"]
                for i, suggestion in enumerate(suggestions[:3], 1):
                    response_parts.append(f"{i}. {suggestion}")
                
                # Add context if available
                if "activity_patterns" in suggestion_analysis:
                    patterns = suggestion_analysis["activity_patterns"]
                    if "productivity_status" in patterns:
                        response_parts.append(f"\nYour current productivity is {patterns['productivity_status']}.")
                
                return "\n".join(response_parts)
            else:
                return "Consider taking a moment to review your current priorities and plan your next steps."
                
        except Exception as e:
            logger.error(f"Error generating fallback suggestions: {e}")
            return "I'd suggest taking a break and coming back to your work with fresh perspective."
    
    async def _generate_enhanced_fallback_suggestions(self, suggestion_analysis: Dict[str, Any], suggest_context: str) -> str:
        """Generate enhanced fallback suggestions using visual context"""
        try:
            # Parse visual context from suggest_context
            lines = suggest_context.split('\n')
            
            current_app = None
            content_type = None
            current_activity = None
            suggestions = suggestion_analysis.get("suggestions", [])
            query_intent = suggestion_analysis.get("query_intent", "unknown")
            
            for line in lines:
                if "Current Application:" in line:
                    current_app = line.split(":", 1)[1].strip()
                elif "Content Type:" in line:
                    content_type = line.split(":", 1)[1].strip()
                elif "Current Activity:" in line:
                    current_activity = line.split(":", 1)[1].strip()
            
            # Generate contextual suggestions
            response_parts = ["Here are some contextual suggestions:"]
            
            # Add app-specific suggestions
            if current_app == "Cursor" and content_type == "code":
                response_parts.extend([
                    "• Consider running tests on your current code",
                    "• Take a quick break to maintain focus while coding",
                    "• Document any complex logic you've just written",
                    "• Review your code for optimization opportunities"
                ])
            elif current_activity == "general_computing":
                response_parts.extend([
                    "• Organize your current work into clear next steps",
                    "• Consider what task would be most productive right now",
                    "• Take a moment to plan your workflow",
                    "• Focus on one task at a time for better productivity"
                ])
            
            # Add general suggestions from analysis
            if suggestions:
                response_parts.append("\nAdditional suggestions based on your patterns:")
                for suggestion in suggestions[:3]:
                    response_parts.append(f"• {suggestion}")
            
            # Add intent-specific advice
            if query_intent == "seeking_suggestions":
                if current_app:
                    response_parts.append(f"\nSince you're using {current_app}, focus on maximizing your productivity within this tool.")
            
            return "\n".join(response_parts) if len(response_parts) > 1 else "Focus on your current task and take breaks when needed."
            
        except Exception as e:
            logger.error(f"Error generating enhanced fallback suggestions: {e}")
            return await self._generate_fallback_suggestions(suggestion_analysis)
    
    async def _fallback_suggest_response(self, request: ChatRequest, start_time: float) -> BrainResponse:
        """Fallback response when enhanced components are not available"""
        response = "I'd be happy to provide suggestions, but the enhanced memory system is not fully available. Consider reviewing your current tasks and taking breaks as needed."
        
        return BrainResponse(
            success=True,
            response=response,
            mode_used=ChatMode.SUGGEST,
            processing_time=time.time() - start_time,
            resources_used=["basic_suggestion"],
            confidence=0.5,
            metadata={"fallback_mode": True, "enhanced_memory_available": False}
        )

# Create handler instance
suggest_mode_handler = SuggestModeHandler()

# Export the handler function
async def handle_suggest_mode(request: ChatRequest) -> BrainResponse:
    """Entry point for Suggest mode handling"""
    return await suggest_mode_handler.handle_request(request)