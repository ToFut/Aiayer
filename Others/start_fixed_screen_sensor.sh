#!/bin/bash
# Start the robust screen sensor

# Create necessary directories
mkdir -p logs/sensors/screen_sensor
mkdir -p cache/screen_sensor
mkdir -p pids

# Kill any existing screen sensor instances
if [ -f "pids/screen_sensor.pid" ]; then
    echo "Stopping existing screen sensor..."
    kill -9 $(cat pids/screen_sensor.pid) 2>/dev/null || true
    rm -f pids/screen_sensor.pid
fi

# Start the fixed screen sensor
echo "Starting fixed screen sensor..."
python3 fixed_screen_sensor.py > logs/sensors/screen_sensor/screen_sensor.log 2>&1 &
SCREEN_SENSOR_PID=$!
echo $SCREEN_SENSOR_PID > pids/screen_sensor.pid
echo "Screen sensor started with PID: $SCREEN_SENSOR_PID"

# Check if sensor started
sleep 2
if [ -f "pids/screen_sensor.pid" ]; then
    echo "✅ Screen sensor started successfully (PID: $(cat pids/screen_sensor.pid))"
else
    echo "❌ Screen sensor failed to start"
fi