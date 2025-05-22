#!/usr/bin/env python3
"""
Comprehensive Connection Test for Tauri Overlay to Backend
Identifies and diagnoses all connection issues between components
"""

import asyncio
import websockets
import json
import time
import subprocess
import requests
import sys
import os
from datetime import datetime
import logging
import psutil
import socket
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/connection_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Color:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_colored(color, message):
    """Print colored message"""
    print(f"{color}{message}{Color.END}")

def print_header(title):
    """Print section header"""
    print_colored(Color.BOLD + Color.CYAN, f"\n{'='*60}")
    print_colored(Color.BOLD + Color.CYAN, f"{title}")
    print_colored(Color.BOLD + Color.CYAN, f"{'='*60}")

def print_success(message):
    """Print success message"""
    print_colored(Color.GREEN, f"✅ {message}")

def print_warning(message):
    """Print warning message"""
    print_colored(Color.YELLOW, f"⚠️  {message}")

def print_error(message):
    """Print error message"""
    print_colored(Color.RED, f"❌ {message}")

def print_info(message):
    """Print info message"""
    print_colored(Color.BLUE, f"ℹ️  {message}")

class ConnectionTester:
    def __init__(self):
        self.ports = {
            'websocket': 8765,
            'bridge': 8766,
            'backend': 8767,
            'tauri_dev': 1420,  # Default Tauri development port
            'vite_dev': 5173    # Default Vite development port
        }
        self.test_results = {
            'port_availability': {},
            'websocket_connections': {},
            'http_endpoints': {},
            'file_permissions': {},
            'process_status': {},
            'configuration_issues': [],
            'memory_issues': [],
            'llm_issues': []
        }
        self.ws_connections = {}

    async def run_comprehensive_test(self):
        """Run all connection tests"""
        print_header("COMPREHENSIVE CONNECTION TEST")
        
        # Test 1: Port Availability
        await self.test_port_availability()
        
        # Test 2: Process Status
        await self.test_process_status()
        
        # Test 3: File Permissions and Existence
        await self.test_file_permissions()
        
        # Test 4: Configuration Issues
        await self.test_configuration_issues()
        
        # Test 5: WebSocket Connections
        await self.test_websocket_connections()
        
        # Test 6: HTTP Endpoints
        await self.test_http_endpoints()
        
        # Test 7: Memory System
        await self.test_memory_system()
        
        # Test 8: LLM Integration
        await self.test_llm_integration()
        
        # Test 9: Tauri-Backend Connection
        await self.test_tauri_backend_connection()
        
        # Generate Report
        await self.generate_report()

    async def test_port_availability(self):
        """Test if required ports are available and listening"""
        print_header("PORT AVAILABILITY TEST")
        
        for service, port in self.ports.items():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                
                if result == 0:
                    print_success(f"Port {port} ({service}) is listening")
                    self.test_results['port_availability'][service] = True
                else:
                    print_error(f"Port {port} ({service}) is not listening")
                    self.test_results['port_availability'][service] = False
                    
            except Exception as e:
                print_error(f"Error testing port {port} ({service}): {e}")
                self.test_results['port_availability'][service] = False

    async def test_process_status(self):
        """Test if required processes are running"""
        print_header("PROCESS STATUS TEST")
        
        required_processes = [
            'fixed_ws_8765.py',
            'fixed_bridge_server_enhanced.py',
            'simple_ws_server_8767.py',
            'enhanced_fixed_process_sensor.py',
            'enhanced_fixed_screen_sensor.py',
            'direct_sensor_to_memory.py',
            'llm_context_connector.py'
        ]
        
        for process_name in required_processes:
            found = False
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                    if process_name in cmdline:
                        print_success(f"Process {process_name} is running (PID: {proc.info['pid']})")
                        self.test_results['process_status'][process_name] = True
                        found = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if not found:
                print_error(f"Process {process_name} is not running")
                self.test_results['process_status'][process_name] = False

    async def test_file_permissions(self):
        """Test file permissions and existence"""
        print_header("FILE PERMISSIONS TEST")
        
        required_files = [
            'fixed_ws_8765.py',
            'fixed_bridge_server_enhanced.py',
            'simple_ws_server_8767.py',
            'sensors/enhanced_fixed_process_sensor.py',
            'sensors/enhanced_fixed_screen_sensor.py',
            'direct_sensor_to_memory.py',
            'llm_context_connector.py',
            'memory/memory_state.json',
            'memory/last_context.json'
        ]
        
        for file_path in required_files:
            if os.path.exists(file_path):
                if os.access(file_path, os.R_OK):
                    print_success(f"File {file_path} exists and is readable")
                    self.test_results['file_permissions'][file_path] = True
                else:
                    print_error(f"File {file_path} exists but is not readable")
                    self.test_results['file_permissions'][file_path] = False
            else:
                print_error(f"File {file_path} does not exist")
                self.test_results['file_permissions'][file_path] = False

    async def test_configuration_issues(self):
        """Test for configuration issues"""
        print_header("CONFIGURATION ISSUES TEST")
        
        # Check WebSocket server configuration
        await self.check_websocket_config()
        
        # Check bridge server configuration
        await self.check_bridge_config()
        
        # Check backend server configuration
        await self.check_backend_config()
        
        # Check Tauri configuration
        await self.check_tauri_config()

    async def check_websocket_config(self):
        """Check WebSocket server configuration"""
        print_info("Checking WebSocket server configuration...")
        
        try:
            if os.path.exists('fixed_ws_8765.py'):
                with open('fixed_ws_8765.py', 'r') as f:
                    content = f.read()
                    
                    # Check port configuration
                    if '8765' in content:
                        print_success("WebSocket server configured for port 8765")
                    else:
                        print_error("WebSocket server port configuration issue")
                        self.test_results['configuration_issues'].append("WebSocket server port not configured for 8765")
                    
                    # Check client type handling
                    if 'chat_overlay' in content or 'ui' in content:
                        print_success("WebSocket server handles overlay client types")
                    else:
                        print_error("WebSocket server missing overlay client type handling")
                        self.test_results['configuration_issues'].append("WebSocket server missing overlay client type handling")
                        
            else:
                print_error("WebSocket server file not found")
                self.test_results['configuration_issues'].append("WebSocket server file missing")
                
        except Exception as e:
            print_error(f"Error checking WebSocket configuration: {e}")
            self.test_results['configuration_issues'].append(f"WebSocket config check failed: {e}")

    async def check_bridge_config(self):
        """Check bridge server configuration"""
        print_info("Checking bridge server configuration...")
        
        try:
            if os.path.exists('fixed_bridge_server_enhanced.py'):
                with open('fixed_bridge_server_enhanced.py', 'r') as f:
                    content = f.read()
                    
                    # Check port configuration
                    if '8766' in content:
                        print_success("Bridge server configured for port 8766")
                    else:
                        print_error("Bridge server port configuration issue")
                        self.test_results['configuration_issues'].append("Bridge server port not configured for 8766")
                        
            else:
                print_error("Bridge server file not found")
                self.test_results['configuration_issues'].append("Bridge server file missing")
                
        except Exception as e:
            print_error(f"Error checking bridge configuration: {e}")
            self.test_results['configuration_issues'].append(f"Bridge config check failed: {e}")

    async def check_backend_config(self):
        """Check backend server configuration"""
        print_info("Checking backend server configuration...")
        
        try:
            if os.path.exists('simple_ws_server_8767.py'):
                with open('simple_ws_server_8767.py', 'r') as f:
                    content = f.read()
                    
                    # Check port configuration
                    if '8767' in content:
                        print_success("Backend server configured for port 8767")
                    else:
                        print_error("Backend server port configuration issue")
                        self.test_results['configuration_issues'].append("Backend server port not configured for 8767")
                        
            else:
                print_error("Backend server file not found")
                self.test_results['configuration_issues'].append("Backend server file missing")
                
        except Exception as e:
            print_error(f"Error checking backend configuration: {e}")
            self.test_results['configuration_issues'].append(f"Backend config check failed: {e}")

    async def check_tauri_config(self):
        """Check Tauri configuration"""
        print_info("Checking Tauri configuration...")
        
        try:
            tauri_config_path = 'src-tauri/tauri.conf.json'
            overlay_config_path = 'overlay/package.json'
            
            # Check Tauri config
            if os.path.exists(tauri_config_path):
                with open(tauri_config_path, 'r') as f:
                    config = json.load(f)
                    print_success("Tauri configuration found")
                    
                    # Check for WebSocket URL in config
                    config_str = json.dumps(config)
                    if 'ws://localhost:8765' in config_str:
                        print_success("Tauri configured to connect to WebSocket server")
                    else:
                        print_warning("Tauri WebSocket URL not found in config")
            else:
                print_error("Tauri configuration not found")
                self.test_results['configuration_issues'].append("Tauri config missing")
            
            # Check overlay config
            if os.path.exists(overlay_config_path):
                with open(overlay_config_path, 'r') as f:
                    config = json.load(f)
                    print_success("Overlay package.json found")
            else:
                print_warning("Overlay package.json not found")
                
        except Exception as e:
            print_error(f"Error checking Tauri configuration: {e}")
            self.test_results['configuration_issues'].append(f"Tauri config check failed: {e}")

    async def test_websocket_connections(self):
        """Test WebSocket connections"""
        print_header("WEBSOCKET CONNECTIONS TEST")
        
        # Test WebSocket server connection
        await self.test_websocket_server()
        
        # Test backend WebSocket connection
        await self.test_backend_websocket()

    async def test_websocket_server(self):
        """Test WebSocket server connection"""
        print_info("Testing WebSocket server connection...")
        
        try:
            uri = "ws://localhost:8765"
            async with websockets.connect(uri) as websocket:
                # Send registration message
                registration_msg = {
                    "type": "register",
                    "client_type": "test_client",
                    "payload": {
                        "client_id": "connection_test"
                    }
                }
                
                await websocket.send(json.dumps(registration_msg))
                print_success("Sent registration message to WebSocket server")
                
                # Wait for response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    response_data = json.loads(response)
                    print_success(f"Received response from WebSocket server: {response_data}")
                    self.test_results['websocket_connections']['websocket_server'] = True
                except asyncio.TimeoutError:
                    print_error("No response from WebSocket server")
                    self.test_results['websocket_connections']['websocket_server'] = False
                    
        except Exception as e:
            print_error(f"Failed to connect to WebSocket server: {e}")
            self.test_results['websocket_connections']['websocket_server'] = False

    async def test_backend_websocket(self):
        """Test backend WebSocket connection"""
        print_info("Testing backend WebSocket connection...")
        
        try:
            uri = "ws://localhost:8767"
            async with websockets.connect(uri) as websocket:
                # Send test message
                test_msg = {
                    "type": "query",
                    "message": "Hello, test connection"
                }
                
                await websocket.send(json.dumps(test_msg))
                print_success("Sent test message to backend WebSocket")
                
                # Wait for response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10)
                    response_data = json.loads(response)
                    print_success(f"Received response from backend: {response_data}")
                    self.test_results['websocket_connections']['backend'] = True
                except asyncio.TimeoutError:
                    print_error("No response from backend WebSocket")
                    self.test_results['websocket_connections']['backend'] = False
                    
        except Exception as e:
            print_error(f"Failed to connect to backend WebSocket: {e}")
            self.test_results['websocket_connections']['backend'] = False

    async def test_http_endpoints(self):
        """Test HTTP endpoints"""
        print_header("HTTP ENDPOINTS TEST")
        
        # Test if any HTTP endpoints are available
        test_urls = [
            'http://localhost:8767/health',
            'http://localhost:8767/status',
            'http://localhost:8766/health',
            'http://localhost:8765/health'
        ]
        
        for url in test_urls:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print_success(f"HTTP endpoint {url} is responding")
                    self.test_results['http_endpoints'][url] = True
                else:
                    print_warning(f"HTTP endpoint {url} returned status {response.status_code}")
                    self.test_results['http_endpoints'][url] = False
            except requests.exceptions.RequestException as e:
                print_info(f"HTTP endpoint {url} not available (expected for WebSocket-only services)")
                self.test_results['http_endpoints'][url] = False

    async def test_memory_system(self):
        """Test memory system functionality"""
        print_header("MEMORY SYSTEM TEST")
        
        # Check memory files
        memory_files = [
            'memory/memory_state.json',
            'memory/last_context.json'
        ]
        
        for file_path in memory_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        print_success(f"Memory file {file_path} is valid JSON")
                        
                        # Check if file has recent data
                        if 'timestamp' in data:
                            timestamp = data['timestamp']
                            if isinstance(timestamp, (int, float)):
                                age = time.time() - timestamp
                                if age < 300:  # 5 minutes
                                    print_success(f"Memory file {file_path} has recent data ({age:.1f}s ago)")
                                else:
                                    print_warning(f"Memory file {file_path} data is old ({age:.1f}s ago)")
                            else:
                                print_warning(f"Memory file {file_path} has invalid timestamp format")
                        else:
                            print_warning(f"Memory file {file_path} missing timestamp")
                            
                except json.JSONDecodeError as e:
                    print_error(f"Memory file {file_path} contains invalid JSON: {e}")
                    self.test_results['memory_issues'].append(f"Invalid JSON in {file_path}")
                except Exception as e:
                    print_error(f"Error reading memory file {file_path}: {e}")
                    self.test_results['memory_issues'].append(f"Error reading {file_path}")
            else:
                print_error(f"Memory file {file_path} not found")
                self.test_results['memory_issues'].append(f"Missing file {file_path}")

    async def test_llm_integration(self):
        """Test LLM integration"""
        print_header("LLM INTEGRATION TEST")
        
        # Check LLM context connector
        if os.path.exists('logs/llm/llm_context.log'):
            try:
                with open('logs/llm/llm_context.log', 'r') as f:
                    content = f.read()
                    
                    if 'Connected to LLM service' in content:
                        print_success("LLM context connector successfully connected")
                    else:
                        print_error("LLM context connector connection issues")
                        self.test_results['llm_issues'].append("LLM context connector not connected")
                    
                    if 'Sent periodic context update' in content:
                        print_success("LLM context connector sending updates")
                    else:
                        print_error("LLM context connector not sending updates")
                        self.test_results['llm_issues'].append("LLM context connector not sending updates")
                        
            except Exception as e:
                print_error(f"Error reading LLM log: {e}")
                self.test_results['llm_issues'].append(f"Error reading LLM log: {e}")
        else:
            print_error("LLM context log not found")
            self.test_results['llm_issues'].append("LLM context log missing")

    async def test_tauri_backend_connection(self):
        """Test Tauri to backend connection simulation"""
        print_header("TAURI-BACKEND CONNECTION TEST")
        
        # Simulate Tauri overlay connection
        try:
            uri = "ws://localhost:8765"
            async with websockets.connect(uri) as websocket:
                # Register as overlay client
                registration_msg = {
                    "type": "register",
                    "client_type": "ui",
                    "payload": {
                        "client_id": "tauri_overlay_test"
                    }
                }
                
                await websocket.send(json.dumps(registration_msg))
                print_success("Simulated Tauri overlay registration")
                
                # Wait for registration confirmation
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    response_data = json.loads(response)
                    
                    if response_data.get('type') == 'registration_confirmed':
                        print_success("Received registration confirmation for overlay")
                        
                        # Test sending a query
                        query_msg = {
                            "type": "query",
                            "client_type": "ui",
                            "message": "Test query from Tauri overlay",
                            "payload": {
                                "context": "Testing connection"
                            }
                        }
                        
                        await websocket.send(json.dumps(query_msg))
                        print_success("Sent test query from simulated Tauri overlay")
                        
                        # Wait for response
                        try:
                            response = await asyncio.wait_for(websocket.recv(), timeout=15)
                            response_data = json.loads(response)
                            print_success(f"Received LLM response: {response_data}")
                            
                            # Check if response is meaningful
                            if 'response' in response_data and response_data['response']:
                                if response_data['response'] != "thinking...":
                                    print_success("LLM response is meaningful")
                                else:
                                    print_error("LLM response stuck on 'thinking...'")
                                    self.test_results['llm_issues'].append("LLM response stuck on thinking")
                            else:
                                print_error("LLM response is empty or invalid")
                                self.test_results['llm_issues'].append("Empty LLM response")
                                
                        except asyncio.TimeoutError:
                            print_error("No response to query from LLM")
                            self.test_results['llm_issues'].append("LLM timeout on query")
                            
                    else:
                        print_error("Invalid registration response")
                        
                except asyncio.TimeoutError:
                    print_error("No registration confirmation received")
                    
        except Exception as e:
            print_error(f"Failed to simulate Tauri overlay connection: {e}")

    async def generate_report(self):
        """Generate comprehensive test report"""
        print_header("COMPREHENSIVE TEST REPORT")
        
        # Summary
        total_tests = 0
        passed_tests = 0
        
        print_info("Test Results Summary:")
        print_info(f"Timestamp: {datetime.now().isoformat()}")
        print("")
        
        # Port availability
        print_colored(Color.BOLD, "Port Availability:")
        for service, result in self.test_results['port_availability'].items():
            total_tests += 1
            if result:
                passed_tests += 1
                print_success(f"  {service}: PASS")
            else:
                print_error(f"  {service}: FAIL")
        print("")
        
        # Process status
        print_colored(Color.BOLD, "Process Status:")
        for process, result in self.test_results['process_status'].items():
            total_tests += 1
            if result:
                passed_tests += 1
                print_success(f"  {process}: PASS")
            else:
                print_error(f"  {process}: FAIL")
        print("")
        
        # WebSocket connections
        print_colored(Color.BOLD, "WebSocket Connections:")
        for connection, result in self.test_results['websocket_connections'].items():
            total_tests += 1
            if result:
                passed_tests += 1
                print_success(f"  {connection}: PASS")
            else:
                print_error(f"  {connection}: FAIL")
        print("")
        
        # Issues found
        print_colored(Color.BOLD, "Issues Found:")
        all_issues = (
            self.test_results['configuration_issues'] +
            self.test_results['memory_issues'] +
            self.test_results['llm_issues']
        )
        
        if all_issues:
            for issue in all_issues:
                print_error(f"  • {issue}")
        else:
            print_success("  No critical issues found")
        print("")
        
        # Overall result
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print_colored(Color.BOLD, f"Overall Test Result: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            print_success("System is in good condition")
        elif success_rate >= 60:
            print_warning("System has some issues that need attention")
        else:
            print_error("System has critical issues that need immediate attention")
        
        # Save detailed report
        await self.save_detailed_report()

    async def save_detailed_report(self):
        """Save detailed report to file"""
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'test_results': self.test_results,
            'recommendations': self.generate_recommendations()
        }
        
        os.makedirs('logs', exist_ok=True)
        with open('logs/connection_test_report.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print_info("Detailed report saved to logs/connection_test_report.json")

    def generate_recommendations(self):
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Port availability issues
        if not self.test_results['port_availability'].get('websocket', True):
            recommendations.append("Start WebSocket server on port 8765")
        
        if not self.test_results['port_availability'].get('backend', True):
            recommendations.append("Start backend server on port 8767")
        
        if not self.test_results['port_availability'].get('bridge', True):
            recommendations.append("Start bridge server on port 8766")
        
        # Process issues
        if not self.test_results['process_status'].get('fixed_ws_8765.py', True):
            recommendations.append("Start WebSocket server process")
        
        if not self.test_results['process_status'].get('simple_ws_server_8767.py', True):
            recommendations.append("Start backend server process")
        
        # Configuration issues
        if self.test_results['configuration_issues']:
            recommendations.append("Fix configuration issues listed in the report")
        
        # Memory issues
        if self.test_results['memory_issues']:
            recommendations.append("Fix memory system issues")
        
        # LLM issues
        if self.test_results['llm_issues']:
            recommendations.append("Fix LLM integration issues")
        
        return recommendations

async def main():
    """Main function"""
    print_colored(Color.BOLD + Color.MAGENTA, "Comprehensive Connection Test for Tauri Overlay to Backend")
    print_colored(Color.BOLD + Color.MAGENTA, "================================================================")
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Run tests
    tester = ConnectionTester()
    await tester.run_comprehensive_test()
    
    print_colored(Color.BOLD + Color.MAGENTA, "\nTest completed. Check logs/connection_test_report.json for detailed results.")

if __name__ == "__main__":
    asyncio.run(main())