#!/bin/bash

# Test script for the Neural UI DO Button fix
echo "=== Testing Neural UI DO Button Fix ==="
echo "Make sure START_ENHANCED_SYSTEM_WITH_NEURAL_UI.sh is running first!"
echo ""

# Check if the required servers are running
echo "Checking if required servers are running..."
python3 -c "import socket; s=socket.socket(); result=s.connect_ex(('localhost', 8767)); exit(1 if result != 0 else 0)" || {
    echo "❌ Error: Backend server (8767) is not running"
    echo "Please run START_ENHANCED_SYSTEM_WITH_NEURAL_UI.sh first and try again"
    exit 1
}

# Run the test script
echo "Running test script..."
python3 test_neural_ui_do_button_fix.py

# Display a reminder about checking logs
echo ""
echo "To verify the fix in the logs, you can check the following:"
echo "- Fix DO Button Connection Bridge: tail -f logs/do_button_fix.log"
echo "- Neural UI DO Button Handler: tail -f logs/neural_ui_do_button.log"
echo "- Ultimate DO Button Server: tail -f logs/ultimate_do_button_server.log"