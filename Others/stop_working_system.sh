#\!/bin/bash

GREEN='\033[0;32m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$SCRIPT_DIR/pids"

echo -e "${GREEN}Stopping working system...${NC}"

# Stop by PID files
for pid_file in "$PID_DIR"/*.pid; do
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        component=$(basename "$pid_file" .pid)
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${GREEN}Stopping $component (PID: $pid)${NC}"
            kill -TERM "$pid" 2>/dev/null || kill -9 "$pid" 2>/dev/null
        fi
        rm -f "$pid_file"
    fi
done

# Kill by port
for port in 8765 8767 8080; do
    if lsof -ti :$port >/dev/null 2>&1; then
        echo -e "${GREEN}Killing processes on port $port${NC}"
        lsof -ti :$port | xargs kill -9 2>/dev/null || true
    fi
done

# Kill by process name
pkill -f "fixed_ws_8765" 2>/dev/null || true
pkill -f "enhanced_backend" 2>/dev/null || true
pkill -f "http.server" 2>/dev/null || true

echo -e "${GREEN}Working system stopped${NC}"
EOF < /dev/null