#!/bin/bash
# Start the enhanced screen sensor

# Create required directories
mkdir -p logs/sensors
mkdir -p cache/screen_sensor
mkdir -p pids

# Kill any existing screen sensor
echo "Stopping any running screen sensor processes..."
pids=$(ps aux | grep -i "screen_sensor.py\|enhanced_screen_sensor.py" | grep -v grep | awk '{print $2}')
if [ -n "$pids" ]; then
  echo "Killing processes: $pids"
  for pid in $pids; do
    kill -9 $pid 2>/dev/null || echo "Process $pid already gone"
  done
  echo "Screen sensor processes stopped"
else
  echo "No screen sensor processes found running"
fi

# Initialize screen cache with proper structure
echo "Initializing screen cache..."
timestamp=$(date +%Y%m%d_%H%M%S)
if [ -f "cache/screen_sensor/screen_cache.json" ] && [ -s "cache/screen_sensor/screen_cache.json" ]; then
  cp "cache/screen_sensor/screen_cache.json" "cache/screen_sensor/screen_cache.json.bak_${timestamp}"
fi

# Make the script executable
chmod +x enhanced_screen_sensor.py

echo "Starting enhanced screen sensor..."
python3 enhanced_screen_sensor.py > logs/sensors/enhanced_screen_sensor_stdout.log 2>&1 &
SENSOR_PID=$!
echo $SENSOR_PID > pids/enhanced_screen_sensor.pid
echo "Enhanced screen sensor started with PID $SENSOR_PID"
echo "To check logs, use:"
echo "tail -f logs/sensors/enhanced_screen_sensor.log"
echo "To stop the sensor:"
echo "kill \$(cat pids/enhanced_screen_sensor.pid 2>/dev/null)"