"""
Test suite for LLM integration
"""
import unittest
from unittest.mock import patch, MagicMock, call
import json
import os
import io
import time
import responses

from llm.model import LocalLLM


class TestLocalLLM(unittest.TestCase):
    """Test the local LLM integration."""
    
    @patch('llm.model.requests.get')
    def test_init_version_check(self, mock_get):
        """Test LLM initialization with Ollama version check."""
        # Mock Ollama API version response
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"version": "0.1.0"}
        )
        
        # Initialize LLM
        llm = LocalLLM(model_name="test-model", host="localhost", port=11434)
        
        # Verify API was called
        mock_get.assert_called_once_with(
            "http://localhost:11434/api/version", 
            timeout=2
        )
    
    @patch('llm.model.requests.get')
    @patch('llm.model.requests.post')
    def test_ensure_model_availability(self, mock_post, mock_get):
        """Test model availability check and auto-download."""
        # Mock Ollama API responses
        mock_get.side_effect = [
            # First call to /api/version endpoint
            MagicMock(status_code=200, json=lambda: {"version": "0.1.0"}),
            # Second call to /api/tags endpoint
            MagicMock(status_code=200, json=lambda: {"models": []})  # No models
        ]
        
        # Mock pull model API response
        mock_pull_response = MagicMock()
        mock_pull_response.status_code = 200
        mock_pull_response.iter_lines.return_value = [
            json.dumps({"status": "pulling model"}).encode(),
            json.dumps({"status": "downloading", "completed": False}).encode(),
            json.dumps({"status": "downloading", "completed": True}).encode()
        ]
        mock_post.return_value = mock_pull_response
        
        # Initialize LLM - should auto-pull the model
        llm = LocalLLM(model_name="test-model", host="localhost", port=11434)
        
        # Check model pull was attempted
        mock_post.assert_called_once_with(
            "http://localhost:11434/api/pull",
            json={"name": "test-model"},
            stream=True
        )
    
    @patch('llm.model.requests.get')
    @patch('llm.model.requests.post')
    def test_generate_response(self, mock_post, mock_get):
        """Test response generation with model."""
        # Mock Ollama API to pass initialization
        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: {"version": "0.1.0"}),
            MagicMock(status_code=200, json=lambda: {"models": [{"name": "test-model"}]})
        ]
        
        # Mock chat API response
        mock_chat_response = MagicMock()
        mock_chat_response.status_code = 200
        mock_chat_response.json.return_value = {
            "message": {
                "role": "assistant",
                "content": "This is a test response from the LLM."
            }
        }
        mock_post.return_value = mock_chat_response
        
        # Initialize LLM and generate a response
        llm = LocalLLM(model_name="test-model", host="localhost", port=11434)
        
        # Test conversation
        conversation = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, test."}
        ]
        
        response = llm.generate_response(conversation)
        
        # Check response
        self.assertEqual(response, "This is a test response from the LLM.")
        
        # Verify API call
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["model"], "test-model")
        self.assertEqual(kwargs["json"]["messages"], conversation)
    
    @patch('llm.model.requests.get')
    @patch('llm.model.requests.post')
    def test_error_handling(self, mock_post, mock_get):
        """Test handling of API errors."""
        # Mock Ollama API to pass initialization
        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: {"version": "0.1.0"}),
            MagicMock(status_code=200, json=lambda: {"models": [{"name": "test-model"}]})
        ]
        
        # Mock API error
        mock_post.return_value = MagicMock(
            status_code=500,
            text="Internal Server Error"
        )
        
        # Initialize LLM and attempt to generate a response
        llm = LocalLLM(model_name="test-model", host="localhost", port=11434)
        response = llm.generate_response([{"role": "user", "content": "Hello"}])
        
        # Check for error indication in response
        self.assertIn("Error", response)
        self.assertIn("500", response)
    
    @patch('llm.model.requests.get')
    @patch('llm.model.requests.post')
    def test_connection_error_retry(self, mock_post, mock_get):
        """Test retry behavior on connection error."""
        # Mock Ollama API to pass initialization
        mock_get.return_value = MagicMock(
            status_code=200, 
            json=lambda: {"version": "0.1.0", "models": [{"name": "test-model"}]}
        )
        
        # Mock connection error then success
        mock_post.side_effect = [
            MagicMock(  # First call raises exception
                side_effect=TimeoutError("Connection timed out")
            ),
            MagicMock(  # Second call succeeds
                status_code=200,
                json=lambda: {"message": {"role": "assistant", "content": "Success after retry"}}
            )
        ]
        
        # Initialize LLM with retry
        llm = LocalLLM(model_name="test-model", host="localhost", port=11434)
        
        # Set short timeout for test
        response = llm.generate_response(
            [{"role": "user", "content": "Test message"}],
            timeout=1,
            max_retries=1
        )
        
        # Verify retry happened and we got the successful response
        self.assertEqual(mock_post.call_count, 2)
        self.assertEqual(response, "Success after retry")
    
    @responses.activate
    def test_api_interaction_full(self):
        """Test full API interaction with responses library."""
        # Setup responses for API endpoints
        responses.add(
            responses.GET, 
            "http://localhost:11434/api/version",
            json={"version": "0.1.14"}, 
            status=200
        )
        
        responses.add(
            responses.GET, 
            "http://localhost:11434/api/tags",
            json={"models": [{"name": "test-model"}]}, 
            status=200
        )
        
        responses.add(
            responses.POST, 
            "http://localhost:11434/api/chat",
            json={"message": {"role": "assistant", "content": "Hello! How can I help you today?"}}, 
            status=200
        )
        
        # Create LLM and generate response
        llm = LocalLLM(model_name="test-model", host="localhost", port=11434)
        response = llm.generate_response([
            {"role": "user", "content": "Hi there!"}
        ])
        
        # Check response
        self.assertEqual(response, "Hello! How can I help you today?")
        
        # Verify request that was made
        self.assertEqual(len(responses.calls), 3)
        
        # Check request body of the generate call
        request_body = json.loads(responses.calls[2].request.body)
        self.assertEqual(request_body["model"], "test-model")
        self.assertEqual(request_body["messages"][0]["role"], "user")
        self.assertEqual(request_body["messages"][0]["content"], "Hi there!")


