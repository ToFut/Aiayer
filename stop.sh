#!/bin/bash

echo "Stopping Local Assistant system..."

RUNNING_PIDS_FILE=".running_pids"

# Function to kill process by PID file
kill_pid_file() {
    local pid_file=$1
    local name=$2
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo "Stopping $name (PID: $pid)..."
            kill -9 $pid > /dev/null 2>&1
        fi
        rm -f "$pid_file"
    fi
}

# Function to kill process by PID
kill_process() {
    local pid=$1
    local name=$2
    if ps -p $pid > /dev/null 2>&1; then
        echo "Stopping $name (PID: $pid)..."
        kill -9 $pid > /dev/null 2>&1
    fi
}

# Kill processes from running PIDs file
if [ -f $RUNNING_PIDS_FILE ]; then
    echo "Found running PIDs file, stopping services..."
    while read line; do
        # Skip header lines and empty lines
        if [[ "$line" == *"#"* ]]; then
            # Extract the PID and name
            pid=$(echo $line | cut -d '#' -f1 | xargs)
            name=$(echo $line | cut -d '#' -f2 | xargs)
            
            if [ -n "$pid" ] && [ "$pid" -eq "$pid" ] 2>/dev/null; then
                # Check if process still exists
                if ps -p $pid > /dev/null 2>&1; then
                    echo "Stopping $name with PID $pid"
                    # Try graceful termination first
                    kill -15 $pid 2>/dev/null
                    sleep 1
                    # Force kill if process still exists
                    if ps -p $pid > /dev/null 2>&1; then
                        echo "Force killing $name (PID: $pid)..."
                        kill -9 $pid 2>/dev/null
                    fi
                else
                    echo "Process $name (PID: $pid) is not running"
                fi
            fi
        fi
    done < $RUNNING_PIDS_FILE
    echo "$(date): All processes stopped" > $RUNNING_PIDS_FILE
else
    echo "No running PIDs file found."
fi

# Kill processes using legacy PID files as a fallback
kill_pid_file .overlay.pid "overlay UI"
kill_pid_file .bridge.pid "bridge service"
kill_pid_file .main.pid "main application"
kill_pid_file .websocket.pid "WebSocket server"
kill_pid_file .ollama.pid "Ollama"

# Kill any processes still using our ports
for port in 8765 8766 5001 5002 11434; do
    if lsof -i :$port > /dev/null 2>&1; then
        echo "Cleaning up port $port..."
        lsof -t -i :$port | xargs kill -9 > /dev/null 2>&1
    fi
done

# Kill any remaining related processes
echo "Checking for remaining processes..."
for process in "tauri" "python main_with_overlay.py" "python websocket_server.py" "ollama serve"; do
    if pgrep -f "$process" > /dev/null; then
        echo "Stopping $process processes..."
        pkill -f "$process"
    fi
done

echo "All processes stopped successfully!"