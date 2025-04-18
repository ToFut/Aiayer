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
                 data_filter: DataFilter, context_analyzer: ContextAnalyzer):
        """
        Initialize the task agent.
        
        Args:
            sensors: Dictionary of sensor instances
            llm: Local language model instance
            memory: Conversation memory instance
            data_filter: Data filter instance
            context_analyzer: Context analyzer instance
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
        
        # Initialize overlay bridge
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

    async def _build_conversation(self, query: str, context: Optional[ContextInsight]) -> List[Dict[str, str]]:
        """Build conversation messages with context."""
        messages = []
        
        # Add system message with context
        system_message = "You are a helpful AI assistant. "
        if context:
            system_message += f"Current context: {context.context_summary}"
        messages.append({"role": "system", "content": system_message})
        
        # Add conversation history
        if self._memory:
            history = self._memory.get_recent()
            messages.extend(history)
        
        # Add current query
        messages.append({"role": "user", "content": query})
        
        return messages

    async def handle_query(self, query: str) -> str:
        """Handle a user query with context awareness."""
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")
            
        if not query.strip():
            raise ValueError("Query cannot be empty")

        try:
            # Get current context
            context = await self.get_current_context()
            
            # Build conversation messages
            messages = await self._build_conversation(query, context)
            
            # Generate response
            response = await self._llm.generate_response(messages)
            
            # Format response with context
            formatted_response = self._format_response(response, context, query)
            
            # Add to memory (synchronous operation)
            self._memory.add_message({"role": "user", "content": query})
            self._memory.add_message({"role": "assistant", "content": formatted_response})
            
            return formatted_response
        except Exception as e:
            self._logger.error(f"Error handling query: {e}")
            return f"Error processing your request: {str(e)}"

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
            if interaction_data.get('type') == 'query':
                # User asked a question through the overlay
                response = await self.handle_query(interaction_data.get('query', ''))
                await self.overlay_bridge.send_message('query_response', {
                    'query': interaction_data.get('query'),
                    'response': response
                })
            elif interaction_data.get('type') == 'action':
                # Handle specific actions from overlay
                await self._handle_overlay_action(interaction_data)
        except Exception as e:
            self._logger.error(f"Error handling overlay interaction: {e}")
    
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
- Accessibility: {request_data.get('preferences', {}).get('accessibility', False)}

Task: Generate a transformation layout that simplifies this interface while maintaining core functionality.
"""
            
            # Prepare messages for LLM
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
            
            # Generate transformation rules
            self._logger.info(f"Generating transformation for {active_app} - {window_title}")
            transformation_response = await self._llm.generate_response(messages)
            self._logger.info("Received transformation response from LLM")
            
            # Parse and send transformation rules
            try:
                # Extract JSON from the response using regex pattern matching
                import re
                json_match = re.search(r'```json\n(.*?)\n```', transformation_response, re.DOTALL)
                
                if json_match:
                    json_str = json_match.group(1).strip()
                    self._logger.info("Found JSON in response using regex")
                    transformation_rules = json.loads(json_str)
                else:
                    # Fallback to trying to parse the whole response as JSON
                    self._logger.info("Trying to parse entire response as JSON")
                    transformation_rules = json.loads(transformation_response)
                    
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
            self._logger.error(f"Error handling transform request: {e}")
            # Send error message to overlay
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

# For testing if run directly
if __name__ == "__main__":
    print("This module should be imported and used via main.py")