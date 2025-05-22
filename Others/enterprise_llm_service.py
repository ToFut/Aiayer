#!/usr/bin/env python3
"""
Enterprise LLM Service
Provides enterprise-grade LLM integration for all mode handlers
"""

import asyncio
import aiohttp
import json
import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class LLMResponse:
    """Structured LLM response"""
    content: str
    confidence: float
    processing_time: float
    model_used: str
    tokens_used: int
    metadata: Dict[str, Any]

class EnterpriseLLMService:
    """Enterprise-grade LLM service with Ollama integration"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model_name = "llama3.2:latest"
        self.session = None
        self.performance_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "total_tokens": 0
        }
        
        # Mode-specific prompts
        self.mode_prompts = {
            "Ask": {
                "system": "You are a knowledgeable assistant specializing in answering questions with context and memory. Provide detailed, informative responses based on available context and user history.",
                "temperature": 0.7
            },
            "Agent": {
                "system": "You are a task-planning agent. Break down user requests into actionable steps and provide clear execution plans. Be practical and specific in your recommendations.",
                "temperature": 0.5
            },
            "Suggest": {
                "system": "You are a proactive suggestion engine. Analyze user queries and provide helpful, actionable suggestions and recommendations. Be creative and forward-thinking.",
                "temperature": 0.8
            },
            "General": {
                "system": "You are a friendly, helpful assistant for general conversation. Be conversational, engaging, and helpful while maintaining a professional tone.",
                "temperature": 0.6
            }
        }
    
    async def initialize(self):
        """Initialize the LLM service"""
        try:
            self.session = aiohttp.ClientSession()
            await self._check_ollama_health()
            logger.info("✅ Enterprise LLM Service initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM service: {e}")
            raise
    
    async def _check_ollama_health(self):
        """Check if Ollama is available and healthy"""
        try:
            async with self.session.get(f"{self.ollama_url}/api/tags") as response:
                if response.status == 200:
                    models = await response.json()
                    available_models = [model['name'] for model in models.get('models', [])]
                    logger.info(f"📋 Available models: {available_models}")
                    
                    # Check if our preferred model is available
                    if not any(self.model_name in model for model in available_models):
                        logger.warning(f"⚠️ Preferred model {self.model_name} not found. Using first available model.")
                        if available_models:
                            self.model_name = available_models[0]
                        else:
                            raise Exception("No models available in Ollama")
                    
                    logger.info(f"🤖 Using model: {self.model_name}")
                else:
                    raise Exception(f"Ollama health check failed: {response.status}")
        except Exception as e:
            logger.error(f"❌ Ollama health check failed: {e}")
            raise
    
    async def generate_response(self, query: str, mode: str, context: Dict[str, Any] = None) -> LLMResponse:
        """Generate response using Ollama LLM"""
        start_time = time.time()
        
        try:
            self.performance_metrics["total_requests"] += 1
            
            # Build enhanced prompt with context
            prompt = await self._build_enhanced_prompt(query, mode, context)
            
            # Get mode configuration
            mode_config = self.mode_prompts.get(mode, self.mode_prompts["General"])
            
            # Prepare request payload
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": mode_config["temperature"],
                    "top_p": 0.9,
                    "top_k": 40,
                    "num_predict": 1024
                }
            }
            
            logger.info(f"🧠 Generating {mode} mode response for query: {query[:100]}...")
            
            # Make request to Ollama
            async with self.session.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    
                    processing_time = time.time() - start_time
                    content = result.get("response", "").strip()
                    
                    # Calculate confidence based on response quality
                    confidence = await self._calculate_confidence(content, query, mode)
                    
                    # Extract tokens used (if available)
                    tokens_used = result.get("eval_count", 0) + result.get("prompt_eval_count", 0)
                    
                    # Update metrics
                    self.performance_metrics["successful_requests"] += 1
                    self.performance_metrics["total_tokens"] += tokens_used
                    self._update_average_response_time(processing_time)
                    
                    logger.info(f"✅ LLM response generated in {processing_time:.2f}s (confidence: {confidence:.2f})")
                    
                    return LLMResponse(
                        content=content,
                        confidence=confidence,
                        processing_time=processing_time,
                        model_used=self.model_name,
                        tokens_used=tokens_used,
                        metadata={
                            "mode": mode,
                            "context_provided": context is not None,
                            "prompt_length": len(prompt),
                            "response_length": len(content)
                        }
                    )
                else:
                    error_text = await response.text()
                    raise Exception(f"Ollama API error {response.status}: {error_text}")
                    
        except Exception as e:
            self.performance_metrics["failed_requests"] += 1
            processing_time = time.time() - start_time
            logger.error(f"❌ LLM generation failed: {e}")
            
            # Return fallback response
            return LLMResponse(
                content=f"I apologize, but I encountered a technical issue while processing your {mode.lower()} request. Please try again in a moment.",
                confidence=0.1,
                processing_time=processing_time,
                model_used="fallback",
                tokens_used=0,
                metadata={
                    "error": str(e),
                    "mode": mode,
                    "fallback_response": True
                }
            )
    
    async def _build_enhanced_prompt(self, query: str, mode: str, context: Dict[str, Any] = None) -> str:
        """Build enhanced prompt with context and mode-specific instructions"""
        mode_config = self.mode_prompts.get(mode, self.mode_prompts["General"])
        
        prompt_parts = [
            f"System: {mode_config['system']}\n",
            f"Mode: {mode}\n"
        ]
        
        # Add context if available
        if context:
            prompt_parts.append("Context:")
            
            # Add memory context
            if context.get("relevant_memories"):
                memories = context["relevant_memories"][:3]  # Top 3 memories
                prompt_parts.append("Previous interactions:")
                for mem in memories:
                    prompt_parts.append(f"- {mem.get('content', '')[:200]}...")
            
            # Add semantic search context
            if context.get("key_topics"):
                prompt_parts.append(f"Related topics: {', '.join(context['key_topics'][:5])}")
            
            # Add user patterns
            if context.get("user_patterns"):
                patterns = context["user_patterns"]
                if patterns.get("most_used_mode"):
                    prompt_parts.append(f"User typically uses {patterns['most_used_mode']} mode")
                if patterns.get("response_preference"):
                    prompt_parts.append(f"User prefers {patterns['response_preference']} responses")
            
            # Add system state
            if context.get("system_state"):
                state = context["system_state"]
                prompt_parts.append(f"System status: {state.get('status', 'unknown')}")
            
            prompt_parts.append("")  # Empty line separator
        
        # Add mode-specific instructions
        if mode == "Ask":
            prompt_parts.append("Instructions: Provide a detailed, informative answer based on the context and your knowledge. If relevant information is available in the context, reference it appropriately.")
        elif mode == "Agent":
            prompt_parts.append("Instructions: Break down the user's request into specific, actionable steps. Create a clear execution plan with numbered steps. Be practical and specific.")
        elif mode == "Suggest":
            prompt_parts.append("Instructions: Provide 3-5 helpful suggestions related to the user's query. Be proactive and creative in your recommendations.")
        elif mode == "General":
            prompt_parts.append("Instructions: Respond in a friendly, conversational manner. Be helpful and engaging.")
        
        # Add the user query
        prompt_parts.append(f"User: {query}")
        prompt_parts.append("Assistant:")
        
        return "\n".join(prompt_parts)
    
    async def _calculate_confidence(self, content: str, query: str, mode: str) -> float:
        """Calculate confidence score for the response"""
        base_confidence = 0.7
        
        # Length factor - reasonable length responses get higher confidence
        length_factor = min(len(content) / 500, 1.0) * 0.1
        
        # Specificity factor - responses that reference the query get higher confidence
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        overlap = len(query_words.intersection(content_words))
        specificity_factor = min(overlap / len(query_words), 1.0) * 0.1
        
        # Mode appropriateness factor
        mode_factor = 0.0
        if mode == "Agent" and any(word in content.lower() for word in ["step", "plan", "first", "next", "execute"]):
            mode_factor = 0.1
        elif mode == "Suggest" and any(word in content.lower() for word in ["suggest", "recommend", "try", "consider"]):
            mode_factor = 0.1
        elif mode == "Ask" and len(content) > 100:  # Detailed responses for Ask mode
            mode_factor = 0.1
        
        return min(base_confidence + length_factor + specificity_factor + mode_factor, 1.0)
    
    def _update_average_response_time(self, processing_time: float):
        """Update average response time metric"""
        total = self.performance_metrics["successful_requests"]
        current_avg = self.performance_metrics["average_response_time"]
        self.performance_metrics["average_response_time"] = (
            (current_avg * (total - 1) + processing_time) / total
        )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self.performance_metrics.copy()
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            start_time = time.time()
            test_response = await self.generate_response("Health check", "General")
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "model": self.model_name,
                "response_time": response_time,
                "performance_metrics": self.get_performance_metrics(),
                "test_response_success": test_response.confidence > 0.5
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "performance_metrics": self.get_performance_metrics()
            }
    
    async def close(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()
        logger.info("🔒 Enterprise LLM Service closed")

# Global instance
_llm_service = None

async def get_llm_service() -> EnterpriseLLMService:
    """Get or create the global LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = EnterpriseLLMService()
        await _llm_service.initialize()
    return _llm_service

async def generate_llm_response(query: str, mode: str, context: Dict[str, Any] = None) -> LLMResponse:
    """Convenience function to generate LLM response"""
    service = await get_llm_service()
    return await service.generate_response(query, mode, context)