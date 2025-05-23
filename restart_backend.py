#!/usr/bin/env python3
"""
Restart Backend Server with UI Automation Fix
"""
import os
import signal
import subprocess
import time

def restart_backend():
    """Kill and restart the backend server"""
    
    print("🔄 Restarting Enterprise Backend Server...")
    
    # Find and kill existing server
    try:
        result = subprocess.run(['lsof', '-i', ':8767'], capture_output=True, text=True)
        if result.stdout:
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            for line in lines:
                if 'Python' in line:
                    parts = line.split()
                    pid = int(parts[1])
                    print(f"🔪 Killing existing server (PID: {pid})")
                    os.kill(pid, signal.SIGTERM)
                    time.sleep(2)
    except Exception as e:
        print(f"⚠️ Error killing existing server: {e}")
    
    # Start new server
    print("🚀 Starting updated backend server...")
    os.chdir('/Users/segevbin/Desktop/SensAI/Aiayer/Others')
    
    # Start server in background
    process = subprocess.Popen(['python', 'enterprise_backend_server.py'])
    
    print(f"✅ Started new backend server (PID: {process.pid})")
    print("🖱️ UI automation fix applied!")
    print("📡 Server should be ready in a few seconds...")
    
    return process.pid

if __name__ == "__main__":
    restart_backend()