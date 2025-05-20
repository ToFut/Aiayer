#!/bin/bash

# Monitor the agent-based system
while true; do
    echo "[2025-05-19 19:03:35] Checking system health..."
    
    # Check if server is running
    if [ -f "pids/agent_based_llm_ws.pid" ]; then
        SERVER_PID=$(cat pids/agent_based_llm_ws.pid)
        if ps -p $SERVER_PID > /dev/null; then
            echo "✅ Server is running (PID: $SERVER_PID)"
        else
            echo "❌ Server process not found despite PID file existing"
        fi
    else
        echo "❌ Server PID file not found"
    fi
    
    # Check if sensor connector is running
    if [ -f "pids/connect_sensors.pid" ]; then
        SENSOR_PID=$(cat pids/connect_sensors.pid)
        if ps -p $SENSOR_PID > /dev/null; then
            echo "✅ Sensor connector is running (PID: $SENSOR_PID)"
        else
            echo "❌ Sensor connector process not found despite PID file existing"
        fi
    else
        echo "❌ Sensor connector PID file not found"
    fi
    
    # Check memory usage
    MEM_USAGE=$(ps -o rss= -p $SERVER_PID | awk '{print $1/1024 " MB"}')
    echo "📊 Server memory usage: $MEM_USAGE"
    
    # Check for issues in logs
    ERROR_COUNT=$(grep -c "ERROR" logs/agent_based_llm_ws.log | tail -100)
    echo "📋 Recent errors in log: $ERROR_COUNT"
    
    echo "---------------------------------------------------"
    sleep 60
done
