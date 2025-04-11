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

# Import sensor modules
from sensors.screen_sensor import ScreenSensor
from sensors.file_sensor import FileSensor, FileEventHandler
from sensors.process_sensor import ProcessSensor
from sensors.browser_sensor import BrowserSensor


class TestScreenSensor(unittest.TestCase):
    """Test the screen sensor functionality."""
    
    @patch('sensors.screen_sensor.mss')
    @patch('sensors.screen_sensor.pytesseract')
    def test_capture_screen_text(self, mock_pytesseract, mock_mss):
        """Test the screen capture and OCR functionality."""
        # Create a mock screenshot
        mock_screenshot = MagicMock()
        mock_screenshot.width = 800
        mock_screenshot.height = 600
        mock_screenshot.rgb = b'dummy_rgb_data'
        
        # Set up the mss mock
        mock_sct = MagicMock()
        mock_sct.__enter__.return_value = mock_sct
        mock_sct.grab.return_value = mock_screenshot
        mock_sct.monitors = [None, {'left': 0, 'top': 0, 'width': 800, 'height': 600}]
        mock_mss.mss.return_value = mock_sct
        
        # Set up the pytesseract mock to return a dummy text
        expected_text = "This is some dummy OCR text."
        mock_pytesseract.image_to_string.return_value = expected_text
        
        # Create the sensor and capture screen
        sensor = ScreenSensor(interval_sec=1)
        text = sensor.capture_screen_text()
        
        # Verify the results
        self.assertEqual(text, expected_text)
        self.assertEqual(sensor.latest_text, expected_text)
        mock_sct.grab.assert_called_once()
        mock_pytesseract.image_to_string.assert_called_once()
    
    def test_start_stop(self):
        """Test starting and stopping the sensor thread."""
        with patch.object(ScreenSensor, 'capture_screen_text', return_value="Test"):
            sensor = ScreenSensor(interval_sec=0.1)
            sensor.start()
            
            # Check that thread started
            self.assertTrue(sensor.thread is not None)
            self.assertTrue(sensor.thread.is_alive())
            
            # Stop the sensor
            sensor.stop()
            
            # Wait for thread to stop
            time.sleep(0.2)
            self.assertFalse(sensor.running)


