"""
Test suite for sensor modules
"""
import os
import time
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import pytest
from PIL import Image
import numpy as np
from datetime import datetime

# Import sensor modules
from sensors.screen_sensor import ScreenSensor
from sensors.file_sensor import FileSensor, FileEventHandler
from sensors.process_sensor import ProcessSensor
from sensors.browser_sensor import BrowserSensor


class TestScreenSensor:
    @pytest.fixture
    def screen_sensor(self):
        """Create a screen sensor instance."""
        return ScreenSensor()

    def test_initialization(self, screen_sensor):
        """Test screen sensor initialization."""
        assert screen_sensor is not None
        assert screen_sensor.sensor_type == "screen"

    @patch('sensors.screen_sensor.ScreenSensor.capture')
    def test_capture_screen(self, mock_capture, screen_sensor):
        """Test screen capture."""
        mock_capture.return_value = "test_screenshot.png"
        result = screen_sensor.capture()
        assert result == "test_screenshot.png"

    def test_has_updates(self, screen_sensor):
        """Test update detection."""
        assert isinstance(screen_sensor.has_updates(), bool)


class TestFileSensor:
    @pytest.fixture
    def file_sensor(self):
        """Create a file sensor instance."""
        return FileSensor(paths=["/test/path"])

    def test_initialization(self, file_sensor):
        """Test file sensor initialization."""
        assert file_sensor is not None
        assert file_sensor.sensor_type == "file"
        assert file_sensor.paths == ["/test/path"]

    @patch('sensors.file_sensor.FileSensor.get_recent_events')
    def test_get_recent_events(self, mock_get_events, file_sensor):
        """Test getting recent file events."""
        mock_get_events.return_value = [
            {"type": "created", "path": "/test/path/file.txt", "time": datetime.now()}
        ]
        events = file_sensor.get_recent_events()
        assert len(events) == 1
        assert events[0]["type"] == "created"

    def test_has_updates(self, file_sensor):
        """Test update detection."""
        assert isinstance(file_sensor.has_updates(), bool)


class TestProcessSensor:
    @pytest.fixture
    def process_sensor(self):
        """Create a process sensor instance."""
        return ProcessSensor()

    def test_initialization(self, process_sensor):
        """Test process sensor initialization."""
        assert process_sensor is not None
        assert process_sensor.sensor_type == "process"

    @patch('sensors.process_sensor.ProcessSensor.get_active_process')
    def test_get_active_app(self, mock_get_active, process_sensor):
        """Test getting active application."""
        mock_get_active.return_value = "test_app"
        result = process_sensor.get_active_process()
        assert result == "test_app"

    @patch('sensors.process_sensor.ProcessSensor.get_window_title')
    def test_get_window_title(self, mock_get_title, process_sensor):
        """Test getting window title."""
        mock_get_title.return_value = "test_window"
        result = process_sensor.get_window_title()
        assert result == "test_window"

    def test_has_updates(self, process_sensor):
        """Test update detection."""
        assert isinstance(process_sensor.has_updates(), bool)


class TestBrowserSensor:
    @pytest.fixture
    def browser_sensor(self):
        """Create a browser sensor instance."""
        return BrowserSensor()

    def test_initialization(self, browser_sensor):
        """Test browser sensor initialization."""
        assert browser_sensor is not None
        assert browser_sensor.sensor_type == "browser"

    @patch('sensors.browser_sensor.BrowserSensor.get_current_url')
    def test_get_current_url(self, mock_get_url, browser_sensor):
        """Test getting current URL."""
        mock_get_url.return_value = "https://example.com"
        result = browser_sensor.get_current_url()
        assert result == "https://example.com"

    @patch('sensors.browser_sensor.BrowserSensor.get_current_title')
    def test_get_current_title(self, mock_get_title, browser_sensor):
        """Test getting current title."""
        mock_get_title.return_value = "Example Page"
        result = browser_sensor.get_current_title()
        assert result == "Example Page"

    @patch('sensors.browser_sensor.BrowserSensor.get_tab_count')
    def test_get_tab_count(self, mock_get_tabs, browser_sensor):
        """Test getting tab count."""
        mock_get_tabs.return_value = 5
        result = browser_sensor.get_tab_count()
        assert result == 5

    def test_has_updates(self, browser_sensor):
        """Test update detection."""
        assert isinstance(browser_sensor.has_updates(), bool)


class TestSensorIntegration:
    @pytest.fixture
    def sensors(self):
        """Create sensor instances for integration testing."""
        return {
            "screen": ScreenSensor(),
            "process": ProcessSensor(),
            "browser": BrowserSensor(),
            "file": FileSensor(paths=["/test/path"])
        }

    def test_sensor_initialization(self, sensors):
        """Test sensor initialization."""
        for sensor in sensors.values():
            assert sensor is not None
            assert hasattr(sensor, "sensor_type")

    def test_sensor_updates(self, sensors):
        """Test sensor update detection."""
        for sensor in sensors.values():
            assert isinstance(sensor.has_updates(), bool)

    def test_sensor_data_formatting(self, sensors):
        """Test sensor data formatting."""
        for sensor in sensors.values():
            data = sensor.get_data()
            assert isinstance(data, dict)
            assert "type" in data
            assert "timestamp" in data


if __name__ == '__main__':
    unittest.main()