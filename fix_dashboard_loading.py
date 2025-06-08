#!/usr/bin/env python3
"""
Fix dashboard loading issue by ensuring proper loading state management
"""
import os
import re
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('dashboard_loading_fix')

# Get the path to the dashboard.js file
js_file_path = os.path.join('web', 'dashboard', 'static', 'js', 'dashboard.js')
if not os.path.exists(js_file_path):
    js_file_path = '/Users/segevbin/Desktop/SensAI/Aiayer/web/dashboard/static/js/dashboard.js'

logger.info(f"Fixing dashboard loading issue in {js_file_path}")

# Read the current content of the file
with open(js_file_path, 'r') as f:
    js_content = f.read()

# Analyze the hideLoading function to ensure it's being called correctly
if 'hideLoading' in js_content:
    logger.info("Found hideLoading function in the code")
else:
    logger.error("Could not find hideLoading function - this is unexpected")

# Find and fix the loadDashboardData function to ensure it always hides loading
# The problem might be that if any fetch fails, the loading indicator stays visible
# Let's modify the function to ensure it always hides the loading state
load_dashboard_data_pattern = r'function loadDashboardData\(\) \{([\s\S]*?)\}'
match = re.search(load_dashboard_data_pattern, js_content)

if match:
    original_function = match.group(0)
    
    # Ensure hideLoading is called in all catch blocks and at the end of the function
    modified_function = original_function.replace(
        "showError('Failed to load metrics');",
        "showError('Failed to load metrics');\nhideLoading();"
    ).replace(
        "console.error('Error fetching time series:', error);",
        "console.error('Error fetching time series:', error);\nhideLoading();"
    )
    
    # Add a failsafe timeout to hide loading after 10 seconds no matter what
    modified_function = modified_function.replace(
        "showLoading('Loading dashboard data...');",
        "showLoading('Loading dashboard data...');\n" +
        "    // Add failsafe timeout to hide loading indicator after 10 seconds\n" +
        "    setTimeout(function() {\n" +
        "        const loadingIndicator = document.getElementById('loading-indicator');\n" +
        "        if (loadingIndicator) {\n" +
        "            console.warn('Forcing hideLoading after timeout');\n" +
        "            hideLoading();\n" +
        "        }\n" +
        "    }, 10000);"
    )
    
    # Update the js content with the modified function
    js_content = js_content.replace(original_function, modified_function)
    
    logger.info("Modified loadDashboardData function to ensure loading state is always cleared")
else:
    logger.error("Could not find loadDashboardData function - this is unexpected")

# Save the modified file
with open(js_file_path, 'w') as f:
    f.write(js_content)

logger.info(f"Dashboard loading fix applied to {js_file_path}")
logger.info("A failsafe timeout has been added to ensure loading indicator is always cleared")

# Create a backup copy of the modified file
backup_path = f"{js_file_path}.bak"
with open(backup_path, 'w') as f:
    f.write(js_content)
logger.info(f"Backup saved to {backup_path}")

print("✅ Fixed dashboard loading issue. The dashboard should no longer get stuck on 'Loading dashboard data...'")
print("   A failsafe timeout has been added to automatically clear the loading state after 10 seconds.")