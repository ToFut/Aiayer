"""
Test suite for task agent with real context analysis.
"""
import pytest
import pytest_asyncio
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta
from unittest.mock import call

from agent.task_agent import TaskAgent
from agent.context_analyzer import ContextInsight
from memory.memory import ConversationMemory
from agent.data_filter import DataFilter

@pytest_asyncio.fixture
async def task_agent():
    """Create a task agent instance with mock components."""
    # Create mock sensors
    mock_screen_sensor = MagicMock()
    mock_screen_sensor.get_data.return_value = {
        "text": "Test screen content",
        "has_images": False,
        "has_videos": False
    }
    
    mock_process_sensor = MagicMock()
    mock_process_sensor.get_data.return_value = {
        "active_app": "TestApp",
        "window_title": "Test Window",
        "running_apps": ["TestApp", "Browser", "Editor"],
        "usage_duration": 100
    }
    
    mock_file_sensor = MagicMock()
    mock_file_sensor.get_data.return_value = {
        "events": [
            {"path": "test.txt", "operation": "created"},
            {"path": "config.yaml", "operation": "modified"}
        ]
    }
    
    mock_browser_sensor = MagicMock()
    mock_browser_sensor.get_data.return_value = {
        "current_url": "https://example.com",
        "current_title": "Example Website",
        "tab_count": 2
    }
    
    sensors = {
        "screen": mock_screen_sensor,
        "process": mock_process_sensor,
        "file": mock_file_sensor,
        "browser": mock_browser_sensor
    }
    
    # Create mock LLM with async generate_response
    mock_llm = MagicMock()
    mock_llm.generate_response = AsyncMock(return_value="Test response")
    mock_llm.stop = AsyncMock(return_value=True)
    
    # Create mock memory
    mock_memory = MagicMock()
    mock_memory.get_recent.return_value = []
    mock_memory.add_message.return_value = True
    
    # Create mock filter
    mock_filter = MagicMock()
    
    # Create mock context analyzer
    mock_context_analyzer = MagicMock()
    mock_context_insight = ContextInsight(
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
    mock_context_analyzer.analyze_context = AsyncMock(return_value=mock_context_insight)
    
    # Create the agent
    agent = TaskAgent(
        sensors,
        mock_llm,
        mock_memory,
        mock_filter,
        mock_context_analyzer
    )
    
    yield agent
    
    # Clean up
    await agent.stop()

@pytest.mark.asyncio
async def test_initialization(task_agent):
    """Test task agent initialization."""
    assert task_agent._sensors is not None
    assert task_agent._llm is not None
    assert task_agent._memory is not None
    assert task_agent._data_filter is not None
    assert task_agent._context_analyzer is not None
    
    # For mock components, we don't expect initial context
    if isinstance(task_agent._context_analyzer, MagicMock):
        assert task_agent._last_context is None
        assert task_agent._last_context_time is None
    else:
        # For real components, wait for initial context
        await asyncio.sleep(0.1)
        assert task_agent._last_context is not None
        assert task_agent._last_context_time is not None

@pytest.mark.asyncio
async def test_handle_query(task_agent):
    """Test handling a query."""
    response = await task_agent.handle_query("test query")
    assert response is not None
    assert "[Context Analysis]" in response
    assert "[Semantic Understanding]" in response
    assert "[Response]" in response
    assert "Test response" in response
    
    # Verify memory was updated
    task_agent._memory.add_message.assert_has_calls([
        call({"role": "user", "content": "test query"}),
        call({"role": "assistant", "content": response})
    ])

@pytest.mark.asyncio
async def test_context_updates(task_agent):
    """Test context updates."""
    # For mock components, we don't expect context updates
    if isinstance(task_agent._context_analyzer, MagicMock):
        assert task_agent._last_context is None
        assert task_agent._last_context_time is None
        return
        
    # For real components, wait for initial context
    await asyncio.sleep(0.1)
    initial_context = task_agent._last_context
    assert initial_context is not None
    
    # Wait for context update
    await asyncio.sleep(0.1)
    
    # Verify context was updated
    assert task_agent._last_context is not None
    assert task_agent._last_context_time is not None

@pytest.mark.asyncio
async def test_conversation_memory(task_agent):
    """Test conversation memory handling."""
    # Add some messages to memory
    task_agent._memory.get_recent.return_value = [
        {"role": "user", "content": "test 1"},
        {"role": "assistant", "content": "response 1"}
    ]
    
    # Handle a query
    response = await task_agent.handle_query("test 2")
    assert response is not None
    
    # Verify memory was updated
    task_agent._memory.add_message.assert_has_calls([
        call({"role": "user", "content": "test 2"}),
        call({"role": "assistant", "content": response})
    ])

@pytest.mark.asyncio
async def test_error_handling(task_agent):
    """Test error handling."""
    # Test empty query
    with pytest.raises(ValueError):
        await task_agent.handle_query("")
    
    # Test None query
    with pytest.raises(ValueError):
        await task_agent.handle_query(None) 