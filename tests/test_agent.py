"""
Test suite for agent module
"""
import unittest
from unittest.mock import patch, MagicMock, call
import time

from agent.task_agent import TaskAgent
from agent.filter import DataFilter
from memory.memory import ConversationMemory


class TestTaskAgent(unittest.TestCase):
    """Test the task agent functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock sensors
        self.mock_screen_sensor = MagicMock()
        self.mock_screen_sensor.latest_text = "Screen text for testing"
        
        self.mock_process_sensor = MagicMock()
        self.mock_process_sensor.active_app = "TestApp"
        self.mock_process_sensor.active_window_title = "Test Window"
        self.mock_process_sensor.running_apps = ["TestApp", "Browser", "Editor"]
        
        self.mock_file_sensor = MagicMock()
        self.mock_file_sensor.get_recent_events.return_value = [
            "12:34:56: created test.txt",
            "12:35:01: modified config.yaml"
        ]
        
        self.mock_browser_sensor = MagicMock()
        self.mock_browser_sensor.current_url = "https://example.com"
        self.mock_browser_sensor.current_title = "Example Website"
        
        # Create dictionary of sensors
        self.sensors = {
            "screen": self.mock_screen_sensor,
            "process": self.mock_process_sensor,
            "file": self.mock_file_sensor,
            "browser": self.mock_browser_sensor
        }
        
        # Create mock LLM
        self.mock_llm = MagicMock()
        self.mock_llm.generate_response.return_value = "This is a test response from the LLM."
        
        # Create memory and filter
        self.memory = ConversationMemory(max_length=10)
        self.filter = DataFilter()
        
        # Create the agent
        self.agent = TaskAgent(self.sensors, self.mock_llm, self.memory, self.filter)
    
    def test_build_context_message(self):
        """Test building context information from sensors."""
        context = self.agent.build_context_message()
        
        # Check that context contains information from all sensors
        self.assertIn("Screen Text", context)
        self.assertIn("Screen text for testing", context)
        self.assertIn("Active Application: TestApp", context)
        self.assertIn("Test Window", context)
        self.assertIn("Running Apps", context)
        self.assertIn("TestApp", context)
        self.assertIn("Recent File Activity", context)
        self.assertIn("created test.txt", context)
        self.assertIn("Current Browser URL", context)
        self.assertIn("https://example.com", context)
    
    def test_handle_query(self):
        """Test processing a user query."""
        # Set up a test query
        test_query = "What am I working on right now?"
        
        # Process the query
        response = self.agent.handle_query(test_query)
        
        # Check the response
        self.assertEqual(response, "This is a test response from the LLM.")
        
        # Verify LLM was called with correct parameters
        self.mock_llm.generate_response.assert_called_once()
        # Extract the messages from the call arguments
        call_args = self.mock_llm.generate_response.call_args[0][0]
        
        # Check system message
        self.assertEqual(call_args[0]["role"], "system")
        self.assertIn("You are a helpful AI assistant", call_args[0]["content"])
        
        # Check that context was included in system message
        self.assertIn("Current context", call_args[0]["content"])
        self.assertIn("TestApp", call_args[0]["content"])
        
        # Check user message
        self.assertEqual(call_args[-1]["role"], "user")
        self.assertEqual(call_args[-1]["content"], test_query)
        
        # Check that messages were added to memory
        memory_messages = self.memory.get_all()
        self.assertEqual(len(memory_messages), 2)
        self.assertEqual(memory_messages[0]["role"], "user")
        self.assertEqual(memory_messages[0]["content"], test_query)
        self.assertEqual(memory_messages[1]["role"], "assistant")
        self.assertEqual(memory_messages[1]["content"], "This is a test response from the LLM.")
    
    @patch('agent.filter.DataFilter.contains_sensitive_data')
    def test_sensitive_data_handling(self, mock_contains_sensitive):
        """Test handling of sensitive data in responses."""
        # Set up mocks
        mock_contains_sensitive.return_value = True
        test_query = "Show me sensitive information"
        
        # Process the query - should sanitize the response
        response = self.agent.handle_query(test_query)
        
        # Check that a warning message was included
        self.assertIn("potentially sensitive information", response)
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data="Test file content")
    def test_query_with_file_context(self, mock_open, mock_exists):
        """Test query processing with file content as context."""
        # Set up mocks
        mock_exists.return_value = True
        test_query = "What does this file say?"
        test_file = "/path/to/test.txt"
        
        # Mock filter to allow file content
        with patch.object(self.filter, 'contains_sensitive_data', return_value=False):
            # Process the query with file
            self.agent.query_with_file_context(test_query, test_file)
            
            # Check that LLM was called with file content
            call_args = self.mock_llm.generate_response.call_args[0][0]
            user_message = call_args[-1]["content"]
            
            # Verify file was mentioned in the query
            self.assertIn(test_file, user_message)
            self.assertIn("Test file content", user_message)
            self.assertIn(test_query, user_message)
            
            # Verify file was opened
            mock_open.assert_called_once_with(test_file, 'r', errors='ignore')
    
    @patch('os.path.exists')
    def test_query_with_nonexistent_file(self, mock_exists):
        """Test query with a file that doesn't exist."""
        # Set up mocks
        mock_exists.return_value = False
        test_query = "What does this file say?"
        test_file = "/path/to/nonexistent.txt"
        
        # Process the query with non-existent file
        response = self.agent.query_with_file_context(test_query, test_file)
        
        # Check error message
        self.assertIn("couldn't find the file", response)
        self.assertIn(test_file, response)
        
        # Verify LLM was not called
        self.mock_llm.generate_response.assert_not_called()
    
    def test_perform_action(self):
        """Test the placeholder action handler."""
        # Try to perform an action
        response = self.agent.perform_action("open_file", file_path="test.txt")
        
        # Check that it returned a placeholder message
        self.assertIn("I understand you want me to perform an action", response)
        self.assertIn("can't directly interact", response)


