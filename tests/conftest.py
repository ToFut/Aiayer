import pytest
from flask import Flask
from ui.chat_server import app
from tests.mock_components import MockAgent, MockContextAnalyzer, MockSensor, ConversationMemory

@pytest.fixture
def test_app():
    """Create a test Flask application."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    return app

@pytest.fixture
def client(test_app):
    """Create a test client for the Flask application."""
    return test_app.test_client()

@pytest.fixture
def mock_components():
    """Create mock components for testing."""
    memory = ConversationMemory()
    agent = MockAgent()
    sensors = {
        "screen": MockSensor("screen"),
        "process": MockSensor("process"),
        "file": MockSensor("file")
    }
    return {
        "memory": memory,
        "agent": agent,
        "sensors": sensors
    }

@pytest.fixture
def initialized_app(test_app, mock_components):
    """Initialize the app with mock components."""
    test_app.agent = mock_components["agent"]
    test_app.memory = mock_components["memory"]
    test_app.sensors = mock_components["sensors"]
    return test_app 