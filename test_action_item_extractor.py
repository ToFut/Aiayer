#!/usr/bin/env python3
"""
Test for Action Item Extractor

A simple test to verify the action item extraction functionality.
"""

import asyncio
import json
import logging
from datetime import datetime

# Configure logging to console only
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Sample screen content for testing
SAMPLE_EMAIL_CONTENT = """
Inbox - user@example.com - Mail

From: manager@example.com
Subject: Team Meeting Thursday

Hi team,

Let's schedule a team meeting for Thursday at 3pm to discuss the new project timeline.

Please come prepared with your status updates and any questions you may have.

Best regards,
Manager
"""

async def test_action_extractor():
    """Test the action item extractor with a sample screen content."""
    try:
        # Import action item extractor
        from memory.action_item_extractor import get_action_extractor
        
        # Get action extractor instance
        extractor = await get_action_extractor()
        print("✅ Action item extractor initialized")
        
        # Process sample content - using fallback LLM method
        print("⏱️ Analyzing screen content...")
        result = await extractor.analyze_screen_content(
            screen_content=SAMPLE_EMAIL_CONTENT,
            active_app="Mail"
        )
        
        # Check if we got a suggestion
        if result.get("has_suggestion", False):
            print("\n✅ Suggestion generated successfully:")
            print(f"  Title: {result.get('title')}")
            print(f"  Description: {result.get('description')}")
            print(f"  Confidence: {result.get('confidence')}")
            print(f"  Action items: {len(result.get('action_items', []))}")
            
            # Print action items in detail
            print("\nAction items:")
            for i, action in enumerate(result.get('action_items', [])):
                print(f"  {i+1}. Type: {action.get('type')}, Target: {action.get('target', 'N/A')}")
                if 'value' in action:
                    print(f"     Value: {action.get('value')}")
            
            # Get extractor stats
            stats = await extractor.get_stats()
            print(f"\n✅ Extractor stats: {json.dumps(stats, indent=2)}")
            
        else:
            print(f"\n⚠️ No suggestion generated: {result.get('reason', 'Unknown reason')}")
            if 'raw_response' in result:
                print(f"\nRaw LLM response: {result.get('raw_response')}")
        
        print("\n✅ Action item extractor test completed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

# Override the fallback LLM call to provide a mock response for testing
async def mock_fallback_llm_call(self, prompt):
    print("Using mock LLM response for testing")
    return """SUGGESTION: Create calendar event | I noticed you're reading about a team meeting on Thursday at 3pm | 0.87
ACTION_ITEMS:
- open_app: Calendar
- input_text: event_title as Team Meeting
- input_text: date as Thursday 3pm
- input_text: description as Discuss new project timeline
"""

# Apply the mock
try:
    from memory.action_item_extractor import ActionItemExtractor
    ActionItemExtractor._fallback_llm_call = mock_fallback_llm_call
except ImportError:
    pass

if __name__ == "__main__":
    print("Starting action item extractor test...")
    asyncio.run(test_action_extractor())