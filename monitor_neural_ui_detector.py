#!/usr/bin/env python3
"""
Neural UI Detector Monitor

This script helps monitor and debug the Neural UI Detector server.
It provides real-time status information, troubleshooting tools,
and can restart the server if needed.
"""

import os
import sys
import time
import json
import argparse
import subprocess
import websockets
import asyncio
import signal
import socket
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

# Terminal colors for better readability
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}\n")

def print_status(text, color=Colors.BLUE):
    """Print status message with timestamp and color"""
    print(f"{color}[{datetime.now().strftime('%H:%M:%S')}] {text}{Colors.ENDC}")

def read_port_from_file() -> int:
    """Read the detector port from various locations"""
    potential_files = [
        'neural_ui_detector_port.txt',
        'logs/neural_ui_detector/server_port.txt',
        'logs/neural_ui_detector_port.txt',
        'logs/neural_do_button_port.txt'  # Try this as fallback
    ]
    
    for file_path in potential_files:
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    port = int(f.read().strip())
                    print_status(f"Found port {port} in {file_path}")
                    return port
        except Exception as e:
            print_status(f"Error reading port from {file_path}: {e}", Colors.YELLOW)
    
    # Default port if not found
    default_port = 8768
    print_status(f"Using default port {default_port}")
    return default_port

