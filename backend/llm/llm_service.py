#!/usr/bin/env python3
"""
LLM Service
Handles interactions with the local Ollama server for generating responses using llama3.2:latest.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
import httpx
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

class LLMService:
    def __init__(self):
        self.initialized = False
        self.model = OLLAMA_MODEL
        self.timeout = 15  # Reduced from 30s to 15s
        self.max_retries = 2  # Reduced from 3 to 2
        self.base_delay = 0.5  # Reduced from 1s to 0.5s
        self.background_tasks = set()
        self.response_cache = {}  # Add response caching
        
    async def initialize(self) -> bool:
        """Initialize the LLM service."""
        try:
            self.initialized = True
            logger.info(f"LLM service initialized with Ollama model: {self.model}")
            return True
        except Exception as e:
            logger.error(f"Error initializing LLM service: {e}")
            return False

    async def generate_agent_response(self, query: str) -> AsyncGenerator[str, None]:
        """Generate a fast initial response for agent mode without heavy context."""
        try:
            if not self.initialized:
                raise RuntimeError("LLM service not initialized")
            if not query:
                raise ValueError("Query cannot be empty")

            # Check cache first
            cache_key = f"agent_{query}"
            if cache_key in self.response_cache:
                logger.info("Using cached response")
                for chunk in self.response_cache[cache_key]:
                    yield chunk
                return

            logger.info(f"Generating fast agent response for: {query[:100]}...")

            # Create prompt for action plan
            prompt = f"""You are an Agent Assistant that helps users with tasks. Break down the user's request into specific, actionable steps. Create a clear execution plan with numbered steps. Be practical and specific.

User request: {query}

Create a numbered list of steps to accomplish this task:"""

            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "temperature": 0.3,  # Lower temperature for more focused responses
                    "max_tokens": 300,    # Reduced token limit for faster responses
                    "top_p": 0.9,        # Added top_p for better quality/speed balance
                    "top_k": 40,         # Added top_k for better quality/speed balance
                    "num_ctx": 512       # Reduced context window for faster processing
                }
            }

            # Return quick response with shorter timeout
            async with httpx.AsyncClient() as client:
                try:
                    response_chunks = []
                    async with client.stream('POST', OLLAMA_API_URL, json=payload, timeout=15) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if line:
                                try:
                                    data = json.loads(line)
                                    if "response" in data:
                                        content = data["response"]
                                        if content:  # Only yield non-empty content
                                            response_chunks.append(content)
                                            yield content
                                except json.JSONDecodeError:
                                    continue
                    
                    # Cache the response
                    self.response_cache[cache_key] = response_chunks
                    
                except asyncio.TimeoutError:
                    logger.error("LLM response generation timed out")
                    # Return a simple fallback plan
                    fallback = [
                        "1. Analyze the request and gather requirements\n",
                        "2. Create a detailed plan based on the requirements\n",
                        "3. Execute the plan and monitor progress\n"
                    ]
                    self.response_cache[cache_key] = fallback
                    for chunk in fallback:
                        yield chunk
                    return

        except Exception as e:
            logger.error(f"Error generating agent response: {e}")
            raise

    async def _analyze_in_background(self, query: str):
        """Run detailed analysis in background with full context."""
        try:
            # Get full context
            context = await self._get_full_context(query)
            
            # Prepare detailed analysis
            messages = []
            if context:
                for item in context:
                    if isinstance(item, dict) and 'content' in item:
                        messages.append({
                            "role": item.get('role', 'user'),
                            "content": item['content']
                        })
            
            messages.append({
                "role": "user",
                "content": f"Analyze this request in detail with full context: {query}"
            })

            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,  # No need to stream background analysis
                "options": {
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            }

            # Run analysis and save results
            async with httpx.AsyncClient() as client:
                response = await client.post(OLLAMA_API_URL, json=payload, timeout=30)
                response.raise_for_status()
                analysis = response.json()
                
                # Save analysis for future use
                await self._save_analysis(query, analysis)

        except Exception as e:
            logger.error(f"Error in background analysis: {e}")

    async def _get_full_context(self, query: str) -> List[Dict[str, Any]]:
        """Get full context for background analysis."""
        # Implement your context retrieval logic here
        return []

    async def _save_analysis(self, query: str, analysis: Dict[str, Any]):
        """Save analysis results for future use."""
        # Implement your analysis storage logic here
        pass

    async def generate_response(self, query: str, context: Optional[List[Dict[str, Any]]] = None) -> AsyncGenerator[str, None]:
        """Generate a streaming response using the local Ollama server."""
        try:
            if not self.initialized:
                raise RuntimeError("LLM service not initialized")
            if not query:
                raise ValueError("Query cannot be empty")

            logger.info(f"Generating response for query: {query[:100]}...")
            if context:
                logger.info(f"Using context with {len(context)} items")

            # Build prompt with context
            prompt = ""
            if context:
                for item in context:
                    if isinstance(item, dict) and 'content' in item:
                        prompt += f"{item['content']}\n"
            prompt += f"\nUser: {query}\nAssistant:"

            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": True
            }

            for attempt in range(self.max_retries):
                try:
                    async with httpx.AsyncClient() as client:
                        async with client.stream('POST', OLLAMA_API_URL, json=payload, timeout=self.timeout) as response:
                            response.raise_for_status()
                            async for line in response.aiter_lines():
                                if line:
                                    try:
                                        data = json.loads(line)
                                        if "response" in data:
                                            content = data["response"]
                                            if content:  # Only yield non-empty content
                                                yield content
                                    except json.JSONDecodeError:
                                        continue
                    return
                except Exception as e:
                    if attempt == self.max_retries - 1:
                        logger.error(f"Request failed after {self.max_retries} attempts: {e}")
                        raise
                    delay = self.base_delay * (2 ** attempt)
                    logger.warning(f"Request failed, retrying in {delay}s (attempt {attempt + 1}/{self.max_retries})")
                    await asyncio.sleep(delay)

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

    async def cleanup(self):
        """Cleanup resources used by the LLM service."""
        try:
            self.initialized = False
            logger.info("LLM service cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up LLM service: {e}") 
