#!/usr/bin/env python3
"""
Test script for the enhanced JSON parsing in universal_intelligent_automation_handler.py
Tests various problematic JSON formats to ensure they're handled correctly
"""

import asyncio
import json
import logging
import sys
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Mock classes to simulate the real environment
class LLMService:
    async def initialize(self):
        logger.info("Mock LLM service initialized")
        
    async def generate_response(self, prompt: str) -> str:
        logger.info(f"Generating mock response for prompt: {prompt[:50]}...")
        # Return the test case based on the prompt
        if "test_valid_json" in prompt:
            return self.valid_json_response()
        elif "test_markdown_json" in prompt:
            return self.markdown_json_response()
        elif "test_messy_json" in prompt:
            return self.messy_json_response()
        elif "test_single_quotes" in prompt:
            return self.single_quotes_json_response()
        elif "test_python_literals" in prompt:
            return self.python_literals_response()
        elif "test_unquoted_keys" in prompt:
            return self.unquoted_keys_response()
        elif "test_coordinate_formats" in prompt:
            return self.various_coordinate_formats_response()
        else:
            return self.valid_json_response()
    
    def valid_json_response(self):
        """Return a perfectly valid JSON response"""
        return """
{
  "title": "Search for Python Tutorials",
  "description": "Find Python tutorials online",
  "request_type": "web_search",
  "complexity_score": 0.3,
  "estimated_duration": 15,
  "success_probability": 0.9,
  "fallback_strategies": ["Try a different search engine", "Refine search terms"],
  "user_guidance_needed": false,
  "steps": [
    {
      "id": "step_1",
      "description": "Open Safari browser",
      "action_type": "open_app",
      "target": "Safari",
      "value": null,
      "coordinates": null,
      "estimated_duration": 2.0,
      "confidence": 0.95,
      "fallback_action": "Try opening Chrome instead",
      "context_hints": ["Spotlight may be used to open Safari"]
    },
    {
      "id": "step_2",
      "description": "Navigate to Google",
      "action_type": "navigate_url",
      "target": "Google homepage",
      "value": "https://www.google.com",
      "coordinates": null,
      "estimated_duration": 3.0,
      "confidence": 0.9,
      "fallback_action": "Try a different search engine",
      "context_hints": ["URL bar is at the top of the browser"]
    }
  ]
}
"""
    
    def markdown_json_response(self):
        """Return JSON wrapped in markdown code blocks"""
        return """
Based on your request, I'll create an automation plan to search for Python tutorials.

```json
{
  "title": "Search for Python Tutorials",
  "description": "Find Python tutorials online",
  "request_type": "web_search",
  "complexity_score": 0.3,
  "estimated_duration": 15,
  "success_probability": 0.9,
  "fallback_strategies": ["Try a different search engine", "Refine search terms"],
  "user_guidance_needed": false,
  "steps": [
    {
      "id": "step_1",
      "description": "Open Safari browser",
      "action_type": "open_app",
      "target": "Safari",
      "value": null,
      "coordinates": null,
      "estimated_duration": 2.0,
      "confidence": 0.95,
      "fallback_action": "Try opening Chrome instead",
      "context_hints": ["Spotlight may be used to open Safari"]
    }
  ]
}
```

This plan will help you find Python tutorials efficiently.
"""
    
    def messy_json_response(self):
        """Return JSON with missing closing braces and formatting issues"""
        return """
{
  "title": "Search for Python Tutorials",
  "description": "Find Python tutorials online",
  "request_type": "web_search",
  "complexity_score": 0.3,
  "estimated_duration": 15,
  "success_probability": 0.9,
  "fallback_strategies": ["Try a different search engine", "Refine search terms"],
  "user_guidance_needed": false,
  "steps": [
    {
      "id": "step_1",
      "description": "Open Safari browser",
      "action_type": "open_app",
      "target": "Safari",
      "value": null,
      "coordinates": null,
      "estimated_duration": 2.0,
      "confidence": 0.95,
      "fallback_action": "Try opening Chrome instead",
      "context_hints": ["Spotlight may be used to open Safari"
    },
    {
      "id": "step_2",
      "description": "Navigate to Google",
      "action_type": "navigate_url",
      "target": "Google homepage",
      "value": "https://www.google.com",
      "coordinates": null,
      "estimated_duration": 3.0,
      "confidence": 0.9,
      "fallback_action": "Try a different search engine",
      "context_hints": ["URL bar is at the top of the browser"]
    }
  ]
"""
    
    def single_quotes_json_response(self):
        """Return JSON with single quotes instead of double quotes"""
        return """
{
  'title': 'Search for Python Tutorials',
  'description': 'Find Python tutorials online',
  'request_type': 'web_search',
  'complexity_score': 0.3,
  'estimated_duration': 15,
  'success_probability': 0.9,
  'fallback_strategies': ['Try a different search engine', 'Refine search terms'],
  'user_guidance_needed': false,
  'steps': [
    {
      'id': 'step_1',
      'description': 'Open Safari browser',
      'action_type': 'open_app',
      'target': 'Safari',
      'value': null,
      'coordinates': null,
      'estimated_duration': 2.0,
      'confidence': 0.95,
      'fallback_action': 'Try opening Chrome instead',
      'context_hints': ['Spotlight may be used to open Safari']
    }
  ]
}
"""
    
    def python_literals_response(self):
        """Return JSON with Python literals (True, False, None) instead of JSON literals"""
        return """
{
  "title": "Search for Python Tutorials",
  "description": "Find Python tutorials online",
  "request_type": "web_search",
  "complexity_score": 0.3,
  "estimated_duration": 15,
  "success_probability": 0.9,
  "fallback_strategies": ["Try a different search engine", "Refine search terms"],
  "user_guidance_needed": False,
  "steps": [
    {
      "id": "step_1",
      "description": "Open Safari browser",
      "action_type": "open_app",
      "target": "Safari",
      "value": None,
      "coordinates": None,
      "estimated_duration": 2.0,
      "confidence": 0.95,
      "fallback_action": "Try opening Chrome instead",
      "context_hints": ["Spotlight may be used to open Safari"]
    }
  ]
}
"""
    
    def unquoted_keys_response(self):
        """Return JSON with unquoted keys"""
        return """
{
  title: "Search for Python Tutorials",
  description: "Find Python tutorials online",
  request_type: "web_search",
  complexity_score: 0.3,
  estimated_duration: 15,
  success_probability: 0.9,
  fallback_strategies: ["Try a different search engine", "Refine search terms"],
  user_guidance_needed: false,
  steps: [
    {
      id: "step_1",
      description: "Open Safari browser",
      action_type: "open_app",
      target: "Safari",
      value: null,
      coordinates: null,
      estimated_duration: 2.0,
      confidence: 0.95,
      fallback_action: "Try opening Chrome instead",
      context_hints: ["Spotlight may be used to open Safari"]
    }
  ]
}
"""

    def various_coordinate_formats_response(self):
        """Return JSON with various coordinate formats"""
        return """
{
  "title": "Test Different Coordinate Formats",
  "description": "Testing different coordinate formats",
  "request_type": "web_search",
  "complexity_score": 0.3,
  "estimated_duration": 15,
  "success_probability": 0.9,
  "steps": [
    {
      "id": "step_1",
      "description": "Coordinates as array",
      "action_type": "click_element",
      "coordinates": [100, 200]
    },
    {
      "id": "step_2",
      "description": "Coordinates as string",
      "action_type": "click_element",
      "coordinates": "300, 400"
    },
    {
      "id": "step_3",
      "description": "Coordinates as string with brackets",
      "action_type": "click_element",
      "coordinates": "[500, 600]"
    },
    {
      "id": "step_4",
      "description": "Coordinates as dictionary",
      "action_type": "click_element",
      "coordinates": {"x": 700, "y": 800}
    },
    {
      "id": "step_5",
      "description": "Coordinates as invalid value",
      "action_type": "click_element",
      "coordinates": "invalid"
    }
  ]
}
"""

