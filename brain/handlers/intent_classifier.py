#!/usr/bin/env python3
"""
Intent Classifier Module for Brain Router

Uses LLM to classify user intents and determine which capabilities to invoke.
"""
import os
import sys
import json
import logging
import asyncio
from typing import Dict, Any, List, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import from parent directories
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import LLM service
try:
    from llm.llm_service import LLMService
    LLM_SERVICE_AVAILABLE = True
except ImportError:
    logger.warning("LLMService not available, using fallback classification")
    LLM_SERVICE_AVAILABLE = False

class IntentClassifier:
    """
    Classifies user intents using LLM to determine which capabilities to invoke.
    """
    
    def __init__(self):
        """Initialize the intent classifier."""
        if LLM_SERVICE_AVAILABLE:
            self.llm_service = LLMService()
        else:
            self.llm_service = None
        
        # Define known capabilities
        self.capabilities = [
            {"name": "folder_access", "description": "Reading, searching, or analyzing files and folders"},
            {"name": "task_execution", "description": "Performing tasks, automating actions, or executing commands"},
            {"name": "information_retrieval", "description": "Answering factual questions or retrieving information from memory"},
            {"name": "suggestion_generation", "description": "Providing recommendations or suggestions"},
            {"name": "system_monitoring", "description": "Checking system status, resources, or logs"}
        ]
        
        # Simple keyword fallbacks if LLM is unavailable
        self.fallback_keywords = {
            "folder_access": [
                "folder", "directory", "file", "files in", "read file", "search folder",
                "documents", "desktop", "downloads", "path", "contents of", "what's in",
                "list files", "show files", "find files", "analyze folder", "summarize folder",
                "browse folder", "explore directory", "check files", "view folder", "scan directory", 
                "look in folder", "browse files", "examine directory", "inspect folder"
            ],
            "task_execution": [
                "run", "execute", "perform", "automate", "start", "create", "make", "build",
                "launch", "open", "close", "stop", "kill", "click", "type", "press"
            ]
        }
        
        logger.info("Intent classifier initialized")
    
    async def classify_intent(self, query: str) -> Dict[str, Any]:
        """
        Classify the user's intent using LLM or fallback mechanisms.
        
        Args:
            query: The user's query
            
        Returns:
            Dictionary with intent classification results
        """
        if not query:
            return {"success": False, "error": "Empty query"}
        
        # Use LLM for classification if available
        if LLM_SERVICE_AVAILABLE and self.llm_service:
            return await self._classify_with_llm(query)
        else:
            # Use keyword-based fallback
            return self._classify_with_keywords(query)
    
    async def _classify_with_llm(self, query: str) -> Dict[str, Any]:
        """
        Use LLM to classify the user's intent.
        """
        try:
            # Prepare prompt for intent classification
            capabilities_str = "\n".join([f"- {cap['name']}: {cap['description']}" for cap in self.capabilities])
            
            prompt = f"""
You are an intent classifier for an AI assistant. Analyze the user query and determine which capabilities are needed to fulfill the request.

Available capabilities:
{capabilities_str}

User query: "{query}"

For each capability, determine if it's required to fulfill this request and provide a confidence score (0-1).
Return your analysis as a JSON object with these fields:
- primary_intent: The main capability needed (string)
- confidence: Confidence in the primary intent (float between 0-1)
- required_capabilities: Array of all capabilities needed to fulfill the request
- reasoning: Brief explanation of your classification

JSON response:
"""
            
            # Get LLM response
            response = await self.llm_service.generate_text(prompt, max_tokens=500)
            
            # Extract and parse JSON from response
            try:
                # Try to find JSON in the response
                json_str = response.strip()
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0].strip()
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0].strip()
                
                intent_data = json.loads(json_str)
                
                # Validate required fields
                if "primary_intent" not in intent_data or "required_capabilities" not in intent_data:
                    raise ValueError("Missing required fields in LLM response")
                
                # Add metadata
                intent_data["success"] = True
                intent_data["method"] = "llm"
                
                logger.info(f"Classified intent using LLM: {intent_data['primary_intent']} with confidence {intent_data.get('confidence', 'unknown')}")
                return intent_data
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Error parsing LLM response: {e}, response: {response[:100]}...")
                # Fall back to keyword matching
                return self._classify_with_keywords(query)
                
        except Exception as e:
            logger.error(f"Error in LLM classification: {e}")
            # Fall back to keyword matching
            return self._classify_with_keywords(query)
    
    def _classify_with_keywords(self, query: str) -> Dict[str, Any]:
        """
        Use keyword matching to classify the user's intent (fallback method).
        """
        query = query.lower()
        matched_capabilities = {}
        
        # Check each capability's keywords
        for capability, keywords in self.fallback_keywords.items():
            matches = [keyword for keyword in keywords if keyword in query]
            if matches:
                matched_capabilities[capability] = {
                    "confidence": min(len(matches) * 0.1, 0.9),  # Higher match count = higher confidence, max 0.9
                    "matched_keywords": matches
                }
        
        # Determine primary intent
        if not matched_capabilities:
            # Default to information retrieval if no matches
            primary_intent = "information_retrieval"
            confidence = 0.5
        else:
            # Get capability with highest confidence
            primary_intent = max(matched_capabilities.items(), key=lambda x: x[1]["confidence"])[0]
            confidence = matched_capabilities[primary_intent]["confidence"]
        
        return {
            "success": True,
            "method": "keyword",
            "primary_intent": primary_intent,
            "confidence": confidence,
            "required_capabilities": list(matched_capabilities.keys()),
            "reasoning": "Classification based on keyword matching (LLM unavailable)",
            "matched_capabilities": matched_capabilities
        }

# Create singleton instance
intent_classifier = IntentClassifier()

async def classify_intent(query: str) -> Dict[str, Any]:
    """
    Classify the user's intent to determine which capabilities are needed.
    
    Args:
        query: The user's query
        
    Returns:
        Dictionary with intent classification results
    """
    return await intent_classifier.classify_intent(query)

# Test function
async def test_classification():
    """Test the intent classifier with sample queries."""
    test_queries = [
        "What files are in my Documents folder?",
        "Search for Python files in my project directory",
        "Summarize the contents of my Downloads folder",
        "What's the weather today?",
        "Open Chrome and go to Google",
        "Create a new text file on my desktop",
        "What's in my project directory?",
        "List all PDF files in my Downloads folder"
    ]
    
    for query in test_queries:
        result = await classify_intent(query)
        print(f"\nQuery: {query}")
        print(f"Primary Intent: {result['primary_intent']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Required Capabilities: {result.get('required_capabilities', [])}")
        print(f"Method: {result.get('method', 'unknown')}")
        print(f"Reasoning: {result.get('reasoning', 'None provided')}")

if __name__ == "__main__":
    asyncio.run(test_classification())