def check_port_status(port: int) -> bool:
    """Check if the port is open and listening"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        return result == 0
    except Exception as e:
        print_status(f"Error checking port status: {e}", Colors.RED)
        return False

def check_server_status(port=8768) -> Tuple[bool, Optional[str]]:
    """Check if the Neural UI Detector is running and gather status info"""
    print_status(f"Checking Neural UI Detector server status on port {port}...")
    
    try:
        # Check port usage
        process = subprocess.run(
            ["lsof", "-i", f":{port}"],
            capture_output=True,
            text=True
        )
        
        if "Python" in process.stdout and "LISTEN" in process.stdout:
            print_status(f"Neural UI Detector server is RUNNING on port {port}", Colors.GREEN)
            
            # Extract PID
            lines = process.stdout.strip().split('\n')
            pid = None
            if len(lines) > 1:
                parts = lines[1].split()
                if len(parts) > 1:
                    pid = parts[1]
                    print_status(f"Server PID: {pid}", Colors.GREEN)
                    
                    # Get process info
                    ps_result = subprocess.run(
                        ["ps", "-p", pid, "-o", "etime=,pcpu="],
                        capture_output=True,
                        text=True
                    )
                    info = ps_result.stdout.strip().split()
                    uptime = info[0] if info else "unknown"
                    cpu = info[1] if len(info) > 1 else "unknown"
                    
                    print_status(f"Server uptime: {uptime}", Colors.GREEN)
                    print_status(f"CPU usage: {cpu}%", Colors.GREEN)
                    
                    # Check active connections
                    active_connections = process.stdout.count("ESTABLISHED")
                    print_status(f"Active connections: {active_connections}", Colors.GREEN)
            
            return True, pid
        else:
            print_status(f"Neural UI Detector server is NOT running on port {port}", Colors.RED)
            return False, None
            
    except Exception as e:
        print_status(f"Error checking server status: {e}", Colors.RED)
        return False, None

def check_log_files(show_errors_only=False, lines=5):
    """Check and display information about log files"""
    print_status("Checking log files...")
    
    log_dir = os.path.join("logs", "neural_ui_detector")
    if not os.path.exists(log_dir):
        print_status(f"Log directory not found: {log_dir}", Colors.RED)
        return False
    
    log_files = {
        "neural_detector.log": "Main detector log",
        "server.log": "WebSocket server log",
        "startup.log": "Server startup log",
        "monitor.log": "Monitor log"
    }
    
    # Also check root logs
    root_logs = {
        "neural_ui_detector_server.log": "Root server log"
    }
    
    # Check for errors across all log files
    error_count = 0
    warning_count = 0
    
    # Process logs in neural_ui_detector directory
    for log_file, description in log_files.items():
        log_path = os.path.join(log_dir, log_file)
        if os.path.exists(log_path):
            size = os.path.getsize(log_path) / 1024  # KB
            mtime = os.path.getmtime(log_path)
            last_modified = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            print_status(f"{log_file}: {size:.1f} KB, Last modified: {last_modified}", Colors.GREEN)
            
            # Show last few lines of important logs
            if log_file in ["neural_detector.log", "server.log", "startup.log"]:
                try:
                    result = subprocess.run(
                        ["tail", "-n", str(lines), log_path],
                        capture_output=True,
                        text=True
                    )
                    
                    # Count errors and warnings
                    for line in result.stdout.strip().split('\n'):
                        if "ERROR" in line:
                            error_count += 1
                        elif "WARNING" in line:
                            warning_count += 1
                    
                    if not show_errors_only:
                        print(f"{Colors.YELLOW}Last {lines} lines of {log_file}:{Colors.ENDC}")
                        for line in result.stdout.strip().split('\n'):
                            if "ERROR" in line:
                                print(f"{Colors.RED}{line}{Colors.ENDC}")
                            elif "WARNING" in line:
                                print(f"{Colors.YELLOW}{line}{Colors.ENDC}")
                            else:
                                print(f"  {line}")
                        print()
                except Exception as e:
                    print_status(f"Error reading log file: {e}", Colors.RED)
        else:
            print_status(f"{log_file}: Not found", Colors.YELLOW)
    
    # Process root log files
    for log_file, description in root_logs.items():
        log_path = os.path.join("logs", log_file)
        if os.path.exists(log_path):
            size = os.path.getsize(log_path) / 1024  # KB
            mtime = os.path.getmtime(log_path)
            last_modified = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            print_status(f"{log_file}: {size:.1f} KB, Last modified: {last_modified}", Colors.GREEN)
            
            # Show last few lines
            try:
                result = subprocess.run(
                    ["tail", "-n", str(lines), log_path],
                    capture_output=True,
                    text=True
                )
                
                # Count errors and warnings
                for line in result.stdout.strip().split('\n'):
                    if "ERROR" in line:
                        error_count += 1
                    elif "WARNING" in line:
                        warning_count += 1
                
                if not show_errors_only:
                    print(f"{Colors.YELLOW}Last {lines} lines of {log_file}:{Colors.ENDC}")
                    for line in result.stdout.strip().split('\n'):
                        if "ERROR" in line:
                            print(f"{Colors.RED}{line}{Colors.ENDC}")
                        elif "WARNING" in line:
                            print(f"{Colors.YELLOW}{line}{Colors.ENDC}")
                        else:
                            print(f"  {line}")
                    print()
            except Exception as e:
                print_status(f"Error reading log file: {e}", Colors.RED)
        else:
            print_status(f"{log_file}: Not found", Colors.YELLOW)
    
    # Print error summary
    if error_count > 0 or warning_count > 0:
        print_status(f"Found {error_count} errors and {warning_count} warnings in logs", 
                     Colors.RED if error_count > 0 else Colors.YELLOW)
    else:
        print_status("No errors or warnings found in logs", Colors.GREEN)
    
    return True

def check_cache_directory():
    """Check the cache directory for detector files"""
    print_status("Checking cache directory...")
    
    cache_dir = os.path.join("cache", "neural_ui_detector")
    if not os.path.exists(cache_dir):
        print_status(f"Cache directory not found: {cache_dir}", Colors.RED)
        return False
    
    # Count files by type
    screenshots = 0
    detections = 0
    other = 0
    latest_file = None
    latest_time = 0
    
    for filename in os.listdir(cache_dir):
        file_path = os.path.join(cache_dir, filename)
        if os.path.isfile(file_path):
            mtime = os.path.getmtime(file_path)
            if mtime > latest_time:
                latest_time = mtime
                latest_file = filename
                
            if filename.startswith("screenshot_"):
                screenshots += 1
            elif filename.startswith("detection_"):
                detections += 1
            else:
                other += 1
    
    print_status(f"Cache contains: {screenshots} screenshots, {detections} detection results, {other} other files", Colors.GREEN)
    
    if latest_file:
        print_status(f"Latest file: {latest_file}, time: {datetime.fromtimestamp(latest_time).strftime('%H:%M:%S')}", Colors.GREEN)
    
    # Check storage usage
    total_size = sum(os.path.getsize(os.path.join(cache_dir, f)) for f in os.listdir(cache_dir) if os.path.isfile(os.path.join(cache_dir, f)))
    print_status(f"Total cache size: {total_size / (1024*1024):.2f} MB", Colors.GREEN)
    
    return True

async def test_websocket_connection(url="ws://localhost:8768", timeout=5):
    """Test connecting to the WebSocket server"""
    print_status(f"Testing WebSocket connection to {url}...")
    
    try:
        # Connect with timeout
        async with asyncio.timeout(timeout):
            async with websockets.connect(url) as websocket:
                print_status("Successfully connected to WebSocket server", Colors.GREEN)
                
                # Receive welcome message
                async with asyncio.timeout(timeout):
                    response = await websocket.recv()
                    data = json.loads(response)
                    print_status(f"Received welcome message: {data.get('message', 'No message')}", Colors.GREEN)
                    
                    if 'capabilities' in data:
                        print_status(f"Server capabilities: {', '.join(data['capabilities'])}", Colors.GREEN)
                
                # Send a ping message
                test_message = {
                    "action": "ping",
                    "timestamp": datetime.now().isoformat()
                }
                
                await websocket.send(json.dumps(test_message))
                print_status("Sent ping message to server", Colors.GREEN)
                
                # Wait for response
                try:
                    async with asyncio.timeout(timeout):
                        response = await websocket.recv()
                        data = json.loads(response)
                        print_status(f"Received response: {json.dumps(data)[:100]}...", Colors.GREEN)
                except:
                    print_status("No response to ping (this is normal if server doesn't implement ping)", Colors.YELLOW)
                
                return True
                
    except asyncio.TimeoutError:
        print_status(f"Timeout connecting to WebSocket after {timeout} seconds", Colors.RED)
        return False
    except Exception as e:
        print_status(f"Error testing WebSocket connection: {e}", Colors.RED)
        return False

def restart_server(port=8768):
    """Restart the Neural UI Detector server"""
    print_header("Restarting Neural UI Detector Server")
    
    # First check if server is running
    is_running, pid = check_server_status(port)
    
    # If running, kill process
    if is_running and pid:
        print_status(f"Stopping server process (PID: {pid})...", Colors.YELLOW)
        try:
            # Kill process gracefully
            os.kill(int(pid), signal.SIGTERM)
            
            # Wait for process to terminate
            max_wait = 5
            for i in range(max_wait):
                time.sleep(1)
                try:
                    # Check if process still exists
                    os.kill(int(pid), 0)
                    print_status(f"Waiting for process to terminate ({i+1}/{max_wait})...", Colors.YELLOW)
                except OSError:
                    # Process is gone
                    print_status("Process terminated successfully", Colors.GREEN)
                    break
            else:
                # Force kill if it didn't terminate
                print_status("Process didn't terminate gracefully, forcing kill...", Colors.RED)
                try:
                    os.kill(int(pid), signal.SIGKILL)
                    time.sleep(1)
                except:
                    pass
        except Exception as e:
            print_status(f"Error stopping server: {e}", Colors.RED)
            return False
    
    # Make sure port is free
    if check_port_status(port):
        print_status(f"Port {port} is still in use, waiting for it to be freed...", Colors.YELLOW)
        for i in range(5):
            time.sleep(1)
            if not check_port_status(port):
                print_status(f"Port {port} is now free", Colors.GREEN)
                break
        else:
            print_status(f"Port {port} is still in use, cannot start server", Colors.RED)
            return False
    
    # Start server
    print_status("Starting Neural UI Detector server...", Colors.YELLOW)
    try:
        # Use nohup to keep server running after script exits
        cmd = f"nohup python3 neural_ui_detector_server.py --port {port} > logs/neural_ui_detector/startup.log 2>&1 &"
        subprocess.run(cmd, shell=True)
        
        # Wait for server to start
        print_status("Waiting for server to start...", Colors.YELLOW)
        max_wait = 10
        for i in range(max_wait):
            time.sleep(1)
            if check_port_status(port):
                print_status(f"Server started successfully on port {port}", Colors.GREEN)
                return True
            print_status(f"Waiting for server to start ({i+1}/{max_wait})...", Colors.YELLOW)
        
        print_status(f"Server didn't start after {max_wait} seconds", Colors.RED)
        return False
    except Exception as e:
        print_status(f"Error starting server: {e}", Colors.RED)
        return False

def display_troubleshooting_tips():
    """Display troubleshooting tips for common issues"""
    print_header("Troubleshooting Tips")
    
    tips = [
        ("WebSocket Connection Failures", 
         "• Check if server is running with 'python monitor_neural_ui_detector.py'\n"
         "• Restart server with 'python monitor_neural_ui_detector.py --restart'\n"
         "• Check for port conflicts with 'lsof -i :8765' and 'lsof -i :8766'"),
        
        ("Detection Hanging", 
         "• The OCR process might be hanging - check disabled components in neural_ui_detector.py\n"
         "• Look for these lines in _run_all_detectors method and ensure template and edge are commented out\n"
         "• Key fix: detection_tasks = {\n"
         "    \"yolo\": self.yolo_detector.detect(screenshot_path) if self.yolo_detector.available else [],\n"
         "    # \"layoutlm\": self.layoutlm_detector.detect(screenshot_path) if self.layoutlm_detector.available else [],  # Disabled - slow\n"
         "    \"accessibility\": self.accessibility_detector.detect() if self.accessibility_detector.available else [],\n"
         "    # \"browser\": self.browser_detector.detect() if self.browser_detector.available else [],  # Disabled - unreliable\n"
         "    \"ocr\": self.ocr_detector.detect(screenshot_path) if self.ocr_detector.available else [],\n"
         "    # \"template\": self.template_detector.detect(screenshot_path) if self.template_detector.available else [],  # Disabled - hanging\n"
         "    # \"edge\": self.edge_detector.detect(screenshot_path) if self.edge_detector.available else [],  # Disabled - unreliable\n"
         "}"),
        
        ("Poor UI Element Recognition", 
         "• Adjust the merging threshold in _merge_elements method\n"
         "• Make sure the OCR detector is working - check logs for 'OCR detected X text elements'\n"
         "• Try using the test page at test_neural_ui_detector_fixed.html in your browser"),
        
        ("Port Conflicts", 
         "• The Neural UI Detector should use port 8768 by default\n"
         "• DO Button server uses port 8765\n"
         "• DO Button Connection Bridge uses port 8766\n"
         "• If there's a conflict, try restarting with a different port: python neural_ui_detector_server.py --port 8769")
    ]
    
    for title, content in tips:
        print(f"{Colors.YELLOW}{Colors.BOLD}{title}{Colors.ENDC}")
        print(f"{content}\n")

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Neural UI Detector Monitor")
    parser.add_argument('--port', type=int, help='Server port (default: auto-detect)')
    parser.add_argument('--check-websocket', action='store_true', help='Test WebSocket connection')
    parser.add_argument('--full', action='store_true', help='Run all checks')
    parser.add_argument('--errors', action='store_true', help='Show only errors in logs')
    parser.add_argument('--lines', type=int, default=5, help='Number of log lines to show (default: 5)')
    parser.add_argument('--tips', action='store_true', help='Display troubleshooting tips')
    parser.add_argument('--restart', action='store_true', help='Restart the server')
    
    args = parser.parse_args()
    
    print_header("Neural UI Detector Monitor")
    
    # Get port
    port = args.port if args.port else read_port_from_file()
    
    # Always check server status
    server_running, pid = check_server_status(port)
    
    # Handle restart request
    if args.restart:
        success = restart_server(port)
        if success:
            print_status("Server restarted successfully", Colors.GREEN)
            server_running = True
        else:
            print_status("Failed to restart server", Colors.RED)
    
    # Optionally test WebSocket connection
    if server_running and (args.check_websocket or args.full):
        await test_websocket_connection(f"ws://localhost:{port}")
    
    # Always check logs
    check_log_files(show_errors_only=args.errors, lines=args.lines)
    
    # Check cache if requested
    if args.full:
        check_cache_directory()
    
    # Show troubleshooting tips if requested
    if args.tips or args.full:
        display_troubleshooting_tips()
    
    print_header("Monitor Complete")
    
    if not server_running and not args.restart:
        print_status(f"⚠️  Server is not running! Run 'python monitor_neural_ui_detector.py --restart' to start it.", Colors.RED)
    
    return 0

if __name__ == "__main__":
    asyncio.run(main())