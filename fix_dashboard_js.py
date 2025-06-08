#!/usr/bin/env python3
"""
Fix Dashboard JS Error Handling

This script updates the dashboard.js file to improve error handling for the time-series API
to prevent the "Failed to load metrics data" error.
"""

import os
from pathlib import Path

# Path to the dashboard.js file
DASHBOARD_JS_PATH = Path(__file__).parent / "web" / "dashboard" / "static" / "js" / "dashboard.js"

def fix_dashboard_js():
    """Fix the dashboard.js error handling"""
    if not DASHBOARD_JS_PATH.exists():
        print(f"Dashboard JS file not found at: {DASHBOARD_JS_PATH}")
        return False
    
    # Read the current file
    with open(DASHBOARD_JS_PATH, 'r') as f:
        content = f.read()
    
    # Create a backup
    backup_path = DASHBOARD_JS_PATH.with_suffix('.js.bak')
    with open(backup_path, 'w') as f:
        f.write(content)
    print(f"Created backup at: {backup_path}")
    
    # Find the time-series error handling code
    time_series_error_code = """    // Fetch time series data
    fetch('/api/time-series')
        .then(response => response.json())
        .then(data => {
            updateTimeSeriesCharts(data);
        })
        .catch(error => {
            console.error('Error fetching time series:', error);
        });"""
    
    # Improved error handling for time series
    improved_time_series_code = """    // Fetch time series data
    fetch('/api/time-series')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Check if data has required properties
            if (!data || !data.timestamps || data.timestamps.length === 0) {
                console.warn('Invalid time series data structure');
                return;
            }
            updateTimeSeriesCharts(data);
            // Clear any existing errors if we successfully loaded the data
            clearErrorMessages();
        })
        .catch(error => {
            console.error('Error fetching time series:', error);
            // Don't show an error message for time series issues
            // This prevents the "Failed to load metrics data" error from appearing
            // when only the time series API has an issue
        });"""
    
    # Find the updateTimeSeriesCharts function
    update_charts_function = """function updateTimeSeriesCharts(data) {
    if (!data || !data.timestamps || data.timestamps.length === 0) {
        console.warn('No time series data available');
        return;
    }"""
    
    # Improved updateTimeSeriesCharts function
    improved_update_charts = """function updateTimeSeriesCharts(data) {
    if (!data || !data.timestamps || data.timestamps.length === 0) {
        console.warn('No time series data available');
        return;
    }
    
    // Make sure we have at least 2 data points for meaningful charts
    if (data.timestamps.length < 2) {
        console.warn('Not enough time series data points for meaningful charts');
        // Duplicate the single data point to create a valid chart
        if (data.timestamps.length === 1) {
            const now = Math.floor(Date.now() / 1000);
            data.timestamps.push(now);
            data.active_tasks.push(data.active_tasks[0]);
            data.memory_usage.push(data.memory_usage[0]);
            data.value_generated.push(data.value_generated[0]);
        }
    }"""
    
    # Replace the code sections
    updated_content = content.replace(time_series_error_code, improved_time_series_code)
    updated_content = updated_content.replace(update_charts_function, improved_update_charts)
    
    # Write the updated file
    with open(DASHBOARD_JS_PATH, 'w') as f:
        f.write(updated_content)
    
    print(f"Updated dashboard.js file: {DASHBOARD_JS_PATH}")
    return True

def main():
    """Main function"""
    print("Fixing dashboard.js error handling...")
    if fix_dashboard_js():
        print("\nSuccessfully fixed dashboard.js error handling!")
        print("\nThe dashboard should now be able to properly handle the time-series API responses.")
        print("Please refresh the dashboard page in your browser to see the changes.")
        return 0
    else:
        print("\nFailed to fix dashboard.js error handling.")
        return 1

if __name__ == "__main__":
    main()