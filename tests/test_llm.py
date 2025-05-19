"""
Test suite for LLM integration
"""
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import json
import aiohttp
from llm.model import LocalLLM

class TestLocalLLM:
    @pytest_asyncio.fixture
    async def llm(self):
        """Create a LocalLLM instance with mocked Ollama API."""
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        
        # Mock version check response
        version_response = AsyncMock()
        version_response.status = 200
        version_response.json.return_value = {"version": "0.1.0"}
        
        # Mock model list response
        model_response = AsyncMock()
        model_response.status = 200
        model_response.json.return_value = {"models": [{"name": "ollam3.2:latest"}]}
        
        # Mock chat response
        chat_response = AsyncMock()
        chat_response.status = 200
        chat_response.json.return_value = {
            "message": {
                "role": "assistant",
                "content": "Test response"
            }
        }
        
        # Set up mock responses
        mock_session.get.side_effect = [version_response, model_response]
        mock_session.post.return_value = chat_response
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            llm = LocalLLM()
            await llm.start()  # Initialize the LLM
            yield llm
            await llm.stop()

    @pytest.mark.asyncio
    async def test_initialization(self, llm):
        """Test LLM initialization."""
        assert llm is not None
        assert llm.model_name == "ollam3.2:latest"
        assert llm.host == "localhost"
        assert llm.port == 11434
        assert llm.running is True

    @pytest.mark.asyncio
    async def test_generate_response(self, llm):
        """Test response generation."""
        messages = [
            {"role": "user", "content": "Hello, how are you?"}
        ]
        
        response = await llm.generate_response(messages)
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_generate_response_with_system_prompt(self, llm):
        """Test response generation with system prompt."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What's the weather like?"}
        ]
        
        response = await llm.generate_response(messages)
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_generate_response_with_history(self, llm):
        """Test response generation with conversation history."""
        messages = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello! How can I help you?"},
            {"role": "user", "content": "What's the weather?"}
        ]
        
        response = await llm.generate_response(messages)
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_generate_response_with_long_input(self, llm):
        """Test response generation with long input."""
        long_text = " ".join(["test"] * 1000)
        messages = [
            {"role": "user", "content": long_text}
        ]
        
        response = await llm.generate_response(messages)
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_generate_response_with_special_characters(self, llm):
        """Test response generation with special characters."""
        messages = [
            {"role": "user", "content": "Hello! @#$%^&*()_+{}|:\"<>?[]\\;',./"}
        ]
        
        response = await llm.generate_response(messages)
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_generate_response_error_handling(self, llm):
        """Test error handling in response generation."""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.post.side_effect = Exception("Test error")
            
            messages = [{"role": "user", "content": "Hello"}]
            response = await llm.generate_response(messages)
            
            assert isinstance(response, str)
            assert "error" in response.lower()

    @pytest.mark.asyncio
    async def test_generate_response_with_empty_input(self, llm):
        """Test response generation with empty input."""
        messages = []
        response = await llm.generate_response(messages)
        assert isinstance(response, str)
        assert "error" in response.lower()

    @pytest.mark.asyncio
    async def test_generate_response_with_invalid_role(self, llm):
        """Test response generation with invalid role."""
        messages = [
            {"role": "invalid", "content": "Hello"}
        ]
        response = await llm.generate_response(messages)
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_generate_response_with_none_content(self, llm):
        """Test response generation with None content."""
        messages = [
            {"role": "user", "content": None}
        ]
        response = await llm.generate_response(messages)
        assert isinstance(response, str)
        assert "error" in response.lower()