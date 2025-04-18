"""
Task Agent Module
Provides intelligent task handling and context-aware assistance using local AI models.
"""
import logging
import asyncio
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from threading import Thread, Event
import json
from unittest.mock import MagicMock
import re

from llm.model import LocalLLM
from memory.memory import ConversationMemory
from agent.data_filter import DataFilter
from agent.context_analyzer import ContextAnalyzer, ContextInsight
from agent.overlay_bridge import OverlayBridge

class TaskAgent:
    """
    Intelligent task agent that provides context-aware assistance using local AI models.
    """
    
    def __init__(self, sensors: Dict, llm: LocalLLM, memory: ConversationMemory, 
                 data_filter: DataFilter, context_analyzer: ContextAnalyzer, 
                 overlay_bridge: Optional[OverlayBridge] = None):
        """
        Initialize the task agent.
        
        Args:
            sensors: Dictionary of sensor instances
            llm: Local language model instance
            memory: Conversation memory instance
            data_filter: Data filter instance
            context_analyzer: Context analyzer instance
            overlay_bridge: Optional existing bridge instance to use
        """
        self._sensors = sensors
        self._llm = llm
        self._memory = memory
        self._data_filter = data_filter
        self._context_analyzer = context_analyzer
        self._logger = logging.getLogger(__name__)
        self._context_update_event = Event()
        self._context_update_thread = None
        self._last_context: Optional[ContextInsight] = None
        self._last_context_time: Optional[datetime] = None
        self._context_update_interval = 30  # seconds
        self._last_insights = []  # Store recent context insights to share with user
        self._user_query_count = 0
        
        # Initialize overlay bridge - reuse existing bridge if provided
        if overlay_bridge:
            self._logger.info("Using existing overlay bridge")
            self.overlay_bridge = overlay_bridge
        else:
            # Import here to avoid circular import
            from main_with_overlay import get_global_bridge
            try:
                self.overlay_bridge = get_global_bridge(port=8765)
                self._logger.info("Using global bridge from main module")
            except (ImportError, NameError):
                self._logger.info("Creating new overlay bridge instance")
                self.overlay_bridge = OverlayBridge(port=8765)
                self.overlay_bridge.start()
        
        # Register callback for user interactions
        self.overlay_bridge.register_callback(
            'user_interaction', 
            self._handle_overlay_interaction
        )
        
        # Register callback for transformation requests
        self.overlay_bridge.register_callback(
            'transform_request',
            self._handle_transform_request
        )
        
        # Register callback for heartbeats to provide continuous status updates
        self.overlay_bridge.register_callback(
            'heartbeat',
            self._handle_heartbeat
        )
        
        # Get initial context synchronously if not using mocks
        if not isinstance(self._context_analyzer, MagicMock):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                self._last_context = loop.run_until_complete(self._context_analyzer.analyze_context())
                self._last_context_time = datetime.now()
            except Exception as e:
                self._logger.error(f"Error getting initial context: {e}")
            finally:
                loop.close()
        
        # Start context update thread
        self._start_context_updates()
        
    def _start_context_updates(self):
        """Start the background thread for context updates."""
        def update_context():
            while not self._context_update_event.is_set():
                try:
                    # Create a new event loop for this thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # Run the context analysis
                    self._last_context = loop.run_until_complete(
                        self._context_analyzer.analyze_context()
                    )
                    self._last_context_time = datetime.now()
                    
                    # Clean up the event loop
                    loop.close()
                except Exception as e:
                    self._logger.error(f"Error updating context: {e}")
                    # Ensure loop is closed even if there's an error
                    try:
                        loop.close()
                    except:
                        pass
                finally:
                    # Wait for the next update interval
                    self._context_update_event.wait(self._context_update_interval)
        
        # Only start thread if not using mocks
        if not isinstance(self._context_analyzer, MagicMock):
            self._context_update_thread = Thread(target=update_context, daemon=True)
            self._context_update_thread.start()
        
    async def stop(self):
        """Stop the context update thread."""
        if self._context_update_thread:
            self._context_update_event.set()
            self._context_update_thread.join()
            # Only call stop() if it's a real LLM instance
            if not isinstance(self._llm, MagicMock):
                await self._llm.stop()
            self._context_update_thread = None
            
    def _build_context_messages(self) -> List[Dict[str, str]]:
        """Build messages with current context for the LLM."""
        messages = []
        
        # Add system message with context awareness
        if self._last_context:
            context_age = (datetime.now() - self._last_context_time).total_seconds() if self._last_context_time else 0
            if context_age < 300:  # Only use context if less than 5 minutes old
                messages.append({
                    "role": "system",
                    "content": f"""Current Context:
Activity: {self._last_context.current_activity}
Summary: {self._last_context.context_summary}
Potential Needs: {', '.join(self._last_context.potential_needs)}
Attention Level: {self._last_context.attention_level}
Confidence: {self._last_context.confidence_score:.2f}"""
                })
        
        # Add conversation history
        messages.extend(self._memory.get_recent())
        
        return messages
        
    async def get_context_age(self) -> float:
        """Get the age of the current context in seconds."""
        if not self._last_context:
            return float('inf')
        return time.time() - self._last_context.timestamp

    async def _build_conversation(self, query: str, context: Optional[ContextInsight], 
                             enhanced_context: Optional[dict] = None) -> List[Dict[str, str]]:
        """Build conversation messages with context and screen data if available."""
        messages = []
        
        # Add system message with context
        system_message = "You are a helpful AI assistant with access to the user's screen content through sensors. "
        
        # Add base context
        if context:
            system_message += f"Current context: {context.context_summary}. "
        
        # Add detailed instructions for screen-related queries
        if enhanced_context and self._is_screen_related_query(query):
            system_message += """
You have access to the text content of the user's screen through OCR. When answering questions about what's on the screen,
use this information to give detailed, helpful responses. Describe what the user is seeing clearly and accurately.

Guidelines for screen-related questions:
1. Focus on the most relevant parts of the screen content for the user's query
2. Be specific about what you see - mention app names, window titles, visible text
3. If there are images or videos detected, mention their presence but don't try to describe their contents
4. If the user asks "what am I looking at" or similar questions, give a complete summary of the screen
5. Suggest relevant actions based on what's on the screen
6. Note that OCR may not be perfect, so acknowledge any uncertainty

Based on the screen content, suggest relevant actions the user might want to take.
"""
        
        messages.append({"role": "system", "content": system_message})
        
        # Add screen content as a separate system message if available
        if enhanced_context and "screen_text" in enhanced_context:
            screen_content = enhanced_context["screen_text"]
            
            # Truncate if too long
            if len(screen_content) > 2000:
                screen_content = screen_content[:2000] + "... [screen content truncated]"
                
            app_info = ""
            if enhanced_context.get("active_app"):
                app_info = f"\nActive application: {enhanced_context.get('active_app')}"
            if enhanced_context.get("window_title"):
                app_info += f"\nWindow title: {enhanced_context.get('window_title')}"
                
            media_info = ""
            if enhanced_context.get("has_images"):
                media_info += "\nImages detected on screen: Yes"
            if enhanced_context.get("has_videos"):
                media_info += "\nVideos detected on screen: Yes"
                
            screen_message = f"""Current screen content detected via OCR:{app_info}{media_info}

SCREEN TEXT:
{screen_content}
"""
            messages.append({"role": "system", "content": screen_message})
        
        # Add conversation history
        if self._memory:
            history = self._memory.get_recent()
            messages.extend(history)
        
        # Add current query
        messages.append({"role": "user", "content": query})
        
        return messages

    async def _handle_heartbeat(self, payload):
        """Handle heartbeat messages from the overlay"""
        try:
            # Get basic system status
            llm_status = "ready" if self._llm else "unavailable"
            sensor_status = {name: "active" for name in self._sensors}
            
            # Only send context update occasionally to avoid overloading the UI
            should_send_context = False
            if not hasattr(self, '_last_heartbeat_context_time'):
                self._last_heartbeat_context_time = 0
            
            # Send context every 10 seconds
            if time.time() - self._last_heartbeat_context_time > 10:
                should_send_context = True
                self._last_heartbeat_context_time = time.time()
            
            # Respond to heartbeat with system status
            await self.overlay_bridge.send_message('heartbeat', {
                'server_time': time.time(),
                'backend_connected': True,
                'system_status': {
                    'llm': llm_status,
                    'sensors': sensor_status,
                    'memory': len(self._memory.get_recent()) if self._memory else 0,
                    'context_analyzer': "active" if self._last_context else "initializing"
                }
            })
            
            # Share context insights occasionally
            if should_send_context and self._last_context:
                # Send current context to the overlay
                await self.overlay_bridge.send_context_update({
                    'activity': self._last_context.current_activity,
                    'summary': self._last_context.context_summary,
                    'needs': self._last_context.potential_needs[:3],
                    'attention_level': self._last_context.attention_level,
                    'timestamp': time.time()
                })
                
                # Check if there are insights to share
                if (self._user_query_count < 1 or len(self._last_insights) > 0) and self._last_context and hasattr(self._last_context, 'semantic_understanding'):
                    # Share a proactive insight
                    insight = {
                        'type': 'context_insight',
                        'insight': self._get_proactive_insight(),
                        'source': 'AI Assistant',
                        'timestamp': time.time(),
                        'context': {
                            'activity': self._last_context.current_activity,
                            'summary': self._last_context.context_summary[:100] + '...' if len(self._last_context.context_summary) > 100 else self._last_context.context_summary
                        }
                    }
                    
                    # Only send if we have valid data
                    if insight['insight']:
                        await self.overlay_bridge.add_system_activity('insight', insight)
        except Exception as e:
            self._logger.error(f"Error handling heartbeat: {e}")
    
    def _get_proactive_insight(self):
        """Generate a proactive insight based on current context"""
        if not self._last_context:
            return None
            
        insights = []
        
        # Add insights about user activity
        if self._last_context.current_activity and self._last_context.current_activity != "Unknown":
            if hasattr(self._last_context, 'semantic_understanding'):
                semantic = self._last_context.semantic_understanding
                
                # Check for challenges
                if 'challenges' in semantic and semantic['challenges']:
                    challenges = semantic['challenges']
                    if isinstance(challenges, list) and len(challenges) > 0:
                        insights.append(f"I notice you might be working on overcoming {challenges[0].lower()}. I can help with strategies for that.")
                    elif isinstance(challenges, str):
                        insights.append(f"I notice you might be working on overcoming {challenges.lower()}. I can help with strategies for that.")
                
                # Check for workflow recommendations
                if 'workflow' in semantic and semantic['workflow']:
                    insights.append(f"Based on your activity, I could suggest some workflow improvements for {self._last_context.current_activity.lower()}.")
                
                # Check for implicit goals
                if 'implicit_goals' in semantic and semantic['implicit_goals']:
                    goals = semantic['implicit_goals']
                    if isinstance(goals, list) and len(goals) > 0:
                        insights.append(f"It looks like you're working toward {goals[0].lower()}. I can offer assistance with that.")
                    elif isinstance(goals, str):
                        insights.append(f"It looks like you're working toward {goals.lower()}. I can offer assistance with that.")
        
        # Add insights about sensor data
        if 'screen' in self._sensors and hasattr(self._sensors['screen'], 'latest_text'):
            text = self._sensors['screen'].latest_text
            if text and len(text) > 100:
                # Look for TODO patterns
                if "todo" in text.lower() or "to do" in text.lower():
                    insights.append("I noticed you have some TODOs on screen. Would you like me to help track or prioritize them?")
                
                # Look for code patterns
                if "{" in text and "}" in text or "def " in text or "function" in text:
                    insights.append("I see you're working with code. I can help explain, refactor, or optimize it if needed.")
                    
                # Look for data patterns
                if ("data" in text.lower() and ("analysis" in text.lower() or "visualization" in text.lower())):
                    insights.append("I notice you're working with data. I can help with analysis approaches or visualization techniques.")
        
        # Store insights for rotation
        if insights:
            # Add to our insights queue if new
            for insight in insights:
                if insight not in self._last_insights:
                    self._last_insights.append(insight)
            
            # Keep the list manageable
            if len(self._last_insights) > 10:
                self._last_insights = self._last_insights[-10:]
            
            # Return one insight (rotating through them)
            if not hasattr(self, '_insight_index'):
                self._insight_index = 0
            else:
                self._insight_index = (self._insight_index + 1) % len(self._last_insights)
            
            return self._last_insights[self._insight_index]
            
        return None

    async def handle_query(self, query: str) -> str:
        """Handle a user query with context awareness."""
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")
            
        if not query.strip():
            raise ValueError("Query cannot be empty")
        
        # Increment query counter for tracking user interaction frequency
        self._user_query_count += 1

        try:
            # Send immediate typing indicator 
            await self.overlay_bridge.send_message('query_status', {
                'status': 'processing',
                'query': query
            })
            
            # Get current context
            context = await self.get_current_context()
            
            # Check if this is a screen-related query
            screen_related = self._is_screen_related_query(query)
            
            # If screen related, gather detailed screen data
            enhanced_context = None
            if screen_related:
                self._logger.info("Detected screen-related query, gathering screen data")
                enhanced_context = await self._gather_screen_data()
                
                # Let the user know we're processing screen data
                await self.overlay_bridge.send_message('query_status', {
                    'status': 'processing',
                    'message': 'Analyzing your screen content...',
                    'query': query
                })
            
            # Share context analysis with the user if appropriate
            if context and self._user_query_count % 3 == 1:  # Share insights every 3rd query
                await self.overlay_bridge.send_context_update({
                    'activity': context.current_activity,
                    'summary': context.context_summary,
                    'needs': context.potential_needs[:3] if hasattr(context, 'potential_needs') else [],
                    'attention_level': context.attention_level,
                    'timestamp': time.time()
                })
            
            # Build conversation messages with enhanced context
            messages = await self._build_conversation(query, context, enhanced_context)
            
            # Generate response
            try:
                # Set a timeout for the LLM response
                response_task = asyncio.create_task(self._llm.generate_response(messages))
                response = await asyncio.wait_for(response_task, timeout=30.0)  # 30 second timeout
            except asyncio.TimeoutError:
                self._logger.warning("LLM response timed out after 30 seconds")
                response = "I apologize, but it's taking me longer than expected to process your request. Let me try again with a simpler approach."
                
                # Try again with a simplified prompt
                simple_messages = [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": query}
                ]
                response = await self._llm.generate_response(simple_messages)
            
            # Create a cleaner response for the chat
            clean_response = response
            if isinstance(response, str) and len(response) > 100:
                # Keep it clean for the UI without all the context markers
                clean_response = response.replace("[Context Analysis]\n", "").replace("[Semantic Understanding]\n", "")
                if "[Response]\n" in clean_response:
                    clean_response = clean_response.split("[Response]\n", 1)[1]
            
            # Add to memory (synchronous operation)
            self._memory.add_message({"role": "user", "content": query})
            self._memory.add_message({"role": "assistant", "content": clean_response})
            
            # Store interaction in knowledge base if available
            try:
                from memory.knowledge_base import KnowledgeBase
                kb = KnowledgeBase()
                kb.store(
                    f"interaction_{int(time.time())}", 
                    {
                        "query": query,
                        "response": clean_response,
                        "context": {
                            "activity": context.current_activity,
                            "summary": context.context_summary,
                            "screen_content": enhanced_context.get("screen_text", "") if enhanced_context else ""
                        }
                    },
                    category="user_interactions"
                )
            except Exception as kb_err:
                self._logger.warning(f"Failed to store in knowledge base: {kb_err}")
            
            # Create suggestions based on the query and response
            suggestions = self._generate_suggestions(query, clean_response, context, enhanced_context)
            
            # Format response with context but send a cleaner version to the UI
            formatted_response = self._format_response(response, context, query)
            
            # Send response to client (most important part)
            self._logger.info(f"Sending response: {clean_response[:100]}...")
            
            # Send as chat_response format first (what the widget actually displays)
            chat_resp_success = await self.overlay_bridge.send_message('chat_response', {
                'text': clean_response,
                'timestamp': time.time()
            })
            
            self._logger.info(f"chat_response message sent successfully: {chat_resp_success}")
            
            # Also send as query_response format (alternative format)
            query_resp_success = await self.overlay_bridge.send_message('query_response', {
                'query': query,
                'response': clean_response,
                'timestamp': time.time()
            })
            
            self._logger.info(f"query_response message sent successfully: {query_resp_success}")
            
            # If both sends failed, try one more time with a delay
            if not chat_resp_success and not query_resp_success:
                self._logger.warning("Both response sends failed, trying again after delay...")
                await asyncio.sleep(0.5)  # Short delay
                await self.overlay_bridge.send_message('chat_response', {
                    'text': clean_response,
                    'timestamp': time.time()
                })
            
            # Send suggestions through overlay bridge
            await self.overlay_bridge.add_system_activity("suggestion", {
                "query": query,
                "suggestion": suggestions[0] if suggestions else "Would you like me to help with anything else?",
                "all_suggestions": suggestions
            })
            
            # Send completion status to overlay
            await self.overlay_bridge.send_message('query_status', {
                'status': 'complete',
                'query': query
            })
            
            return clean_response
        except Exception as e:
            self._logger.error(f"Error handling query: {e}")
            await self.overlay_bridge.send_message('query_status', {
                'status': 'error',
                'message': str(e)
            })
            
            # Try to save the interaction even if something failed
            try:
                self._memory.add_message({"role": "user", "content": query})
                self._memory.add_message({"role": "assistant", "content": f"Error: {str(e)}"})
            except:
                pass
                
            return f"Error processing your request: {str(e)}"

    def _is_screen_related_query(self, query: str) -> bool:
        """Determine if the query is related to the screen content."""
        screen_keywords = [
            "screen", "see", "seeing", "looking at", "display", "showing", 
            "what's on", "what is on", "what am i", "looking", "view", "visible",
            "window", "app", "application", "interface", "ui", "showing"
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in screen_keywords)
        
    async def _gather_screen_data(self) -> dict:
        """Gather detailed data from screen sensor."""
        screen_data = {}
        
        try:
            if 'screen' in self._sensors:
                # Get fresh screen capture
                screen_sensor = self._sensors['screen']
                latest_text = screen_sensor.capture()
                screen_data["screen_text"] = latest_text
                screen_data["has_images"] = screen_sensor.has_images
                screen_data["has_videos"] = screen_sensor.has_videos
                
                # Add process information if available
                if 'process' in self._sensors:
                    process_sensor = self._sensors['process']
                    screen_data["active_app"] = process_sensor.active_app
                    screen_data["window_title"] = process_sensor.active_window_title
                    
                self._logger.info(f"Gathered screen data: {len(latest_text)} chars of text, "
                                 f"images: {screen_data.get('has_images')}, "
                                 f"videos: {screen_data.get('has_videos')}")
        except Exception as e:
            self._logger.error(f"Error gathering screen data: {e}")
            
        return screen_data
            
    def _generate_suggestions(self, query: str, response: str, context: ContextInsight, 
                          enhanced_context: Optional[dict] = None) -> List[str]:
        """Generate contextual suggestions based on the query and response."""
        suggestions = []
        
        # Screen-specific suggestions if this was a screen-related query
        if self._is_screen_related_query(query) and enhanced_context:
            # Check if there's an active app and add suggestions based on it
            app = enhanced_context.get("active_app", "")
            if app:
                suggestions.append(f"Tell me more about what I can do in {app}")
                
                # App-specific suggestions
                if "code" in app.lower() or "editor" in app.lower():
                    suggestions.append("Can you explain what this code does?")
                    suggestions.append("How can I improve this code?")
                elif "browser" in app.lower():
                    suggestions.append("Can you summarize this webpage for me?")
                    suggestions.append("What are the key points of this article?")
                elif "excel" in app.lower() or "sheets" in app.lower():
                    suggestions.append("How can I optimize this spreadsheet?")
                    suggestions.append("Can you suggest a formula for this data?")
                elif "terminal" in app.lower() or "command" in app.lower():
                    suggestions.append("What command should I use for this task?")
                    suggestions.append("Can you explain this terminal output?")
                elif "presentation" in app.lower() or "slides" in app.lower() or "powerpoint" in app.lower():
                    suggestions.append("How can I improve this slide?")
                    suggestions.append("Can you suggest content for my next slide?")
                    
            # Check if there's text about knowledge or TODOs visible
            if enhanced_context.get("screen_text"):
                screen_text = enhanced_context["screen_text"].lower()
                
                if "todo" in screen_text:
                    suggestions.append("Can you help me prioritize these TODOs?")
                    
                if "technology" in screen_text or "model" in screen_text:
                    suggestions.append("Can you explain these technologies to me?")
                    
                if "storage" in screen_text or "database" in screen_text:
                    suggestions.append("What are best practices for data storage?")
                    
                if "encryption" in screen_text or "secure" in screen_text:
                    suggestions.append("How can I ensure this data is secure?")
                    
                # If there's any code-like structure visible
                if "{" in screen_text and "}" in screen_text or "def " in screen_text:
                    suggestions.append("Can you explain this code pattern?")
                
            # Add general screen-related suggestions
            suggestions.append("What else can you tell me about my screen?")
            suggestions.append("Can you help me organize what I'm seeing?")
        
        # If we already have enough screen-specific suggestions, return those
        if len(suggestions) >= 3:
            return suggestions[:3]
        
        # Add suggestion based on current activity
        if context and context.current_activity and context.current_activity != "Unknown":
            suggestions.append(f"I can help you more with {context.current_activity.lower()}")
        
        # Add suggestions from context needs
        if context and context.potential_needs:
            for need in context.potential_needs[:2]:  # Only use top 2 needs
                if need and len(need) > 3:  # Simple validation
                    suggestions.append(f"Would you like help with {need.lower()}?")
        
        # Generate suggestion based on the app being used if not already done
        if not self._is_screen_related_query(query) and 'process' in self._sensors and hasattr(self._sensors['process'], 'active_app'):
            app = self._sensors['process'].active_app
            if app:
                if "code" in app.lower() or "editor" in app.lower():
                    suggestions.append("I can help explain or optimize this code")
                elif "browser" in app.lower():
                    suggestions.append("I can summarize this webpage content")
                elif "excel" in app.lower() or "sheets" in app.lower():
                    suggestions.append("I can help with formulas or data analysis")
        
        # Default suggestions if we don't have enough
        if len(suggestions) < 2:
            suggestions.append("Ask me to explain this in more detail")
            suggestions.append("How can I help you with your current task?")
            
        return suggestions[:3]  # Limit to top 3 suggestions

    def _format_response(self, response: str, context: ContextInsight, query: str) -> str:
        """Format the response with context analysis."""
        formatted = "[Context Analysis]\n"
        formatted += f"- Current Activity: {context.current_activity}\n"
        formatted += f"- Context Summary: {context.context_summary}\n"
        formatted += f"- Potential Needs: {context.potential_needs}\n"
        formatted += f"- Attention Level: {context.attention_level}\n\n"
        
        formatted += "[Semantic Understanding]\n"
        formatted += f"- Task Purpose: {context.semantic_understanding.get('task_purpose', 'N/A')}\n"
        formatted += f"- Workflow: {context.semantic_understanding.get('workflow', 'N/A')}\n"
        formatted += f"- Challenges: {context.semantic_understanding.get('challenges', '')}\n"
        formatted += f"- Related Concepts: {context.semantic_understanding.get('related_concepts', '')}\n"
        formatted += f"- Implicit Goals: {context.semantic_understanding.get('implicit_goals', '')}\n\n"
        
        formatted += "[Query]\n"
        formatted += query + "\n\n"
        
        formatted += "[Response]\n"
        formatted += response
        
        # Add conversation history if available
        if self._memory:
            history = self._memory.get_recent()
            if history:
                formatted += "\n\n[Conversation History]\n"
                for msg in history[-5:]:  # Show last 5 messages
                    formatted += f"{msg['role']}: {msg['content']}\n"
        
        return formatted
        
    async def get_current_context(self) -> Optional[ContextInsight]:
        """Get the current context analysis."""
        try:
            if not self._last_context or (datetime.now() - self._last_context_time).total_seconds() > 30:
                # Create a new event loop for this operation
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    self._last_context = await self._context_analyzer.analyze_context()
                    self._last_context_time = datetime.now()
                finally:
                    loop.close()
            return self._last_context
        except Exception as e:
            self._logger.error(f"Error getting current context: {e}")
            # Return a default context if there's an error
            return ContextInsight(
                current_activity="Unknown",
                context_summary="Error analyzing context",
                potential_needs=[],
                attention_level="medium",
                confidence_score=0.0,
                source_model="error",
                semantic_understanding={
                    "purpose": "Error in context analysis",
                    "workflow": "Error in context analysis",
                    "challenges": ["Context analysis error"],
                    "related_concepts": [],
                    "implicit_goals": []
                }
            )

    @property
    def llm(self) -> LocalLLM:
        """Get the LLM instance."""
        return self._llm

    async def _handle_overlay_interaction(self, interaction_data):
        """Handle user interaction from the overlay"""
        try:
            self._logger.info(f"Handling overlay interaction: {interaction_data}")
            
            if interaction_data.get('type') == 'query':
                # User asked a question through the overlay (original format)
                query = interaction_data.get('query', '')
                self._logger.info(f"Processing query: {query}")
                
                # Notify that we're thinking - important to use a direct message here
                thinking_sent = await self.overlay_bridge.send_message('query_status', {
                    'status': 'processing',
                    'query': query,
                    'message': 'Thinking...',
                    'timestamp': time.time()
                })
                
                self._logger.info(f"Thinking status sent: {thinking_sent}")
                
                # For better UI feedback, also send a typing chat message
                await self.overlay_bridge.send_message('chat_response', {
                    'text': '...',
                    'isTyping': True,
                    'timestamp': time.time()
                })
                
                # Generate response through the main handler
                response = await self.handle_query(query)
                self._logger.info(f"Query handled, response length: {len(response) if response else 0}")
                
            elif interaction_data.get('type') == 'chat_message' and 'text' in interaction_data.get('data', {}):
                # User sent a message in the chat format
                query = interaction_data['data']['text']
                self._logger.info(f"Processing chat message: {query}")
                
                # Notify that we're thinking - important to use a direct message here
                thinking_sent = await self.overlay_bridge.send_message('query_status', {
                    'status': 'processing',
                    'query': query,
                    'message': 'Thinking...',
                    'timestamp': time.time()
                })
                
                self._logger.info(f"Thinking status sent: {thinking_sent}")
                
                # For better UI feedback, also send a typing chat message
                await self.overlay_bridge.send_message('chat_response', {
                    'text': '...',
                    'isTyping': True,
                    'timestamp': time.time()
                })
                
                # Generate response through the main handler
                response = await self.handle_query(query)
                self._logger.info(f"Chat message handled, response length: {len(response) if response else 0}")
                
            elif interaction_data.get('type') == 'action':
                # Handle specific actions from overlay
                await self._handle_overlay_action(interaction_data)
            else:
                self._logger.warning(f"Unknown interaction type: {interaction_data.get('type')}")
                
        except Exception as e:
            self._logger.error(f"Error handling overlay interaction: {e}")
            # Send error status - important to use a direct message
            await self.overlay_bridge.send_message('query_status', {
                'status': 'error',
                'message': str(e),
                'timestamp': time.time()
            })
            
            # Also send an error message in chat format
            await self.overlay_bridge.send_message('chat_response', {
                'text': f"I'm sorry, I encountered an error: {str(e)}",
                'isError': True,
                'timestamp': time.time()
            })
    
    async def _handle_transform_request(self, request_data):
        """Handle interface transformation request"""
        try:
            # Get current screen content
            screen_text = self._sensors['screen'].latest_text if 'screen' in self._sensors else "No screen data available"
            
            # Get information about active application
            active_app = self._sensors['process'].active_app if 'process' in self._sensors else "Unknown"
            window_title = self._sensors['process'].active_window_title if 'process' in self._sensors else "Unknown"
            
            # Create transformation prompt with better LLM instructions
            system_prompt = """You are an expert UI transformer that simplifies complex interfaces. Your task is to:

1. Analyze the given screen content and identify UI elements
2. Create a simplified, more usable interface based on the content
3. Generate a layout of UI elements that can be rendered on top of the original interface
4. Return your transformation as structured JSON

Your response MUST follow this exact format:
```json
{
  "layout": {
    "elements": [
      {
        "id": "unique_id",
        "type": "button|text|rectangle",
        "bounds": {"x": 100, "y": 100, "width": 200, "height": 50},
        "content": "Label or text",
        "style": {
          "backgroundColor": "rgba(255,255,255,0.9)",
          "color": "#333",
          "borderRadius": "4px"
        }
      }
    ]
  },
  "interactionMap": {
    "unique_id": {
      "action": "click|hover|focus",
      "target": "element_to_interact_with",
      "data": {}
    }
  },
  "metadata": {
    "purpose": "Brief explanation of transformation purpose",
    "originalElements": 10,
    "transformedElements": 5
  }
}
```

Focus on:
1. Identifying the main purpose of the interface
2. Removing unnecessary elements (aim for 70% reduction)
3. Grouping related items into logical sections
4. Emphasizing the most important actions
5. Maintaining core functionality

The overlay will render these elements on top of the original interface."""
            
            # Prepare message for LLM with detailed context and user preferences
            user_content = f"""Screen Content:
{screen_text}

Active Application: {active_app}
Window Title: {window_title}

User Preferences:
- Simplify UI: {request_data.get('preferences', {}).get('simplifyUI', True)}
- Highlight Important: {request_data.get('preferences', {}).get('highlight', True)}
- Accessibility: {request_data.get('preferences', {}).get('accessibility', False)}"""

            # Get transformation from LLM
            transformation_response = await self.llm.generate_response(
                system_prompt=system_prompt,
                user_content=user_content
            )
            
            # Extract JSON from response using regex
            json_match = re.search(r'```json\n(.*?)\n```', transformation_response, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(1).strip()
                self._logger.info("Found JSON in response using regex")
                transformation_rules = json.loads(json_str)
            else:
                # Fallback to trying to parse the whole response as JSON
                self._logger.info("Trying to parse entire response as JSON")
                transformation_rules = json.loads(transformation_response)
            
            try:    
                # Validate the transformation rules contain required fields
                if 'layout' not in transformation_rules or 'elements' not in transformation_rules.get('layout', {}):
                    self._logger.error("Invalid transformation format: missing layout or elements")
                    raise ValueError("Invalid transformation format")
                
                # Enhance the transformation with additional context data
                transformation_data = {
                    'layout': transformation_rules.get('layout'),
                    'interactionMap': transformation_rules.get('interactionMap', {}),
                    'metadata': transformation_rules.get('metadata', {
                        'purpose': 'Interface simplification',
                        'application': active_app,
                        'windowTitle': window_title
                    }),
                    'screen_data': {
                        'text': screen_text[:1000] + "..." if len(screen_text) > 1000 else screen_text,
                        'active_app': active_app,
                        'window_title': window_title
                    },
                    'timestamp': time.time()
                }
                
                try:
                    # Send transformation data to overlay
                    self._logger.info(f"Sending transformation with {len(transformation_data['layout'].get('elements', []))} elements to overlay")
                    success = await self.overlay_bridge.send_message('transform-interface', transformation_data)
                    
                    if success:
                        self._logger.info("Successfully sent transformation to overlay")
                    else:
                        self._logger.warning("Failed to send transformation to overlay - no clients connected")
                    
                except json.JSONDecodeError as e:
                    self._logger.error(f"Error parsing transformation rules: {e}")
                    # Send error message to overlay
                    await self.overlay_bridge.send_message('transform-error', {
                        'error': 'Invalid JSON format',
                        'message': str(e)
                    })
                except Exception as e:
                    self._logger.error(f"Error processing transformation: {e}")
                    await self.overlay_bridge.send_message('transform-error', {
                        'error': 'Internal error',
                        'message': str(e)
                    })
            
            except Exception as e:
                self._logger.error(f"Error parsing transformation rules: {e}")
                # Send error message to overlay
                await self.overlay_bridge.send_message('transform-error', {
                    'error': 'Internal error',
                    'message': str(e)
                })
                
        except Exception as e:
            self._logger.error(f"Error handling transform request: {e}")
            await self.overlay_bridge.send_message('transform-error', {
                'error': 'Internal error',
                'message': str(e)
            })
    
    async def _handle_overlay_action(self, action_data):
        """Handle specific actions from overlay"""
        action_type = action_data.get('action_type')
        
        if action_type == 'fill_form':
            # Handle form filling action
            form_data = action_data.get('form_data', {})
            # Implement form filling logic
            pass
        elif action_type == 'extract_data':
            # Handle data extraction action
            extraction_rules = action_data.get('rules', {})
            # Implement data extraction logic
            pass
        # Add more action types as needed

    def handle_overlay_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tasks related to the overlay widget."""
        try:
            overlay_sensor = self._sensors.get('overlay')
            if not overlay_sensor:
                return {"success": False, "error": "Overlay sensor not available"}

            action = task.get('action')
            if action == 'start':
                success = overlay_sensor.start()
                return {"success": success}
            elif action == 'stop':
                success = overlay_sensor.stop()
                return {"success": success}
            elif action == 'send_message':
                message = task.get('message', '')
                success = overlay_sensor.send_message(message)
                return {"success": success}
            else:
                return {"success": False, "error": f"Unknown overlay action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single task."""
        try:
            task_type = task.get('type')
            if task_type == 'overlay':
                return self.handle_overlay_task(task)
            # ... existing code ...
            return {"success": False, "error": f"Unknown task type: {task_type}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

# For testing if run directly
if __name__ == "__main__":
    print("This module should be imported and used via main.py")