class TestTaskAgentWithHistoryContextManagement(unittest.TestCase):
    """Test task agent conversation history and context management."""
    
    def setUp(self):
        """Set up test fixtures with mock components."""
        # Create simplified mocks - we'll focus on conversation history
        self.mock_sensors = {
            "screen": MagicMock(latest_text="Screen text"),
            "process": MagicMock(active_app="TestApp"),
            "file": MagicMock()
        }
        
        self.mock_llm = MagicMock()
        self.memory = ConversationMemory(max_length=5)
        self.filter = MagicMock()
        
        # Create the agent
        self.agent = TaskAgent(self.mock_sensors, self.mock_llm, self.memory, self.filter)
    
    def test_conversation_history_management(self):
        """Test that conversation history is properly managed and included in context."""
        # Add some initial history
        self.memory.add_message({"role": "user", "content": "Initial question"})
        self.memory.add_message({"role": "assistant", "content": "Initial answer"})
        
        # Process a new query
        self.agent.handle_query("Follow-up question")
        
        # Check the LLM call - should include previous messages
        call_args = self.mock_llm.generate_response.call_args[0][0]
        
        # Find history messages
        has_history = False
        for msg in call_args:
            if msg["role"] == "user" and msg["content"] == "Initial question":
                has_history = True
                break
        
        self.assertTrue(has_history, "Conversation history not included in context")
        
        # Check that the new query was added
        self.assertEqual(call_args[-1]["role"], "user")
        self.assertEqual(call_args[-1]["content"], "Follow-up question")
    
    def test_memory_overflow(self):
        """Test that memory limits are respected when context gets too large."""
        # Add maximum messages (5) to fill the memory
        for i in range(5):
            self.memory.add_message({"role": "user", "content": f"Question {i}"})
            self.memory.add_message({"role": "assistant", "content": f"Answer {i}"})
        
        # Memory should have the most recent 5 messages
        self.assertEqual(len(self.memory.get_all()), 5)
        
        # Process a new query
        self.agent.handle_query("New question")
        
        # Check memory - should still have 5 messages, with oldest removed
        all_messages = self.memory.get_all()
        self.assertEqual(len(all_messages), 5)
        
        # The newest user message should be present
        self.assertEqual(all_messages[-2]["content"], "New question")
        
        # The oldest message should be gone (Question 0 and Answer 0)
        first_msg_content = all_messages[0]["content"]
        self.assertNotEqual(first_msg_content, "Question 0")
        self.assertNotEqual(first_msg_content, "Answer 0")


if __name__ == '__main__':
    unittest.main()