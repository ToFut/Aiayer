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
from agent.knowledge_base import KnowledgeBase
from sensors.llm_analyzer import LocalLLMAnalyzer
from screen_controller import ScreenController
from memory import Memory

logger = logging.getLogger(__name__)

class TaskAgent:
    """
    Intelligent task agent that provides context-aware assistance using local AI models.
    """
    
    def __init__(self, sensors: Dict, llm: LocalLLM, memory: ConversationMemory, 
                 data_filter: DataFilter, context_analyzer: ContextAnalyzer, 
                 overlay_bridge: Optional[OverlayBridge] = None,
                 knowledge_base: Optional[KnowledgeBase] = None,
                 screen_controller: Optional[ScreenController] = None,
                 llm_analyzer: Optional[LocalLLMAnalyzer] = None):
        """
        Initialize the task agent.
        
        Args:
            sensors: Dictionary of sensor instances
            llm: Local language model instance
            memory: Conversation memory instance
            data_filter: Data filter instance
            context_analyzer: Context analyzer instance
            overlay_bridge: Optional existing bridge instance to use
            knowledge_base: Optional knowledge base instance to use
            screen_controller: Optional screen controller instance to use
            llm_analyzer: Optional LLM analyzer instance to use
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
        self._knowledge_base = knowledge_base or KnowledgeBase()
        
        # Use shared screen controller if provided
        self.screen_controller = screen_controller
        
        # Use shared analyzer if provided, otherwise create new one
        self.llm_analyzer = llm_analyzer
        
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
        system_message = "You are a helpful AI assistant. Keep your responses concise and to the point, under 150 words. "
        
        # Add base context
        if context:
            system_message += f"Current context: {context.context_summary}. "
        
        # Add simplified instructions for screen-related queries
        if enhanced_context and self._is_screen_related_query(query):
            system_message += """
