#!/usr/bin/env python3
"""
Test the intent classification fix for Agent mode
Tests whether "search Spotify omer adam" is correctly routed to Ask mode instead of creating automation plans
"""

import asyncio
import sys
import os
import time
from dataclasses import dataclass

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the improved agent mode handler
from brain.handlers.improved_agent_mode_handler import ImprovedAgentModeHandler
from brain.core.brain_router import ChatRequest, ChatMode
from intent_classifier import classify_user_intent

async def test_intent_classification_fix():
    """Test the intent classification fix"""
    
    print("🧪 Testing Intent Classification Fix")
    print("=" * 60)
    
    # Test queries
    test_queries = [
        "search Spotify omer adam",  # Should route to Ask mode
        "open Safari and go to Google",  # Should create automation plan
        "what is the weather today?",  # Should route to Ask mode
        "suggest good restaurants",  # Should route to Suggest mode
        "help me book a flight",  # Should create automation plan
    ]
    
    # Test intent classifier first
    print("\n🔍 Testing Intent Classifier:")
    print("-" * 40)
    
    for query in test_queries:
        result = classify_user_intent(query)
        print(f"Query: '{query}'")
        print(f"Intent: {result.intent.value}")
        print(f"Should Automate: {result.should_automate}")
        print(f"Suggested Mode: {result.suggested_mode}")
        print(f"Confidence: {result.confidence:.2f}")
        print()
    
    # Test the improved agent mode handler
    print("\n🤖 Testing Improved Agent Mode Handler:")
    print("-" * 40)
    
    handler = ImprovedAgentModeHandler()
    
    for query in test_queries:
        print(f"\nTesting: '{query}'")
        
        # Create a test request
        request = ChatRequest(
            mode=ChatMode.AGENT,
            query=query,
            user_id="test_user",
            session_id="test_session",
            timestamp=time.time(),
            context={}
        )
        
        try:
            # Handle the request
            response = await handler.handle_request(request)
            
            print(f"Success: {response.success}")
            print(f"Mode Used: {response.mode_used.value}")
            print(f"Processing Time: {response.processing_time:.2f}s")
            print(f"Confidence: {response.confidence:.2f}")
            
            # Check metadata for routing information
            metadata = response.metadata
            if "routed_to" in metadata:
                print(f"🔀 Routed from Agent to {metadata['routed_to']}")
                print(f"Intent: {metadata.get('intent_classification', 'unknown')}")
                print(f"Intent Confidence: {metadata.get('intent_confidence', 0):.2f}")
                print(f"Reasoning: {metadata.get('intent_reasoning', 'none')}")
            elif "automation_plan_created" in metadata:
                if metadata["automation_plan_created"]:
                    print("🤖 Automation plan created")
                else:
                    print("❌ Automation plan failed")
            
            # Show first 100 characters of response
            response_preview = response.response[:100]
            if len(response.response) > 100:
                response_preview += "..."
            print(f"Response: {response_preview}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 40)

if __name__ == "__main__":
    asyncio.run(test_intent_classification_fix())