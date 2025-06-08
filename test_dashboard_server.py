#!/usr/bin/env python3
"""
Test script for dashboard server connectivity and response.
"""
import requests
import json
import time
import webbrowser
import os
import signal
import sys
from datetime import datetime

# Dashboard server URL
BASE_URL = "http://localhost:8081"

def print_with_timestamp(message):
    """Print message with timestamp."""
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] {message}")

def test_dashboard_server():
    """Test dashboard server connectivity and response."""
    print_with_timestamp("Testing dashboard server connectivity...")
    
    try:
        # Test main dashboard page
        response = requests.get(f"{BASE_URL}/")
        print_with_timestamp(f"Main page response status: {response.status_code}")
        if response.status_code == 200:
            print_with_timestamp("Dashboard server is running and responding to requests.")
        else:
            print_with_timestamp("Dashboard server returned an unexpected status code.")
            return False
        
        # Test metrics API
        print_with_timestamp("\nTesting metrics API...")
        response = requests.get(f"{BASE_URL}/api/metrics")
        print_with_timestamp(f"Metrics API response status: {response.status_code}")
        if response.status_code == 200:
            metrics_data = response.json()
            print_with_timestamp("Metrics API is working.")
            print_with_timestamp(f"Server timestamp: {datetime.fromtimestamp(metrics_data.get('server_timestamp', 0))}")
            print_with_timestamp(f"Data timestamp: {datetime.fromtimestamp(metrics_data.get('timestamp', 0))}")
            memory_metrics = metrics_data.get('memory_metrics', {})
            print_with_timestamp(f"Records count: {memory_metrics.get('records_count', 'N/A')}")
        else:
            print_with_timestamp("Metrics API returned an unexpected status code.")
            return False
        
        # Test time series API
        print_with_timestamp("\nTesting time series API...")
        response = requests.get(f"{BASE_URL}/api/time-series")
        print_with_timestamp(f"Time series API response status: {response.status_code}")
        if response.status_code == 200:
            time_series_data = response.json()
            print_with_timestamp("Time series API is working.")
            timestamps = time_series_data.get('timestamps', [])
            print_with_timestamp(f"Number of data points: {len(timestamps)}")
            if timestamps:
                print_with_timestamp(f"First timestamp: {datetime.fromtimestamp(timestamps[0])}")
                print_with_timestamp(f"Last timestamp: {datetime.fromtimestamp(timestamps[-1])}")
        else:
            print_with_timestamp("Time series API returned an unexpected status code.")
            return False
        
        return True
    
    except requests.exceptions.ConnectionError:
        print_with_timestamp("Failed to connect to dashboard server. Make sure it's running.")
        return False
    except Exception as e:
        print_with_timestamp(f"An error occurred: {str(e)}")
        return False

def open_test_dashboard():
    """Open the test dashboard HTML page in the default browser."""
    test_dashboard_path = os.path.join(os.getcwd(), "web", "dashboard", "test_dashboard.html")
    
    if os.path.exists(test_dashboard_path):
        print_with_timestamp(f"Opening test dashboard: {test_dashboard_path}")
        webbrowser.open(f"file://{test_dashboard_path}")
    else:
        print_with_timestamp(f"Test dashboard file not found at: {test_dashboard_path}")

def main():
    """Main function."""
    print_with_timestamp("Starting dashboard server test...")
    
    if test_dashboard_server():
        print_with_timestamp("\nAll tests passed. Dashboard server is working properly.")
        
        # Ask if user wants to open the test dashboard
        answer = input("\nDo you want to open the test dashboard in your browser? (y/n): ")
        if answer.lower() == 'y':
            open_test_dashboard()
    else:
        print_with_timestamp("\nSome tests failed. Dashboard server may not be working properly.")
    
    print_with_timestamp("Test completed.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_with_timestamp("\nTest interrupted by user.")
        sys.exit(0)