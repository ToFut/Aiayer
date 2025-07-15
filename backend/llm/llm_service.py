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
        self.timeout = 120  # Increased to 2 minutes for complex JSON generation
        self.max_retries = 3  # Increased from 2 to 3
        self.base_delay = 2.0  # Increased from 1s to 2s for better retry strategy
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

    async def cleanup(self):
        """Cleanup resources used by the LLM service."""
        try:
            self.initialized = False
            logger.info("LLM service cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up LLM service: {e}")

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

            # Use different settings for JSON generation
            is_json_request = "json" in query.lower() or "plan" in query.lower()
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "temperature": 0.1 if is_json_request else 0.7,  # Lower temperature for JSON
                    "max_tokens": 2000 if is_json_request else 1000,  # More tokens for JSON
                    "top_p": 0.9,
                    "top_k": 40,
                    "num_ctx": 4096 if is_json_request else 2048  # Larger context for JSON
                }
            }

            for attempt in range(self.max_retries):
                try:
                    # Use longer timeout for JSON requests
                    request_timeout = 90 if is_json_request else self.timeout
                    
                    async with httpx.AsyncClient() as client:
                        async with client.stream('POST', OLLAMA_API_URL, json=payload, timeout=request_timeout) as response:
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

    async def generate_response_with_fallback(self, query: str, context: Optional[List[Dict[str, Any]]] = None) -> AsyncGenerator[str, None]:
        """Generate response with robust fallback mechanisms."""
        try:
            # Enhanced prompt engineering for better responses
            enhanced_prompt = f"""Create an automation plan for this user request: "{query}"

IMPORTANT INSTRUCTIONS:
1. Use SPECIFIC app names like "Calculator", "Safari", "Finder", "Terminal" - NOT generic names like "app1", "app2", "app"
2. Create MULTIPLE steps for complex requests
3. Use specific actions like "open_app", "navigate_to", "click", "type", "wait", "screenshot"
4. Provide detailed descriptions for each step
5. Return ONLY a single, complete, valid JSON object

Return this EXACT JSON structure:
{{
  "apps": ["specific_app_name"],
  "steps": [
    {{
      "action": "specific_action",
      "app": "specific_app_name", 
      "description": "detailed_description_of_what_this_step_does"
    }}
  ]
}}

CRITICAL: Ensure the JSON is complete and valid. No extra text, no explanations, just the JSON object."""

            async for chunk in self.generate_response(enhanced_prompt, context):
                yield chunk
                
        except Exception as e:
            logger.error(f"Error in generate_response_with_fallback: {e}")
            # Generate a fallback response
            fallback_response = self._create_fallback_response(query)
            yield fallback_response

    def _create_fallback_response(self, query: str) -> str:
        """Create a fallback response when LLM fails."""
        try:
            # Extract app names from the query
            app_mapping = {
                "calculator": "Calculator",
                "safari": "Safari", 
                "finder": "Finder",
                "terminal": "Terminal",
                "chrome": "Chrome",
                "firefox": "Firefox",
                "mail": "Mail",
                "messages": "Messages",
                "photos": "Photos",
                "music": "Music",
                "notes": "Notes",
                "reminders": "Reminders",
                "calendar": "Calendar",
                "maps": "Maps",
                "facetime": "FaceTime",
                "camera": "Camera",
                "preferences": "System Preferences",
                "activity": "Activity Monitor",
                "disk": "Disk Utility",
                "console": "Console"
            }
            
            query_lower = query.lower()
            detected_apps = []
            
            for app_keyword, app_name in app_mapping.items():
                if app_keyword in query_lower:
                    detected_apps.append(app_name)
            
            # If no specific apps detected, use a generic approach
            if not detected_apps:
                if "open" in query_lower:
                    detected_apps = ["Calculator"]  # Default fallback
                else:
                    detected_apps = []
            
            # Create a simple but valid plan
            if detected_apps:
                plan = {
                    "apps": detected_apps,
                    "steps": [
                        {
                            "action": "open_app",
                            "app": detected_apps[0],
                            "description": f"Open {detected_apps[0]} as requested"
                        }
                    ]
                }
            else:
                plan = {
                    "apps": [],
                    "steps": [
                        {
                            "action": "wait",
                            "duration": 2,
                            "description": "Wait for system to be ready"
                        }
                    ]
                }
            
            return json.dumps(plan, indent=2)
            
        except Exception as e:
            logger.error(f"Error creating fallback response: {e}")
            # Ultimate fallback
            return json.dumps({
                "apps": ["Calculator"],
                "steps": [
                    {
                        "action": "open_app",
                        "app": "Calculator",
                        "description": "Open Calculator as fallback"
                    }
                ]
            }, indent=2) 
