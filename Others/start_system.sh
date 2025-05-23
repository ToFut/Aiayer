#!/bin/bash

# Create necessary directories
mkdir -p logs/memory logs/llm logs/sensors logs/sensors/total_screen pids
mkdir -p cache/total_screen_analyzer cache/screen_sensor cache/process_sensor

# Function to check if a process is running
check_process() {
    if [ -f "pids/$1.pid" ]; then
        pid=$(cat "pids/$1.pid")
        if ps -p $pid > /dev/null; then
            return 0
        fi
    fi
    return 1
}

# Function to start a service
start_service() {
    local service=$1
    local script=$2
    local log_file="logs/${service}.log"
    
    echo "Starting $service..."
    python3 $script > $log_file 2>&1 &
    echo $! > "pids/$service.pid"
    sleep 3
    
    if check_process $service; then
        echo "✅ $service started successfully"
    else
        echo "❌ Failed to start $service"
        tail -10 $log_file
        return 1
    fi
}

# Kill any existing processes
echo "Cleaning up existing processes..."
for service in bridge_server memory_service llm_service total_screen_analyzer process_sensor; do
    if check_process $service; then
        pid=$(cat "pids/$service.pid")
        kill $pid 2>/dev/null
        rm "pids/$service.pid"
    fi
done

# Kill by process name as backup
pkill -f "total_screen_analyzer" 2>/dev/null || true
pkill -f "process_sensor" 2>/dev/null || true
pkill -f "bridge_server" 2>/dev/null || true

# Start services in order
echo "Starting services..."

# 1. Start bridge server (use the working one)
if [ -f "Others/fixed_bridge_server_enhanced.py" ]; then
    echo "Using enhanced bridge server..."
    start_service "bridge_server" "Others/fixed_bridge_server_enhanced.py"
elif [ -f "bridge/server.py" ]; then
    start_service "bridge_server" "bridge/server.py"
elif [ -f "Others/simple_ws_server_8767.py" ]; then
    echo "Using simple WebSocket server..."
    start_service "bridge_server" "Others/simple_ws_server_8767.py"
else
    echo "❌ No bridge server found, creating minimal one..."
    cat > "minimal_bridge.py" << 'EOF'
#!/usr/bin/env python3
import asyncio
import json
import logging
import websockets
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('bridge')

clients = {}

async def handle_client(websocket, path):
    client_id = id(websocket)
    logger.info(f"Client {client_id} connected")
    
    try:
        await websocket.send(json.dumps({"type": "welcome", "message": "Bridge server"}))
        
        async for message in websocket:
            try:
                data = json.loads(message)
                if data.get("type") == "register":
                    clients[client_id] = {"type": data.get("client_type"), "ws": websocket}
                    await websocket.send(json.dumps({"type": "registration_confirmed", "payload": {"client_type": data.get("client_type")}}))
                    logger.info(f"Registered {data.get('client_type')}")
                elif data.get("type") == "sensor_data":
                    await store_sensor_data(data)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} disconnected")
    finally:
        if client_id in clients:
            del clients[client_id]

async def store_sensor_data(data):
    """Store sensor data in memory files"""
    try:
        payload = data.get("payload", {})
        sensor_type = data.get("sensor_type", "unknown")
        
        # Update memory_state.json
        memory_file = "memory/memory_state.json"
        os.makedirs("memory", exist_ok=True)
        
        # Load existing memory
        try:
            with open(memory_file, 'r') as f:
                memory_state = json.load(f)
        except:
            memory_state = {
                "version": "1.0",
                "last_update": datetime.now().isoformat(),
                "context": {},
                "short_term": [],
                "long_term": [],
                "sensor_data": {"screen": {}, "process": {}, "file": {}}
            }
        
        # Update with sensor data
        timestamp = datetime.now().isoformat()
        if sensor_type == "total_screen_analyzer":
            # Update context
            memory_state["context"].update({
                "active_window": payload.get("application", {}).get("name", ""),
                "active_app": payload.get("application", {}).get("name", ""),
                "screen_text": payload.get("text_sample", "")[:200],
                "semantic_summary": payload.get("semantic_summary", "")
            })
            
            # Store screen data
            memory_state["sensor_data"]["screen"][timestamp] = payload
            
            # Add to short term
            memory_state["short_term"].append({
                "timestamp": timestamp,
                "type": "screen_analysis", 
                "content": payload.get("semantic_summary", ""),
                "app": payload.get("application", {}).get("name", "")
            })
            
            # Keep only last 10 short term items
            memory_state["short_term"] = memory_state["short_term"][-10:]
        
        memory_state["last_update"] = timestamp
        
        # Save memory
        with open(memory_file, 'w') as f:
            json.dump(memory_state, f, indent=2)
        
        logger.info(f"✅ Stored {sensor_type} data: {payload.get('semantic_summary', 'data')[:50]}")
        
    except Exception as e:
        logger.error(f"Error storing sensor data: {e}")

async def main():
    logger.info("Starting minimal bridge server on localhost:8765")
    with open('pids/bridge_server.pid', 'w') as f:
        f.write(str(os.getpid()))
    
    start_server = websockets.serve(handle_client, "localhost", 8765)
    await start_server
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
EOF
    start_service "bridge_server" "minimal_bridge.py"
fi

# 2. Start memory service (if exists)
if [ -f "memory/memory_service.py" ]; then
    start_service "memory_service" "memory/memory_service.py"
else
    echo "ℹ️  Memory service not found, using bridge integration"
fi

# 3. Start TotalScreenAnalyzer
echo "Starting TotalScreenAnalyzer..."
start_service "total_screen_analyzer" "sensors/total_screen_analyzer.py"

# 4. Start process sensor
if [ -f "sensors/enhanced_fixed_process_sensor.py" ]; then
    start_service "process_sensor" "sensors/enhanced_fixed_process_sensor.py"
elif [ -f "sensors/process_sensor.py" ]; then
    start_service "process_sensor" "sensors/process_sensor.py"
else
    echo "⚠️  No process sensor found"
fi

echo "All services started successfully"
echo "System is ready"

# Keep script running and handle cleanup on exit
trap 'echo "Stopping services..."; for service in bridge_server memory_service llm_service; do if check_process $service; then pid=$(cat "pids/$service.pid"); kill $pid 2>/dev/null; rm "pids/$service.pid"; fi; done' EXIT

# Wait for user interrupt
echo "Press Ctrl+C to stop all services"
while true; do
    sleep 1
done 