class TestLocalLLMFallbacks(unittest.TestCase):
    """Test fallback methods for LLM integration."""
    
    @patch('llm.model.requests.get')
    @patch('llm.model.subprocess.run')
    def test_cli_fallback(self, mock_run, mock_get):
        """Test CLI fallback when API fails."""
        # Mock API failure but CLI success
        mock_get.side_effect = Exception("API not available")
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Model list output"
        mock_run.return_value = mock_result
        
        # Initialize with API error - should fall back to CLI
        with patch('llm.model.os.popen') as mock_popen:
            mock_popen.return_value = io.StringIO("test-model (loaded)\n")
            llm = LocalLLM(model_name="test-model")
            
            # Verify CLI was used
            mock_popen.assert_called()
    
    @patch('llm.model.LocalLLM._fallback_generate_windows')
    @patch('llm.model.platform.system')
    @patch('llm.model.requests.post')
    def test_windows_fallback_placeholder(self, mock_post, mock_platform, mock_fallback):
        """Test Windows fallback method (placeholder)."""
        # Mock platform to return Windows
        mock_platform.return_value = "Windows"
        
        # Mock API error
        mock_post.side_effect = Exception("Cannot connect to API")
        
        # Mock fallback to return simulated response
        mock_fallback.return_value = "Fallback Windows response"
        
        # Initialize LLM and ensure initialization passes without error
        with patch('llm.model.os.popen') as mock_popen:
            mock_popen.return_value = io.StringIO("No models found")
            llm = LocalLLM(model_name="test-model")
            
            # Attempt to generate - should use fallback
            response = llm.generate_response([{"role": "user", "content": "Test windows fallback"}])
            
            # Verify fallback was called
            mock_fallback.assert_called_once()
            self.assertEqual(response, "Fallback Windows response")


if __name__ == '__main__':
    unittest.main()