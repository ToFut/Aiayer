#!/usr/bin/env python3
"""
Test Agent Automation
Tests the input controller and agent capabilities on the test HTML page.
"""
import asyncio
import time
import logging
import sys
import os
import webbrowser
from datetime import datetime
import json
from typing import Dict, Any, List, Optional

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our agent components
from agent_workflow.input_controller import InputController

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestConfig:
    """Configuration for test automation."""
    
    def __init__(self, config_file: str = "test_config.json"):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        default_config = {
            "test_page": {
                "url": "file:///Users/segevbin/Desktop/SensAI/Aiayer/test_automation.html",
                "load_timeout": 3
            },
            "mouse": {
                "movement_speed": 0.5,
                "click_delay": 0.3
            },
            "keyboard": {
                "typing_speed": 0.1,
                "shortcut_delay": 0.5
            },
            "form_data": {
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "+1-555-0123",
                "country": "United States",
                "message": "This is a test message from the AI agent automation system."
            },
            "test_targets": {
                "click_positions": [
                    {"name": "Target 1", "x": 300, "y": 600},
                    {"name": "Target 2", "x": 500, "y": 600},
                    {"name": "Target 3", "x": 700, "y": 600}
                ]
            },
            "retry": {
                "max_attempts": 3,
                "delay": 1.0
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                    # Deep merge user config with defaults
                    self._deep_merge(default_config, user_config)
            return default_config
        except Exception as e:
            logger.warning(f"Failed to load config file: {str(e)}. Using defaults.")
            return default_config
    
    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> None:
        """Deep merge two dictionaries."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value

class AgentAutomationTester:
    """Test the agent automation capabilities."""
    
    def __init__(self, config_file: str = "test_config.json"):
        """Initialize the tester."""
        self.config = TestConfig(config_file)
        self.input_controller = InputController(safety_level="medium")
        self.test_results = []
        self.screenshot_dir = "test_screenshots"
        
        # Create screenshot directory if it doesn't exist
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)
    
    def take_screenshot(self, test_name: str):
        """Take a screenshot for debugging purposes."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.screenshot_dir}/{test_name}_{timestamp}.png"
            self.input_controller.take_screenshot(filename)
            return filename
        except Exception as e:
            logger.error(f"Failed to take screenshot: {str(e)}")
            return None

    def retry_on_failure(self, func, *args, **kwargs):
        """Retry a function on failure with exponential backoff."""
        for attempt in range(self.config.get("retry", {}).get("max_attempts", 3)):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == self.config.get("retry", {}).get("max_attempts", 3) - 1:
                    raise
                wait_time = self.config.get("retry", {}).get("delay", 1.0) * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results with additional metadata."""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "screenshot": self.take_screenshot(test_name) if not success else None,
            "system_info": {
                "platform": sys.platform,
                "python_version": sys.version,
                "screen_resolution": self.input_controller.get_screen_resolution()
            }
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {test_name}: {details}")
        
        if not success and result["screenshot"]:
            logger.info(f"Screenshot saved: {result['screenshot']}")
    
    def open_test_page(self):
        """Open the test HTML page in the default browser."""
        try:
            test_file = os.path.join(os.path.dirname(__file__), "test_automation.html")
            test_url = f"file://{test_file}"
            
            logger.info(f"Opening test page: {test_url}")
            webbrowser.open(test_url)
            
            # Wait for page to load
            time.sleep(self.config.get("test_page", {}).get("load_timeout", 3))
            
            self.log_test("Open Test Page", True, "Successfully opened test page")
            return True
            
        except Exception as e:
            self.log_test("Open Test Page", False, f"Error: {str(e)}")
            return False
    
    def test_basic_mouse_movement(self):
        """Test basic mouse movement."""
        try:
            logger.info("Testing mouse movement...")
            
            # Get current position
            start_pos = self.input_controller.get_current_position()
            logger.info(f"Starting position: {start_pos}")
            
            # Move to different positions
            test_positions = [
                (300, 200),
                (500, 300),
                (700, 400),
                (400, 250)
            ]
            
            for i, (x, y) in enumerate(test_positions):
                logger.info(f"Moving to position {i+1}: ({x}, {y})")
                success = self.input_controller.move_to(x, y, duration=self.config.get("mouse", {}).get("movement_speed", 0.5))
                
                if success:
                    time.sleep(0.5)  # Allow movement to complete
                    current_pos = self.input_controller.get_current_position()
                    logger.info(f"Current position: {current_pos}")
                else:
                    self.log_test("Mouse Movement", False, f"Failed to move to ({x}, {y})")
                    return False
            
            self.log_test("Mouse Movement", True, f"Successfully moved through {len(test_positions)} positions")
            return True
            
        except Exception as e:
            self.log_test("Mouse Movement", False, f"Error: {str(e)}")
            return False
    
    def test_form_filling(self):
        """Test automated form filling."""
        try:
            logger.info("Testing form filling automation...")
            
            # Define form filling sequence
            form_actions = [
                # Click on name field and type
                {"action": "click", "x": 400, "y": 320},  # Name field approximate position
                {"action": "wait", "duration": 0.5},
                {"action": "type", "text": self.config.get("form_data", {}).get("name", "John Doe")},
                
                # Tab to email field and type
                {"action": "press", "key": "tab"},
                {"action": "wait", "duration": 0.3},
                {"action": "type", "text": self.config.get("form_data", {}).get("email", "john@example.com")},
                
                # Tab to phone field and type
                {"action": "press", "key": "tab"},
                {"action": "wait", "duration": 0.3},
                {"action": "type", "text": self.config.get("form_data", {}).get("phone", "+1-555-0123")},
                
                # Tab to country dropdown and select
                {"action": "press", "key": "tab"},
                {"action": "wait", "duration": 0.3},
                {"action": "press", "key": "down"},  # Open dropdown
                {"action": "press", "key": "down"},  # Select "United States"
                {"action": "press", "key": "enter"}, # Confirm selection
                
                # Tab to message field and type
                {"action": "press", "key": "tab"},
                {"action": "wait", "duration": 0.3},
                {"action": "type", "text": self.config.get("form_data", {}).get("message", "This is a test message from the AI agent automation system.")},
                
                # Submit the form
                {"action": "press", "key": "tab"},
                {"action": "wait", "duration": 0.3},
                {"action": "press", "key": "enter"}
            ]
            
            # Execute the form filling sequence
            logger.info(f"Executing {len(form_actions)} form actions...")
            success = self.input_controller.execute_action_sequence(form_actions)
            
            if success:
                self.log_test("Form Filling", True, "Successfully filled and submitted form")
                return True
            else:
                self.log_test("Form Filling", False, "Failed to execute form filling sequence")
                return False
                
        except Exception as e:
            self.log_test("Form Filling", False, f"Error: {str(e)}")
            return False
    
    def test_click_automation(self):
        """Test clicking on various targets."""
        try:
            logger.info("Testing click automation...")
            
            # Approximate positions of click targets (these would be detected by screen analysis in real usage)
            click_targets = self.config.get("test_targets", {}).get("click_positions", [])
            
            successful_clicks = 0
            
            for target in click_targets:
                logger.info(f"Clicking on {target['name']} at ({target['x']}, {target['y']})")
                
                # Move to target and click
                if self.input_controller.move_to(target['x'], target['y'], duration=self.config.get("mouse", {}).get("click_delay", 0.3)):
                    time.sleep(0.3)
                    if self.input_controller.click():
                        successful_clicks += 1
                        time.sleep(0.5)  # Wait between clicks
                
            if successful_clicks == len(click_targets):
                self.log_test("Click Automation", True, f"Successfully clicked {successful_clicks}/{len(click_targets)} targets")
                return True
            else:
                self.log_test("Click Automation", False, f"Only clicked {successful_clicks}/{len(click_targets)} targets")
                return False
                
        except Exception as e:
            self.log_test("Click Automation", False, f"Error: {str(e)}")
            return False
    
    def test_keyboard_shortcuts(self):
        """Test keyboard shortcut automation."""
        try:
            logger.info("Testing keyboard shortcuts...")
            
            # Click on the shortcut test textarea
            textarea_x, textarea_y = 500, 750  # Approximate position
            
            if not self.input_controller.move_to(textarea_x, textarea_y):
                self.log_test("Keyboard Shortcuts", False, "Failed to move to textarea")
                return False
            
            time.sleep(0.3)
            if not self.input_controller.click():
                self.log_test("Keyboard Shortcuts", False, "Failed to click textarea")
                return False
            
            time.sleep(0.5)
            
            # Test various keyboard shortcuts
            shortcuts_to_test = [
                # Type some text first
                {"action": "type", "text": "Testing keyboard shortcuts: "},
                
                # Test Ctrl+A (Select All)
                {"action": "hotkey", "keys": ["command", "a"]},  # Use "command" on macOS
                {"action": "wait", "duration": 0.5},
                
                # Type replacement text
                {"action": "type", "text": "Selected all and replaced! "},
                
                # Test Ctrl+C and Ctrl+V
                {"action": "hotkey", "keys": ["command", "a"]},  # Select all again
                {"action": "hotkey", "keys": ["command", "c"]},  # Copy
                {"action": "press", "key": "right"},  # Move cursor
                {"action": "type", "text": "\nPasted content: "},
                {"action": "hotkey", "keys": ["command", "v"]},  # Paste
                
                # Test Enter key
                {"action": "press", "key": "enter"},
                {"action": "type", "text": "Keyboard shortcuts test completed!"}
            ]
            
            # Execute shortcuts
            success = self.input_controller.execute_action_sequence(shortcuts_to_test)
            
            if success:
                self.log_test("Keyboard Shortcuts", True, "Successfully executed keyboard shortcuts")
                return True
            else:
                self.log_test("Keyboard Shortcuts", False, "Failed to execute keyboard shortcuts")
                return False
                
        except Exception as e:
            self.log_test("Keyboard Shortcuts", False, f"Error: {str(e)}")
            return False
    
    def test_complex_workflow(self):
        """Test a complex workflow combining multiple actions."""
        try:
            logger.info("Testing complex workflow...")
            
            # Complex workflow: Navigate through page and perform multiple actions
            workflow_actions = [
                # Scroll to top of page
                {"action": "scroll", "clicks": -5},
                {"action": "wait", "duration": 1},
                
                # Click on first form field
                {"action": "click", "x": 400, "y": 320},
                {"action": "wait", "duration": 0.5},
                
                # Clear and fill form with different data
                {"action": "hotkey", "keys": ["command", "a"]},
                {"action": "type", "text": "Agent Test User"},
                
                # Navigate to email field and fill
                {"action": "press", "key": "tab"},
                {"action": "wait", "duration": 0.3},
                {"action": "hotkey", "keys": ["command", "a"]},
                {"action": "type", "text": "agent@aitest.com"},
                
                # Scroll down to see more content
                {"action": "scroll", "clicks": 3},
                {"action": "wait", "duration": 1},
                
                # Click on one of the click targets
                {"action": "click", "x": 400, "y": 650},
                {"action": "wait", "duration": 0.5},
                
                # Scroll back up
                {"action": "scroll", "clicks": -3},
                {"action": "wait", "duration": 1}
            ]
            
            success = self.input_controller.execute_action_sequence(workflow_actions)
            
            if success:
                self.log_test("Complex Workflow", True, "Successfully executed complex workflow")
                return True
            else:
                self.log_test("Complex Workflow", False, "Failed to execute complex workflow")
                return False
                
        except Exception as e:
            self.log_test("Complex Workflow", False, f"Error: {str(e)}")
            return False
    
    def generate_html_report(self, output_file: str = "test_report.html"):
        """Generate an HTML report of test results."""
        try:
            total_tests = len(self.test_results)
            passed_tests = sum(1 for r in self.test_results if r["success"])
            failed_tests = total_tests - passed_tests
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Test Automation Report</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .header {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
                    .summary {{ margin: 20px 0; }}
                    .test-case {{ margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
                    .pass {{ background: #e8f5e9; }}
                    .fail {{ background: #ffebee; }}
                    .screenshot {{ max-width: 800px; margin: 10px 0; }}
                    .details {{ margin-top: 10px; font-size: 0.9em; }}
                    .timestamp {{ color: #666; font-size: 0.8em; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Test Automation Report</h1>
                    <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <div class="summary">
                    <h2>Summary</h2>
                    <p>Total Tests: {total_tests}</p>
                    <p>Passed: {passed_tests}</p>
                    <p>Failed: {failed_tests}</p>
                    <p>Success Rate: {(passed_tests/total_tests*100):.1f}%</p>
                </div>
                
                <div class="test-cases">
                    <h2>Test Cases</h2>
            """
            
            for result in self.test_results:
                status_class = "pass" if result["success"] else "fail"
                html_content += f"""
                    <div class="test-case {status_class}">
                        <h3>{result['test']}</h3>
                        <p>Status: {'✅ PASS' if result['success'] else '❌ FAIL'}</p>
                        <p>Details: {result['details']}</p>
                        <p class="timestamp">Time: {result['timestamp']}</p>
                """
                
                if not result["success"] and result["screenshot"]:
                    html_content += f"""
                        <div class="screenshot">
                            <h4>Screenshot:</h4>
                            <img src="{result['screenshot']}" alt="Test failure screenshot">
                        </div>
                    """
                
                if "system_info" in result:
                    html_content += """
                        <div class="details">
                            <h4>System Information:</h4>
                            <ul>
                    """
                    for key, value in result["system_info"].items():
                        html_content += f"<li>{key}: {value}</li>"
                    html_content += "</ul></div>"
                
                html_content += "</div>"
            
            html_content += """
                </div>
            </body>
            </html>
            """
            
            with open(output_file, 'w') as f:
                f.write(html_content)
            
            logger.info(f"HTML report generated: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate HTML report: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all test cases and generate report."""
        try:
            logger.info("Starting test suite...")
            
            # Run all test cases
            test_cases = [
                self.test_basic_mouse_movement,
                self.test_form_filling,
                self.test_click_automation,
                self.test_keyboard_shortcuts,
                self.test_complex_workflow
            ]
            
            for test_case in test_cases:
                self.retry_on_failure(test_case)
            
            # Generate report
            self.generate_html_report()
            
            # Print summary
            passed = sum(1 for r in self.test_results if r["success"])
            total = len(self.test_results)
            self.print_test_summary(passed, total)
            
            return passed == total
            
        except Exception as e:
            logger.error(f"Test suite failed: {str(e)}")
            return False
    
    def print_test_summary(self, passed: int, total: int):
        """Print test summary."""
        logger.info("\n" + "=" * 50)
        logger.info("🧪 AUTOMATION TEST RESULTS")
        logger.info("=" * 50)
        
        for result in self.test_results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            logger.info(f"{status} - {result['test']}: {result['details']}")
        
        logger.info("=" * 50)
        success_rate = (passed / total) * 100 if total > 0 else 0
        logger.info(f"📊 SUMMARY: {passed}/{total} tests passed ({success_rate:.1f}%)")
        
        if passed == total:
            logger.info("🎉 All tests passed! Agent automation is working correctly.")
        elif passed > total * 0.7:
            logger.info("⚠️  Most tests passed. Minor issues may need attention.")
        else:
            logger.info("❌ Multiple tests failed. Agent automation needs debugging.")
        
        logger.info("=" * 50)

def main():
    """Main function to run automation tests."""
    try:
        tester = AgentAutomationTester()
        tester.run_all_tests()
        
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
    except Exception as e:
        logger.error(f"Test error: {e}")
    finally:
        logger.info("Test completed")

if __name__ == "__main__":
    main()