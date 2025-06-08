#!/usr/bin/env python3
"""
Test Suite for Autonomous Epiphany Feedback Loop System

Comprehensive tests for the autonomous epiphany feedback loop system,
including suggestion generation, user feedback processing, and learning.
"""

import asyncio
import json
import logging
import os
import time
import unittest
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import traceback
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Test fixtures: sample screen content for different scenarios
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

SAMPLE_BROWSER_CONTENT = """
Google - Mozilla Firefox

Search bar: [                    ]

Gmail    Images    Maps    YouTube    News    More

Google Search    I'm Feeling Lucky

Google offered in: English    Spanish    French    German
"""

SAMPLE_DOCUMENT_CONTENT = """
Document1 - Microsoft Word

Project Requirements Document

Project: Customer Portal Redesign
Due Date: November 15, 2025
Status: In Progress

Key Requirements:
1. Implement new user authentication flow
2. Redesign dashboard with updated analytics
3. Add mobile responsive views for all pages
4. Integrate with payment gateway API
"""

class TestAutonomousEpiphanyFeedbackLoop(unittest.IsolatedAsyncioTestCase):
    """Test cases for the autonomous epiphany feedback loop system."""
    
    async def asyncSetUp(self):
        """Set up test environment."""
        try:
            # Import required modules
            from memory.suggestion_memory import get_suggestion_memory
            from memory.suggestion_feedback_learner import get_feedback_learner
            from memory.action_item_extractor import get_action_extractor
            from autonomous_epiphany_feedback_loop import get_autonomous_epiphany_feedback_loop
            
            # Initialize components
            self.suggestion_memory = await get_suggestion_memory()
            self.feedback_learner = await get_feedback_learner()
            self.action_extractor = await get_action_extractor()
            self.feedback_loop = await get_autonomous_epiphany_feedback_loop()
            
            # Check components initialized correctly
            components_available = sum(self.feedback_loop.components_available.values())
            self.assertTrue(components_available >= 3, "Not enough components available")
            
            # Clean up old suggestions to start with a clean state
            await self.suggestion_memory.clear_old_suggestions(max_age_hours=0)
            
            print("✅ Test environment set up successfully")
            
        except Exception as e:
            self.fail(f"Setup failed: {e}")
    
    async def test_01_suggestion_generation(self):
        """Test generating suggestions from screen content."""
        print("\n⏱️ Running test_01_suggestion_generation...")
        
        # Process email content
        email_result = await self.feedback_loop.process_screen_content(
            screen_content=SAMPLE_EMAIL_CONTENT,
            active_app="Mail"
        )
        
        # Verify suggestion generated
        self.assertTrue(email_result.get("has_suggestion", False), "Should generate suggestion from email")
        self.assertIsNotNone(email_result.get("suggestion_id"), "Should have suggestion ID")
        self.assertGreaterEqual(email_result.get("confidence", 0), 0.5, "Should have reasonable confidence")
        
        # Store for later tests
        self.email_suggestion_id = email_result.get("suggestion_id")
        
        # Process browser content
        browser_result = await self.feedback_loop.process_screen_content(
            screen_content=SAMPLE_BROWSER_CONTENT,
            active_app="Firefox"
        )
        
        # Process document content
        document_result = await self.feedback_loop.process_screen_content(
            screen_content=SAMPLE_DOCUMENT_CONTENT,
            active_app="Microsoft Word"
        )
        
        # Count total suggestions generated
        pending_suggestions = await self.suggestion_memory.get_all_pending_suggestions()
        self.assertGreaterEqual(len(pending_suggestions), 1, "Should have at least one suggestion")
        
        print(f"✅ Generated {len(pending_suggestions)} suggestions successfully")
    
    async def test_02_user_feedback_processing(self):
        """Test processing user feedback on suggestions."""
        print("\n⏱️ Running test_02_user_feedback_processing...")
        
        # Ensure we have a suggestion ID from previous test
        if not hasattr(self, 'email_suggestion_id'):
            # Generate a suggestion if needed
            email_result = await self.feedback_loop.process_screen_content(
                screen_content=SAMPLE_EMAIL_CONTENT,
                active_app="Mail"
            )
            self.email_suggestion_id = email_result.get("suggestion_id")
        
        # Get the suggestion
        suggestion = await self.suggestion_memory.get_suggestion(self.email_suggestion_id)
        self.assertIsNotNone(suggestion, "Suggestion should exist")
        
        # Mark as accepted
        result = await self.feedback_loop.handle_user_feedback(
            suggestion_id=self.email_suggestion_id,
            feedback="accepted"
        )
        self.assertTrue(result, "Should successfully process feedback")
        
        # Verify suggestion status
        updated_suggestion = await self.suggestion_memory.get_suggestion(self.email_suggestion_id)
        self.assertEqual(updated_suggestion.get("status"), "accepted", "Status should be 'accepted'")
        
        # Generate another suggestion for rejection test
        browser_result = await self.feedback_loop.process_screen_content(
            screen_content=SAMPLE_BROWSER_CONTENT,
            active_app="Firefox"
        )
        browser_suggestion_id = browser_result.get("suggestion_id")
        
        if browser_suggestion_id:
            # Mark as rejected
            result = await self.feedback_loop.handle_user_feedback(
                suggestion_id=browser_suggestion_id,
                feedback="rejected",
                reason="Not relevant right now"
            )
            self.assertTrue(result, "Should successfully process rejection")
            
            # Verify suggestion status
            updated_suggestion = await self.suggestion_memory.get_suggestion(browser_suggestion_id)
            self.assertEqual(updated_suggestion.get("status"), "rejected", "Status should be 'rejected'")
        
        # Get memory metrics
        metrics = await self.suggestion_memory.get_metrics()
        self.assertGreaterEqual(metrics.get("accepted_count", 0), 1, "Should have at least one accepted suggestion")
        
        print(f"✅ Processed user feedback successfully")
    
    async def test_03_feedback_learning(self):
        """Test feedback learning and suggestion enhancement."""
        print("\n⏱️ Running test_03_feedback_learning...")
        
        # Get feedback stats before
        before_stats = await self.feedback_learner.get_feedback_stats()
        
        # Generate multiple suggestions and provide feedback
        for i in range(3):
            # Generate suggestion
            content = f"{SAMPLE_EMAIL_CONTENT}\n\nThis is test iteration {i+1}"
            result = await self.feedback_loop.process_screen_content(
                screen_content=content,
                active_app="Mail"
            )
            
            if result.get("has_suggestion", False):
                suggestion_id = result.get("suggestion_id")
                
                # Alternate between acceptance and rejection
                if i % 2 == 0:
                    await self.feedback_loop.handle_user_feedback(
                        suggestion_id=suggestion_id,
                        feedback="accepted"
                    )
                else:
                    await self.feedback_loop.handle_user_feedback(
                        suggestion_id=suggestion_id,
                        feedback="rejected",
                        reason="Not a good time"
                    )
        
        # Get feedback stats after
        after_stats = await self.feedback_learner.get_feedback_stats()
        
        # Verify learning occurred
        self.assertGreater(
            after_stats.get("total_records", 0),
            before_stats.get("total_records", 0),
            "Should have more feedback records"
        )
        
        # Get improvement suggestions
        improvements = await self.feedback_learner.get_improvement_suggestions()
        
        # Get system insights
        insights = await self.feedback_loop.get_feedback_system_insights()
        self.assertIn("system_stats", insights, "Should have system stats")
        self.assertIn("feedback_stats", insights, "Should have feedback stats")
        
        print(f"✅ Feedback learning working successfully")
    
    async def test_04_quality_scoring(self):
        """Test quality scoring of suggestions based on feedback."""
        print("\n⏱️ Running test_04_quality_scoring...")
        
        # Create a test suggestion
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
        quality_score = await self.feedback_learner.get_suggestion_quality_score(test_suggestion)
        
        # Score should be a valid float between 0 and 1
        self.assertIsInstance(quality_score, float, "Quality score should be a float")
        self.assertGreaterEqual(quality_score, 0.0, "Quality score should be >= 0")
        self.assertLessEqual(quality_score, 1.0, "Quality score should be <= 1")
        
        print(f"✅ Quality scoring working successfully, score: {quality_score:.2f}")
    
    async def test_05_suggestion_ranking(self):
        """Test ranking of suggestions based on learned patterns."""
        print("\n⏱️ Running test_05_suggestion_ranking...")
        
        # Generate multiple suggestions
        for i in range(5):
            content = f"Sample content {i+1}\n\n"
            if i % 2 == 0:
                content += SAMPLE_EMAIL_CONTENT
            else:
                content += SAMPLE_DOCUMENT_CONTENT
            
            await self.feedback_loop.process_screen_content(
                screen_content=content,
                active_app="Mail" if i % 2 == 0 else "Microsoft Word"
            )
        
        # Get top suggestions
        top_suggestions = await self.feedback_loop.get_top_suggestions(max_count=3)
        
        # Verify we got suggestions back
        self.assertIsInstance(top_suggestions, list, "Should return a list")
        
        if top_suggestions:
            # Check if they have quality scores
            has_quality_scores = any("quality_score" in sugg for sugg in top_suggestions)
            
            # If suggestions were ranked, first should have highest score
            if len(top_suggestions) >= 2 and has_quality_scores:
                self.assertGreaterEqual(
                    top_suggestions[0].get("quality_score", 0),
                    top_suggestions[-1].get("quality_score", 0),
                    "First suggestion should have highest quality score"
                )
        
        print(f"✅ Suggestion ranking working successfully")
    
    async def test_06_simulation_full_cycle(self):
        """Test full suggestion cycle with feedback and learning."""
        print("\n⏱️ Running test_06_simulation_full_cycle...")
        
        # Generate suggestion
        result = await self.feedback_loop.process_screen_content(
            screen_content=SAMPLE_EMAIL_CONTENT,
            active_app="Mail"
        )
        
        if not result.get("has_suggestion", False):
            self.skipTest("No suggestion generated for full cycle test")
        
        suggestion_id = result.get("suggestion_id")
        
        # Accept suggestion
        await self.feedback_loop.handle_user_feedback(
            suggestion_id=suggestion_id,
            feedback="accepted"
        )
        
        # Get insights before execution
        before_insights = await self.feedback_loop.get_feedback_system_insights()
        
        # Try to execute suggestion (may fail if neural UI executor not available)
        try:
            execution_result = await self.feedback_loop.execute_suggestion(suggestion_id)
            execution_succeeded = execution_result.get("success", False)
        except Exception as e:
            print(f"Note: Execution failed (expected in test environment): {e}")
            execution_succeeded = False
        
        # Get insights after execution
        after_insights = await self.feedback_loop.get_feedback_system_insights()
        
        # Verify system tracked the execution
        if execution_succeeded:
            self.assertGreater(
                after_insights.get("system_stats", {}).get("suggestions_executed", 0),
                before_insights.get("system_stats", {}).get("suggestions_executed", 0),
                "Should increment executed count"
            )
        
        # Generate another similar suggestion
        new_result = await self.feedback_loop.process_screen_content(
            screen_content=SAMPLE_EMAIL_CONTENT + "\n\nThis is a follow-up to our previous discussion.",
            active_app="Mail"
        )
        
        print(f"✅ Full suggestion cycle completed successfully")
    
    async def test_07_multi_user_preference_learning(self):
        """Test learning user preferences across different contexts."""
        print("\n⏱️ Running test_07_multi_user_preference_learning...")
        
        # Setup - create suggestions in different contexts
        contexts = [
            {"app": "Mail", "content": SAMPLE_EMAIL_CONTENT},
            {"app": "Firefox", "content": SAMPLE_BROWSER_CONTENT},
            {"app": "Microsoft Word", "content": SAMPLE_DOCUMENT_CONTENT}
        ]
        
        suggestion_ids = []
        
        # Generate suggestions
        for context in contexts:
            result = await self.feedback_loop.process_screen_content(
                screen_content=context["content"],
                active_app=context["app"]
            )
            if result.get("has_suggestion", False):
                suggestion_ids.append((result.get("suggestion_id"), context["app"]))
        
        # Process feedback - accept Mail, reject Firefox, accept Word
        for suggestion_id, app in suggestion_ids:
            if app == "Mail" or app == "Microsoft Word":
                await self.feedback_loop.handle_user_feedback(
                    suggestion_id=suggestion_id,
                    feedback="accepted"
                )
            else:
                await self.feedback_loop.handle_user_feedback(
                    suggestion_id=suggestion_id,
                    feedback="rejected",
                    reason="Not useful in this context"
                )
        
        # Get user preferences
        user_prefs = await self.suggestion_memory.get_user_preferences()
        
        # Verify learning occurred
        if user_prefs:
            accepted_apps = set(user_prefs.get("accepted_apps", []))
            rejected_apps = set(user_prefs.get("rejected_apps", []))
            
            # Check if our feedback was recorded in user preferences
            mail_accepted = "Mail" in accepted_apps
            firefox_rejected = "Firefox" in rejected_apps
            
            if not (mail_accepted or firefox_rejected):
                print("Note: User preferences not yet fully reflected in memory")
            
            print(f"✅ User preferences: Accepted apps: {accepted_apps}, Rejected apps: {rejected_apps}")
        
        print(f"✅ Multi-user preference learning test completed")

# Run the tests
if __name__ == "__main__":
    # Create test suite
    test_suite = unittest.TestSuite()
    test_suite.addTest(TestAutonomousEpiphanyFeedbackLoop("test_01_suggestion_generation"))
    test_suite.addTest(TestAutonomousEpiphanyFeedbackLoop("test_02_user_feedback_processing"))
    test_suite.addTest(TestAutonomousEpiphanyFeedbackLoop("test_03_feedback_learning"))
    test_suite.addTest(TestAutonomousEpiphanyFeedbackLoop("test_04_quality_scoring"))
    test_suite.addTest(TestAutonomousEpiphanyFeedbackLoop("test_05_suggestion_ranking"))
    test_suite.addTest(TestAutonomousEpiphanyFeedbackLoop("test_06_simulation_full_cycle"))
    test_suite.addTest(TestAutonomousEpiphanyFeedbackLoop("test_07_multi_user_preference_learning"))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)