"""
Pytest configuration and fixtures for Aiayer tests
"""

import pytest
import asyncio
import tempfile
import os
import yaml
from pathlib import Path
from unittest.mock import Mock, AsyncMock

# Add project root to path
project_root = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(project_root))

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def temp_config():
    """Create a temporary configuration file for testing."""
    config = {
        'system': {
            'name': 'Test AI Assistant',
            'version': '0.1.0',
            'debug': True
        },
        'sensors': {
            'screen': {
                'enabled': False,
                'interval_sec': 1
            },
            'file': {
                'enabled': False,
                'paths': []
            },
            'process': {
                'enabled': False,
                'interval_sec': 1
            },
            'browser': {
                'enabled': False,
                'check_interval': 1
            }
        },
        'llm': {
            'model_name': 'test-model',
            'host': 'localhost',
            'port': 11434,
            'request_timeout_sec': 10,
            'temperature': 0.7,
            'max_tokens': 100
        },
        'memory': {
            'max_conversation_length': 10,
            'max_token_budget': 20,
            'store_timestamps': False
        },
        'logging': {
            'level': 'DEBUG',
            'file': 'test.log',
            'max_size_mb': 1,
            'backup_count': 1,
            'log_to_console': False
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config, f)
        temp_config_path = f.name
    
    yield temp_config_path
    
    # Cleanup
    os.unlink(temp_config_path)

@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service for testing."""
    mock_service = Mock()
    mock_service.initialize = AsyncMock(return_value=True)
    mock_service.generate_response = AsyncMock(return_value="Test response")
    mock_service.initialized = True
    return mock_service

@pytest.fixture
def mock_auth_system():
    """Create a mock authentication system for testing."""
    mock_auth = Mock()
    mock_auth.initialize = AsyncMock(return_value=True)
    mock_auth.cleanup = AsyncMock(return_value=True)
    mock_auth.authenticate = AsyncMock(return_value=True)
    return mock_auth

@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for test logs."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture
def sample_document():
    """Sample document for testing."""
    return {
        'id': 'test-doc-1',
        'title': 'Test Document',
        'content': 'This is a test document for unit testing.',
        'metadata': {
            'created': '2024-01-01T00:00:00Z',
            'modified': '2024-01-01T00:00:00Z',
            'type': 'text/plain'
        }
    }

@pytest.fixture
def sample_memory_entry():
    """Sample memory entry for testing."""
    return {
        'id': 'test-memory-1',
        'type': 'conversation',
        'content': 'Test conversation entry',
        'timestamp': '2024-01-01T00:00:00Z',
        'metadata': {
            'source': 'test',
            'priority': 'normal'
        }
    } 