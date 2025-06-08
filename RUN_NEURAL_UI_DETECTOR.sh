#!/bin/bash
# Neural UI Detector Launcher
# This script runs the improved Neural UI Detector with proper handling for different modes

# Set default values
DEBUG=false
PORT=8768
FIXED=true
TEST=false
HELP=false
BROWSER=true
TESTING_FRAMEWORK=false

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --debug|-d) DEBUG=true ;;
        --port|-p) PORT="$2"; shift ;;
        --test|-t) TEST=true ;;
        --no-browser|-n) BROWSER=false ;;
        --help|-h) HELP=true ;;
        --original|-o) FIXED=false ;;
        --test-framework|-f) TESTING_FRAMEWORK=true ;;
        *) echo "Unknown parameter: $1"; HELP=true ;;
    esac
    shift
done

# Show help
if [ "$HELP" = true ]; then
    echo "Neural UI Detector Launcher"
    echo "============================="
    echo "Usage: ./RUN_NEURAL_UI_DETECTOR.sh [options]"
    echo ""
    echo "Options:"
    echo "  --debug, -d        Enable debug logging"
    echo "  --port, -p PORT    Use specific port (default: 8768)"
    echo "  --test, -t         Run in test mode with test page"
    echo "  --no-browser, -n   Don't open browser automatically"
    echo "  --original, -o     Run original version instead of fixed version"
    echo "  --test-framework, -f Run the testing framework"
    echo "  --help, -h         Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./RUN_NEURAL_UI_DETECTOR.sh                   # Run fixed version on port 8768"
    echo "  ./RUN_NEURAL_UI_DETECTOR.sh --debug --test    # Run fixed version in test mode with debug logging"
    echo "  ./RUN_NEURAL_UI_DETECTOR.sh --original        # Run original version"
    echo "  ./RUN_NEURAL_UI_DETECTOR.sh --test-framework  # Run the testing framework"
    exit 0
fi

# Print banner
echo "=================================================================="
echo "                    NEURAL UI DETECTOR LAUNCHER                    "
echo "=================================================================="
echo "Mode: $([ "$FIXED" = true ] && echo "FIXED" || echo "ORIGINAL")"
echo "Port: $PORT"
echo "Debug: $([ "$DEBUG" = true ] && echo "ENABLED" || echo "DISABLED")"
echo "Test Mode: $([ "$TEST" = true ] && echo "ENABLED" || echo "DISABLED")"
echo "Browser: $([ "$BROWSER" = true ] && echo "ENABLED" || echo "DISABLED")"
echo "Testing Framework: $([ "$TESTING_FRAMEWORK" = true ] && echo "ENABLED" || echo "DISABLED")"
echo "=================================================================="
echo ""

# Function to verify dependencies
check_dependencies() {
    echo "Checking dependencies..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo "Python 3 is required but not found"
        exit 1
    fi
    
    # Check required Python packages
    python3 -c "import websockets" 2>/dev/null || { echo "Python package 'websockets' is required. Install with: pip install websockets"; exit 1; }
    
    # Check for required files
    if [ "$FIXED" = true ]; then
        if [ ! -f "fixed_neural_ui_detector_server.py" ]; then
            echo "Fixed server script not found: fixed_neural_ui_detector_server.py"
            exit 1
        fi
    else
        if [ ! -f "neural_ui_detector_server.py" ]; then
            echo "Original server script not found: neural_ui_detector_server.py"
            exit 1
        fi
    fi
    
    if [ "$TEST" = true ] && [ ! -f "test_neural_ui_detector_fixed.html" ]; then
        echo "Test HTML file not found: test_neural_ui_detector_fixed.html"
        exit 1
    fi
    
    if [ "$TESTING_FRAMEWORK" = true ] && [ ! -f "do_button_testing_framework.py" ]; then
        echo "Testing framework script not found: do_button_testing_framework.py"
        exit 1
    fi
    
    echo "All dependencies found."
}

