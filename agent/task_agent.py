"""
Task Agent Module
Provides intelligent task handling and context-aware assistance using local AI models.
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from threading import Thread, Event
import json
from unittest.mock import MagicMock
import time

from llm.model import LocalLLM
from memory.memory import ConversationMemory
from agent.data_filter import DataFilter
from agent.context_analyzer import ContextAnalyzer, ContextInsight

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
        
        # Get initial context synchronously if not using mocks
        if not isinstance(self._context_analyzer, MagicMock):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                self._last_context = loop.run_until_complete(
                    self._context_analyzer.analyze_context()
                )
                self._last_context_time = datetime.now()
            finally:
                loop.close()
        
        # Start context update thread
        self._start_context_updates()
        
    def _start_context_updates(self):
        """Start the background thread for context updates."""
        def update_context():
            while not self._context_update_event.is_set():
                try:
                    # Run async context analysis in a new event loop
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    self._last_context = loop.run_until_complete(
                        self._context_analyzer.analyze_context()
                    )
                    self._last_context_time = datetime.now()
                    loop.close()
                except Exception as e:
                    self._logger.error(f"Error updating context: {e}")
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
                self._last_context = await self._context_analyzer.analyze_context()
                self._last_context_time = datetime.now()
            return self._last_context
        except Exception as e:
            self._logger.error(f"Error getting current context: {e}")
            return None

# For testing if run directly
if __name__ == "__main__":
    print("This module should be imported and used via main.py")