You have access to the text content of the user's screen. Be concise and only describe the most relevant information.
"""
        
        messages.append({"role": "system", "content": system_message})
        
        # Add screen content as a separate system message if available
        if enhanced_context and "screen_text" in enhanced_context:
            screen_content = enhanced_context["screen_text"]
            
            # Truncate more aggressively
            if len(screen_content) > 800:
                screen_content = screen_content[:800] + "... [content truncated]"
                
            app_info = ""
            if enhanced_context.get("active_app"):
                app_info = f"\nApp: {enhanced_context.get('active_app')}"
                
            screen_message = f"""Screen content: {app_info}
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

    async def handle_query(self, query: str) -> Dict:
        """Handle a user query with proper async/await patterns and timeout handling."""
        try:
            # Send immediate typing indicator
            await self.overlay_bridge.send_message('query_status', {
                'status': 'processing',
                'query': query
            })

            # Get current context with timeout
            try:
                context = await asyncio.wait_for(
                    self._context_analyzer.get_current_context(),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                self._logger.warning("Context analysis timed out, using cached context")
                context = self._last_context or {
                    'browser': {'status': 'timeout'},
                    'process': {'status': 'timeout'},
                    'overlay': {'status': 'timeout'},
                    'timestamp': datetime.now().isoformat()
                }

            # Generate response with timeout
            try:
                response = await asyncio.wait_for(
                    self._generate_response(query, context),
                    timeout=10.0
                )
            except asyncio.TimeoutError:
                self._logger.warning("Response generation timed out")
                response = "I'm having trouble processing that right now. Please try again."

            # Send completion status
            await self.overlay_bridge.send_message('query_status', {
                'status': 'complete',
                'query': query
            })

            return {
                'status': 'success',
                'response': response,
                'context': context
            }

        except Exception as e:
            self._logger.error(f"Error handling query: {e}")
            # Send error status
            await self.overlay_bridge.send_message('query_status', {
                'status': 'error',
                'error': str(e)
            })
            return {
                'status': 'error',
                'error': str(e)
            }

    async def _generate_response(self, query: str, context: Dict) -> str:
        """Generate a response using the language model and context."""
        try:
            # Prepare context for the model
            context_str = json.dumps(context, indent=2)
            
            # Generate response with timeout
            response = await asyncio.wait_for(
                self._llm.generate(
                    f"Context: {context_str}\n\nQuery: {query}\n\nResponse:"
                ),
                timeout=10.0
            )
            
            return response
            
        except asyncio.TimeoutError:
            self._logger.warning("Response generation timed out")
            return "I'm having trouble processing that right now. Please try again."
            
        except Exception as e:
            self._logger.error(f"Error generating response: {e}")
            return "I encountered an error while processing your request."

    def _is_screen_related_query(self, query: str) -> bool:
        """Determine if the query is related to the screen content."""
        screen_keywords = [
            "screen", "see", "seeing", "looking at", "display", "showing", 
            "what's on", "what is on", "what am i", "looking", "view", "visible",
            "window", "app", "application", "interface", "ui", "showing"
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in screen_keywords)
        
    async def _gather_screen_data(self) -> Optional[Dict[str, Any]]:
        """Gather screen data using shared components when possible."""
        try:
            # If we have a screen controller, use its latest analysis
            if self.screen_controller:
                latest = self.screen_controller.get_latest_analysis()
                if latest:
                    return latest
                    
            # If we have a shared analyzer but no controller
            if self.llm_analyzer:
                # TODO: Implement direct screen capture and analysis
                pass
                
            return None
            
        except Exception as e:
            logger.error(f"Error gathering screen data: {e}")
            return None
            
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
            # Check if we have a recent context
            if self._last_context and self._last_context_time:
                context_age = (datetime.now() - self._last_context_time).total_seconds()
                if context_age < 5:  # Use cached context if less than 5 seconds old
                    return self._last_context
            
            # Get fresh context with timeout and better error handling
            try:
                # First try to get process info since it's most reliable
                process_context = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, self._context_analyzer.analyze_process_context
                    ),
                    timeout=2.0
                )
                
                # Then try browser context with shorter timeout
                try:
                    browser_context = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None, self._context_analyzer.analyze_browser_context
                        ),
                        timeout=1.5
                    )
                except asyncio.TimeoutError:
                    self._logger.warning("Browser context timed out, using default")
                    browser_context = {"status": "timeout"}
                except Exception as e:
                    self._logger.error(f"Error getting browser context: {e}")
                    browser_context = {"status": "error", "error": str(e)}
                
                # Finally try overlay context
                try:
                    overlay_context = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None, self._context_analyzer.analyze_overlay_context
                        ),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    self._logger.warning("Overlay context timed out, using default")
                    overlay_context = {"status": "timeout"}
                except Exception as e:
                    self._logger.error(f"Error getting overlay context: {e}")
                    overlay_context = {"status": "error", "error": str(e)}
                
                # Combine contexts
                context = {
                    "process": process_context,
                    "browser": browser_context,
                    "overlay": overlay_context,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Create a new context insight with more detailed info
                self._last_context = ContextInsight(
                    current_activity=process_context.get('active_app', 'Unknown'),
                    context_summary=f"Using {process_context.get('active_app', 'Unknown')} - {process_context.get('window_title', '')}",
                    potential_needs=self._determine_potential_needs(context),
                    attention_level=self._determine_attention_level(context),
                    confidence_score=self._calculate_confidence(context),
                    source_model="context_analyzer",
                    semantic_understanding={
                        "purpose": "Context analysis with partial data",
                        "workflow": process_context.get('app_category', 'unknown'),
                        "challenges": ["Some sensors timed out"],
                        "related_concepts": [],
                        "implicit_goals": []
                    }
                )
                self._last_context_time = datetime.now()
                
                return self._last_context
                
            except asyncio.TimeoutError:
                self._logger.warning("Process context timed out, using cached context")
                return self._last_context or ContextInsight(
                    current_activity="Unknown",
                    context_summary="Context analysis timed out",
                    potential_needs=[],
                    attention_level="medium",
                    confidence_score=0.0,
                    source_model="timeout"
                )
                
        except Exception as e:
            self._logger.error(f"Error getting current context: {e}")
            return ContextInsight(
                current_activity="Unknown",
                context_summary="Error analyzing context",
                potential_needs=[],
                attention_level="medium",
                confidence_score=0.0,
                source_model="error"
            )
            
    def _determine_potential_needs(self, context: Dict) -> List[str]:
        """Determine potential user needs based on context."""
        needs = []
        
        # Check process context
        process = context.get('process', {})
        if process.get('active_app'):
            app_category = process.get('app_category', '')
            if app_category == 'development':
                needs.append("Code assistance or documentation")
            elif app_category == 'browser':
                needs.append("Web content analysis or search help")
            elif app_category == 'document':
                needs.append("Document editing or formatting help")
                
        # Check browser context
        browser = context.get('browser', {})
        if browser.get('status') == 'timeout':
            needs.append("Browser response optimization")
            
        # Check overlay context
        overlay = context.get('overlay', {})
        if overlay.get('status') == 'stopped':
            needs.append("Overlay service restart")
            
        return needs or ["General assistance"]
        
    def _determine_attention_level(self, context: Dict) -> str:
        """Determine the required attention level based on context."""
        # Default to medium
        attention = "medium"
        
        # Check for error conditions that might need high attention
        if any(c.get('status') == 'error' for c in context.values()):
            attention = "high"
        
        # Check for timeouts that might need medium-high attention
        elif any(c.get('status') == 'timeout' for c in context.values()):
            attention = "medium-high"
            
        return attention
        
    def _calculate_confidence(self, context: Dict) -> float:
        """Calculate confidence score based on available context."""
        # Start with base confidence
        confidence = 0.5
        
        # Add confidence for each successful sensor
        for sensor_data in context.values():
            if isinstance(sensor_data, dict):
                if sensor_data.get('status') not in ['error', 'timeout', 'unavailable']:
                    confidence += 0.1
                elif sensor_data.get('status') == 'timeout':
                    confidence -= 0.05
                elif sensor_data.get('status') == 'error':
                    confidence -= 0.1
                    
        # Ensure confidence stays in valid range
        return max(0.1, min(0.9, confidence))

    @property
    def llm(self) -> LocalLLM:
        """Get the LLM instance."""
        return self._llm

    async def _handle_overlay_interaction(self, interaction_data):
        """Handle user interaction with knowledge base support"""
        try:
            # Extract query
            query = self._extract_query(interaction_data)
            if not query:
                return
                
            # Send thinking status
            await self._send_thinking_status(query)
            
            # Check knowledge base first
            knowledge_results = await self._knowledge_base.retrieve(query)
            
            # Gather context from sensors
            context = await self._gather_sensor_context()
            
            # Prepare messages for LLM with knowledge base results
            messages = self._prepare_messages(query, context, knowledge_results)
            
            # Generate response
            response = await self.llm.generate_response(messages)
            
            # Store useful information in knowledge base
            await self._store_useful_knowledge(query, response, context)
            
            # Send response back
            await self._send_response(query, response, context)
            
        except Exception as e:
            self._logger.error(f"Error handling overlay interaction: {e}")
            await self._send_error_response(query, str(e))
            
    def _prepare_messages(self, query: str, context: Dict, knowledge_results: List[Dict]) -> List[Dict]:
        """Prepare messages with knowledge base results"""
        messages = []
        
        # Add system message with context
        system_message = """You are a helpful AI assistant with access to a knowledge base.
Use the provided knowledge and context to give accurate, helpful responses."""
        
        # Add knowledge base results if available
        if knowledge_results:
            system_message += "\n\nRelevant knowledge from previous interactions:"
            for result in knowledge_results:
                system_message += f"\n- {result['content']}"
                if result.get('context'):
                    system_message += f"\n  Context: {json.dumps(result['context'])}"
                    
        messages.append({"role": "system", "content": system_message})
        
        # Add current context
        if context:
            messages.append({
                "role": "system",
                "content": f"Current context: {json.dumps(context)}"
            })
            
        # Add conversation history
        messages.extend(self._memory.get_recent())
        
        # Add current query
        messages.append({"role": "user", "content": query})
        
        return messages
        
    async def _store_useful_knowledge(self, query: str, response: str, context: Dict):
        """Store useful information in knowledge base"""
        try:
            # Determine if the response contains useful information
            if self._is_useful_knowledge(response):
                # Extract key information
                knowledge_content = self._extract_knowledge(response)
                
                # Store in knowledge base
                await self._knowledge_base.store(
                    content=knowledge_content,
                    context={
                        'query': query,
                        'response': response,
                        'timestamp': datetime.now().isoformat()
                    },
                    category=self._determine_category(query),
                    confidence=0.8  # Initial confidence
                )
                
        except Exception as e:
            self._logger.error(f"Error storing knowledge: {e}")
            
    def _is_useful_knowledge(self, response: str) -> bool:
        """Determine if response contains useful information to store"""
        # Check for factual information, instructions, or explanations
        useful_patterns = [
            r"how to",
            r"steps to",
            r"explanation",
            r"definition",
            r"fact",
            r"tip",
            r"best practice"
        ]
        
        response_lower = response.lower()
        return any(pattern in response_lower for pattern in useful_patterns)
        
    def _extract_knowledge(self, response: str) -> str:
        """Extract key information from response"""
        # Simple extraction for now
        # TODO: Implement more sophisticated extraction
        return response
        
    def _determine_category(self, query: str) -> str:
        """Determine category for knowledge entry"""
        categories = {
            'how_to': ['how to', 'how do i', 'steps to'],
            'explanation': ['what is', 'explain', 'define'],
            'troubleshooting': ['error', 'fix', 'problem', 'issue'],
            'best_practices': ['best way', 'should i', 'recommendation']
        }
        
        query_lower = query.lower()
        for category, patterns in categories.items():
            if any(pattern in query_lower for pattern in patterns):
                return category
                
        return 'general'

    async def _gather_sensor_context(self) -> Dict[str, Any]:
        """Gather context from all available sensors"""
        context = {}
        for name, sensor in self._sensors.items():
            try:
                if hasattr(sensor, 'get_context'):
                    context[name] = await sensor.get_context()
                elif hasattr(sensor, 'capture'):
                    context[name] = await sensor.capture()
                else:
                    context[name] = {"status": "unavailable"}
            except Exception as e:
                self._logger.error(f"Error getting context from sensor {name}: {e}")
                context[name] = {"error": str(e), "status": "error"}
        return context

    async def _send_thinking_status(self, query: str):
        """Send thinking status to overlay"""
        await self.overlay_bridge.send_message('query_status', {
            'status': 'processing',
            'query': query,
            'message': 'Analyzing context and preparing response...',
            'timestamp': time.time()
        })
        
        await self.overlay_bridge.send_message('chat_response', {
            'text': '...',
            'isTyping': True,
            'timestamp': time.time()
        })

    async def _send_response(self, query: str, response: str, context: Dict[str, Any]):
        """Send response back to overlay with context"""
        await self.overlay_bridge.send_message('chat_response', {
            'text': response,
            'timestamp': time.time(),
            'context': context
        })
        
        await self.overlay_bridge.send_message('query_status', {
            'status': 'completed',
            'query': query,
            'message': 'Response sent',
            'timestamp': time.time()
        })

    async def _send_error_response(self, query: str, error: str):
        """Send error response to overlay"""
        await self.overlay_bridge.send_message('query_status', {
            'status': 'error',
            'query': query,
            'message': f'Error: {error}',
            'timestamp': time.time()
        })
        
        await self.overlay_bridge.send_message('chat_response', {
            'text': f"I'm sorry, I encountered an error: {error}",
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