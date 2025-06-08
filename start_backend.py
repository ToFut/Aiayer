#!/usr/bin/env python3
import os
import sys
import subprocess
import time

# Try to import the enhanced backend first
try:
    print("Attempting to start enhanced_enterprise_backend_with_context.py...")
    process = subprocess.Popen(
        ["python3", "enhanced_enterprise_backend_with_context.py"],
        stdout=open("logs/backend/enhanced_enterprise_8767.log", "w"),
        stderr=subprocess.STDOUT
    )
    
    # Wait a bit to see if it starts successfully
    time.sleep(5)
    
    # Check if it's still running
    if process.poll() is not None:
        print("Enhanced backend failed to start. Trying simple_backend_server.py...")
        # If not, try the simple backend
        subprocess.Popen(
            ["python3", "simple_backend_server.py"],
            stdout=open("logs/backend/simple_backend.log", "w"),
            stderr=subprocess.STDOUT
        )
    else:
        print("Enhanced backend started successfully!")
except Exception as e:
    print(f"Error starting backend: {e}")
    print("Trying simple_backend_server.py as fallback...")
    try:
        subprocess.Popen(
            ["python3", "simple_backend_server.py"],
            stdout=open("logs/backend/simple_backend.log", "w"),
            stderr=subprocess.STDOUT
        )
    except Exception as e2:
        print(f"Error starting simple backend: {e2}")
        sys.exit(1)
