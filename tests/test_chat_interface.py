import unittest
import requests
from flask import Flask
from ui.chat_server import app
from tests.mock_components import MockAgent, MockContextAnalyzer, MockSensor, ConversationMemory

class TestChatInterface(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create mock components
        cls.mock_agent = MockAgent()
        cls.mock_memory = cls.mock_agent.memory  # Use the agent's memory
        cls.mock_sensors = {
            "screen": MockSensor("screen"),
            "process": MockSensor("process"),
            "file": MockSensor("file")
        }
        
        # Configure the Flask app for testing
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        cls.client = app.test_client()
        
        # Set the mock components in the app
        app.agent = cls.mock_agent
        app.memory = cls.mock_memory
        app.sensors = cls.mock_sensors

    def test_chat_interface(self):
        # Test 1: Send a simple query
        response = self.client.post(
            '/ask',
            json={'query': 'Hello, can you help me?'},
            headers={'Content-Type': 'application/json'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertFalse(data['error'])
        
        # Verify response format
        reply = data['reply']
        self.assertIn('[Context Analysis]', reply)
        self.assertIn('[Semantic Understanding]', reply)
        self.assertIn('[Response]', reply)
        self.assertIn('Current Activity:', reply)
        self.assertIn('Context Summary:', reply)
        self.assertIn('Potential Needs:', reply)
        self.assertIn('Attention Level:', reply)
        
        # Test 2: Send another query to verify context persistence
        response = self.client.post(
            '/ask',
            json={'query': 'What was my previous question?'},
            headers={'Content-Type': 'application/json'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertFalse(data['error'])
        
        # Verify memory is working
        self.assertEqual(len(self.mock_memory.get_all()), 4)  # 2 user messages + 2 assistant responses

    def test_error_handling(self):
        # Test empty query
        response = self.client.post(
            '/ask',
            json={'query': ''},
            headers={'Content-Type': 'application/json'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['error'])
        self.assertEqual(data['reply'], 'Please enter a query')

if __name__ == '__main__':
    unittest.main() 