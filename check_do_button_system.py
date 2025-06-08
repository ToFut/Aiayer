#!/usr/bin/env python3
"""
DO Button System Health Check

This script checks all WebSocket servers needed for the DO button system:
- WebSocket server on 8765 (Neural UI Detector)
- DO Button Fix Proxy on 8766
- Enhanced Enterprise Backend on 8767
- Ultimate DO Button Server on 8768
"""

import socket
import json
import sys
import os
import subprocess
import time
import websocket
import threading
from datetime import datetime

def check_port(port):
    """Check if a port is open"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result == 0

def check_websocket(url, timeout=5):
    """Check if a WebSocket server is running"""
    try:
        ws = websocket.create_connection(url, timeout=timeout)
        response = ws.recv()
        ws.close()
        return True, response
    except Exception as e:
        return False, str(e)

def check_process(keyword):
    """Check if a process is running"""
    try:
        result = subprocess.run(['pgrep', '-f', keyword], 
                              capture_output=True, 
                              text=True,
                              check=False)
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, ""
    except Exception as e:
        return False, str(e)

def format_status(name, status, details=""):
    """Format a status message with color"""
    if status:
        return f"✅ {name}: Running {details}"
    else:
        return f"❌ {name}: Not running {details}"

def main():
    print("=" * 60)
    print(f"DO BUTTON SYSTEM HEALTH CHECK - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Check all required ports
    ports = [
        (8765, "WebSocket Server (Neural UI Detector)"),
        (8766, "DO Button Fix Proxy"),
        (8767, "Enhanced Enterprise Backend"),
        (8768, "Ultimate DO Button Server")
    ]
    
    all_ports_open = True
    for port, name in ports:
        is_open = check_port(port)
        print(format_status(f"Port {port} - {name}", is_open))
        all_ports_open = all_ports_open and is_open
    
    # Check key processes
    processes = [
        ("neural_ui_detector", "Neural UI Detector Server"),
        ("ultimate_do_button_server", "Ultimate DO Button Server"),
        ("fix_do_button_plan_persistence", "DO Button Fix Proxy"),
        ("enhanced_enterprise_backend_with_context", "Enhanced Enterprise Backend")
    ]
    
    all_processes_running = True
    for keyword, name in processes:
        is_running, pids = check_process(keyword)
        print(format_status(name, is_running, f"PIDs: {pids}" if is_running else ""))
        all_processes_running = all_processes_running and is_running
    
    # Check WebSocket connections
    websockets = [
        ("ws://localhost:8765", "Neural UI Detector WebSocket"),
        ("ws://localhost:8766", "DO Button Fix Proxy WebSocket"),
        ("ws://localhost:8767", "Enhanced Enterprise Backend WebSocket"),
        ("ws://localhost:8768", "Ultimate DO Button Server WebSocket")
    ]
    
    all_websockets_working = True
    for url, name in websockets:
        is_working, response = check_websocket(url)
        response_preview = response[:50] + "..." if len(str(response)) > 50 else response
        print(format_status(name, is_working, f"Response: {response_preview}" if is_working else f"Error: {response}"))
        all_websockets_working = all_websockets_working and is_working
    
    # Check plan persistence
    print("\n" + "=" * 60)
    print("DO BUTTON PLAN PERSISTENCE CHECK")
    print("=" * 60)
    
    plans_dir = os.path.join("cache", "plans")
    if os.path.exists(plans_dir):
        plans = [f for f in os.listdir(plans_dir) if f.endswith('.json')]
        print(f"✅ Plans directory exists with {len(plans)} plan files")
        for plan in plans[:5]:  # Show first 5 plans
            print(f"  - {plan}")
        if len(plans) > 5:
            print(f"  - ... and {len(plans) - 5} more")
    else:
        print("❌ Plans directory does not exist")
    
    # Overall status
    print("\n" + "=" * 60)
    print("OVERALL SYSTEM STATUS")
    print("=" * 60)
    
    if all_ports_open and all_processes_running and all_websockets_working:
        print("✅ DO BUTTON SYSTEM IS FULLY OPERATIONAL")
        print("  All required servers are running and accepting connections")
    else:
        print("❌ DO BUTTON SYSTEM HAS ISSUES")
        if not all_ports_open:
            print("  - Some required ports are not open")
        if not all_processes_running:
            print("  - Some required processes are not running")
        if not all_websockets_working:
            print("  - Some WebSocket connections are not working")
        
        print("\nTo fix these issues:")
        print("1. Stop the system: ./STOP_ENHANCED_SYSTEM_WITH_NEURAL_UI.sh")
        print("2. Start the system: ./START_ENHANCED_SYSTEM_WITH_NEURAL_UI.sh")
        print("3. Run this check again: python3 check_do_button_system.py")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()