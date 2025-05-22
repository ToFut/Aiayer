#!/bin/bash
# Start the Total Screen Analyzer

# Create required directories
mkdir -p logs/sensors/total_screen
mkdir -p cache/total_screen_analyzer
mkdir -p pids

# Kill any existing screen sensor processes
echo "Stopping any running screen sensor processes..."
pids=$(ps aux | grep -i "screen_sensor.py\|enhanced_screen_sensor.py\|fixed_screen_sensor.py" | grep -v grep | awk '{print $2}')
if [ -n "$pids" ]; then
  echo "Killing processes: $pids"
  for pid in $pids; do
    kill -9 $pid 2>/dev/null || echo "Process $pid already gone"
  done
  echo "Screen sensor processes stopped"
else
  echo "No screen sensor processes found running"
fi

# Initialize analyzer cache with proper structure
echo "Initializing analyzer cache..."
timestamp=$(date +%Y%m%d_%H%M%S)
if [ -f "cache/total_screen_analyzer/analysis_cache.json" ] && [ -s "cache/total_screen_analyzer/analysis_cache.json" ]; then
  cp "cache/total_screen_analyzer/analysis_cache.json" "cache/total_screen_analyzer/analysis_cache.json.bak_${timestamp}"
fi

# Make the script executable
chmod +x sensors/total_screen_analyzer.py

echo "Starting Total Screen Analyzer..."
python3 sensors/total_screen_analyzer.py > logs/sensors/total_screen/total_screen_analyzer.log 2>&1 &
ANALYZER_PID=$!
echo $ANALYZER_PID > pids/total_screen_analyzer.pid
echo "Total Screen Analyzer started with PID $ANALYZER_PID"
echo "To check logs, use:"
echo "tail -f logs/sensors/total_screen/total_screen_analyzer.log"
echo "To stop the analyzer:"
echo "kill \$(cat pids/total_screen_analyzer.pid 2>/dev/null)"