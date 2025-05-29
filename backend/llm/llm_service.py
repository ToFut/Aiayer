#!/usr/bin/env python3
"""
LLM Service
Handles interactions with the local Ollama server for generating responses using llama3.2:latest.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

class LLMService:
    def __init__(self):
        self.initialized = False
        self.model = OLLAMA_MODEL
        
    async def initialize(self) -> bool:
        """Initialize the LLM service."""
        try:
            # Optionally, you could check if the Ollama server is up here
            self.initialized = True
            logger.info(f"LLM service initialized with Ollama model: {self.model}")
            return True
        except Exception as e:
            logger.error(f"Error initializing LLM service: {e}")
            return False
            
    async def generate_response(self, query: str, context: Optional[List[Dict[str, Any]]] = None) -> str:
        """Generate a response using the local Ollama server."""
        try:
            if not self.initialized:
                raise RuntimeError("LLM service not initialized")
            if not query:
                raise ValueError("Query cannot be empty")

            logger.info(f"Generating response for query: {query[:100]}...")
            if context:
                logger.info(f"Using context with {len(context)} items")

            # Prepare the chat history for Ollama
            messages = []
            # Add context if available
            if context:
                for item in context:
                    if isinstance(item, dict) and 'content' in item:
                        messages.append({
                            "role": item.get('role', 'user'),
                            "content": item['content']
                        })
            # Add the current user query
            messages.append({
                "role": "user",
                "content": query
            })

            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(OLLAMA_API_URL, json=payload, timeout=60)
                response.raise_for_status()
                data = response.json()
                response_text = data["message"]["content"] if "message" in data and "content" in data["message"] else data.get("response", "[No response]")

            logger.info(f"Generated response: {response_text[:100]}...")
            return response_text
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