class TestFileSensor(unittest.TestCase):
    """Test the file system sensor functionality."""
    
    def setUp(self):
        """Set up test environment with a temporary directory."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = self.temp_dir.name
        self.sensor = FileSensor(paths=[self.temp_path])
        self.handler = self.sensor.event_handler
    
    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()
    
    def test_file_created_event(self):
        """Test detection of file creation events."""
        # Simulate a file creation event
        test_file_path = os.path.join(self.temp_path, "test_file.txt")
        event = MagicMock()
        event.is_directory = False
        event.src_path = test_file_path
        
        # Call the handler method directly
        self.handler.on_created(event)
        
        # Check that the event was recorded
        self.assertGreaterEqual(len(self.sensor.recent_events), 1)
        
        # Find the event (it might not be the last one if tests run in parallel)
        found = False
        for ts, evt_type, path in self.sensor.recent_events:
            if evt_type == "created" and path == test_file_path:
                found = True
                break
        
        self.assertTrue(found, "File creation event was not recorded")
    
    def test_file_modified_event(self):
        """Test detection of file modification events."""
        # Simulate a file modification event
        test_file_path = os.path.join(self.temp_path, "test_file.txt")
        event = MagicMock()
        event.is_directory = False
        event.src_path = test_file_path
        
        # Call the handler method directly
        self.handler.on_modified(event)
        
        # Check that the event was recorded
        found = False
        for ts, evt_type, path in self.sensor.recent_events:
            if evt_type == "modified" and path == test_file_path:
                found = True
                break
        
        self.assertTrue(found, "File modification event was not recorded")
    
    def test_get_recent_events(self):
        """Test retrieving formatted recent events."""
        # Add some test events
        self.sensor.recent_events.append((time.time(), "created", os.path.join(self.temp_path, "file1.txt")))
        self.sensor.recent_events.append((time.time(), "modified", os.path.join(self.temp_path, "file2.txt")))
        
        # Get formatted events
        events = self.sensor.get_recent_events(count=2, format_str=True)
        
        # Check results
        self.assertEqual(len(events), 2)
        for event in events:
            self.assertIsInstance(event, str)
            self.assertIn("file", event)  # Should contain filename


class TestProcessSensor(unittest.TestCase):
    """Test the process monitoring sensor."""
    
    @patch('sensors.process_sensor.platform')
    @patch('sensors.process_sensor.psutil')
    def test_update_process_list(self, mock_psutil, mock_platform):
        """Test updating the list of running processes."""
        # Mock process information
        mock_proc1 = MagicMock()
        mock_proc1.info = {'name': 'test_app1', 'pid': 123}
        mock_proc2 = MagicMock()
        mock_proc2.info = {'name': 'test_app2', 'pid': 456}
        
        # Set up the psutil mock
        mock_psutil.process_iter.return_value = [mock_proc1, mock_proc2]
        
        # Create the sensor and update process list
        sensor = ProcessSensor(interval_sec=1)
        sensor.running_apps = set()  # Clear initial apps
        
        result = sensor.update_process_list()
        
        # Verify the results
        self.assertTrue(result)
        self.assertEqual(len(sensor.running_apps), 2)
        self.assertIn('test_app1', sensor.running_apps)
        self.assertIn('test_app2', sensor.running_apps)
    
    @patch('sensors.process_sensor.platform')
    @patch('sensors.process_sensor.subprocess')
    def test_update_active_window_macos(self, mock_subprocess, mock_platform):
        """Test getting active window info on macOS."""
        # Mock platform to return Darwin (macOS)
        mock_platform.system.return_value = "Darwin"
        
        # Mock subprocess to return app name and window title
        mock_subprocess.check_output.side_effect = [b"TestApp\n", b"Test Window\n"]
        
        # Create the sensor and update active window
        sensor = ProcessSensor(interval_sec=1)
        result = sensor.update_active_window()
        
        # Verify the results
        self.assertTrue(result)
        self.assertEqual(sensor.active_app, "TestApp")
        self.assertEqual(sensor.active_window_title, "Test Window")
        self.assertEqual(mock_subprocess.check_output.call_count, 2)
    
    @unittest.skip("Windows-specific test")
    def test_update_active_window_windows(self):
        """Test getting active window info on Windows (skip if not on Windows)."""
        # This test only runs on Windows with pywin32 installed
        import platform
        if platform.system() != "Windows":
            self.skipTest("Test only applicable on Windows")
        
        try:
            import win32gui
        except ImportError:
            self.skipTest("pywin32 not installed")
        
        # Create the sensor and update active window
        sensor = ProcessSensor(interval_sec=1)
        result = sensor.update_active_window()
        
        # Just verify that it runs without error and sets some values
        self.assertTrue(result)
        self.assertIsNotNone(sensor.active_app)
    
    def test_get_recent_windows(self):
        """Test retrieving window history."""
        sensor = ProcessSensor(interval_sec=1)
        
        # Add some test window history
        now = time.time()
        sensor.window_history.append((now - 10, "TestApp1", "Window1"))
        sensor.window_history.append((now - 5, "TestApp2", "Window2"))
        
        # Get recent windows
        windows = sensor.get_recent_windows(count=2)
        
        # Check results
        self.assertEqual(len(windows), 2)
        for window in windows:
            self.assertIsInstance(window, str)
            self.assertTrue("TestApp" in window)


class TestBrowserSensor(unittest.TestCase):
    """Test the browser integration sensor."""
    
    def test_update_from_browser(self):
        """Test updating browser information."""
        sensor = BrowserSensor()
        
        # Update with URL only
        sensor.update_from_browser("https://example.com")
        self.assertEqual(sensor.current_url, "https://example.com")
        self.assertIsNone(sensor.selected_text)
        
        # Update with URL and text
        sensor.update_from_browser("https://example.org", "Selected text")
        self.assertEqual(sensor.current_url, "https://example.org")
        self.assertEqual(sensor.selected_text, "Selected text")
    
    def test_get_recent_urls(self):
        """Test retrieving URL history."""
        sensor = BrowserSensor()
        
        # Add some test URL history
        now = time.time()
        sensor.url_history.append((now - 10, "https://example.com", "Example Site"))
        sensor.url_history.append((now - 5, "https://test.org", "Test Site"))
        
        # Get recent URLs
        urls = sensor.get_recent_urls(count=2)
        
        # Check results
        self.assertEqual(len(urls), 2)
        for url in urls:
            self.assertIsInstance(url, str)
            self.assertTrue("Example Site" in url or "Test Site" in url)


if __name__ == '__main__':
    unittest.main()