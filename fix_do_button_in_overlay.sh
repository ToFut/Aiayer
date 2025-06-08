#\!/bin/bash

echo "==== DO Button Fix for Neural UI Enhanced System ===="
echo ""
echo "This script will configure your overlay to connect to the DO Button handler on port 8768."
echo ""

# Find all current HTML files that might contain WebSocket connections
echo "Searching for overlay HTML files..."
OVERLAY_FILES=$(find . -name "*.html" | xargs grep -l "WebSocket" | sort)

echo "Found these potential overlay files:"
echo "$OVERLAY_FILES"
echo ""

echo "To fix the DO button, run this in your browser console:"
echo ""
echo "// Fix DO button WebSocket connection"
echo "window.originalWebSocket = window.WebSocket;"
echo "window.WebSocket = function(url, protocols) {"
echo "  // If connecting to port 8765, redirect to our DO button handler"
echo "  if (url.includes('8765')) {"
echo "    console.log('Redirecting WebSocket connection to DO button handler on port 8768');"
echo "    return new window.originalWebSocket('ws://localhost:8768', protocols);"
echo "  }"
echo "  // Otherwise, use the original WebSocket"
echo "  return new window.originalWebSocket(url, protocols);"
echo "};"
echo "console.log('DO button fix applied. WebSocket connections to port 8765 will be redirected to 8768.');"
echo ""
echo "Alternatively, manually change the WebSocket URL in the overlay to:"
echo "ws://localhost:8768"
echo ""
echo "==== Test Your DO Button ===="
echo "Open the test page: http://localhost:8080/test_do_button_fix.html"
echo "Click the 'Connect' button with ws://localhost:8768 in the URL field"
echo "Then try each of the button formats to verify the handler is working"
