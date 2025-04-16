"""
Test suite for agent module
"""
import unittest
from unittest.mock import patch, MagicMock, call, AsyncMock
import time
import asyncio
from datetime import datetime, timedelta

from agent.task_agent import TaskAgent
from agent.filter import DataFilter
from memory.memory import ConversationMemory
from agent.context_analyzer import ContextInsight


def async_test(coro):
    """Decorator to run async tests."""
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro(*args, **kwargs))
    return wrapper


class TestTaskAgent(unittest.TestCase):
    """Test the task agent functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock sensors
        self.mock_screen_sensor = MagicMock()
        self.mock_screen_sensor.get_data.return_value = {
            "text": "Screen text for testing",
            "has_images": False,
            "has_videos": False
        }
        
        self.mock_process_sensor = MagicMock()
        self.mock_process_sensor.get_data.return_value = {
            "active_app": "TestApp",
            "window_title": "Test Window",
            "running_apps": ["TestApp", "Browser", "Editor"],
            "usage_duration": 100
        }
        
        self.mock_file_sensor = MagicMock()
        self.mock_file_sensor.get_data.return_value = {
            "events": [
                {"path": "test.txt", "operation": "created"},
                {"path": "config.yaml", "operation": "modified"}
            ]
        }
        
        self.mock_browser_sensor = MagicMock()
        self.mock_browser_sensor.get_data.return_value = {
            "current_url": "https://example.com",
            "current_title": "Example Website",
            "tab_count": 2
        }
        
        # Create dictionary of sensors
        self.sensors = {
            "screen": self.mock_screen_sensor,
            "process": self.mock_process_sensor,
            "file": self.mock_file_sensor,
            "browser": self.mock_browser_sensor
        }
        
        # Create mock LLM with async generate_response
        self.mock_llm = MagicMock()
        self.mock_llm.generate_response = AsyncMock(return_value="This is a test response from the LLM.")
        self.mock_llm.stop = AsyncMock(return_value=True)
        
        # Create memory and filter
        self.memory = ConversationMemory(max_length=10)
        self.filter = DataFilter()
        
        # Create mock context analyzer
        self.mock_context_analyzer = MagicMock()
        self.mock_context_insight = ContextInsight(
            current_activity="Testing",
            context_summary="Unit testing the TaskAgent",
            potential_needs=["Code verification", "Bug detection"],
            attention_level="high",
            confidence_score=0.95,
            source_model="test",
            semantic_understanding={
                "task_purpose": "Testing",
                "workflow": "Unit Tests",
                "challenges": ["Test coverage"],
                "related_concepts": ["Mocking", "Assertions"],
                "implicit_goals": ["Code quality"]
            }
        )
        self.mock_context_analyzer.analyze_context = AsyncMock(return_value=self.mock_context_insight)
        
        # Create the agent
        self.agent = TaskAgent(
            self.sensors, 
            self.mock_llm, 
            self.memory, 
            self.filter,
            self.mock_context_analyzer
        )
    
    @async_test
    async def test_handle_query(self):
        """Test processing a user query."""
        # Stop background thread to prevent extra context analysis calls
        await self.agent.stop()
        
        # Set up a test query
        test_query = "What am I working on right now?"
        
        # Process the query
        response = await self.agent.handle_query(test_query)
        
        # Check the response format
        self.assertIn("[Context Analysis]", response)
        self.assertIn("[Semantic Understanding]", response)
        self.assertIn("[Response]", response)
        self.assertIn("This is a test response from the LLM.", response)
        
        # Verify context analyzer was called
        self.mock_context_analyzer.analyze_context.assert_called_once()
        
        # Check that messages were added to memory
        memory_messages = self.memory.get_recent()
        self.assertEqual(len(memory_messages), 2)
        self.assertEqual(memory_messages[0]["role"], "user")
        self.assertEqual(memory_messages[0]["content"], test_query)
        self.assertEqual(memory_messages[1]["role"], "assistant")
        self.assertIn("[Context Analysis]", memory_messages[1]["content"])
    
    @async_test
    async def test_get_current_context(self):
        """Test getting current context."""
        # Set up last context
        self.agent._last_context = self.mock_context_insight
        self.agent._last_context_time = datetime.now()
        
        context = await self.agent.get_current_context()
        self.assertEqual(context, self.mock_context_insight)
    
    @async_test
    async def test_get_context_age(self):
        """Test getting context age."""
        age = await self.agent.get_context_age()
        self.assertEqual(age, float('inf'))  # Should be infinity initially
        
        # Set a context and test age
        self.agent._last_context = ContextInsight(
            current_activity="test",
            context_summary="test",
            potential_needs=["test"],
            attention_level="medium",
            confidence_score=0.8,
            source_model="test",
            timestamp=time.time() - 10,  # 10 seconds ago
            raw_response="test",
            semantic_understanding={}
        )
        age = await self.agent.get_context_age()
        self.assertAlmostEqual(age, 10.0, delta=1.0)  # Allow 1 second difference
    
    @async_test
    async def tearDown(self):
        """Clean up after tests."""
        await self.agent.stop()


class TestTaskAgentWithHistoryContextManagement(unittest.TestCase):
    """Test task agent conversation history and context management."""
    
    def setUp(self):
        """Set up test fixtures with mock components."""
        # Create simplified mocks - we'll focus on conversation history
        self.mock_sensors = {
            "screen": MagicMock(),
            "process": MagicMock(),
            "file": MagicMock()
        }
        
        # Set up mock sensor data
        for sensor in self.mock_sensors.values():
            sensor.get_data.return_value = {}
        
        # Create mock LLM with async generate_response
        self.mock_llm = MagicMock()
        self.mock_llm.generate_response = AsyncMock(return_value="Test response")
        self.mock_llm.stop = AsyncMock(return_value=True)
        
        self.memory = ConversationMemory(max_length=5)
        self.filter = MagicMock()
        
        # Create mock context analyzer
        self.mock_context_analyzer = MagicMock()
        self.mock_context_insight = ContextInsight(
            current_activity="Testing History",
            context_summary="Testing conversation history",
            potential_needs=["Memory management"],
            attention_level="medium",
            confidence_score=0.85,
            source_model="test",
            semantic_understanding={}
        )
        self.mock_context_analyzer.analyze_context = AsyncMock(return_value=self.mock_context_insight)
        
        # Create the agent
        self.agent = TaskAgent(
            self.mock_sensors,
            self.mock_llm,
            self.memory,
            self.filter,
            self.mock_context_analyzer
        )
    
    @async_test
    async def tearDown(self):
        """Clean up after tests."""
        await self.agent.stop()
    
    @async_test
    async def test_conversation_history_management(self):
        """Test that conversation history is properly managed and included in context."""
        # Add some initial history
        self.memory.add_message({"role": "user", "content": "Initial question"})
        self.memory.add_message({"role": "assistant", "content": "Initial answer"})
        
        # Process a new query
        test_query = "Follow-up question"
        response = await self.agent.handle_query(test_query)
        
        # Check that history was included in the response
        self.assertIn("Initial question", response)
        self.assertIn("Initial answer", response)
        self.assertIn("Follow-up question", response)
        
        # Verify memory was updated
        memory_messages = self.memory.get_recent()
        self.assertEqual(len(memory_messages), 4)  # Initial messages + new query and response
    
    @async_test
    async def test_memory_overflow(self):
        """Test that memory properly handles overflow."""
        # Fill memory to capacity
        for i in range(6):
            self.memory.add_message({"role": "user", "content": f"Message {i}"})
            self.memory.add_message({"role": "assistant", "content": f"Response {i}"})
        
        # Process a new query
        test_query = "New question after overflow"
        response = await self.agent.handle_query(test_query)
        
        # Verify memory was trimmed
        memory_messages = self.memory.get_recent()
        self.assertEqual(len(memory_messages), 5)  # Max length is 5
        
        # Check that oldest messages were removed
        self.assertNotIn("Message 0", str(memory_messages))
        self.assertIn("New question after overflow", str(memory_messages))


if __name__ == '__main__':
    unittest.main()