#!/usr/bin/env python3
"""
Test for Suggestion Feedback Learner

A simple test to verify the feedback learning system works correctly.
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

async def test_feedback_learner():
    """Test the feedback learner with simple suggestion examples."""
    try:
        # Import feedback learner
        from memory.suggestion_feedback_learner import get_feedback_learner, SuggestionFeature, FeedbackRecord
        
        # Get feedback learner instance
        learner = await get_feedback_learner()
        print("✅ Feedback learner initialized")
        
        # Create test feedback records directly (without needing suggestion memory)
        test_features = [
            SuggestionFeature("app", "Mail", 1.5),
            SuggestionFeature("action_type", "create_calendar", 1.2),
            SuggestionFeature("time_of_day", "afternoon", 1.0),
            SuggestionFeature("suggestion_type", "calendar", 1.3)
        ]
        
        # Create and process accepted feedback
        accepted_feedback = FeedbackRecord(
            suggestion_id="test_suggestion_1",
            features=test_features,
            outcome="accepted"
        )
        
        # Add feedback directly to the learner's records
        learner.feedback_records.append(accepted_feedback)
        
        # Update feature success rates manually
        learner._update_feature_success_rates(accepted_feedback)
        
        print("✅ Added accepted feedback record")
        
        # Create and process rejected feedback with different features
        rejected_features = [
            SuggestionFeature("app", "Firefox", 1.5),
            SuggestionFeature("action_type", "web_search", 1.2),
            SuggestionFeature("time_of_day", "morning", 1.0),
            SuggestionFeature("suggestion_type", "search", 1.3)
        ]
        
        rejected_feedback = FeedbackRecord(
            suggestion_id="test_suggestion_2",
            features=rejected_features,
            outcome="rejected",
            rejection_reason="Not relevant right now"
        )
        
        # Add feedback directly
        learner.feedback_records.append(rejected_feedback)
        learner._update_feature_success_rates(rejected_feedback)
        learner.rejection_reasons[rejected_feedback.rejection_reason] += 1
        
        print("✅ Added rejected feedback record")
        
        # Test suggestion for quality scoring
        test_suggestion = {
            "title": "Create calendar event for team meeting",
            "description": "I noticed you're reading an email about a team meeting on Thursday",
            "confidence": 0.75,
            "action_items": [
                {"type": "open_app", "target": "Calendar"},
                {"type": "input_text", "target": "event_title", "value": "Team Meeting"},
                {"type": "input_text", "target": "date", "value": "Thursday 3pm"}
            ],
            "context": {
                "source": "email",
                "app": "Mail",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Calculate quality score
        quality_score = await learner.get_suggestion_quality_score(test_suggestion)
        print(f"✅ Quality score for test suggestion: {quality_score:.2f}")
        
        # Get feedback stats
        stats = await learner.get_feedback_stats()
        print(f"✅ Feedback stats: {json.dumps(stats, indent=2)}")
        
        # Get improvement suggestions
        improvements = await learner.get_improvement_suggestions()
        print(f"✅ Improvement suggestions: {len(improvements)}")
        for i, improvement in enumerate(improvements):
            print(f"  {i+1}. {improvement.get('suggestion', '')}")
        
        print("\n✅ All tests completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting feedback learner test...")
    asyncio.run(test_feedback_learner())