# Import the module to test
from universal_intelligent_automation_handler import UniversalIntelligentAutomationHandler

async def test_json_parsing():
    """Test the JSON parsing capabilities of the automation handler"""
    # Create the automation handler
    handler = UniversalIntelligentAutomationHandler()
    
    # Mock the LLM service
    handler.llm_service = LLMService()
    handler.llm_initialized = True
    
    # Test cases
    test_cases = [
        "test_valid_json",
        "test_markdown_json",
        "test_messy_json",
        "test_single_quotes",
        "test_python_literals",
        "test_unquoted_keys",
        "test_coordinate_formats"
    ]
    
    print("\n===== JSON PARSING TEST RESULTS =====\n")
    
    # Run each test case
    for test_case in test_cases:
        print(f"\n----- Testing: {test_case} -----")
        try:
            # Run the test
            plan = await handler._create_advanced_llm_plan(test_case, "test_session")
            print(f"✅ SUCCESS: Created plan '{plan.title}' with {len(plan.steps)} steps")
            
            # Print some details of the plan
            print(f"  - Description: {plan.description}")
            print(f"  - Request type: {plan.request_type}")
            print(f"  - First step: {plan.steps[0].description if plan.steps else 'No steps'}")
            
            # For coordinate test, show the parsed coordinates
            if test_case == "test_coordinate_formats" and plan.steps:
                print("\n  Coordinate parsing results:")
                for step in plan.steps:
                    print(f"  - {step.description}: {step.coordinates}")
            
        except Exception as e:
            print(f"❌ FAILED: {test_case} - {type(e).__name__}: {str(e)}")
    
    print("\n===== TEST COMPLETED =====\n")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_json_parsing())