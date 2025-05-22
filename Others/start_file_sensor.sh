#!/bin/bash

# Create necessary directories
mkdir -p logs/sensors/sensor_file
mkdir -p cache/file_sensor
mkdir -p pids

# Start the file sensor
echo "Starting file sensor..."
python3 sensors/file_sensor.py > logs/sensors/sensor_file/file_sensor.log 2>&1 &
FILE_SENSOR_PID=$!
echo "File sensor started with PID $FILE_SENSOR_PID"
echo $FILE_SENSOR_PID > pids/file_sensor.pid

# Wait briefly to ensure process starts
sleep 2

# Check if file sensor is running
if [ -f "pids/file_sensor.pid" ]; then
    pid=$(cat "pids/file_sensor.pid")
    if ps -p $pid > /dev/null; then
        echo "✅ File sensor is running (PID: $pid)"
    else
        echo "❌ File sensor failed to start"
        echo "See logs/sensors/sensor_file/file_sensor.log for details"
    fi
fi

echo "=== File Sensor Started ==="
echo "To check logs, use:"
echo "tail -f logs/sensors/sensor_file/file_sensor.log"
echo ""
echo "To stop the file sensor:"
echo "kill \$(cat pids/file_sensor.pid)" 