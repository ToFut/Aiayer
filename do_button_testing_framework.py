#!/usr/bin/env python3
"""
Neural UI Detector Testing Framework

This script provides a comprehensive testing framework for the Neural UI Detector system.
It performs the following tests:
1. Port conflict resolution
2. UI element detection reliability
3. Detection accuracy validation
4. Integration with DO Button system
5. Performance benchmarking
"""

import asyncio
import argparse
import json
import os
import sys
import time
import logging
import subprocess
import webbrowser
import signal
import tempfile
import random
from typing import Dict, Any, List, Optional, Tuple
import websockets
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# Configure logging
os.makedirs('logs/neural_ui_detector', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/neural_ui_detector/test_framework.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("neural_ui_test_framework")

# Define server ports
NEURAL_UI_DETECTOR_PORT = 8768
DO_BUTTON_SERVER_PORT = 8765
BACKEND_SERVER_PORT = 8767
WS_PROXY_PORT = 8766

# Define paths
TEST_HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_neural_ui_detector_fixed.html")
PORT_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "neural_ui_detector_port.txt")

# Test data
TEST_UI_ELEMENTS = [
    {"type": "button", "text": "Click Me"},
    {"type": "text_field", "placeholder": "Enter text here"},
    {"type": "search_box", "placeholder": "Search..."},
    {"type": "checkbox", "label": "Check me"}
]

