#!/usr/bin/env python3
"""
Simple Test for Autonomous Epiphany Feedback Loop

Tests the basic functionality of the feedback loop without relying on heavy neural UI components.
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

async def test_simple_feedback_loop():
    """Test the autonomous epiphany feedback loop with simplified functionality."""
    try:
        # Apply mock LLM response
        try:
            from memory.action_item_extractor import ActionItemExtractor
            ActionItemExtractor._fallback_llm_call = mock_fallback_llm_call
        except ImportError:
            print("⚠️ Could not patch action item extractor")
        
        # Import feedback loop
        from autonomous_epiphany_feedback_loop import get_autonomous_epiphany_feedback_loop
        
        # Get feedback loop instance
        feedback_loop = await get_autonomous_epiphany_feedback_loop()
        print("✅ Autonomous epiphany feedback loop initialized")
        
        # 1. PROCESS SCREEN CONTENT
        print("\n⏱️ Processing screen content...")
        result = await feedback_loop.process_screen_content(
            screen_content=SAMPLE_EMAIL_CONTENT,
            active_app="Mail"
        )
        
        if not result.get("has_suggestion", False):
            print(f"⚠️ No suggestion generated: {result.get('reason', 'Unknown reason')}")
            return False
        
        suggestion_id = result.get("suggestion_id")
        print(f"✅ Generated suggestion: {result.get('title')} (ID: {suggestion_id})")
        print(f"  Description: {result.get('description')}")
        print(f"  Confidence: {result.get('confidence')}")
        print(f"  Action items: {len(result.get('action_items', []))}")
        
        # 2. PROCESS USER FEEDBACK (ACCEPTANCE)
        print("\n⏱️ Processing user feedback (acceptance)...")
        feedback_result = await feedback_loop.handle_user_feedback(
            suggestion_id=suggestion_id,
            feedback="accepted"
        )
        print(f"✅ Processed acceptance feedback: {feedback_result}")
        
        # 3. GET INSIGHTS AFTER ACCEPTANCE
        print("\n⏱️ Getting system insights...")
        insights = await feedback_loop.get_feedback_system_insights()
        print(f"✅ System stats: {json.dumps(insights.get('system_stats', {}), indent=2)}")
        
        # 4. GET TOP SUGGESTIONS
        print("\n⏱️ Getting top suggestions...")
        top_suggestions = await feedback_loop.get_top_suggestions(max_count=3)
        print(f"✅ Found {len(top_suggestions)} top suggestions")
        
        # 5. GENERATE ANOTHER SUGGESTION
        print("\n⏱️ Generating another suggestion...")
        result2 = await feedback_loop.process_screen_content(
            screen_content=SAMPLE_EMAIL_CONTENT + "\n\nThis is a follow-up with more details.",
            active_app="Mail"
        )
        
        if result2.get("has_suggestion", False):
            suggestion_id2 = result2.get("suggestion_id")
            print(f"✅ Generated second suggestion: {result2.get('title')} (ID: {suggestion_id2})")
            
            # 6. REJECT SECOND SUGGESTION
            print("\n⏱️ Processing user feedback (rejection)...")
            feedback_result2 = await feedback_loop.handle_user_feedback(
                suggestion_id=suggestion_id2,
                feedback="rejected",
                reason="Already handled this meeting"
            )
            print(f"✅ Processed rejection feedback: {feedback_result2}")
            
            # 7. GET FINAL INSIGHTS
            print("\n⏱️ Getting final system insights...")
            final_insights = await feedback_loop.get_feedback_system_insights()
            print(f"✅ Updated system stats: {json.dumps(final_insights.get('system_stats', {}), indent=2)}")
            
            # Print any improvement suggestions
            improvements = final_insights.get('improvement_suggestions', [])
            if improvements:
                print(f"\n✅ Found {len(improvements)} improvement suggestions:")
                for i, improvement in enumerate(improvements):
                    print(f"  {i+1}. {improvement.get('suggestion', '')}")
            else:
                print("\n⚠️ No improvement suggestions found (normal for limited data)")
        
        print("\n✅ All tests completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting simple feedback loop test...")
    asyncio.run(test_simple_feedback_loop())