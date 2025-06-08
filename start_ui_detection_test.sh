#!/bin/bash

# Start a simple HTTP server to serve the test page
python3 -m http.server 8080 &
HTTP_SERVER_PID=$!

echo "Started HTTP server on port 8080 (PID: $HTTP_SERVER_PID)"

# Open the test page in the default browser
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open http://localhost:8080/ui_detection_input_controller_test.html
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    xdg-open http://localhost:8080/ui_detection_input_controller_test.html
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # Windows
    start http://localhost:8080/ui_detection_input_controller_test.html
else
    echo "Please open http://localhost:8080/ui_detection_input_controller_test.html in your browser"
fi

# Wait for user to press Ctrl+C
echo "Press Ctrl+C to stop the server"
trap "kill $HTTP_SERVER_PID; echo 'Server stopped'; exit 0" INT
wait $HTTP_SERVER_PID