class NeuralUITestFramework:
    """Test framework for Neural UI Detector"""
    
    def __init__(self):
        self.processes = {}
        self.ws_client = None
        self.neural_ui_ws_url = f"ws://localhost:{NEURAL_UI_DETECTOR_PORT}"
        self.actual_port = NEURAL_UI_DETECTOR_PORT
        self.test_results = {
            "port_conflict": {"success": False, "details": ""},
            "detection_reliability": {"success": False, "details": "", "accuracy": 0.0},
            "integration": {"success": False, "details": ""},
            "performance": {"success": False, "details": "", "avg_time": 0.0}
        }
    
    async def connect_to_server(self) -> bool:
        """Connect to Neural UI Detector WebSocket server"""
        try:
            # Check if port file exists and read actual port
            if os.path.exists(PORT_FILE_PATH):
                with open(PORT_FILE_PATH, 'r') as f:
                    try:
                        port = int(f.read().strip())
                        self.actual_port = port
                        self.neural_ui_ws_url = f"ws://localhost:{port}"
                        logger.info(f"Using port from file: {port}")
                    except ValueError:
                        logger.warning(f"Invalid port in file, using default: {NEURAL_UI_DETECTOR_PORT}")
            
            # Connect to server
            logger.info(f"Connecting to Neural UI Detector at {self.neural_ui_ws_url}")
            self.ws_client = await websockets.connect(self.neural_ui_ws_url)
            
            # Wait for welcome message
            welcome = await self.ws_client.recv()
            try:
                welcome_data = json.loads(welcome)
                logger.info(f"Connected to server: {welcome_data.get('type')} - {welcome_data.get('message')}")
                return True
            except json.JSONDecodeError:
                logger.error(f"Received invalid welcome message: {welcome}")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to Neural UI Detector: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from WebSocket server"""
        if self.ws_client:
            await self.ws_client.close()
            self.ws_client = None
            logger.info("Disconnected from WebSocket server")
    
    async def start_servers(self):
        """Start Neural UI Detector and related servers"""
        try:
            # Kill any existing processes on our ports to avoid conflicts
            await self.kill_port_processes([NEURAL_UI_DETECTOR_PORT, DO_BUTTON_SERVER_PORT])
            
            # Start Neural UI Detector server
            detector_cmd = [sys.executable, "fixed_neural_ui_detector_server.py", "--port", str(NEURAL_UI_DETECTOR_PORT)]
            self.processes["detector"] = subprocess.Popen(
                detector_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            logger.info(f"Started Neural UI Detector server: PID {self.processes['detector'].pid}")
            
            # Give it some time to start
            await asyncio.sleep(2)
            
            # Verify detector is running by checking for port file
            port_found = False
            for _ in range(5):  # Try 5 times
                if os.path.exists(PORT_FILE_PATH):
                    port_found = True
                    break
                await asyncio.sleep(1)
            
            if not port_found:
                logger.error("Neural UI Detector server did not create port file")
                return False
            
            # Read actual port
            with open(PORT_FILE_PATH, 'r') as f:
                try:
                    port = int(f.read().strip())
                    self.actual_port = port
                    self.neural_ui_ws_url = f"ws://localhost:{port}"
                    logger.info(f"Neural UI Detector running on port: {port}")
                except ValueError:
                    logger.warning(f"Invalid port in file, using default: {NEURAL_UI_DETECTOR_PORT}")
            
            # Start test HTTP server for the test page
            http_port = 8080
            http_cmd = [sys.executable, "-m", "http.server", str(http_port)]
            self.processes["http"] = subprocess.Popen(
                http_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            logger.info(f"Started HTTP server: PID {self.processes['http'].pid}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to start servers: {e}")
            await self.stop_servers()
            return False
    
    async def stop_servers(self):
        """Stop all servers started by this framework"""
        for name, process in self.processes.items():
            try:
                process.terminate()
                logger.info(f"Terminated {name} server (PID {process.pid})")
            except Exception as e:
                logger.error(f"Error terminating {name} server: {e}")
        
        # Wait for processes to terminate
        await asyncio.sleep(1)
        
        # Force kill if needed
        for name, process in list(self.processes.items()):
            try:
                if process.poll() is None:
                    process.kill()
                    logger.info(f"Force killed {name} server (PID {process.pid})")
                self.processes.pop(name)
            except Exception as e:
                logger.error(f"Error killing {name} server: {e}")
        
        # Kill any remaining processes on our ports
        await self.kill_port_processes([NEURAL_UI_DETECTOR_PORT, DO_BUTTON_SERVER_PORT])
    
    async def kill_port_processes(self, ports: List[int]):
        """Kill processes using specified ports"""
        try:
            for port in ports:
                if sys.platform == "darwin" or sys.platform.startswith("linux"):
                    # For macOS and Linux, use lsof
                    result = subprocess.run(['lsof', f'-ti:{port}'], capture_output=True, text=True)
                    pids = result.stdout.strip().split('\n')
                    
                    for pid in pids:
                        if pid and pid.strip():
                            try:
                                pid_int = int(pid.strip())
                                os.kill(pid_int, signal.SIGKILL)
                                logger.info(f"Killed process {pid_int} on port {port}")
                            except (ValueError, ProcessLookupError) as e:
                                logger.warning(f"Failed to kill process {pid}: {e}")
                elif sys.platform == "win32":
                    # For Windows, use netstat and taskkill
                    result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
                    lines = result.stdout.strip().split('\n')
                    
                    for line in lines:
                        if f":{port}" in line:
                            parts = line.split()
                            if len(parts) >= 5:
                                pid = parts[4].strip()
                                try:
                                    subprocess.run(['taskkill', '/F', '/PID', pid])
                                    logger.info(f"Killed process {pid} on port {port}")
                                except Exception as e:
                                    logger.warning(f"Failed to kill process {pid}: {e}")
        except Exception as e:
            logger.error(f"Error killing port processes: {e}")
    
    async def open_test_page(self):
        """Open the test HTML page in the default browser"""
        try:
            # Use the correct port in the URL
            test_url = f"http://localhost:8080/test_neural_ui_detector_fixed.html"
            logger.info(f"Opening test page: {test_url}")
            
            # Open browser
            webbrowser.open(test_url)
            
            # Wait for the page to load
            await asyncio.sleep(2)
            
            return True
        except Exception as e:
            logger.error(f"Failed to open test page: {e}")
            return False
    
    async def test_port_conflict_resolution(self) -> bool:
        """Test port conflict resolution by starting another server on the same port"""
        logger.info("Testing port conflict resolution...")
        
        try:
            # Record the original port
            original_port = self.actual_port
            logger.info(f"Original Neural UI Detector port: {original_port}")
            
            # Try to start another server on the same port
            conflict_cmd = [sys.executable, "fixed_neural_ui_detector_server.py", "--port", str(original_port)]
            conflict_process = subprocess.Popen(
                conflict_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            logger.info(f"Started conflicting server: PID {conflict_process.pid}")
            
            # Give it some time to start
            await asyncio.sleep(3)
            
            # Read the port file again
            if os.path.exists(PORT_FILE_PATH):
                with open(PORT_FILE_PATH, 'r') as f:
                    try:
                        new_port = int(f.read().strip())
                        logger.info(f"New server port: {new_port}")
                        
                        # Check if the port changed
                        if new_port != original_port:
                            logger.info(f"Port conflict resolution successful: {original_port} -> {new_port}")
                            self.test_results["port_conflict"] = {
                                "success": True,
                                "details": f"Successfully resolved port conflict: {original_port} -> {new_port}"
                            }
                            
                            # Kill the conflict process
                            try:
                                conflict_process.terminate()
                                await asyncio.sleep(1)
                                if conflict_process.poll() is None:
                                    conflict_process.kill()
                            except Exception as e:
                                logger.error(f"Error terminating conflict process: {e}")
                            
                            return True
                    except ValueError:
                        logger.error("Invalid port in file")
            
            # Kill the conflict process
            try:
                conflict_process.terminate()
                await asyncio.sleep(1)
                if conflict_process.poll() is None:
                    conflict_process.kill()
            except Exception as e:
                logger.error(f"Error terminating conflict process: {e}")
            
            logger.error("Port conflict resolution test failed")
            self.test_results["port_conflict"] = {
                "success": False,
                "details": "Failed to resolve port conflict"
            }
            return False
        except Exception as e:
            logger.error(f"Error in port conflict test: {e}")
            self.test_results["port_conflict"] = {
                "success": False,
                "details": f"Error during test: {str(e)}"
            }
            return False
    
    async def test_detection_reliability(self, num_tests=5) -> bool:
        """Test UI element detection reliability by running multiple detections"""
        logger.info(f"Testing detection reliability with {num_tests} iterations...")
        
        try:
            if not self.ws_client or self.ws_client.closed:
                logger.info("Reconnecting to Neural UI Detector")
                connected = await self.connect_to_server()
                if not connected:
                    logger.error("Failed to connect to Neural UI Detector")
                    self.test_results["detection_reliability"] = {
                        "success": False,
                        "details": "Failed to connect to Neural UI Detector",
                        "accuracy": 0.0
                    }
                    return False
            
            # Run multiple detection tests
            detection_results = []
            
            for i in range(num_tests):
                logger.info(f"Detection test {i+1}/{num_tests}")
                
                # Send detection request
                detect_message = {
                    "action": "detect",
                    "timestamp": time.time()
                }
                
                await self.ws_client.send(json.dumps(detect_message))
                
                # Receive response with timeout
                response = None
                try:
                    response = await asyncio.wait_for(self.ws_client.recv(), timeout=30.0)
                except asyncio.TimeoutError:
                    logger.error(f"Detection test {i+1} timed out")
                    detection_results.append({"success": False, "count": 0, "time": 30.0})
                    continue
                
                try:
                    response_data = json.loads(response)
                    
                    if response_data.get("type") == "detection_result":
                        element_count = len(response_data.get("elements", []))
                        execution_time = response_data.get("execution_time", 0)
                        logger.info(f"Detection found {element_count} elements in {execution_time:.2f}s")
                        
                        detection_results.append({
                            "success": True,
                            "count": element_count,
                            "time": execution_time
                        })
                    else:
                        logger.warning(f"Unexpected response type: {response_data.get('type')}")
                        detection_results.append({"success": False, "count": 0, "time": 0})
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON response: {response[:100]}...")
                    detection_results.append({"success": False, "count": 0, "time": 0})
                
                # Wait between tests
                await asyncio.sleep(2)
            
            # Calculate success rate and average times
            success_count = sum(1 for r in detection_results if r["success"])
            success_rate = success_count / num_tests if num_tests > 0 else 0
            
            if success_count > 0:
                avg_time = sum(r["time"] for r in detection_results if r["success"]) / success_count
            else:
                avg_time = 0
            
            logger.info(f"Detection reliability: {success_rate:.2%} ({success_count}/{num_tests})")
            logger.info(f"Average detection time: {avg_time:.2f}s")
            
            # Interpret the results
            if success_rate >= 0.8:  # 80% success rate is considered good
                self.test_results["detection_reliability"] = {
                    "success": True,
                    "details": f"Detection reliability: {success_rate:.2%} ({success_count}/{num_tests})",
                    "accuracy": success_rate,
                    "avg_time": avg_time
                }
                return True
            else:
                self.test_results["detection_reliability"] = {
                    "success": False,
                    "details": f"Low detection reliability: {success_rate:.2%} ({success_count}/{num_tests})",
                    "accuracy": success_rate,
                    "avg_time": avg_time
                }
                return False
        except Exception as e:
            logger.error(f"Error in detection reliability test: {e}")
            self.test_results["detection_reliability"] = {
                "success": False,
                "details": f"Error during test: {str(e)}",
                "accuracy": 0.0
            }
            return False
    
    async def test_integration(self) -> bool:
        """Test integration with DO Button system"""
        logger.info("Testing integration with DO Button system...")
        
        try:
            if not self.ws_client or self.ws_client.closed:
                logger.info("Reconnecting to Neural UI Detector")
                connected = await self.connect_to_server()
                if not connected:
                    logger.error("Failed to connect to Neural UI Detector")
                    self.test_results["integration"] = {
                        "success": False,
                        "details": "Failed to connect to Neural UI Detector"
                    }
                    return False
            
            # Create a test plan
            plan_id = f"test_plan_{int(time.time())}"
            
            # Send execution request with multiple steps
            execute_message = {
                "action": "execute",
                "steps": [
                    {
                        "action": "detect",
                        "description": "Detect UI elements"
                    },
                    {
                        "action": "find",
                        "description": "button",
                        "element_type": "button"
                    }
                ],
                "plan_id": plan_id,
                "timestamp": time.time()
            }
            
            await self.ws_client.send(json.dumps(execute_message))
            
            # Receive response with timeout
            response = None
            try:
                response = await asyncio.wait_for(self.ws_client.recv(), timeout=30.0)
            except asyncio.TimeoutError:
                logger.error("Integration test timed out")
                self.test_results["integration"] = {
                    "success": False,
                    "details": "Test timed out waiting for response"
                }
                return False
            
            try:
                response_data = json.loads(response)
                
                if response_data.get("type") == "execute_result":
                    success = response_data.get("success", False)
                    success_count = response_data.get("success_count", 0)
                    total_steps = response_data.get("total_steps", 0)
                    
                    logger.info(f"Execution result: {success_count}/{total_steps} steps successful")
                    
                    if success:
                        self.test_results["integration"] = {
                            "success": True,
                            "details": f"Successfully executed {success_count}/{total_steps} steps"
                        }
                        return True
                    else:
                        self.test_results["integration"] = {
                            "success": False,
                            "details": f"Execution partially failed: {success_count}/{total_steps} steps successful"
                        }
                        return False
                else:
                    logger.warning(f"Unexpected response type: {response_data.get('type')}")
                    self.test_results["integration"] = {
                        "success": False,
                        "details": f"Unexpected response type: {response_data.get('type')}"
                    }
                    return False
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON response: {response[:100]}...")
                self.test_results["integration"] = {
                    "success": False,
                    "details": "Invalid JSON response"
                }
                return False
        except Exception as e:
            logger.error(f"Error in integration test: {e}")
            self.test_results["integration"] = {
                "success": False,
                "details": f"Error during test: {str(e)}"
            }
            return False
    
    async def test_performance(self, num_tests=10) -> bool:
        """Test performance by measuring detection times"""
        logger.info(f"Testing performance with {num_tests} iterations...")
        
        try:
            if not self.ws_client or self.ws_client.closed:
                logger.info("Reconnecting to Neural UI Detector")
                connected = await self.connect_to_server()
                if not connected:
                    logger.error("Failed to connect to Neural UI Detector")
                    self.test_results["performance"] = {
                        "success": False,
                        "details": "Failed to connect to Neural UI Detector",
                        "avg_time": 0.0
                    }
                    return False
            
            # Run multiple performance tests
            performance_results = []
            
            for i in range(num_tests):
                logger.info(f"Performance test {i+1}/{num_tests}")
                
                # Send detection request
                detect_message = {
                    "action": "detect",
                    "timestamp": time.time()
                }
                
                # Record start time
                start_time = time.time()
                
                await self.ws_client.send(json.dumps(detect_message))
                
                # Receive response with timeout
                response = None
                try:
                    response = await asyncio.wait_for(self.ws_client.recv(), timeout=30.0)
                except asyncio.TimeoutError:
                    logger.error(f"Performance test {i+1} timed out")
                    performance_results.append({"success": False, "time": 30.0})
                    continue
                
                # Record end time
                end_time = time.time()
                response_time = end_time - start_time
                
                try:
                    response_data = json.loads(response)
                    
                    if response_data.get("type") == "detection_result":
                        execution_time = response_data.get("execution_time", 0)
                        logger.info(f"Detection time: {execution_time:.2f}s (response time: {response_time:.2f}s)")
                        
                        performance_results.append({
                            "success": True,
                            "execution_time": execution_time,
                            "response_time": response_time
                        })
                    else:
                        logger.warning(f"Unexpected response type: {response_data.get('type')}")
                        performance_results.append({"success": False, "time": response_time})
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON response: {response[:100]}...")
                    performance_results.append({"success": False, "time": response_time})
                
                # Wait between tests
                await asyncio.sleep(1)
            
            # Calculate average times
            success_count = sum(1 for r in performance_results if r.get("success", False))
            
            if success_count > 0:
                avg_execution_time = sum(r.get("execution_time", 0) for r in performance_results if r.get("success", False)) / success_count
                avg_response_time = sum(r.get("response_time", 0) for r in performance_results if r.get("success", False)) / success_count
            else:
                avg_execution_time = 0
                avg_response_time = 0
            
            logger.info(f"Average execution time: {avg_execution_time:.2f}s")
            logger.info(f"Average response time: {avg_response_time:.2f}s")
            
            # Interpret the results (consider anything under 5 seconds to be good performance)
            if avg_execution_time < 5.0:
                self.test_results["performance"] = {
                    "success": True,
                    "details": f"Good performance: {avg_execution_time:.2f}s execution time, {avg_response_time:.2f}s response time",
                    "avg_time": avg_execution_time
                }
                return True
            else:
                self.test_results["performance"] = {
                    "success": False,
                    "details": f"Slow performance: {avg_execution_time:.2f}s execution time, {avg_response_time:.2f}s response time",
                    "avg_time": avg_execution_time
                }
                return False
        except Exception as e:
            logger.error(f"Error in performance test: {e}")
            self.test_results["performance"] = {
                "success": False,
                "details": f"Error during test: {str(e)}",
                "avg_time": 0.0
            }
            return False
    
    def generate_report(self) -> str:
        """Generate test report"""
        logger.info("Generating test report...")
        
        report = []
        report.append("=" * 80)
        report.append("NEURAL UI DETECTOR TEST REPORT")
        report.append("=" * 80)
        report.append(f"Test Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Neural UI Detector Port: {self.actual_port}")
        report.append("-" * 80)
        
        # Port Conflict Test
        port_result = self.test_results["port_conflict"]
        report.append("1. Port Conflict Resolution Test")
        report.append(f"   Result: {'PASS' if port_result['success'] else 'FAIL'}")
        report.append(f"   Details: {port_result['details']}")
        report.append("")
        
        # Detection Reliability Test
        reliability_result = self.test_results["detection_reliability"]
        report.append("2. Detection Reliability Test")
        report.append(f"   Result: {'PASS' if reliability_result['success'] else 'FAIL'}")
        report.append(f"   Details: {reliability_result['details']}")
        report.append(f"   Accuracy: {reliability_result.get('accuracy', 0):.2%}")
        report.append(f"   Average Time: {reliability_result.get('avg_time', 0):.2f}s")
        report.append("")
        
        # Integration Test
        integration_result = self.test_results["integration"]
        report.append("3. DO Button Integration Test")
        report.append(f"   Result: {'PASS' if integration_result['success'] else 'FAIL'}")
        report.append(f"   Details: {integration_result['details']}")
        report.append("")
        
        # Performance Test
        performance_result = self.test_results["performance"]
        report.append("4. Performance Test")
        report.append(f"   Result: {'PASS' if performance_result['success'] else 'FAIL'}")
        report.append(f"   Details: {performance_result['details']}")
        report.append(f"   Average Execution Time: {performance_result.get('avg_time', 0):.2f}s")
        report.append("")
        
        # Overall Result
        overall_success = all(r["success"] for r in self.test_results.values())
        report.append("-" * 80)
        report.append(f"Overall Result: {'PASS' if overall_success else 'FAIL'}")
        report.append("=" * 80)
        
        report_text = "\n".join(report)
        
        # Save report to file
        report_file = f"neural_ui_detector_test_report_{int(time.time())}.txt"
        with open(report_file, "w") as f:
            f.write(report_text)
        
        logger.info(f"Test report saved to {report_file}")
        return report_text
    
    async def run_all_tests(self) -> bool:
        """Run all tests"""
        logger.info("Running all tests...")
        
        try:
            # Start servers
            logger.info("Starting servers...")
            servers_started = await self.start_servers()
            if not servers_started:
                logger.error("Failed to start servers")
                return False
            
            # Connect to server
            logger.info("Connecting to Neural UI Detector...")
            connected = await self.connect_to_server()
            if not connected:
                logger.error("Failed to connect to Neural UI Detector")
                await self.stop_servers()
                return False
            
            # Open test page
            logger.info("Opening test page...")
            page_opened = await self.open_test_page()
            if not page_opened:
                logger.warning("Failed to open test page, continuing with tests...")
            
            # Wait for page to load and servers to initialize
            logger.info("Waiting for initialization...")
            await asyncio.sleep(5)
            
            # Run tests
            await self.test_port_conflict_resolution()
            await self.test_detection_reliability()
            await self.test_integration()
            await self.test_performance()
            
            # Generate report
            report = self.generate_report()
            print("\n" + report)
            
            # Cleanup
            await self.disconnect()
            await self.stop_servers()
            
            # Return overall success
            overall_success = all(r["success"] for r in self.test_results.values())
            return overall_success
        except Exception as e:
            logger.error(f"Error running tests: {e}")
            await self.disconnect()
            await self.stop_servers()
            return False

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Neural UI Detector Testing Framework")
    parser.add_argument("--port", type=int, default=NEURAL_UI_DETECTOR_PORT, help="Neural UI Detector port")
    parser.add_argument("--skip-browser", action="store_true", help="Skip opening browser for test page")
    
    args = parser.parse_args()
    
    # Set port
    NEURAL_UI_DETECTOR_PORT = args.port
    
    # Print header
    print("\n" + "=" * 80)
    print(" NEURAL UI DETECTOR TESTING FRAMEWORK ")
    print("=" * 80)
    
    # Create and run test framework
    framework = NeuralUITestFramework()
    
    try:
        # Run all tests
        success = await framework.run_all_tests()
        
        if success:
            print("\n✅ All tests passed!")
            return 0
        else:
            print("\n❌ Some tests failed. See report for details.")
            return 1
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        await framework.disconnect()
        await framework.stop_servers()
        return 130
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        await framework.disconnect()
        await framework.stop_servers()
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))