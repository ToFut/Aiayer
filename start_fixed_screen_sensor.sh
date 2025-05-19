#!/bin/bash
# Start the robust screen sensor

# Kill any existing screen sensor instances
if [ -f "pids/screen_sensor.pid" ]; then
    echo "Stopping existing screen sensor..."
    kill -9 $(cat pids/screen_sensor.pid) 2>/dev/null || true
    rm -f pids/screen_sensor.pid
fi

# Start new robust screen sensor
echo "Starting robust screen sensor..."
mkdir -p logs/sensors
python3 robust_screen_sensor.py > logs/sensors/screen_sensor_stdout.log 2>&1 &

# Check if sensor started
sleep 2
if [ -f "pids/screen_sensor.pid" ]; then
    echo "✅ Screen sensor started successfully (PID: $(cat pids/screen_sensor.pid))"
else
    echo "❌ Screen sensor failed to start"
fi