# Function to kill processes on a specific port
kill_port_process() {
    local port=$1
    
    # Check for processes using the port
    if [ "$(uname)" == "Darwin" ]; then
        # macOS
        local pid=$(lsof -ti:$port)
        if [ ! -z "$pid" ]; then
            echo "Killing process using port $port: PID $pid"
            kill -9 $pid 2>/dev/null
        fi
    elif [ "$(uname)" == "Linux" ]; then
        # Linux
        local pid=$(lsof -ti:$port)
        if [ ! -z "$pid" ]; then
            echo "Killing process using port $port: PID $pid"
            kill -9 $pid 2>/dev/null
        fi
    elif [[ "$(uname)" == MINGW* ]] || [[ "$(uname)" == CYGWIN* ]]; then
        # Windows with Git Bash or Cygwin
        local pid=$(netstat -ano | grep ":$port" | awk '{print $5}' | head -n 1)
        if [ ! -z "$pid" ]; then
            echo "Killing process using port $port: PID $pid"
            taskkill /F /PID $pid 2>/dev/null
        fi
    else
        echo "Unsupported platform: $(uname)"
    fi
}

# Function to run the Neural UI Detector server
run_server() {
    # Kill any existing processes on the port
    kill_port_process $PORT
    
    # Prepare command
    if [ "$FIXED" = true ]; then
        CMD="python3 fixed_neural_ui_detector_server.py --port $PORT"
    else
        CMD="python3 neural_ui_detector_server.py --port $PORT"
    fi
    
    # Add debug flag if needed
    if [ "$DEBUG" = true ]; then
        CMD="$CMD --debug"
    fi
    
    # Run the server
    echo "Starting Neural UI Detector server..."
    echo "Command: $CMD"
    eval $CMD &
    SERVER_PID=$!
    
    # Wait for server to start
    echo "Waiting for server to start..."
    sleep 3
    
    # Check if server is running
    if ! ps -p $SERVER_PID > /dev/null; then
        echo "Server failed to start. Check logs for details."
        exit 1
    fi
    
    echo "Server started with PID $SERVER_PID"
    
    # Start HTTP server for test page if needed
    if [ "$TEST" = true ]; then
        # Kill any existing HTTP server on port 8080
        kill_port_process 8080
        
        echo "Starting HTTP server for test page..."
        python3 -m http.server 8080 &
        HTTP_PID=$!
        
        # Wait for HTTP server to start
        sleep 2
        
        # Check if HTTP server is running
        if ! ps -p $HTTP_PID > /dev/null; then
            echo "HTTP server failed to start."
            kill -9 $SERVER_PID 2>/dev/null
            exit 1
        fi
        
        echo "HTTP server started with PID $HTTP_PID"
        
        # Open browser if enabled
        if [ "$BROWSER" = true ]; then
            echo "Opening test page in browser..."
            sleep 1
            
            # Try to open browser based on platform
            if [ "$(uname)" == "Darwin" ]; then
                # macOS
                open "http://localhost:8080/test_neural_ui_detector_fixed.html"
            elif [ "$(uname)" == "Linux" ]; then
                # Linux
                xdg-open "http://localhost:8080/test_neural_ui_detector_fixed.html" 2>/dev/null || \
                sensible-browser "http://localhost:8080/test_neural_ui_detector_fixed.html" 2>/dev/null || \
                echo "Could not open browser automatically. Please open http://localhost:8080/test_neural_ui_detector_fixed.html manually."
            elif [[ "$(uname)" == MINGW* ]] || [[ "$(uname)" == CYGWIN* ]]; then
                # Windows
                start "http://localhost:8080/test_neural_ui_detector_fixed.html"
            else
                echo "Could not open browser automatically. Please open http://localhost:8080/test_neural_ui_detector_fixed.html manually."
            fi
        fi
        
        # Wait for both processes
        echo "Servers running. Press Ctrl+C to stop."
        wait $SERVER_PID $HTTP_PID
    else
        # Wait for server only
        echo "Server running. Press Ctrl+C to stop."
        wait $SERVER_PID
    fi
}

# Function to run the testing framework
run_testing_framework() {
    echo "Running Neural UI Detector Testing Framework..."
    
    # Run the testing framework
    python3 do_button_testing_framework.py
    
    # Check the result
    if [ $? -eq 0 ]; then
        echo "Testing framework completed successfully."
    else
        echo "Testing framework failed. Check logs for details."
    fi
}

# Main script
check_dependencies

if [ "$TESTING_FRAMEWORK" = true ]; then
    run_testing_framework
else
    run_server
fi

echo "Done."
exit 0