"""
Unit tests for main application entry point
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from main import AiayerApplication

class TestAiayerApplication:
    """Test cases for AiayerApplication class"""
    
    @pytest.mark.asyncio
    async def test_application_initialization(self, temp_config):
        """Test application initialization with valid config"""
        app = AiayerApplication(temp_config)
        
        # Mock the dependencies
        with patch('main.AuthSystem') as mock_auth_class, \
             patch('main.EnhancedEnterpriseBackend') as mock_backend_class, \
             patch('main.setup_logging') as mock_setup_logging:
            
            mock_auth = Mock()
            mock_auth.initialize = AsyncMock(return_value=True)
            mock_auth_class.return_value = mock_auth
            
            mock_backend = Mock()
            mock_backend.initialize = AsyncMock(return_value=True)
            mock_backend_class.return_value = mock_backend
            
            # Test initialization
            result = await app.initialize()
            
            assert result is True
            assert app.auth_system is not None
            assert app.backend is not None
            mock_setup_logging.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_application_initialization_failure(self, temp_config):
        """Test application initialization failure"""
        app = AiayerApplication(temp_config)
        
        with patch('main.AuthSystem') as mock_auth_class:
            mock_auth = Mock()
            mock_auth.initialize = AsyncMock(side_effect=Exception("Auth failed"))
            mock_auth_class.return_value = mock_auth
            
            result = await app.initialize()
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_application_start(self, temp_config):
        """Test application start"""
        app = AiayerApplication(temp_config)
        
        # Mock backend
        mock_backend = Mock()
        mock_backend.start = AsyncMock(return_value=True)
        app.backend = mock_backend
        
        result = await app.start()
        
        assert result is True
        assert app.running is True
        mock_backend.start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_application_start_failure(self, temp_config):
        """Test application start failure"""
        app = AiayerApplication(temp_config)
        
        # Mock backend
        mock_backend = Mock()
        mock_backend.start = AsyncMock(side_effect=Exception("Start failed"))
        app.backend = mock_backend
        
        result = await app.start()
        
        assert result is False
        assert app.running is False
    
    @pytest.mark.asyncio
    async def test_application_stop(self, temp_config):
        """Test application stop"""
        app = AiayerApplication(temp_config)
        app.running = True
        
        # Mock dependencies
        mock_backend = Mock()
        mock_backend.stop = AsyncMock(return_value=True)
        app.backend = mock_backend
        
        mock_auth = Mock()
        mock_auth.cleanup = AsyncMock(return_value=True)
        app.auth_system = mock_auth
        
        result = await app.stop()
        
        assert result is True
        assert app.running is False
        mock_backend.stop.assert_called_once()
        mock_auth.cleanup.assert_called_once()
    
    def test_load_config_success(self, temp_config):
        """Test successful config loading"""
        app = AiayerApplication(temp_config)
        
        result = app.load_config()
        
        assert result is True
        assert app.config is not None
        assert 'system' in app.config
    
    def test_load_config_failure(self):
        """Test config loading failure"""
        app = AiayerApplication("nonexistent_config.yaml")
        
        result = app.load_config()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_application_run_success(self, temp_config):
        """Test successful application run"""
        app = AiayerApplication(temp_config)
        
        with patch.object(app, 'initialize', return_value=True), \
             patch.object(app, 'start', return_value=True), \
             patch.object(app, 'stop', return_value=True), \
             patch('asyncio.sleep') as mock_sleep:
            
            # Simulate keyboard interrupt after a short delay
            mock_sleep.side_effect = KeyboardInterrupt()
            
            await app.run()
            
            app.initialize.assert_called_once()
            app.start.assert_called_once()
            app.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_application_run_initialization_failure(self, temp_config):
        """Test application run with initialization failure"""
        app = AiayerApplication(temp_config)
        
        with patch.object(app, 'initialize', return_value=False), \
             patch('sys.exit') as mock_exit:
            
            await app.run()
            
            mock_exit.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_application_run_start_failure(self, temp_config):
        """Test application run with start failure"""
        app = AiayerApplication(temp_config)
        
        with patch.object(app, 'initialize', return_value=True), \
             patch.object(app, 'start', return_value=False), \
             patch('sys.exit') as mock_exit:
            
            await app.run()
            
            mock_exit.assert_called_once_with(1) 