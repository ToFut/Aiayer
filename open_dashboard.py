#!/usr/bin/env python3
"""
Script to open the dashboard in a browser.
"""
import webbrowser
import time
import os
import sys
from datetime import datetime

def print_with_timestamp(message):
    """Print message with timestamp."""
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] {message}")

def open_dashboard():
    """Open the dashboard in the default browser."""
    dashboard_url = "http://localhost:8081/"
    test_dashboard_path = os.path.join(os.getcwd(), "web", "dashboard", "test_dashboard.html")
    
    print_with_timestamp(f"Opening dashboard: {dashboard_url}")
    webbrowser.open(dashboard_url)
    
    time.sleep(2)  # Wait a bit before opening the test dashboard
    
    print_with_timestamp(f"Opening test dashboard: file://{test_dashboard_path}")
    webbrowser.open(f"file://{test_dashboard_path}")

if __name__ == "__main__":
    print_with_timestamp("Opening dashboard in browser...")
    try:
        open_dashboard()
        print_with_timestamp("Done. Check your browser for the dashboard.")
    except Exception as e:
        print_with_timestamp(f"An error occurred: {str(e)}")
        sys.exit(1)