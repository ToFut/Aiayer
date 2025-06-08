#!/usr/bin/env python3
"""
Test Suite for Autonomous Epiphany System

End-to-end tests for the autonomous epiphany mode, including:
- Suggestion generation from screen content
- Action item extraction
- Suggestion memory storage and retrieval
- Notification generation
- User confirmation flow
- Action execution
"""

import asyncio
import json
import logging
import os
import time
import unittest
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/tests/autonomous_epiphany_tests.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create logs directory
os.makedirs('logs/tests', exist_ok=True)

# Import components under test
try:
    from memory.suggestion_memory import get_suggestion_memory, SuggestionMemory
    from memory.action_item_extractor import get_action_extractor, ActionItemExtractor
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.error("Please run this test from the project root directory")
    raise

class TestAutonomousEpiphanySystem(unittest.IsolatedAsyncioTestCase):
    """Test cases for the autonomous epiphany system."""
    
    async def asyncSetUp(self):
        """Setup test environment."""
        # Get component instances
        self.suggestion_memory = await get_suggestion_memory()
        self.action_extractor = await get_action_extractor()
        
        # Test data
        self.test_screen_contents = {
            "email": """
            Inbox - user@example.com - Mail
            
            From: manager@example.com
            Subject: Team Meeting Thursday
            
            Hi team,
            
            Let's schedule a team meeting for Thursday at 3pm to discuss the new project timeline.
            
            Please come prepared with your status updates and any questions you may have.
            
            Best regards,
            Manager
            """,
            
            "browser": """
            Flight Search Results - Airline Website
            
            Search Results for: New York to London
            Departure: June 15, 2025
            Return: June 22, 2025
            
            Flight 1: $850 - Departing 9:00 AM - 7 hour flight - Economy
            Flight 2: $1,200 - Departing 2:00 PM - 6.5 hour flight - Economy Plus
            Flight 3: $750 - Departing 10:30 PM - 7.5 hour flight - Economy
            
            Sort by: Price (Low to High)
            """,
            
            "document": """
            Quarterly Report - Q2 2025 - Word
            
            Revenue: $2.5M
            Expenses: $1.8M
            Profit: $700K
            
            Key Metrics:
            - Customer Acquisition: +15%
            - Retention Rate: 85%
            - Average Order Value: $95
            
            Action Items:
            1. Schedule budget meeting
            2. Review marketing expenses
            3. Prepare presentation for shareholders
            """,
            
            "no_suggestion": """
            System Preferences
            
            General
            Desktop & Screen Saver
            Dock & Menu Bar
            Mission Control
            Siri
            Spotlight
            Language & Region
            Notifications
            Internet Accounts
            
            Click an item to change its settings.
            """
        }
    
    async def test_action_item_extraction(self):
        """Test extracting action items from screen content."""
        # Test with email content
        email_result = await self.action_extractor.analyze_screen_content(
            screen_content=self.test_screen_contents["email"],
            active_app="Mail"
        )
        
        # Check that suggestion was extracted
        self.assertTrue(email_result["has_suggestion"], "Should extract suggestion from email content")
        self.assertGreaterEqual(email_result["confidence"], 0.7, "Confidence should be high for clear suggestion")
        self.assertGreaterEqual(len(email_result["action_items"]), 1, "Should extract at least one action item")
        
        # Test with browser content
        browser_result = await self.action_extractor.analyze_screen_content(
            screen_content=self.test_screen_contents["browser"],
            active_app="Chrome"
        )
        
        # Check that suggestion was extracted
        self.assertTrue(browser_result["has_suggestion"], "Should extract suggestion from flight search")
        
        # Test with content that shouldn't generate suggestions
        no_sugg_result = await self.action_extractor.analyze_screen_content(
            screen_content=self.test_screen_contents["no_suggestion"],
            active_app="System Preferences"
        )
        
        # Check that no suggestion was extracted
        self.assertFalse(no_sugg_result["has_suggestion"], "Should not extract suggestion from system preferences")
    
    async def test_suggestion_memory_operations(self):
        """Test suggestion memory storage and retrieval."""
        # Create test suggestion
        test_suggestion = {
            "id": f"test_{uuid.uuid4().hex[:6]}",
            "title": "Book cheapest flight",
            "description": "I found the cheapest flight option for your trip",
            "confidence": 0.85,
            "action_items": [
                {"type": "click", "target": "Flight 3"},
                {"type": "click", "target": "Select"},
                {"type": "input_text", "target": "passenger_name", "value": "Test User"}
            ],
            "context": {
                "source": "browser",
                "app": "Chrome",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Add to suggestion memory
        suggestion_id = await self.suggestion_memory.add_suggestion(test_suggestion)
        self.assertIsNotNone(suggestion_id, "Should return suggestion ID")
        
        # Retrieve suggestion
        retrieved = await self.suggestion_memory.get_suggestion(suggestion_id)
        self.assertIsNotNone(retrieved, "Should retrieve suggestion by ID")
        self.assertEqual(retrieved["title"], test_suggestion["title"], "Title should match")
        
        # Test acceptance flow
        await self.suggestion_memory.mark_suggestion_accepted(suggestion_id)
        
        # Check metrics
        metrics = await self.suggestion_memory.get_metrics()
        self.assertGreaterEqual(metrics["accepted_suggestions"], 1, "Metrics should track accepted suggestions")
        
        # Test execution flow
        await self.suggestion_memory.mark_suggestion_executed(suggestion_id, success=True)
        
        # Verify suggestion moved to history
        retrieved_after_exec = await self.suggestion_memory.get_suggestion(suggestion_id)
        self.assertEqual(retrieved_after_exec["status"], "executed", "Status should be executed")
    
    async def test_end_to_end_flow(self):
        """Test the complete end-to-end flow."""
        # 1. Start with screen content
        screen_content = self.test_screen_contents["document"]
        active_app = "Word"
        
        # 2. Extract action items
        extraction_result = await self.action_extractor.analyze_screen_content(
            screen_content=screen_content,
            active_app=active_app
        )
        
        # Verify extraction
        self.assertTrue(extraction_result["has_suggestion"], "Should extract suggestion from document")
        suggestion_id = extraction_result.get("id")
        self.assertIsNotNone(suggestion_id, "Extraction should generate suggestion ID")
        
        # 3. Verify suggestion stored in memory
        suggestion = await self.suggestion_memory.get_suggestion(suggestion_id)
        self.assertIsNotNone(suggestion, "Suggestion should be stored in memory")
        
        # 4. Simulate user acceptance
        await self.suggestion_memory.mark_suggestion_accepted(suggestion_id)
        
        # 5. Simulate execution
        await self.suggestion_memory.mark_suggestion_executed(suggestion_id, success=True)
        
        # 6. Check metrics update
        metrics = await self.suggestion_memory.get_metrics()
        self.assertGreaterEqual(metrics["executed_suggestions"], 1, "Should track executed suggestions")
    
    async def test_multiple_suggestions(self):
        """Test handling multiple suggestions."""
        # Add several suggestions
        suggestion_ids = []
        for i in range(3):
            test_suggestion = {
                "title": f"Test Suggestion {i}",
                "description": f"This is test suggestion {i}",
                "confidence": 0.7 + (i * 0.1),  # 0.7, 0.8, 0.9
                "action_items": [
                    {"type": "click", "target": f"Button {i}"}
                ],
                "context": {
                    "source": "test",
                    "app": "TestApp"
                }
            }
            
            suggestion_id = await self.suggestion_memory.add_suggestion(test_suggestion)
            suggestion_ids.append(suggestion_id)
        
        # Get pending suggestions (should be sorted by confidence)
        pending = await self.suggestion_memory.get_all_pending_suggestions()
        self.assertEqual(len(pending), 3, "Should have 3 pending suggestions")
        
        # Verify order (highest confidence first)
        self.assertGreaterEqual(
            pending[0]["confidence"], 
            pending[1]["confidence"],
            "Pending suggestions should be sorted by confidence"
        )
        
        # Get top suggestion
        top_suggestion = await self.suggestion_memory.get_top_suggestion()
        self.assertEqual(top_suggestion["confidence"], 0.9, "Top suggestion should have highest confidence")
    
    async def test_clear_old_suggestions(self):
        """Test clearing old suggestions."""
        # Add a suggestion
        test_suggestion = {
            "title": "Old suggestion",
            "description": "This should be cleared",
            "confidence": 0.7,
            "action_items": [{"type": "click", "target": "Something"}],
            "context": {"source": "test"}
        }
        
        suggestion_id = await self.suggestion_memory.add_suggestion(test_suggestion)
        
        # Clear old suggestions (age = 0 to force clearing all)
        cleared_count = await self.suggestion_memory.clear_old_suggestions(max_age_hours=0)
        self.assertGreaterEqual(cleared_count, 1, "Should clear at least one suggestion")
        
        # Verify suggestion moved to history
        suggestion = await self.suggestion_memory.get_suggestion(suggestion_id)
        self.assertEqual(suggestion["status"], "expired", "Status should be expired")

# Extra test cases for specific scenarios
class TestSpecificScenarios(unittest.IsolatedAsyncioTestCase):
    """Test specific edge cases and scenarios."""
    
    async def asyncSetUp(self):
        """Setup test environment."""
        self.suggestion_memory = await get_suggestion_memory()
        self.action_extractor = await get_action_extractor()
    
    async def test_low_confidence_filtering(self):
        """Test filtering of low-confidence suggestions."""
        # Create low confidence suggestion
        low_conf_suggestion = {
            "title": "Low confidence suggestion",
            "description": "This should be filtered",
            "confidence": 0.3,  # Below threshold
            "action_items": [{"type": "click", "target": "Something"}],
            "context": {"source": "test"}
        }
        
        # Add to memory
        suggestion_id = await self.suggestion_memory.add_suggestion(low_conf_suggestion)
        
        # Should be rejected due to low confidence
        self.assertIsNone(suggestion_id, "Low confidence suggestion should be filtered")
    
    async def test_suggestion_rejection_flow(self):
        """Test rejection flow."""
        # Create suggestion
        test_suggestion = {
            "title": "Test rejection",
            "description": "This will be rejected",
            "confidence": 0.8,
            "action_items": [{"type": "click", "target": "Something"}],
            "context": {"source": "test", "app": "TestApp"}
        }
        
        # Add to memory
        suggestion_id = await self.suggestion_memory.add_suggestion(test_suggestion)
        
        # Reject with reason
        await self.suggestion_memory.mark_suggestion_rejected(
            suggestion_id, 
            reason="Not relevant"
        )
        
        # Verify rejection
        suggestion = await self.suggestion_memory.get_suggestion(suggestion_id)
        self.assertEqual(suggestion["status"], "rejected", "Status should be rejected")
        self.assertEqual(suggestion["rejection_reason"], "Not relevant", "Rejection reason should be stored")
        
        # Check metrics
        metrics = await self.suggestion_memory.get_metrics()
        self.assertGreaterEqual(metrics["rejected_suggestions"], 1, "Metrics should track rejections")
        
        # Verify user preferences updated
        preferences = await self.suggestion_memory.get_user_preferences()
        self.assertIn("TestApp", preferences["rejected_apps"], "App should be added to rejected apps")

# Main test runner
if __name__ == "__main__":
    async def run_tests():
        # Create test suites
        suite1 = unittest.TestLoader().loadTestsFromTestCase(TestAutonomousEpiphanySystem)
        suite2 = unittest.TestLoader().loadTestsFromTestCase(TestSpecificScenarios)
        
        # Combine suites
        all_tests = unittest.TestSuite([suite1, suite2])
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(all_tests)
        
        # Print summary
        print(f"\nTest Summary:")
        print(f"Ran {result.testsRun} tests")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        print(f"Skipped: {len(result.skipped)}")
        
        return result
    
    # Run test suite
    asyncio.run(run_tests())