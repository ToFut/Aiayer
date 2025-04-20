import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional

from .context_analyzer import ContextAnalyzer
from ..memory.memory import Memory
from ..llm.model import LocalLLM

logger = logging.getLogger(__name__)

class Agent:
    """
    Core agent that processes user queries and manages tasks.
    Integrates with context analyzer, LLM, and memory modules.
    """
    
    def __init__(self, llm: LocalLLM, memory: Memory, context_analyzer: Optional[ContextAnalyzer] = None):
        """
        Initialize the agent.
        
        Args:
            llm: Language model instance
            memory: Memory instance for persisting data
            context_analyzer: Optional context analyzer for enhanced understanding
        """
        self.llm = llm
        self.memory = memory
        self.context_analyzer = context_analyzer
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
    
    async def startup(self):
        """Initialize the agent components."""
        try:
            # Start the LLM
            if hasattr(self.llm, 'start'):
                success = await self.llm.start()
                if not success:
                    self.logger.error("Failed to start LLM model")
                    return False
            
            # Initialize memory
            if hasattr(self.memory, 'initialize'):
                await self.memory.initialize()
                
            return True
        except Exception as e:
            self.logger.error(f"Error during agent startup: {e}")
            return False
            
    async def shutdown(self):
        """Shutdown the agent components."""
        try:
            # Stop the LLM
            if self.llm and hasattr(self.llm, 'stop'):
                await self.llm.stop()
                
            # Persist memory if needed
            if hasattr(self.memory, 'persist'):
                await self.memory.persist()
                
            return True
        except Exception as e:
            self.logger.error(f"Error during agent shutdown: {e}")
            return False
    
    async def process_query(self, query: str, timeout: int = 60) -> Dict[str, Any]:
        """
        Process a user query and return a response.
        
        Args:
            query: The user's query text
            timeout: Timeout in seconds for LLM response
            
        Returns:
            Dictionary containing the response and additional data
        """
        try:
            # Validate input
            if not query or not isinstance(query, str):
                return {
                    "response": "*(Please provide a valid query)*",
                    "status": "error",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Check if LLM is available
            if not self.llm:
                return {
                    "response": "*(Error: Language model not available)*",
                    "status": "error",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Get context from context analyzer if available
            context_data = None
            if self.context_analyzer:
                try:
                    context_insight = await self.context_analyzer.analyze_context()
                    if context_insight:
                        context_data = {
                            "current_activity": context_insight.current_activity,
                            "context_summary": context_insight.context_summary,
                            "potential_needs": context_insight.potential_needs,
                            "attention_level": context_insight.attention_level,
                            "confidence": context_insight.confidence_score,
                            "semantic_understanding": context_insight.semantic_understanding
                        }
                        self.logger.info(f"Context analysis: {context_insight.context_summary} (confidence: {context_insight.confidence_score})")
                except Exception as e:
                    self.logger.error(f"Error analyzing context: {e}")
            
            # Prepare the conversation with context if available
            conversation = self.memory.get_conversation()
            
            # Add context if available
            if context_data:
                # Add subtle context hints to the system message
                if conversation and conversation[0]['role'] == 'system':
                    # Update the existing system message with context
                    original_content = conversation[0]['content']
                    context_hint = f"\nThe user appears to be {context_data['current_activity']}. "
                    context_hint += f"Context: {context_data['context_summary']}"
                    
                    # Avoid duplicate context information
                    if context_hint not in original_content:
                        conversation[0]['content'] = original_content + "\n\n" + context_hint
                else:
                    # Create a new system message with context
                    context_message = {
                        "role": "system", 
                        "content": f"You are a helpful assistant. The user appears to be {context_data['current_activity']}. Context: {context_data['context_summary']}"
                    }
                    conversation.insert(0, context_message)
            
            # Add user query to conversation
            conversation.append({"role": "user", "content": query})
            
            # Generate response with timeout
            self.logger.info(f"Generating response for query: {query} with timeout {timeout}s")
            
            try:
                # Generate response with explicit timeout
                response = await self.llm.generate_response(conversation, context_data, timeout=timeout)
                
                # Validate response
                if not response or not isinstance(response, str):
                    return {
                        "response": "*(Error: Invalid response from language model)*",
                        "status": "error",
                        "timestamp": datetime.now().isoformat()
                    }
                
                # Update memory
                conversation.append({"role": "assistant", "content": response})
                self.memory.update_conversation(conversation)
                
                # Extract potential suggestions from context if available
                suggestions = []
                if context_data and 'potential_needs' in context_data:
                    suggestions = context_data['potential_needs'][:3]  # Limit to top 3 suggestions
                
                # Return structured response
                return {
                    "response": response,
                    "status": "success",
                    "timestamp": datetime.now().isoformat(),
                    "suggestions": suggestions,
                    "context": context_data
                }
                
            except asyncio.TimeoutError:
                self.logger.error(f"Request timed out after {timeout} seconds")
                return {
                    "response": "*(The response is taking longer than expected. Please try a shorter query.)*",
                    "status": "timeout",
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                self.logger.error(f"Error generating response: {e}")
                return {
                    "response": f"*(Error: {str(e)})*",
                    "status": "error",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            return {
                "response": "*(Error: Could not process query. Please try again.)*",
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_llm_status(self) -> Dict[str, Any]:
        """Get the status of the language model."""
        try:
            if not self.llm:
                return {"status": "unavailable"}
                
            is_healthy = False
            if hasattr(self.llm, 'is_healthy'):
                is_healthy = self.llm.is_healthy()
            elif hasattr(self.llm, 'running'):
                is_healthy = self.llm.running
                
            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "model": getattr(self.llm, 'model_name', 'unknown')
            }
        except Exception as e:
            self.logger.error(f"Error getting LLM status: {e}")
            return {"status": "error", "error": str(e)}
            
    def get_memory_status(self) -> Dict[str, Any]:
        """Get the status of the memory component."""
        try:
            if not self.memory:
                return {"status": "unavailable"}
                
            conversation = self.memory.get_conversation()
            message_count = len(conversation) if conversation else 0
            
            return {
                "status": "available",
                "message_count": message_count,
                "has_system_message": message_count > 0 and conversation[0]["role"] == "system"
            }
        except Exception as e:
            self.logger.error(f"Error getting memory status: {e}")
            return {"status": "error", "error": str(e)}
            
    def get_context_status(self) -> Dict[str, Any]:
        """Get the status of the context analyzer."""
        try:
            if not self.context_analyzer:
                return {"status": "unavailable"}
                
            last_analysis = self.context_analyzer.get_last_analysis()
            if not last_analysis:
                return {"status": "idle"}
                
            analysis_age = self.context_analyzer.get_analysis_age() or 0
                
            return {
                "status": "active" if analysis_age < 300 else "stale",  # Stale after 5 minutes
                "age_seconds": analysis_age,
                "current_activity": last_analysis.current_activity,
                "confidence": last_analysis.confidence_score
            }
        except Exception as e:
            self.logger.error(f"Error getting context status: {e}")
            return {"status": "error", "error": str(e)}

def process_query(self, query: str, timeout: int = 30) -> str:
    """Process a user query and return a response."""
    try:
        # Validate input
        if not query or not isinstance(query, str):
            return "*(Please provide a valid query)*"
        
        # Check if LLM is available
        if not self.llm:
            return "*(Error: Language model not available)*"
        
        # Prepare the conversation
        conversation = self.memory.get_conversation()
        conversation.append({"role": "user", "content": query})
        
        # Generate response with timeout
        try:
            response = self.llm.generate_response(conversation, timeout=timeout)
            
            # Validate response
            if not response or not isinstance(response, str):
                return "*(Error: Invalid response from language model)*"
            
            # Update memory
            conversation.append({"role": "assistant", "content": response})
            self.memory.update_conversation(conversation)
            
            return response
            
        except TimeoutError:
            return "*(Error: Request timed out. Please try again.)*"
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "*(Error: Could not generate response. Please try again.)*"
            
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return "*(Error: Could not process query. Please try again.)*" 